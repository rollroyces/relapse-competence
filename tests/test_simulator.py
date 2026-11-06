"""Simulator tests.

The simulator is the ground truth for everything else in the package, so these
tests check the properties that the rest of the code silently assumes.
"""

from __future__ import annotations

import pytest

from relapse_competence.config import PatientArm, Regime, SimulationConfig
from relapse_competence.simulator import LongitudinalSimulator


@pytest.fixture(scope="module")
def post_treatment_cohort():
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=60, n_draws=8
    )
    return cfg, LongitudinalSimulator(cfg).generate_cohort()


def test_cohort_has_all_post_treatment_arms(post_treatment_cohort) -> None:
    _, cohort = post_treatment_cohort
    assert set(cohort) == {
        PatientArm.RESPONDER,
        PatientArm.PERSISTENT,
        PatientArm.RESISTANT,
    }
    for arm, patients in cohort.items():
        assert len(patients) == 60, arm


def test_every_patient_has_the_requested_number_of_draws(post_treatment_cohort) -> None:
    cfg, cohort = post_treatment_cohort
    for patients in cohort.values():
        for patient in patients:
            assert len(patient.measurements) == cfg.n_draws


def test_responders_never_reach_the_relapse_threshold(post_treatment_cohort) -> None:
    cfg, cohort = post_treatment_cohort
    for patient in cohort[PatientArm.RESPONDER]:
        assert patient.relapse_draw is None
        for m in patient.measurements[1:]:
            assert m.tumour_volume_mm3 < cfg.relapse_volume_threshold_mm3


def test_relapse_is_never_counted_at_the_pre_treatment_draw(post_treatment_cohort) -> None:
    """Draw 0 is pre-treatment. A patient cannot relapse on day zero."""
    _, cohort = post_treatment_cohort
    for patients in cohort.values():
        for patient in patients:
            if patient.relapse_draw is not None:
                assert patient.relapse_draw >= 1, patient.patient_id


def test_resistant_patients_regrow_from_a_small_residual(post_treatment_cohort) -> None:
    _, cohort = post_treatment_cohort
    regrew = [p for p in cohort[PatientArm.RESISTANT] if p.relapse_draw is not None]
    assert regrew, "expected at least some resistant patients to relapse within the window"
    for patient in regrew:
        assert patient.residual_volume_mm3 > 0.0
        volumes = [m.tumour_volume_mm3 for m in patient.measurements]
        # After therapy the burden drops, then climbs again.
        assert volumes[1] < volumes[0]
        assert max(volumes[1:]) > volumes[1]


def test_background_only_patients_track_the_background_floor() -> None:
    cfg = SimulationConfig(
        regime=Regime.POST_TREATMENT, n_patients_per_arm=40, n_draws=6
    )
    cohort = LongitudinalSimulator(cfg).generate_cohort()
    for patient in cohort[PatientArm.RESPONDER]:
        for m in patient.measurements[1:]:
            assert m.true_vaf == 0.0
            assert m.tumour_volume_mm3 == 0.0


def test_simulation_is_reproducible_from_the_seed() -> None:
    cfg = SimulationConfig(n_patients_per_arm=30, n_draws=5)
    a = LongitudinalSimulator(cfg).generate_cohort()
    b = LongitudinalSimulator(cfg).generate_cohort()
    for arm in a:
        for pa, pb in zip(a[arm], b[arm], strict=False):
            assert pa.measurements[0].mutant_reads == pb.measurements[0].mutant_reads
            assert pa.residual_volume_mm3 == pb.residual_volume_mm3


def test_reads_are_bounded_by_total_reads() -> None:
    cfg = SimulationConfig(n_patients_per_arm=40, n_draws=5)
    cohort = LongitudinalSimulator(cfg).generate_cohort()
    for patients in cohort.values():
        for patient in patients:
            for m in patient.measurements:
                assert 0 <= m.mutant_reads <= m.total_reads
                assert m.total_reads == cfg.sequencing_depth * cfg.n_loci
                assert m.genome_equivalents > 0
