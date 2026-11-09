"""Fidelity-extension tests.

The fidelity extensions -- multi-clone resistance, Gompertzian growth,
site-dependent shedding, per-locus background variation -- exist to bound how
much the published numbers depend on the model's simplifications. Two things
have to hold for them to be worth anything:

1. the published numbers do not move when they are switched off, and
2. when they are switched on, they actually change the model.

The first is guarded by a captured reference: the default configuration has to
reproduce ``tests/fixtures/default_model_reference.json`` exactly.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

from relapse_competence.config import PatientArm, Regime, SimulationConfig
from relapse_competence.fidelity import MODEL_VARIANTS, run_split_model_validation
from relapse_competence.simulator import LongitudinalSimulator

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "default_model_reference.json"
)
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_default_model_reference.py"


def _load_script():
    """The reference check is a standalone script, not a package module."""
    spec = importlib.util.spec_from_file_location(
        "check_default_model_reference", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference_check = _load_script()


def _reference() -> dict:
    return json.loads(FIXTURE.read_text())


def _current(config: SimulationConfig) -> dict:
    cohort = LongitudinalSimulator(config).generate_cohort()
    return {
        arm.value: [
            {
                "patient_id": t.patient_id,
                "residual_volume_mm3": t.residual_volume_mm3,
                "doubling_time_days": t.doubling_time_days,
                "state_fraction": t.state_fraction,
                "relapse_draw": t.relapse_draw,
                "has_chip": t.has_chip,
                "measurements": [
                    {
                        "draw_index": m.draw_index,
                        "mutant_reads": m.mutant_reads,
                        "observed_vaf": m.observed_vaf,
                        "true_vaf": m.true_vaf,
                        "tumour_volume_mm3": m.tumour_volume_mm3,
                        "electrical_reads": m.electrical_reads,
                        "background_vaf": m.background_vaf,
                        "genome_equivalents": m.genome_equivalents,
                    }
                    for m in t.measurements
                ],
            }
            for t in trajectories
        ]
        for arm, trajectories in cohort.items()
    }


def test_default_output_matches_the_captured_reference() -> None:
    """The published numbers may not move when the extensions are off."""
    reference = _reference()
    configs = {
        "post_treatment_default": SimulationConfig(
            regime=Regime.POST_TREATMENT, seed=20261106, n_patients_per_arm=8
        ),
        "with_electrical_channel": SimulationConfig(
            regime=Regime.POST_TREATMENT,
            seed=20261106,
            n_patients_per_arm=8,
            n_electrical_loci=50,
        ),
        "screening_default": SimulationConfig(
            regime=Regime.SCREENING, seed=20261106, n_patients_per_arm=8
        ),
    }
    for name, config in configs.items():
        problems = reference_check.diff(
            reference["configs"][name], _current(config)
        )
        assert not problems, (name, problems[:5])


def test_the_reference_guard_catches_a_changed_number() -> None:
    """The guard must fail when a number moves, not merely when it differs.

    A check that has never been attacked is an untested claim, and this is
    the check that stands between a refactor and the published numbers.
    """
    reference = _reference()
    config = SimulationConfig(
        regime=Regime.POST_TREATMENT, seed=20261106, n_patients_per_arm=8
    )
    current = _current(config)
    assert not reference_check.diff(
        reference["configs"]["post_treatment_default"], current
    )

    moved = json.loads(json.dumps(current))
    moved["responder"][0]["doubling_time_days"] *= 1.000001
    assert reference_check.diff(
        reference["configs"]["post_treatment_default"], moved
    ), "a changed doubling time must be caught"

    renamed = json.loads(json.dumps(current))
    renamed["responder"][0]["patient_id"] = "responder-99999"
    assert reference_check.diff(
        reference["configs"]["post_treatment_default"], renamed
    ), "a changed identifier must be caught"

    recut = json.loads(json.dumps(current))
    recut["responder"][0]["measurements"][0]["mutant_reads"] += 1
    assert reference_check.diff(
        reference["configs"]["post_treatment_default"], recut
    ), "a changed read count must be caught"


def test_the_reference_tolerance_absorbs_a_platform_difference() -> None:
    """The tolerance covers a last-bit difference and nothing larger.

    One or two units in the last place is about 1e-15 relative, and is what
    ``exp`` and ``log`` do differently on two platforms. A change in the
    model is many orders of magnitude larger.
    """
    assert reference_check.diff({"v": 1.0}, {"v": 1.0 + 1e-15}) == []
    assert reference_check.diff({"v": 1.0}, {"v": 1.0 + 1e-9})
    # A structural zero may come back as a denormal on another platform.
    assert reference_check.diff({"v": 0.0}, {"v": 1e-18}) == []
    assert reference_check.diff({"v": 0.0}, {"v": 1e-9})


def test_the_published_variant_is_the_base_configuration() -> None:
    """The fidelity comparison must include the published model unchanged."""
    published = MODEL_VARIANTS[0]
    assert published.name == "published"
    assert published.overrides == {}


def test_multi_clone_produces_several_clones_with_different_fitness() -> None:
    config = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=20,
        n_clones=3,
        clone_residual_fraction_sd=0.6,
        clone_shedding_sd=0.5,
    )
    cohort = LongitudinalSimulator(config).generate_cohort()
    resistant = cohort[PatientArm.RESISTANT]
    for patient in resistant:
        assert len(patient.clone_doubling_times) == 3
        assert len(set(patient.clone_doubling_times)) > 1, "clones share a fitness"


def test_single_clone_keeps_one_doubling_time() -> None:
    config = SimulationConfig(
        regime=Regime.POST_TREATMENT, seed=20261106, n_patients_per_arm=5
    )
    cohort = LongitudinalSimulator(config).generate_cohort()
    for patient in cohort[PatientArm.RESISTANT]:
        assert len(patient.clone_doubling_times) == 1


def test_gompertzian_growth_is_monotone_and_bounded() -> None:
    config = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=20,
        growth_model="gompertz",
    )
    cohort = LongitudinalSimulator(config).generate_cohort()
    for patient in cohort[PatientArm.RESISTANT]:
        # Draw 0 is the pre-treatment tumour; the residual clone grows from
        # draw 1 onwards, and only that part has to be monotone.
        volumes = [m.tumour_volume_mm3 for m in patient.measurements[1:]]
        for earlier, later in zip(volumes, volumes[1:], strict=False):
            assert later >= earlier
        assert max(volumes) <= config.max_tumour_volume_mm3


def test_gompertzian_growth_decelerates() -> None:
    """The point of Gompertzian growth: the doubling time lengthens."""
    config = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        growth_model="gompertz",
        resistant_doubling_time_days=60.0,
        residual_fraction=0.2,
    )
    cohort = LongitudinalSimulator(config).generate_cohort()
    early = []
    late = []
    for patient in cohort[PatientArm.RESISTANT]:
        volumes = [m.tumour_volume_mm3 for m in patient.measurements[1:]]
        if len(volumes) < 4 or volumes[0] <= 0 or volumes[1] <= 0:
            continue
        early.append(math.log2(volumes[1] / volumes[0]))
        if volumes[2] > 0:
            late.append(math.log2(volumes[2] / volumes[1]))
    assert early, "no patient produced a usable growth estimate"
    assert late, "no patient produced a usable late growth estimate"
    assert sum(late) / len(late) < sum(early) / len(early)


def test_site_shedding_assigns_a_site_and_changes_the_signal() -> None:
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT, seed=20261106, n_patients_per_arm=40
    )
    without = LongitudinalSimulator(base).generate_cohort()
    with_sites = LongitudinalSimulator(
        SimulationConfig(
            regime=Regime.POST_TREATMENT,
            seed=20261106,
            n_patients_per_arm=40,
            site_shedding_enabled=True,
        )
    ).generate_cohort()
    sites = {p.relapse_site for p in with_sites[PatientArm.RESISTANT]}
    assert "" not in sites
    assert len(sites) > 1, "every patient relapsed at the same site"
    assert all(p.relapse_site == "" for p in without[PatientArm.RESISTANT])


def test_per_locus_background_is_overdispersed() -> None:
    """A varying background floor cannot be a single Poisson draw."""
    config = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        background_vaf_mean=1e-4,
        background_vaf_sd=0.0,
        per_locus_background_log_sd=1.5,
    )
    cohort = LongitudinalSimulator(config).generate_cohort()
    counts = [
        m.mutant_reads
        for patient in cohort[PatientArm.RESPONDER]
        for m in patient.measurements[1:]
    ]
    mean = sum(counts) / len(counts)
    variance = sum((c - mean) ** 2 for c in counts) / (len(counts) - 1)
    assert variance > mean, "the read count is not over-dispersed"


def test_split_model_validation_reports_both_operating_points() -> None:
    config = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        n_electrical_loci=50,
    )
    result = run_split_model_validation(config)
    assert "published_model_published_detector" in result
    evaluations = result["evaluations"]
    assert evaluations, "no variant was evaluated"
    for evaluation in evaluations:
        for key in (
            "variant_model_published_detector",
            "variant_model_refitted_detector",
            "cost_of_not_recalibrating",
            "model_gap_with_detector_held_fixed",
        ):
            assert key in evaluation
        assert evaluation["read_threshold_published"] > 0
        assert evaluation["read_threshold_refit"] > 0
