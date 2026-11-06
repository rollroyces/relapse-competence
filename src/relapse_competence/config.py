"""Typed configuration.

Every knob that can move a reported number lives in exactly one of these
dataclasses. Nothing else in the package holds mutable state. This is what
makes a benchmark result reproducible from a single JSON blob.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PatientArm(str, Enum):
    """Ground-truth arms produced by the simulator."""

    HEALTHY = "healthy"
    """Screening regime: never develops a tumour."""

    CANCER = "cancer"
    """Screening regime: tumour grows exponentially from a small baseline."""

    RESPONDER = "responder"
    """Post-treatment regime: no residual disease; signal decays to the floor."""

    PERSISTENT = "persistent"
    """Post-treatment regime: residual disease persists but does not relapse
    inside the observation window.

    This arm exists because it is the clinical problem that makes MRD
    imperfect: an MRD-positive patient is not necessarily a patient who will
    relapse. Without this arm, MRD sensitivity and MRD positive predictive
    value are not measurable at all.
    """

    RESISTANT = "resistant"
    """Post-treatment regime: a residual clone survives therapy and regrows."""


class Regime(str, Enum):
    """Which clinical question the simulation is answering."""

    SCREENING = "screening"
    """Pre-diagnosis. The question is 'is there a growing tumour?'"""

    POST_TREATMENT = "post_treatment"
    """Post-resection / post-therapy. The question is 'is there residual disease?'"""


@dataclass(frozen=True)
class SimulationConfig:
    """Ground-truth generation parameters.

    Defaults are literature-calibrated; see :mod:`relapse_competence.calibration`
    for the anchor values and their sources.
    """

    regime: Regime = Regime.POST_TREATMENT
    seed: int = 20261106

    # --- sequencing / sampling ---
    sequencing_depth: int = 50_000
    """Reads per locus per draw. Matches a deep targeted panel (Phallen 2017)."""

    n_loci: int = 50
    """Tracked somatic loci per patient.

    Real tumour-informed MRD panels track 50-500 loci and flag on the *total*
    mutant read count across them. Modelling one locus would understate
    sensitivity by roughly an order of magnitude.
    """

    genome_equivalents_per_ml: float = 300.0
    """cfDNA concentration (Snyder 2016)."""

    ge_cv: float = 0.267
    """Concentration CV: 300 +/- 80 genome equivalents per mL."""

    # --- background floor ---
    background_vaf_mean: float = 1e-6
    """Per-locus background mutant-read rate at a tracked position.

    This is the *error floor at a tumour-specific site* under duplex/UMI error
    suppression, not the genome-wide sequencing error rate. It already absorbs
    residual germline artefacts.
    """

    background_vaf_sd: float = 2e-7
    """Across-draw biological + technical variation of the background floor."""

    # --- clonal haematopoiesis (CHIP) ---
    chip_prevalence: float = 0.10
    """Fraction of patients carrying a CHIP mutation. ~10% of people over 60."""

    chip_vaf: float = 1e-3
    """Persistent VAF of a CHIP mutation (0.1-2% range in the literature)."""

    chip_filtered: bool = True
    """Whether the tracked panel excludes known CHIP genes.

    When True, CHIP is not tracked and cannot cause a false positive. When
    False, CHIP is tracked at :attr:`chip_vaf` and will be flagged. The
    benchmark reports both settings.
    """

    # --- tumour biology ---
    tumor_vaf_per_mm3: float = 4.5e-10
    """``VAF = tumor_vaf_per_mm3 * tumour_volume_mm3``.

    Calibrated so that a stage I NSCLC burden (~14,000 mm3) yields ~6e-6 median
    ctDNA VAF (Phallen 2017) and a stage IV burden (~1e6 mm3) yields ~5e-4.
    """

    doubling_time_days: float = 200.0
    """Median tumour doubling time for early lung cancer."""

    doubling_time_cv: float = 0.35
    """Across-patient spread of doubling time."""

    # --- post-treatment dynamics ---
    residual_fraction: float = 0.02
    """Fraction of tumour volume surviving therapy as a resistant clone."""

    residual_fraction_sd: float = 0.015
    """Across-patient spread of the residual fraction."""

    resistant_doubling_time_days: float = 60.0
    """Doubling time of the residual resistant clone.

    Relapsing clones are typically more aggressive than the primary tumour.
    """

    relapse_volume_threshold_mm3: float = 10_000.0
    """Tumour burden treated as radiographic relapse.

    10 cm3 is roughly a 2.7 cm diameter pulmonary nodule: the point at which
    a lung primary becomes visible on imaging. This is the reference point
    for lead time.
    """

    baseline_volume_mm3: float = 20_000.0
    """Median pre-treatment tumour burden (resectable stage I-II NSCLC)."""

    max_tumour_volume_mm3: float = 5_000_000.0
    """Carrying capacity for tumour growth, in cubic millimetres.

    Without a cap the exponential model runs away: a residual clone of a few
    hundred cubic millimetres doubling every 60 days reaches tens of litres
    inside a 33-month window, which drives the per-locus VAF above 1 and makes
    the Poisson sampler reject the draw. Disseminated disease does grow, but
    not without bound. 5 litres is far above the 10 cm3 radiographic
    threshold, so it does not alter the lead-time dynamics; it only keeps the
    late draws physical.
    """

    baseline_volume_cv: float = 0.9
    """Log-normal spread of the baseline burden."""

    # --- bulk electrical / epigenetic channel ---
    n_electrical_loci: int = 0
    """Ion-channel loci read as a bulk feature, separate from the mutation panel.

    ``0`` (the default) disables the channel entirely, which reproduces the
    original single-channel simulator exactly. See ``state_fraction`` for why
    a bulk channel carries the state only weakly.
    """

    electrical_fold_change: float = 3.0
    """Fold-upregulation of the ion-channel marker in state-bearing cells."""

    state_fraction_resistant: float = 0.25
    """Mean fraction of the resistant clone that is relapse-competent."""

    state_fraction_resistant_sd: float = 0.12
    state_fraction_persistent: float = 0.10
    """Mean fraction of a persistent (MRD-positive, non-relapsing) clone that
    is relapse-competent."""

    state_fraction_persistent_sd: float = 0.12
    """The two distributions overlap heavily, so the electrical channel is
    informative but nowhere near an oracle."""

    state_fraction_responder: float = 0.0
    """Responders carry no residual clone, hence no state."""

    mutation_clonal_fraction: float = 1.0
    """Fraction of tumour cells carrying each tracked mutation.

    ``1.0`` means the tracked mutation is clonal, which is the assumption the
    original single-channel model made. Values below 1 model a tumour-informed
    panel that tracks subclonal mutations, whose per-locus signal is weaker
    and whose detection floor is higher.
    """

    # --- cohort and schedule ---
    n_patients_per_arm: int = 400
    sampling_interval_days: int = 90
    n_draws: int = 12
    """Draws per patient. Draw 0 is pre-treatment baseline in the
    post-treatment regime."""

    # --- measurement error ---
    shedding_cv: float = 0.45
    """Across-draw and across-patient variability of ctDNA shedding."""

    screening_baseline_mm3: float = 3_000.0
    """Median baseline burden in the screening regime."""

    # --- model fidelity -----------------------------------------------------
    # Everything in this block is **default-off**. The published numbers come
    # from the single-clone, exponential, uniform-shedding model, and turning
    # any of these knobs on must not move a published figure: the extensions
    # use their own random streams, so the draws the published numbers depend
    # on are untouched.
    n_clones: int = 1
    """Number of resistant clones carried by each patient.

    ``1`` (the default) is the single-clone model. Above 1, the residual
    burden is split across clones with different fitness and different
    shedding, which is how real resistant disease is heterogeneous.
    """

    clone_residual_fraction_sd: float = 0.0
    """Log-normal spread of each clone's share of the residual burden."""

    clone_doubling_time_cv: float = 0.35
    """Across-clone spread of the doubling time."""

    clone_shedding_sd: float = 0.0
    """Log-normal spread of each clone's shedding multiplier."""

    growth_model: str = "exponential"
    """``"exponential"`` (the published model) or ``"gompertz"``.

    Gompertzian growth decelerates as the tumour approaches its carrying
    capacity, which exponential growth with a constant doubling time
    overstates. The rate is calibrated per patient so that the *initial*
    doubling time still matches the configured value.
    """

    relapse_sites: tuple[tuple[str, float, float], ...] = (
        ("lung", 0.40, 1.0),
        ("bone", 0.20, 0.6),
        ("liver", 0.20, 1.5),
        ("brain", 0.15, 3.0),
        ("other", 0.05, 1.0),
    )
    """Metastatic sites as ``(name, weight, shedding multiplier)``.

    The multipliers are **assumptions for a sensitivity analysis**, not
    literature estimates: the point of the sweep is to measure how far the
    conclusions move under plausible heterogeneity, not to assert a fold
    change that has not been measured.
    """

    site_shedding_enabled: bool = False
    """Whether each patient is assigned a relapse site with its own shedding."""

    per_locus_background_log_sd: float = 0.0
    """Log-normal spread of the background floor across tracked loci.

    Real error floors vary by locus, batch and germline status. Above 0, the
    per-locus background is drawn and the mutant read count becomes a sum of
    per-locus Poisson draws, which is over-dispersed relative to a single
    Poisson on the aggregate.
    """


@dataclass(frozen=True)
class DetectorConfig:
    """Detector parameters."""

    # --- tumour-informed MRD threshold ---
    mrd_read_threshold: int = 3
    """Flag when total mutant reads across the tracked loci reach this count.

    This is how tumour-informed MRD assays actually work: a read count, not
    a VAF, because the aggregate VAF threshold is just
    ``k / (depth * n_loci)``.
    """

    # --- sequential rise detector (screening regime) ---
    cusum_slack: float = 0.5
    """CUSUM slack, in reads. Excesses smaller than this do not accumulate."""

    cusum_threshold: float = 12.0
    """Default CUSUM decision threshold. Normally replaced by a value
    calibrated on a held-out healthy split -- see
    :func:`relapse_competence.benchmark.calibrate_sequential_threshold`."""

    streak_bonus_weight: float = 0.30
    trend_bonus_weight: float = 0.30
    learning_rate: float = 0.50
    """Exponential weight on the most recent draw in the trend estimate."""

    min_relative_rise: float = 1.5
    """Reserved for single-timepoint comparator calibration."""

    delta_sigma: float = 0.55
    """Reserved. Retained so that earlier configurations remain loadable."""
