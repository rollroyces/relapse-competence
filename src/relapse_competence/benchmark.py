"""Benchmark engine.

Honest-evaluation rules baked into the code, not left to the reader:

1. **The read threshold is chosen on a held-out calibration split.** Choosing
   ``k`` on the same patients used to report specificity would be optimistic.
   Calibration uses even-indexed responders; evaluation uses the odd-indexed
   ones plus all resistant patients.
2. **The threshold rule is stated in advance**: the smallest ``k`` whose
   calibration specificity meets the target. No per-configuration tuning.
3. **A flag that arrives at or after radiographic relapse is not a
   detection.** Such patients count as false negatives for the sensitivity
   figure and are reported separately as ``n_flagged_late``. The MRD test is
   only useful if it fires while the patient is still radiographically
   disease-free.
4. **Lead time is computed continuously**, not in draw intervals. A patient
   flagged at draw *k* with tumour burden *V* has lead time
   ``T * log2(relapse_threshold / V)`` under the exponential growth model, so
   the figure is not quantised to the 90-day sampling interval.
5. **Sensitivity is also reported inside clinical windows** (180 and 360 days
   after treatment). A flag at month 36 is not actionable.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, replace

from .config import DetectorConfig, PatientArm, Regime, SimulationConfig
from .detectors import (
    DEFAULT_CUSUM_THRESHOLDS,
    ElectricalChannelDetector,
    MrdThresholdDetector,
    SequentialRiseDetector,
)
from .simulator import LongitudinalSimulator, Measurement, PatientTrajectory

__all__ = [
    "MrdBenchmarkResult",
    "PatientOutcome",
    "collect_outcomes",
    "calibrate_electrical_cutoff",
    "run_channel_allocation_sweep",
    "run_mrd_benchmark",
    "run_depth_sweep",
    "run_screening_benchmark",
    "select_read_threshold",
    "calibrate_sequential_threshold",
    "calibrate_single_timepoint_vaf",
]


@dataclass(frozen=True)
class MrdBenchmarkResult:
    """Outcome of one MRD benchmark configuration."""

    sequencing_depth: int
    n_loci: int
    total_reads_per_draw: int
    """``depth * n_loci``. The dominant cost driver."""

    read_threshold: int
    target_specificity: float
    target_reached: bool
    """Whether any threshold met the specificity bar. If False, the reported
    specificity is below target and the configuration is not deployable."""

    sensitivity: float
    """Fraction of relapsing patients flagged *before* radiographic relapse."""

    specificity: float
    ppv: float
    sensitivity_within_180d: float
    sensitivity_within_360d: float

    n_resistant: int
    n_responder: int

    median_lead_time_days: float | None
    """Median days of detection before radiographic relapse, among patients
    flagged in time. ``None`` when nobody was flagged in time."""

    median_lead_time_among_all_resistant_days: float | None
    """Median lead time over *all* relapsing patients, treating a missed or
    late detection as zero lead time. This is the conservative figure."""

    n_flagged_before_relapse: int
    n_flagged_late: int

    nominal_vaf_threshold: float
    nominal_volume_threshold_mm3: float
    median_volume_at_flag_mm3: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "sequencing_depth": self.sequencing_depth,
            "n_loci": self.n_loci,
            "total_reads_per_draw": self.total_reads_per_draw,
            "read_threshold": self.read_threshold,
            "target_specificity": self.target_specificity,
            "target_reached": self.target_reached,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "ppv": self.ppv,
            "sensitivity_within_180d": self.sensitivity_within_180d,
            "sensitivity_within_360d": self.sensitivity_within_360d,
            "n_resistant": self.n_resistant,
            "n_responder": self.n_responder,
            "median_lead_time_days": self.median_lead_time_days,
            "median_lead_time_among_all_resistant_days": (
                self.median_lead_time_among_all_resistant_days
            ),
            "n_flagged_before_relapse": self.n_flagged_before_relapse,
            "n_flagged_late": self.n_flagged_late,
            "nominal_vaf_threshold": self.nominal_vaf_threshold,
            "nominal_volume_threshold_mm3": self.nominal_volume_threshold_mm3,
            "median_volume_at_flag_mm3": self.median_volume_at_flag_mm3,
        }


# ----------------------------------------------------------------------
# threshold selection
# ----------------------------------------------------------------------
def _specificity_at(responders: list[PatientTrajectory], k: int) -> float:
    detector = MrdThresholdDetector(read_threshold=k)
    if not responders:
        return 1.0
    negatives = sum(1 for r in responders if not detector.run(r.measurements).flagged)
    return negatives / len(responders)


def _max_threshold(config: SimulationConfig) -> int:
    """Largest read threshold worth searching.

    The background floor contributes ``background_vaf_mean * depth * n_loci``
    expected mutant reads per draw, so the useful threshold scales with it.
    """
    background_reads = config.background_vaf_mean * config.sequencing_depth * config.n_loci
    return max(60, int(background_reads * 6 + 25))


def select_read_threshold(
    calibration_responders: list[PatientTrajectory],
    target_specificity: float,
    max_k: int = 60,
) -> int | None:
    """Smallest ``k`` whose calibration specificity meets the target.

    Returns ``None`` if no ``k`` up to ``max_k`` reaches the target, which is
    itself a meaningful result: the configuration cannot hit the specificity
    bar at any usable read threshold.
    """
    for k in range(1, max_k + 1):
        if _specificity_at(calibration_responders, k) >= target_specificity:
            return k
    return None


# ----------------------------------------------------------------------
# screening threshold calibration
# ----------------------------------------------------------------------
def calibrate_sequential_threshold(
    healthy_calibration: list[PatientTrajectory],
    background_reads: float,
    detector_config: DetectorConfig | None = None,
    target_specificity: float = 0.98,
    thresholds: tuple[float, ...] = DEFAULT_CUSUM_THRESHOLDS,
) -> tuple[float, bool]:
    """Smallest CUSUM threshold meeting the patient-level specificity target.

    Returns ``(threshold, target_reached)``.
    """
    detector_config = detector_config or DetectorConfig()
    for h in thresholds:
        detector = SequentialRiseDetector(
            detector_config, background_reads=background_reads, threshold=h
        )
        if not healthy_calibration:
            return h, True
        negatives = sum(1 for p in healthy_calibration if not detector.run(p.measurements).flagged)
        if negatives / len(healthy_calibration) >= target_specificity:
            return h, True
    return thresholds[-1], False


def calibrate_single_timepoint_vaf(
    healthy_calibration: list[PatientTrajectory],
    background_vaf: float,
    target_specificity: float = 0.98,
    multipliers: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0, 48.0, 64.0),
) -> tuple[float, bool]:
    """Smallest single-timepoint VAF threshold meeting the specificity target.

    Returns ``(vaf_threshold, target_reached)``.
    """
    if not healthy_calibration:
        return background_vaf, True
    for mult in multipliers:
        threshold = background_vaf * mult
        fp = sum(
            1 for p in healthy_calibration if p.measurements[-1].observed_vaf >= threshold
        )
        if fp / len(healthy_calibration) <= (1.0 - target_specificity):
            return threshold, True
    return background_vaf * multipliers[-1], False


# ----------------------------------------------------------------------
# MRD benchmark
# ----------------------------------------------------------------------
def _continuous_lead_time_days(
    volume_at_flag: float,
    relapse_threshold_mm3: float,
    doubling_time_days: float,
) -> float:
    """Days between detection at ``volume_at_flag`` and radiographic relapse.

    Under the exponential growth model, ``lead = T * log2(V_relapse / V_flag)``.
    A non-positive value means the flag arrived at or after relapse.
    """
    if volume_at_flag <= 0.0:
        return float("-inf")
    ratio = relapse_threshold_mm3 / volume_at_flag
    if ratio <= 0.0:
        return float("-inf")
    return doubling_time_days * math.log2(ratio)


def run_mrd_benchmark(
    config: SimulationConfig,
    detector_config: DetectorConfig | None = None,
    target_specificity: float = 0.98,
) -> MrdBenchmarkResult:
    """Run the post-treatment MRD benchmark for one configuration."""
    cfg = config
    if cfg.regime is not Regime.POST_TREATMENT:
        raise ValueError("run_mrd_benchmark requires the POST_TREATMENT regime")

    detector_config = detector_config or DetectorConfig()
    simulator = LongitudinalSimulator(cfg)
    cohort = simulator.generate_cohort()

    responders = cohort[PatientArm.RESPONDER]
    resistant = cohort[PatientArm.RESISTANT]

    calibration = responders[0::2]
    evaluation = responders[1::2]

    search_max = _max_threshold(cfg)
    k = select_read_threshold(calibration, target_specificity, max_k=search_max)
    target_reached = k is not None
    if k is None:
        # No threshold reaches the specificity bar. Use the most conservative
        # threshold available; the reported specificity will show that the
        # configuration is not deployable.
        k = search_max

    detector = MrdThresholdDetector(read_threshold=k)

    # --- evaluation over resistant patients ---
    tp = 0
    tp_180 = 0
    tp_360 = 0
    flagged_late = 0
    lead_times: list[float] = []
    lead_times_all: list[float] = []
    volumes_at_flag: list[float] = []

    for patient in resistant:
        result = detector.run(patient.measurements)
        if not result.flagged:
            lead_times_all.append(0.0)
            continue
        assert result.flag_draw is not None
        volume = patient.measurements[result.flag_draw].tumour_volume_mm3
        volumes_at_flag.append(volume)
        lead = _continuous_lead_time_days(
            volume, cfg.relapse_volume_threshold_mm3, patient.doubling_time_days
        )
        if lead <= 0.0:
            flagged_late += 1
            lead_times_all.append(0.0)
            continue
        tp += 1
        lead_times.append(lead)
        lead_times_all.append(lead)
        if patient.measurements[result.flag_draw].day <= 180:
            tp_180 += 1
        if patient.measurements[result.flag_draw].day <= 360:
            tp_360 += 1

    n_resistant = len(resistant)
    fp = sum(1 for r in evaluation if detector.run(r.measurements).flagged)
    tn = len(evaluation) - fp

    sensitivity = tp / n_resistant if n_resistant else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 1.0
    ppv = tp / (tp + fp) if (tp + fp) else 0.0

    nominal_vaf = k / (cfg.sequencing_depth * cfg.n_loci)
    nominal_volume = nominal_vaf / cfg.tumor_vaf_per_mm3

    return MrdBenchmarkResult(
        sequencing_depth=cfg.sequencing_depth,
        n_loci=cfg.n_loci,
        total_reads_per_draw=cfg.sequencing_depth * cfg.n_loci,
        read_threshold=k,
        target_specificity=target_specificity,
        target_reached=target_reached,
        sensitivity=sensitivity,
        specificity=specificity,
        ppv=ppv,
        sensitivity_within_180d=tp_180 / n_resistant if n_resistant else 0.0,
        sensitivity_within_360d=tp_360 / n_resistant if n_resistant else 0.0,
        n_resistant=n_resistant,
        n_responder=len(evaluation),
        median_lead_time_days=statistics.median(lead_times) if lead_times else None,
        median_lead_time_among_all_resistant_days=(
            statistics.median(lead_times_all) if lead_times_all else None
        ),
        n_flagged_before_relapse=tp,
        n_flagged_late=flagged_late,
        nominal_vaf_threshold=nominal_vaf,
        nominal_volume_threshold_mm3=nominal_volume,
        median_volume_at_flag_mm3=(
            statistics.median(volumes_at_flag) if volumes_at_flag else None
        ),
    )


def run_depth_sweep(
    base_config: SimulationConfig,
    depths: tuple[int, ...] = (5_000, 50_000, 200_000, 500_000),
    locus_counts: tuple[int, ...] = (50, 200),
    detector_config: DetectorConfig | None = None,
    target_specificity: float = 0.98,
) -> list[MrdBenchmarkResult]:
    """Benchmark a grid of (depth x loci) configurations.

    The answer this produces is the actionable one: what depth and panel size
    are required to reach a given lead time.
    """
    results: list[MrdBenchmarkResult] = []
    for depth in depths:
        for n_loci in locus_counts:
            cfg = replace(base_config, sequencing_depth=depth, n_loci=n_loci)
            results.append(
                run_mrd_benchmark(
                    cfg,
                    detector_config=detector_config,
                    target_specificity=target_specificity,
                )
            )
    return results


# ----------------------------------------------------------------------
# screening benchmark
# ----------------------------------------------------------------------
def run_screening_benchmark(
    config: SimulationConfig,
    detector_config: DetectorConfig | None = None,
    target_specificity: float = 0.98,
) -> dict[str, object]:
    """Compare the sequential rise detector against a single-timepoint threshold.

    Secondary to the MRD benchmark, but it answers the question the sequencing
    literature keeps asking: does a trajectory beat a snapshot?

    Both detectors are calibrated on the same held-out split of healthy
    patients, at the same specificity target, and are then evaluated on the
    complementary split. Neither is allowed a specificity advantage the other
    does not have.
    """
    cfg = config
    if cfg.regime is not Regime.SCREENING:
        raise ValueError("run_screening_benchmark requires the SCREENING regime")

    detector_config = detector_config or DetectorConfig()
    simulator = LongitudinalSimulator(cfg)
    cohort = simulator.generate_cohort()

    healthy = cohort[PatientArm.HEALTHY]
    cancer = cohort[PatientArm.CANCER]

    healthy_calibration = healthy[0::2]
    healthy_evaluation = healthy[1::2]

    background_reads = cfg.background_vaf_mean * cfg.sequencing_depth * cfg.n_loci
    background_vaf = cfg.background_vaf_mean

    cusum_threshold, cusum_reached = calibrate_sequential_threshold(
        healthy_calibration,
        background_reads=background_reads,
        detector_config=detector_config,
        target_specificity=target_specificity,
    )
    single_threshold, single_reached = calibrate_single_timepoint_vaf(
        healthy_calibration,
        background_vaf=background_vaf,
        target_specificity=target_specificity,
    )

    seq = SequentialRiseDetector(
        detector_config, background_reads=background_reads, threshold=cusum_threshold
    )

    tp = fn = fp = tn = 0
    detection_volumes: list[float] = []

    for patient in cancer:
        result = seq.run(patient.measurements)
        if result.flagged:
            tp += 1
            assert result.flag_draw is not None
            detection_volumes.append(patient.measurements[result.flag_draw].tumour_volume_mm3)
        else:
            fn += 1

    for patient in healthy_evaluation:
        if seq.run(patient.measurements).flagged:
            fp += 1
        else:
            tn += 1

    st_tp = sum(1 for p in cancer if p.measurements[-1].observed_vaf >= single_threshold)
    st_fp = sum(
        1 for p in healthy_evaluation if p.measurements[-1].observed_vaf >= single_threshold
    )

    return {
        "calibration": {
            "target_specificity": target_specificity,
            "n_healthy_calibration": len(healthy_calibration),
            "n_healthy_evaluation": len(healthy_evaluation),
            "background_reads_per_draw": background_reads,
            "cusum_threshold": cusum_threshold,
            "cusum_target_reached": cusum_reached,
            "single_timepoint_vaf_threshold": single_threshold,
            "single_timepoint_target_reached": single_reached,
        },
        "sequential": {
            "sensitivity": tp / (tp + fn) if (tp + fn) else 0.0,
            "specificity": tn / (tn + fp) if (tn + fp) else 1.0,
            "n_true_positive": tp,
            "n_false_negative": fn,
            "n_false_positive": fp,
            "n_true_negative": tn,
            "median_volume_at_detection_mm3": (
                statistics.median(detection_volumes) if detection_volumes else None
            ),
        },
        "single_timepoint_at_final_draw": {
            "vaf_threshold": single_threshold,
            "sensitivity": st_tp / len(cancer) if cancer else 0.0,
            "false_positive_rate": st_fp / len(healthy_evaluation) if healthy_evaluation else 0.0,
        },
    }


# =======================================================================
# Channel allocation sweep
# =======================================================================
@dataclass(frozen=True)
class PatientOutcome:
    """Per-patient outcome used by the channel allocation analysis."""

    patient_id: str
    arm: PatientArm
    relapsed: bool
    mrd_flagged: bool
    mrd_flag_draw: int | None
    lead_days: float | None
    """Days of MRD lead before radiographic relapse. None when not flagged
    in time, or when the patient did not relapse."""

    electrical_raw: float
    """Largest electrical read count across draws (burden proxy)."""

    electrical_enrichment: float
    """Per-locus VAF ratio, electrical over mutation, maximised over draws.

    The burden cancels in this ratio, so what remains is the marker
    enrichment contributed by the state-bearing fraction.
    """

    state_fraction: float
    split: str
    """``calibration`` or ``evaluation``."""

    electrical_enrichment_attributable: float = 0.0
    """The same ratio with the leukocyte compartment removed.

    Equal to ``electrical_enrichment`` when the model has no leukocyte
    compartment, which is the default.
    """

    electrical_enrichment_reference_corrected: float = 0.0
    """The enrichment with the background estimated from the reference loci.

    Equal to ``electrical_enrichment`` when the model has no leukocyte
    compartment and no reference set, which is the default.
    """

    mutation_vaf: float = 0.0
    """The mutation channel's pooled per-locus VAF.

    This is the tumour's share of the cfDNA pool, with the sequencing-error
    floor in it, so it is what the electrical channel has to be read against.
    """


def _auc(scores: list[float], labels: list[bool]) -> float:
    """Tie-corrected Mann-Whitney AUC. Pure numpy, no sklearn dependency."""
    positives = sum(1 for x in labels if x)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return float("nan")
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    rank_sum = sum(r for r, lab in zip(ranks, labels, strict=False) if lab)
    u = rank_sum - positives * (positives + 1) / 2.0
    return u / (positives * negatives)


def _pooled_mutation_vaf(
    measurements: tuple[Measurement, ...] | list[Measurement],
) -> float:
    """The mutation channel's pooled per-locus VAF over the post-baseline draws."""
    mutant_reads = 0
    total_reads = 0
    for m in measurements[1:]:
        mutant_reads += m.mutant_reads
        total_reads += m.total_reads
    return (mutant_reads / total_reads) if total_reads else 0.0


