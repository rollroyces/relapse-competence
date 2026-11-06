"""Ground-truth generation.

Design notes
------------
**Multi-locus read counting.** Real tumour-informed MRD panels track tens to
hundreds of somatic loci and flag on the *total* mutant read count across
them. Modelling a single locus understates sensitivity by roughly an order of
magnitude and would make any comparison to published MRD assays meaningless.

**The Poisson floor is reproduced, not assumed away.** Mutant reads are drawn
from a Poisson distribution, so a 6e-6 VAF at 50,000x really is near
unobservable at one locus. That is the reason multi-locus counting exists.

**Depth is assumed saturated.** Panel depth is fixed per draw. cfDNA
concentration is tracked for context but does not modulate depth.

**The bulk electrical channel is a bulk feature, and that matters.** The
ion-channel / methylation signature is present in *all* tumour cells, so its
per-locus signal is not diluted by clonality the way a subclonal mutation is.
But the relapse-competent *state* is a minority subpopulation, so the state
information the channel carries is diluted by ``state_fraction``. That tension
-- earlier detection, weaker discrimination -- is the thing the channel
allocation sweep is built to measure.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from typing import Final

import numpy as np

from .config import PatientArm, Regime, SimulationConfig

__all__ = [
    "Measurement",
    "PatientTrajectory",
    "LongitudinalSimulator",
    "SIMULATION_REGIMES",
]


@dataclass(frozen=True)
class Measurement:
    """One blood draw from one patient."""

    draw_index: int
    day: int
    mutant_reads: int
    """Total mutant reads across the tracked mutation loci."""

    total_reads: int
    """``depth * n_loci``."""

    genome_equivalents: int
    """cfDNA input molecules drawn for this sample.

    Recorded as assay context. Depth is assumed saturated, so this does not
    scale the read count -- but a real assay that cannot saturate would, and
    the field makes that assumption inspectable rather than implicit.
    """

    observed_vaf: float
    """``mutant_reads / total_reads``. This is the aggregate tumour VAF."""

    true_vaf: float
    """Tumour-derived VAF, excluding the background floor."""

    tumour_volume_mm3: float
    is_relapse_draw: bool
    has_chip: bool
    background_vaf: float

    # --- bulk electrical channel ---
    electrical_reads: int = 0
    """Reads across the ion-channel loci. Zero when the channel is disabled."""

    electrical_total_reads: int = 0
    """``depth * n_electrical_loci``."""

    state_fraction: float = 0.0
    """Fraction of this patient's tumour that is relapse-competent.

    The ground-truth latent state. No channel observes it directly; the
    electrical channel sees only its diluted effect on bulk marker abundance.
    """


@dataclass(frozen=True)
class PatientTrajectory:
    """One simulated patient."""

    patient_id: str
    arm: PatientArm
    measurements: tuple[Measurement, ...]
    relapse_draw: int | None
    """Index of the first draw at or above the radiographic threshold."""

    residual_volume_mm3: float
    doubling_time_days: float
    has_chip: bool
    state_fraction: float


#: Which arms are simulated in which regime.
SIMULATION_REGIMES: Final[dict[Regime, tuple[PatientArm, ...]]] = {
    Regime.SCREENING: (PatientArm.HEALTHY, PatientArm.CANCER),
    Regime.POST_TREATMENT: (
        PatientArm.RESPONDER,
        PatientArm.PERSISTENT,
        PatientArm.RESISTANT,
    ),
}


class LongitudinalSimulator:
    """Generates ground-truth trajectories for a given configuration."""

    #: Arms whose patients are generated from a derived stream rather than
    #: the shared one, so that adding an arm cannot shift the numbers already
    #: published for the existing arms.
    SIDE_STREAM_ARMS: Final = frozenset({PatientArm.PERSISTENT})

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self._rng = np.random.default_rng(config.seed)
        self._state_rngs: dict[PatientArm, np.random.Generator] = {}

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def generate_cohort(self) -> dict[PatientArm, list[PatientTrajectory]]:
        """Generate one cohort per arm defined for the configured regime."""
        arms = SIMULATION_REGIMES[self.config.regime]
        return {arm: self._generate_arm(arm) for arm in arms}

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _arm_rng(self, arm: PatientArm):
        """RNG for an arm's patients.

        The shared stream is used for the arms that existed before the
        electrical channel was added, so that extending the model does not
        silently change already-published results.
        """
        if arm in self.SIDE_STREAM_ARMS:
            return np.random.default_rng([self.config.seed, zlib.crc32(arm.value.encode())])
        return self._rng

    def _state_rng(self, arm: PatientArm):
        """RNG for the latent state-fraction draw.

        Kept separate from every patient-level stream: the state fraction is
        a property of the biology, and drawing it must not perturb the
        volumes, shedding or read counts that earlier runs already fixed.
        """
        if arm not in self._state_rngs:
            self._state_rngs[arm] = np.random.default_rng(
                [self.config.seed, zlib.crc32(arm.value.encode()), 7]
            )
        return self._state_rngs[arm]

    def _generate_arm(self, arm: PatientArm) -> list[PatientTrajectory]:
        cfg = self.config
        rng = self._arm_rng(arm)
        saved = self._rng
        self._rng = rng
        try:
            return [self._generate_patient(arm, i) for i in range(cfg.n_patients_per_arm)]
        finally:
            self._rng = saved

    def _generate_patient(self, arm: PatientArm, index: int) -> PatientTrajectory:
        cfg = self.config
        rng = self._rng

        doubling = cfg.doubling_time_days * float(np.exp(rng.normal(0.0, cfg.doubling_time_cv)))
        shedding = float(np.exp(rng.normal(0.0, cfg.shedding_cv)))
        has_chip = bool(rng.random() < cfg.chip_prevalence) and not cfg.chip_filtered

        if cfg.regime is Regime.SCREENING:
            baseline = 0.0
            if arm is PatientArm.CANCER:
                baseline = float(np.exp(rng.normal(np.log(cfg.screening_baseline_mm3), 0.9)))
            residual = 0.0
            resistant_doubling = doubling
            state_fraction = 0.0
        else:
            # Draw order and count here are identical to the pre-refactor
            # model, so the volumes, shedding and read counts of the
            # RESPONDER and RESISTANT arms are bit-identical to earlier runs.
            baseline = float(
                np.exp(rng.normal(np.log(cfg.baseline_volume_mm3), cfg.baseline_volume_cv))
            )
            residual = float(
                np.clip(rng.normal(cfg.residual_fraction, cfg.residual_fraction_sd), 1e-4, 0.6)
            )
            resistant_doubling = cfg.resistant_doubling_time_days * float(
                np.exp(rng.normal(0.0, cfg.doubling_time_cv))
            )
            if arm is PatientArm.RESPONDER:
                # No residual clone at all.
                residual = 0.0
                state_fraction = cfg.state_fraction_responder
            else:
                if arm is PatientArm.PERSISTENT:
                    # Persists, but too slowly to cross the relapse threshold
                    # inside the observation window.
                    resistant_doubling = 900.0 * float(
                        np.exp(rng.normal(0.0, cfg.doubling_time_cv))
                    )
                # The state fraction is drawn from its own stream, so it never
                # perturbs the patient-level draws above.
                state_rng = self._state_rng(arm)
                if arm is PatientArm.PERSISTENT:
                    state_fraction = float(
                        np.clip(
                            state_rng.normal(
                                cfg.state_fraction_persistent,
                                cfg.state_fraction_persistent_sd,
                            ),
                            0.0,
                            1.0,
                        )
                    )
                else:
                    state_fraction = float(
                        np.clip(
                            state_rng.normal(
                                cfg.state_fraction_resistant,
                                cfg.state_fraction_resistant_sd,
                            ),
                            0.0,
                            1.0,
                        )
                    )

        volumes = self._volumes(arm, baseline, residual, doubling, resistant_doubling)
        relapse_draw = self._relapse_draw(volumes)

        measurements = tuple(
            self._measure(draw_index, volume, shedding, has_chip, state_fraction)
            for draw_index, volume in enumerate(volumes)
        )

        return PatientTrajectory(
            patient_id=f"{arm.value}-{index:05d}",
            arm=arm,
            measurements=measurements,
            relapse_draw=relapse_draw,
            residual_volume_mm3=baseline * residual if residual else 0.0,
            doubling_time_days=(
                resistant_doubling if cfg.regime is Regime.POST_TREATMENT else doubling
            ),
            has_chip=has_chip,
            state_fraction=state_fraction,
        )

    def _volumes(
        self,
        arm: PatientArm,
        baseline: float,
        residual: float,
        doubling: float,
        resistant_doubling: float,
    ) -> list[float]:
        cfg = self.config
        volumes: list[float] = []
        for draw_index in range(cfg.n_draws):
            day = draw_index * cfg.sampling_interval_days
            if cfg.regime is Regime.SCREENING:
                if arm is PatientArm.HEALTHY:
                    volumes.append(0.0)
                else:
                    volumes.append(
                        min(
                            baseline * (2.0 ** (day / doubling)),
                            cfg.max_tumour_volume_mm3,
                        )
                    )
                continue

            if draw_index == 0:
                volumes.append(baseline)
            elif arm is PatientArm.RESPONDER:
                volumes.append(0.0)
            else:
                residual_volume = baseline * residual
                elapsed = day - cfg.sampling_interval_days
                volumes.append(
                    min(
                        residual_volume * (2.0 ** (elapsed / resistant_doubling)),
                        cfg.max_tumour_volume_mm3,
                    )
                )
        return volumes

    def _relapse_draw(self, volumes: list[float]) -> int | None:
        """First draw at or above the radiographic threshold.

        In the post-treatment regime the scan starts at draw 1. Draw 0 is the
        pre-treatment baseline, where the patient is known to have disease;
        counting it as a relapse would make every treated patient look like
        they relapsed on day zero.
        """
        threshold = self.config.relapse_volume_threshold_mm3
        start = 1 if self.config.regime is Regime.POST_TREATMENT else 0
        for i in range(start, len(volumes)):
            if volumes[i] >= threshold:
                return i
        return None

    def _measure(
        self,
        draw_index: int,
        volume: float,
        shedding: float,
        has_chip: bool,
        state_fraction: float,
    ) -> Measurement:
        cfg = self.config
        rng = self._rng

        # cfDNA input, recorded as assay context (depth is assumed saturated).
        ge_per_ml = cfg.genome_equivalents_per_ml * float(np.exp(rng.normal(0.0, cfg.ge_cv)))
        ge_total = max(1, int(rng.poisson(ge_per_ml * 10.0)))

        background = max(0.0, float(rng.normal(cfg.background_vaf_mean, cfg.background_vaf_sd)))
        if has_chip:
            background = max(background, cfg.chip_vaf)

        # --- mutation channel ---
        # A per-locus variant fraction cannot exceed 1. The carrying capacity
        # already keeps this physical, but clamp defensively so no parameter
        # combination can produce an impossible sample.
        true_vaf = min(
            cfg.tumor_vaf_per_mm3 * volume * shedding * cfg.mutation_clonal_fraction, 1.0
        )
        total_vaf = true_vaf + background
        mutant_reads = int(rng.poisson(cfg.sequencing_depth * cfg.n_loci * total_vaf))
        total_reads = cfg.sequencing_depth * cfg.n_loci

        # --- bulk electrical channel ---
        electrical_reads = 0
        electrical_total_reads = 0
        if cfg.n_electrical_loci > 0:
            # Bulk feature: present in all tumour cells, so its per-locus signal
            # is not reduced by clonality. The state boosts it in the
            # state-bearing fraction only, which is where the dilution lives.
            electrical_vaf = min(
                cfg.tumor_vaf_per_mm3
                * volume
                * shedding
                * (1.0 + cfg.electrical_fold_change * state_fraction),
                1.0,
            )
            electrical_total_vaf = electrical_vaf + background
            electrical_reads = int(
                rng.poisson(cfg.sequencing_depth * cfg.n_electrical_loci * electrical_total_vaf)
            )
            electrical_total_reads = cfg.sequencing_depth * cfg.n_electrical_loci

        day = draw_index * cfg.sampling_interval_days
        is_relapse = volume >= cfg.relapse_volume_threshold_mm3

        return Measurement(
            draw_index=draw_index,
            day=day,
            mutant_reads=mutant_reads,
            total_reads=total_reads,
            genome_equivalents=ge_total,
            observed_vaf=(mutant_reads / total_reads) if total_reads else 0.0,
            true_vaf=true_vaf,
            tumour_volume_mm3=volume,
            is_relapse_draw=is_relapse,
            has_chip=has_chip,
            background_vaf=background,
            electrical_reads=electrical_reads,
            electrical_total_reads=electrical_total_reads,
            state_fraction=state_fraction,
        )
