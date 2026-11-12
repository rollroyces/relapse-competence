"""Detectors.

Two detectors, matched to the two clinical regimes.

``MrdThresholdDetector``
    Tumour-informed MRD. Flags when the *total* mutant read count across the
    tracked loci reaches a threshold. This is how real MRD assays work: the
    aggregate VAF threshold is a consequence of the read threshold, not an
    input.

``SequentialRiseDetector``
    Screening. A CUSUM over excess mutant reads, plus a streak bonus for
    consecutive signal-consistent elevations and a trend bonus for a rising
    slope. The background level is an *assay constant* (characterised once
    during validation), not estimated from the patient, because estimating it
    from a handful of ultra-low-count draws is itself a false-positive
    source.

    An earlier log-scale SPRT formulation was discarded: at 1-5 expected
    mutant reads per draw the log transform amplifies Poisson noise, and the
    healthy-arm false-positive rate reached 17%. A count-domain CUSUM does
    not have that failure mode.

    Both thresholds are calibrated on a held-out split, never on the split
    used to report performance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import DetectorConfig
from .simulator import Measurement

__all__ = [
    "DetectorResult",
    "ElectricalChannelDetector",
    "MrdThresholdDetector",
    "SequentialRiseDetector",
    "DEFAULT_CUSUM_THRESHOLDS",
]

#: Candidate CUSUM thresholds, searched in ascending order during calibration.
DEFAULT_CUSUM_THRESHOLDS: tuple[float, ...] = (
    1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 70.0, 100.0,
)


@dataclass
class DetectorResult:
    """Outcome of running a detector over one patient's trajectory."""

    flagged: bool
    flag_draw: int | None
    """Index of the draw at which the detector fired, if any."""

    flag_day: int | None
    scores: list[float] = field(default_factory=list)
    """Per-draw evidence score, for diagnostics."""


class MrdThresholdDetector:
    """Tumour-informed MRD detector: flag on total mutant read count."""

    def __init__(self, read_threshold: int = 3) -> None:
        if read_threshold < 1:
            raise ValueError("read_threshold must be >= 1")
        self.read_threshold = read_threshold

    def run(self, measurements: tuple[Measurement, ...] | list[Measurement]) -> DetectorResult:
        """Run over a trajectory.

        Draw 0 is the pre-treatment baseline and is never evaluated: the
        patient is known to be diseased at that point.
        """
        scores: list[float] = []
        for m in measurements[1:]:
            score = float(m.mutant_reads)
            scores.append(score)
            if score >= self.read_threshold:
                return DetectorResult(
                    flagged=True, flag_draw=m.draw_index, flag_day=m.day, scores=scores
                )
        return DetectorResult(flagged=False, flag_draw=None, flag_day=None, scores=scores)


class SequentialRiseDetector:
    """CUSUM detector for a rising tumour signal in the read-count domain."""

    def __init__(
        self,
        config: DetectorConfig | None = None,
        background_reads: float = 2.5,
        threshold: float | None = None,
    ) -> None:
        self.config = config or DetectorConfig()
        self.background_reads = max(float(background_reads), 0.05)
        """Expected background mutant reads per draw (an assay constant)."""

        self.threshold = float(threshold if threshold is not None else self.config.cusum_threshold)

    def run(self, measurements: tuple[Measurement, ...] | list[Measurement]) -> DetectorResult:
        cfg = self.config
        lam0 = self.background_reads
        c = 0.0
        streak = 0
        history: list[float] = []
        scores: list[float] = []

        for m in measurements:
            x = float(m.mutant_reads)
            excess = x - lam0

            # CUSUM over excess reads, reset at zero.
            c = max(0.0, c + excess - cfg.cusum_slack)

            # Streak: consecutive draws whose count is consistent with signal,
            # not merely larger than the previous draw.
            if x > lam0:
                streak += 1
            else:
                streak = 0

            # Trend: exponentially weighted slope of the excess history.
            history.append(excess)
            trend = max(0.0, _weighted_slope(history, cfg.learning_rate))

            score = c + cfg.streak_bonus_weight * streak + cfg.trend_bonus_weight * trend
            scores.append(score)

            if score >= self.threshold:
                return DetectorResult(
                    flagged=True, flag_draw=m.draw_index, flag_day=m.day, scores=scores
                )

        return DetectorResult(flagged=False, flag_draw=None, flag_day=None, scores=scores)


