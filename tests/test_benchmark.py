"""Benchmark engine tests.

These are the tests that would have caught the failure mode this package
exists to prevent: a benchmark that reports numbers it did not compute.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from relapse_competence.benchmark import (
    calibrate_sequential_threshold,
    calibrate_single_timepoint_vaf,
    run_channel_allocation_sweep,
    run_depth_sweep,
    run_mrd_benchmark,
    run_screening_benchmark,
    select_read_threshold,
)
from relapse_competence.config import PatientArm, Regime, SimulationConfig
from relapse_competence.simulator import LongitudinalSimulator


@pytest.fixture(scope="module")
def small_cohort():
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=120, n_draws=8
    )
    return cfg, LongitudinalSimulator(cfg).generate_cohort()


def test_read_threshold_selection_is_monotone(small_cohort) -> None:
    cfg, cohort = small_cohort
    responders = cohort[PatientArm.RESPONDER]
    calibration = responders[0::2]
    k = select_read_threshold(calibration, target_specificity=0.95, max_k=200)
    assert k is not None
    # Raising the read threshold can only reduce false positives, so
    # specificity must not decrease.
    from relapse_competence.benchmark import _specificity_at

    assert _specificity_at(calibration, k + 1) >= _specificity_at(calibration, k)


def test_read_threshold_selection_reports_failure(small_cohort) -> None:
    _, cohort = small_cohort
    responders = cohort[PatientArm.RESPONDER]
    # An unreachable target must return None rather than a bogus threshold.
    assert select_read_threshold(responders[0::2], target_specificity=1.0, max_k=5) is None


def test_mrd_benchmark_reports_every_required_field() -> None:
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=120, n_draws=8
    )
    result = run_mrd_benchmark(cfg, target_specificity=0.95)
    payload = result.as_dict()
    for key in (
        "sensitivity",
        "specificity",
        "ppv",
        "median_lead_time_days",
        "n_flagged_before_relapse",
        "n_flagged_late",
        "nominal_vaf_threshold",
        "nominal_volume_threshold_mm3",
        "target_reached",
    ):
        assert key in payload, key
    assert 0.0 <= payload["sensitivity"] <= 1.0
    assert 0.0 <= payload["specificity"] <= 1.0


def test_mrd_benchmark_rejects_the_wrong_regime() -> None:
    cfg = SimulationConfig(regime=Regime.SCREENING)
    with pytest.raises(ValueError):
        run_mrd_benchmark(cfg)


def test_depth_sweep_covers_the_grid() -> None:
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=60, n_draws=6
    )
    results = run_depth_sweep(cfg, depths=(5_000, 50_000), locus_counts=(50,))
    assert len(results) == 2
    assert {r.sequencing_depth for r in results} == {5_000, 50_000}


def test_deeper_sequencing_never_lowers_the_minimum_detectable_volume() -> None:
    """More depth must not make the assay less sensitive, all else equal."""
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=120, n_draws=8
    )
    shallow = run_mrd_benchmark(
        replace(cfg, sequencing_depth=5_000), target_specificity=0.95
    )
    deep = run_mrd_benchmark(
        replace(cfg, sequencing_depth=200_000), target_specificity=0.95
    )
    assert deep.nominal_volume_threshold_mm3 <= shallow.nominal_volume_threshold_mm3


def test_channel_allocation_sweep_covers_the_grid() -> None:
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=80, n_draws=6
    )
    rows = run_channel_allocation_sweep(
        cfg, total_loci=(50,), depth=5_000, electrical_fractions=(0.0, 0.5, 1.0)
    )
    assert len(rows) == 3
    for row in rows:
        assert row["n_mutation_loci"] + row["n_electrical_loci"] == 50
        assert 0.0 <= row["mrd_sensitivity"] <= 1.0
        assert 0.0 <= row["mrd_specificity"] <= 1.0


def test_channel_allocation_preserves_total_read_budget() -> None:
    """Splitting loci must not change the total read budget."""
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=40, n_draws=4
    )
    rows = run_channel_allocation_sweep(
        cfg, total_loci=(50,), depth=5_000, electrical_fractions=(0.0, 0.5, 1.0)
    )
    budgets = {row["total_reads_per_draw"] for row in rows}
    assert budgets == {5_000 * 50}


def test_auc_helper_matches_known_values() -> None:
    from relapse_competence.benchmark import _auc

    assert _auc([1.0, 2.0, 3.0, 4.0], [False, False, True, True]) == 1.0
    assert _auc([4.0, 3.0, 2.0, 1.0], [False, False, True, True]) == 0.0
    assert _auc([1.0, 1.0, 1.0, 1.0], [False, False, True, True]) == 0.5


def test_screening_benchmark_calibrates_on_a_held_out_split() -> None:
    cfg = SimulationConfig(
        regime=Regime.SCREENING, n_patients_per_arm=120, n_draws=8
    )
    payload = run_screening_benchmark(cfg, target_specificity=0.95)
    calibration = payload["calibration"]
    assert calibration["n_healthy_calibration"] > 0
    assert calibration["n_healthy_evaluation"] > 0
    assert calibration["n_healthy_calibration"] + calibration["n_healthy_evaluation"] == 120
    assert 0.0 <= payload["sequential"]["specificity"] <= 1.0
    assert 0.0 <= payload["sequential"]["sensitivity"] <= 1.0


def test_screening_benchmark_rejects_the_wrong_regime() -> None:
    cfg = SimulationConfig(regime=Regime.POST_TREATMENT)
    with pytest.raises(ValueError):
        run_screening_benchmark(cfg)


def test_calibrators_return_a_target_reached_flag() -> None:
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=60, n_draws=6
    )
    cohort = LongitudinalSimulator(cfg).generate_cohort()
    responders = cohort[PatientArm.RESPONDER]
    threshold, reached = calibrate_sequential_threshold(
        responders[0::2], background_reads=2.5, target_specificity=0.95
    )
    assert threshold > 0
    assert isinstance(reached, bool)
    vaf, reached2 = calibrate_single_timepoint_vaf(
        responders[0::2], background_vaf=1e-6, target_specificity=0.95
    )
    assert vaf > 0
    assert isinstance(reached2, bool)