def collect_outcomes(
    config: SimulationConfig,
    target_specificity: float = 0.98,
    read_threshold: int | None = None,
) -> tuple[list[PatientOutcome], int]:
    """Run the mutation channel over a cohort and collect per-patient outcomes.

    The mutation read threshold is calibrated on the even-indexed responders
    (the false-positive population) and applied to everyone. Each arm is split
    by index parity, so both the calibration and the evaluation halves stay
    arm-balanced.

    Passing ``read_threshold`` applies that threshold instead of calibrating
    one, which is what the split-model validation needs: a detector fitted on
    one model has to be applied to another without being refitted.
    """
    cfg = config
    simulator = LongitudinalSimulator(cfg)
    cohort = simulator.generate_cohort()

    responders = cohort[PatientArm.RESPONDER]
    calibration_responders = responders[0::2]
    if read_threshold is None:
        k = select_read_threshold(
            calibration_responders, target_specificity, max_k=_max_threshold(cfg)
        )
        if k is None:
            k = _max_threshold(cfg)
    else:
        k = read_threshold
    detector = MrdThresholdDetector(read_threshold=k)

    outcomes: list[PatientOutcome] = []
    for arm, patients in cohort.items():
        for index, patient in enumerate(patients):
            result = detector.run(patient.measurements)
            relapsed = patient.relapse_draw is not None
            lead: float | None = None
            # A flag that arrives at or after radiographic relapse is not a
            # detection. This matches the definition used by the headline MRD
            # benchmark, so the two stay comparable.
            flagged_in_time = bool(result.flagged) and (
                not relapsed
                or (result.flag_draw is not None and result.flag_draw < patient.relapse_draw)
            )
            if relapsed and flagged_in_time and result.flag_draw is not None:
                # Continuous lead time, identical to the headline benchmark:
                # T * log2(V_relapse / V_at_flag). Using the same definition
                # keeps the two analyses directly comparable.
                lead = _continuous_lead_time_days(
                    patient.measurements[result.flag_draw].tumour_volume_mm3,
                    cfg.relapse_volume_threshold_mm3,
                    patient.doubling_time_days,
                )
            outcomes.append(
                PatientOutcome(
                    patient_id=patient.patient_id,
                    arm=arm,
                    relapsed=relapsed,
                    mrd_flagged=flagged_in_time,
                    mrd_flag_draw=result.flag_draw,
                    lead_days=lead,
                    electrical_raw=ElectricalChannelDetector.raw_score(patient.measurements),
                    electrical_enrichment=ElectricalChannelDetector.state_enrichment(
                        patient.measurements
                    ),
                    electrical_enrichment_attributable=(
                        ElectricalChannelDetector.state_enrichment_attributable(
                            patient.measurements
                        )
                    ),
                    electrical_enrichment_reference_corrected=(
                        ElectricalChannelDetector.state_enrichment_reference_corrected(
                            patient.measurements
                        )
                    ),
                    mutation_vaf=_pooled_mutation_vaf(patient.measurements),
                    state_fraction=patient.state_fraction,
                    split="calibration" if index % 2 == 0 else "evaluation",
                )
            )
    return outcomes, k