class ElectricalChannelDetector:
    """Detector for the bulk electrical (ion-channel locus) channel.

    Two quantities are produced, and the distinction between them is the
    whole point of the channel:

    ``raw_score``
        The largest number of electrical reads seen on any draw. This is a
        *burden* proxy as much as a state proxy: the marker is present in all
        tumour cells, so it scales with tumour volume.

    ``state_enrichment``
        The per-locus VAF ratio between the electrical channel and the
        mutation channel, maximised over draws. Dividing by the mutation
        channel's per-locus VAF cancels the shared burden, leaving only the
        marker enrichment contributed by the state-bearing fraction. **This is
        the quantity that carries state information independently of tumour
        amount**, and it is the one that decides whether the channel earns its
        read budget.
    """

    def __init__(self, read_threshold: int = 3) -> None:
        if read_threshold < 1:
            raise ValueError("read_threshold must be >= 1")
        self.read_threshold = read_threshold

    def run(self, measurements: tuple[Measurement, ...] | list[Measurement]) -> DetectorResult:
        """Flag on the electrical read count. Draw 0 is pre-treatment."""
        scores: list[float] = []
        for m in measurements[1:]:
            score = float(m.electrical_reads)
            scores.append(score)
            if score >= self.read_threshold:
                return DetectorResult(
                    flagged=True, flag_draw=m.draw_index, flag_day=m.day, scores=scores
                )
        return DetectorResult(flagged=False, flag_draw=None, flag_day=None, scores=scores)

    @staticmethod
    def raw_score(measurements: tuple[Measurement, ...] | list[Measurement]) -> float:
        """Largest electrical read count seen after the pre-treatment draw."""
        counts = [float(m.electrical_reads) for m in measurements[1:]]
        return max(counts) if counts else 0.0

    @staticmethod
    def state_enrichment(
        measurements: tuple[Measurement, ...] | list[Measurement],
    ) -> float:
        """Pooled per-locus VAF ratio, electrical channel over mutation channel.

        Reads are pooled across all post-baseline draws and the two channels'
        per-locus VAFs are divided. Because both channels scale with the same
        tumour burden, the ratio is burden-invariant: it isolates the marker
        enrichment contributed by the state-bearing fraction.

        Pooling rather than taking a per-draw maximum is deliberate. A
        per-draw ratio divides by a possibly tiny mutation read count, so a
        single noisy early draw can produce an arbitrarily large ratio; taking
        the maximum over draws then selects for whoever had the smallest
        denominator rather than the strongest state signal. The pooled form
        has far lower variance and is what the discriminant analysis uses.
        """
        mutation_reads = 0
        mutation_total = 0
        electrical_reads = 0
        electrical_total = 0
        for m in measurements[1:]:
            mutation_reads += m.mutant_reads
            mutation_total += m.total_reads
            electrical_reads += m.electrical_reads
            electrical_total += m.electrical_total_reads
        if mutation_total <= 0 or electrical_total <= 0:
            return 0.0
        mutation_vaf = mutation_reads / mutation_total
        electrical_vaf = electrical_reads / electrical_total
        if mutation_vaf <= 0.0:
            return 0.0
        return electrical_vaf / mutation_vaf

    @staticmethod
    def state_enrichment_attributable(
        measurements: tuple[Measurement, ...] | list[Measurement],
    ) -> float:
        """The enrichment with the leukocyte compartment removed.

        The raw enrichment divides the electrical channel's per-locus signal by
        the mutation channel's. The mutation channel is tumour-specific, but
        when the plasma cfDNA pool carries a leukocyte compartment the
        electrical channel's signal is the mixture of both compartments, so
        the raw ratio carries the leukocyte contribution divided by the
        tumour's own cfDNA share -- and that term is inversely related to
        tumour burden.

        Subtracting the leukocyte reads before the division leaves what the
        tumour contributed, which is what a readout that localises the channel
        transcript to the tumour would measure. With no leukocyte compartment
        this is identical to ``state_enrichment``.
        """
        mutation_reads = 0
        mutation_total = 0
        electrical_reads = 0
        electrical_total = 0
        leukocyte_reads = 0
        for m in measurements[1:]:
            mutation_reads += m.mutant_reads
            mutation_total += m.total_reads
            electrical_reads += m.electrical_reads
            electrical_total += m.electrical_total_reads
            leukocyte_reads += m.electrical_leukocyte_reads
        if mutation_total <= 0 or electrical_total <= 0:
            return 0.0
        mutation_vaf = mutation_reads / mutation_total
        attributable = max(0, electrical_reads - leukocyte_reads)
        electrical_vaf = attributable / electrical_total
        if mutation_vaf <= 0.0:
            return 0.0
        return electrical_vaf / mutation_vaf

    @staticmethod
    def state_enrichment_localised(
        measurements: tuple[Measurement, ...] | list[Measurement],
    ) -> float:
        """The enrichment with the channel's tumour-derived molecules counted.

        The statistic the assay specification defines: the numerator is the
        channel-transcript reads that carry an informative tumour signature,
        counted directly, and the denominator is the mutation channel's
        per-locus VAF.

        This is the same shape as ``state_enrichment`` with one change: the
        numerator is *counted* tumour-derived rather than *inferred* by
        subtraction, so the leukocyte compartment does not enter it at all.
        The noise is therefore proportional to the square root of the
        tumour's own share rather than to the whole pool, and the division by
        the mutation channel cancels it as it did in the published model.

        Returns 0.0 when the participant has no attributable reads, which is
        the case for every participant when the attribution model is off, and
        for a participant with no informative position when it is on.
        """
        mutation_reads = 0
        total_reads = 0
        attributed_reads = 0
        channel_total_reads = 0
        for m in measurements[1:]:
            mutation_reads += m.mutant_reads
            total_reads += m.total_reads
            attributed_reads += m.attributed_reads
            channel_total_reads += m.electrical_total_reads
        if total_reads <= 0 or mutation_reads <= 0 or channel_total_reads <= 0:
            return 0.0
        mutation_vaf = mutation_reads / total_reads
        if mutation_vaf <= 0.0:
            return 0.0
        channel_attributed_p = attributed_reads / channel_total_reads
        return channel_attributed_p / mutation_vaf

    @staticmethod
    def state_enrichment_localised_corrected(
        measurements: tuple[Measurement, ...] | list[Measurement],
        background_vaf: float = 0.0,
    ) -> float:
        """The localised enrichment with the error floor out of the denominator.

        The assay specification requires the denominator to be the
        participant's *tumour* cfDNA fraction, estimated from the somatic
        variants the mutation panel reads (section 4.2), rather than the raw
        observed per-locus VAF. The two differ by the panel's sequencing-error
        floor, and the difference matters: the floor sits in the denominator
        of both statistics, but only in the numerator of the published one.

        So the published statistic has the floor in numerator and denominator
        and the floor partly cancels, while the localised one has it in the
        denominator only. Removing it from the denominator is what makes the
        two comparable, and it is what the specification's own denominator
        requires.

        Returns 0.0 when the participant has no attributable reads or no
        measurable tumour share.
        """
        mutation_reads = 0
        total_reads = 0
        attributed_reads = 0
        channel_total_reads = 0
        for m in measurements[1:]:
            mutation_reads += m.mutant_reads
            total_reads += m.total_reads
            attributed_reads += m.attributed_reads
            channel_total_reads += m.electrical_total_reads
        if total_reads <= 0 or channel_total_reads <= 0:
            return 0.0
        observed_vaf = mutation_reads / total_reads
        tumour_share = max(0.0, observed_vaf - background_vaf)
        if tumour_share <= 0.0:
            return 0.0
        channel_attributed_p = attributed_reads / channel_total_reads
        return channel_attributed_p / tumour_share

    @staticmethod
    def state_enrichment_reference_corrected(
        measurements: tuple[Measurement, ...] | list[Measurement],
    ) -> float:
        """The enrichment with the background *estimated* from the reference loci.

        The leukocyte reference loci carry the leukocyte compartment's signal
        in the same library, so their reads estimate the background the
        electrical channel sits on. Subtracting that estimate leaves what the
        tumour contributed.

        The difference from ``state_enrichment_attributable`` is that the
        background is measured rather than known, and the measurement's own
        counting noise is amplified: the result is divided by the tumour's
        own cfDNA share, which is small, so an error in the background
        estimate is multiplied up. That is the price of measuring the
        background in the sample rather than subtracting it with foreknowledge.
        """
        mutation_reads = 0
        mutation_total = 0
        electrical_reads = 0
        electrical_total = 0
        reference_reads = 0
        reference_total = 0
        for m in measurements[1:]:
            mutation_reads += m.mutant_reads
            mutation_total += m.total_reads
            electrical_reads += m.electrical_reads
            electrical_total += m.electrical_total_reads
            reference_reads += m.leukocyte_reference_reads
            reference_total += m.leukocyte_reference_total_reads
        if mutation_total <= 0 or electrical_total <= 0:
            return 0.0
        mutation_vaf = mutation_reads / mutation_total
        if mutation_vaf <= 0.0:
            return 0.0
        attributable_reads = electrical_reads
        if reference_total > 0:
            background_fraction = reference_reads / reference_total
            attributable_reads = max(
                0, electrical_reads - background_fraction * electrical_total
            )
        return (attributable_reads / electrical_total) / mutation_vaf


def _weighted_slope(history: list[float], learning_rate: float) -> float:
    """Exponentially weighted slope of a series."""
    if len(history) < 2:
        return 0.0
    weights = [learning_rate ** (len(history) - 1 - i) for i in range(len(history))]
    total = sum(weights)
    if total <= 0.0:
        return 0.0
    mean_x = sum(w * i for i, w in enumerate(weights)) / total
    mean_y = sum(w * y for y, w in zip(history, weights, strict=False)) / total
    num = sum(w * (i - mean_x) * (y - mean_y) for i, (y, w) in enumerate(zip(history, weights, strict=False)))
    den = sum(w * (i - mean_x) ** 2 for i, w in enumerate(weights))
    if den <= 0.0:
        return 0.0
    return num / den
