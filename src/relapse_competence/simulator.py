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
"""

from __future__ import annotations

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
    """Total mutant reads across the tracked loci."""

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


#: Which arms are simulated in which regime.
SIMULATION_REGIMES: Final[dict[Regime, tuple[PatientArm, ...]]] = {
    Regime.SCREENING: (PatientArm.HEALTHY, PatientArm.CANCER),
    Regime.POST_TREATMENT: (PatientArm.RESPONDER, PatientArm.RESISTANT),
}


class LongitudinalSimulator:
    """Generates ground-truth trajectories for a given configuration."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self._rng = np.random.default_rng(config.seed)

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
    def _generate_arm(self, arm: PatientArm) -> list[PatientTrajectory]:
        cfg = self.config
        out: list[PatientTrajectory] = []
        for i in range(cfg.n_patients_per_arm):
            out.append(self._generate_patient(arm, i))
        return out

    def _generate_patient(self, arm: PatientArm, index: int) -> PatientTrajectory:
        cfg = self.config
        rng = self._rng

        doubling = cfg.doubling_time_days * float(np.exp(rng.normal(0.0, cfg.doubling_time_cv)))
        shedding = float(np.exp(rng.normal(0.0, cfg.shedding_cv)))
        has_chip = bool(rng.random() < cfg.chip_prevalence) and not cfg.chip_filtered

        if cfg.regime is Regime.SCREENING:
            baseline = 0.0
            if arm is PatientArm.CANCER:
                baseline = float(
                    np.exp(rng.normal(np.log(cfg.screening_baseline_mm3), 0.9))
                )
            residual = 0.0
            resistant_doubling = doubling
        else:
            baseline = float(
                np.exp(rng.normal(np.log(cfg.baseline_volume_mm3), cfg.baseline_volume_cv))
            )
            residual = float(
                np.clip(
                    rng.normal(cfg.residual_fraction, cfg.residual_fraction_sd),
                    1e-4,
                    0.6,
                )
            )
            resistant_doubling = cfg.resistant_doubling_time_days * float(
                np.exp(rng.normal(0.0, cfg.doubling_time_cv))
            )

        volumes = self._volumes(arm, baseline, residual, doubling, resistant_doubling)
        relapse_draw = self._relapse_draw(volumes)

        measurements = []
        for draw_index, volume in enumerate(volumes):
            measurements.append(
                self._measure(draw_index, volume, shedding, has_chip, arm)
            )

        return PatientTrajectory(
            patient_id=f"{arm.value}-{index:05d}",
            arm=arm,
            measurements=tuple(measurements),
            relapse_draw=relapse_draw,
            residual_volume_mm3=baseline * residual if residual else 0.0,
            doubling_time_days=resistant_doubling if cfg.regime is Regime.POST_TREATMENT else doubling,
            has_chip=has_chip,
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
                    volumes.append(baseline * (2.0 ** (day / doubling)))
                continue

            if draw_index == 0:
                volumes.append(baseline)
            elif arm is PatientArm.RESPONDER:
                volumes.append(0.0)
            else:
                residual_volume = baseline * residual
                elapsed = day - cfg.sampling_interval_days
                volumes.append(residual_volume * (2.0 ** (elapsed / resistant_doubling)))
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
        arm: PatientArm,
    ) -> Measurement:
        cfg = self.config
        rng = self._rng

        # cfDNA input, recorded as assay context (depth is assumed saturated).
        ge_per_ml = cfg.genome_equivalents_per_ml * float(np.exp(rng.normal(0.0, cfg.ge_cv)))
        ge_total = max(1, int(rng.poisson(ge_per_ml * 10.0)))

        true_vaf = cfg.tumor_vaf_per_mm3 * volume * shedding

        background = max(0.0, float(rng.normal(cfg.background_vaf_mean, cfg.background_vaf_sd)))
        if has_chip:
            background = max(background, cfg.chip_vaf)

        total_vaf = true_vaf + background
        mutant_reads = int(rng.poisson(cfg.sequencing_depth * cfg.n_loci * total_vaf))
        total_reads = cfg.sequencing_depth * cfg.n_loci

        day = draw_index * cfg.sampling_interval_days
        is_relapse = volume >= cfg.relapse_volume_threshold_mm3

        return Measurement(
            draw_index=draw_index,
            day=day,
            mutant_reads=mutant_reads,
            total_reads=total_reads,
            genome_equivalents=ge_total,
            observed_vaf=mutant_reads / total_reads,
            true_vaf=true_vaf,
            tumour_volume_mm3=volume,
            is_relapse_draw=is_relapse,
            has_chip=has_chip,
            background_vaf=background,
        )