def calibrate_electrical_cutoff(
    mrd_positive: list[PatientOutcome],
    target_retained_sensitivity: float = 0.90,
) -> float:
    """Choose the electrical read-count cutoff that retains relapsers.

    The operating point is defined *within the MRD-positive population*: the
    cutoff is set to keep at least ``target_retained_sensitivity`` of the
    relapsing MRD-positive patients, which is the decision rule a clinician
    would actually apply -- "MRD positive, and this looks like the
    relapse-competent state".
    """
    relapsers = sorted(o.electrical_raw for o in mrd_positive if o.relapsed)
    if not relapsers:
        return float("inf")
    keep = max(1, int(round(len(relapsers) * target_retained_sensitivity)))
    # Cutoff = the value of the keep-th lowest relapser score.
    return relapsers[keep - 1]


def run_channel_allocation_sweep(
    base_config: SimulationConfig,
    total_loci: tuple[int, ...] = (50, 200),
    depth: int = 50_000,
    electrical_fractions: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0),
    target_specificity: float = 0.98,
    target_retained_sensitivity: float = 0.90,
    n_leukocyte_reference_loci: int = 0,
) -> list[dict[str, object]]:
    """Sweep how a fixed read budget is split between the two channels.

    The budget is fixed: ``depth * total_loci`` reads per draw. The split
    decides how many loci go to the mutation panel and how many to the bulk
    ion-channel panel.

    This is the decision the gap audit leaves open: an MRD-positive result is
    not the same as a relapse, and the question is whether a bulk electrical
    signature can separate the two -- and whether it can do so without taking
    reads away from the mutation channel.
    """
    rows: list[dict[str, object]] = []
    for loci in total_loci:
        for fraction in electrical_fractions:
            n_electrical = int(round(loci * fraction))
            n_mutation = loci - n_electrical - n_leukocyte_reference_loci
            cfg = replace(
                base_config,
                regime=Regime.POST_TREATMENT,
                sequencing_depth=depth,
                n_loci=n_mutation,
                n_electrical_loci=n_electrical,
                n_leukocyte_reference_loci=n_leukocyte_reference_loci,
            )
            outcomes, k = collect_outcomes(cfg, target_specificity=target_specificity)

            evaluation = [o for o in outcomes if o.split == "evaluation"]
            calibration = [o for o in outcomes if o.split == "calibration"]

            relapsers = [o for o in evaluation if o.relapsed]
            non_relapsed = [o for o in evaluation if not o.relapsed]
            mrd_sensitivity = (
                sum(1 for o in relapsers if o.mrd_flagged) / len(relapsers) if relapsers else 0.0
            )
            mrd_specificity = (
                sum(1 for o in non_relapsed if not o.mrd_flagged) / len(non_relapsed)
                if non_relapsed
                else 1.0
            )
            leads = [o.lead_days for o in relapsers if o.lead_days is not None]
            median_lead = statistics.median(leads) if leads else None

            mrd_positive_eval = [o for o in evaluation if o.mrd_flagged]
            mrd_positive_cal = [o for o in calibration if o.mrd_flagged]

            ppv = (
                sum(1 for o in mrd_positive_eval if o.relapsed) / len(mrd_positive_eval)
                if mrd_positive_eval
                else float("nan")
            )

            cutoff = calibrate_electrical_cutoff(
                mrd_positive_cal, target_retained_sensitivity=target_retained_sensitivity
            )
            refined = [o for o in mrd_positive_eval if o.electrical_raw >= cutoff]
            ppv_refined = (
                sum(1 for o in refined if o.relapsed) / len(refined) if refined else float("nan")
            )
            retained = (
                sum(1 for o in refined if o.relapsed) / len(relapsers) if relapsers else 0.0
            )

            auc_raw = _auc(
                [o.electrical_raw for o in mrd_positive_eval],
                [o.relapsed for o in mrd_positive_eval],
            )
            auc_enrichment = _auc(
                [o.electrical_enrichment for o in mrd_positive_eval],
                [o.relapsed for o in mrd_positive_eval],
            )

            degenerate = n_mutation == 0
            def _specificity_for(
                arm_name: str, population: list[PatientOutcome] = non_relapsed
            ) -> float:
                subset = [o for o in population if o.arm.value == arm_name]
                if not subset:
                    return float("nan")
                return sum(1 for o in subset if not o.mrd_flagged) / len(subset)

            persistent_share = (
                sum(1 for o in mrd_positive_eval if o.arm is PatientArm.PERSISTENT)
                / len(mrd_positive_eval)
                if mrd_positive_eval
                else float("nan")
            )

            rows.append(
                {
                    "degenerate": degenerate,
                    "mrd_specificity_vs_responders": _specificity_for("responder"),
                    "mrd_specificity_vs_persistent": _specificity_for("persistent"),
                    "persistent_share_of_mrd_positive": persistent_share,
                    "degenerate_reason": (
                        "no mutation loci: the read budget is entirely spent on the "
                        "electrical channel, so there is no MRD assay to refine"
                        if degenerate
                        else ""
                    ),
                    "total_loci": loci,
                    "depth": depth,
                    "electrical_fraction": fraction,
                    "n_mutation_loci": n_mutation,
                    "n_electrical_loci": n_electrical,
                    "total_reads_per_draw": depth * loci,
                    "n_leukocyte_reference_loci": n_leukocyte_reference_loci,
                    "mutation_read_threshold": k,
                    "mrd_sensitivity": mrd_sensitivity,
                    "mrd_specificity": mrd_specificity,
                    "median_lead_time_days": median_lead,
                    "n_mrd_positive_evaluation": len(mrd_positive_eval),
                    "ppv_within_mrd_positive": ppv,
                    "electrical_cutoff": cutoff,
                    "ppv_after_electrical_refinement": ppv_refined,
                    "relapse_fraction_retained_by_refinement": retained,
                    "auc_electrical_raw_within_mrd_positive": auc_raw,
                    "auc_electrical_enrichment_within_mrd_positive": auc_enrichment,
                }
            )
    return rows
