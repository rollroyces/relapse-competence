"""Tests for the leukocyte compartment and the audit built on it.

The compartment is an extension to the published model, so two things have to
hold: with it off the model is unchanged, bit for bit, and with it on the
readout's behaviour changes in the direction the audit reports. Both are
asserted here, along with the control that ties the audit to the published
numbers.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pytest

from relapse_competence.benchmark import _auc, collect_outcomes
from relapse_competence.config import Regime, SimulationConfig
from relapse_competence.detectors import ElectricalChannelDetector
from relapse_competence.simulator import LongitudinalSimulator

AUDIT = Path("results/leukocyte_audit/leukocyte_audit.json")
REPORT = Path("docs/LEUKOCYTE-AUDIT.md")
FIXTURE = Path("tests/fixtures/default_model_reference.json")
CAPTURE = Path("scripts/capture_default_model_reference.py")
CHECK = Path("scripts/check_default_model_reference.py")

#: The published operating-point AUCs, which the audit's control reproduces.
PUBLISHED_AUC = {
    ("NSCLC", "KCNN4"): 0.9928621553884712,
    ("SCLC", "KCNN4"): 0.706544901065449,
    ("SCLC", "PIEZO1"): 0.6945048256673333,
}


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def audit() -> dict:
    if not AUDIT.exists():
        pytest.skip("the leukocyte audit artefact has not been generated")
    return json.loads(AUDIT.read_text())


def test_the_compartment_is_default_off() -> None:
    """An extension that is on by default would move the published numbers."""
    assert SimulationConfig().leukocyte_channel_fraction == 0.0


def test_the_golden_fixture_is_unchanged_with_the_compartment_off() -> None:
    """The guard that the extension does not move the published model.

    The committed fixture was captured on macOS, and the simulator's last-bit
    float output differs on Linux by the one or two units in the last place
    that ``exp`` and ``log`` produce differently there. So the invariant is
    the one the repository's own golden check already uses: the regenerated
    fixture must match the committed one within that platform tolerance, on
    every platform. On the platform that captured it, the two are byte
    identical.
    """
    capture = _load_script("capture_default_model_reference", CAPTURE)
    checker = _load_script("check_default_model_reference", CHECK)
    committed = json.loads(FIXTURE.read_text())
    problems = checker.diff(committed, capture.capture())
    assert not problems, problems[:5]


def test_the_compartment_off_makes_no_extra_random_draw() -> None:
    """The platform-independent half of the guard.

    The extra Poisson draw that carries the leukocyte compartment is inside a
    guard on the compartment being present, so with it off every measurement
    records no leukocyte reads at all.
    """
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        n_electrical_loci=50,
        n_loci=150,
    )
    cohort = LongitudinalSimulator(base).generate_cohort()
    seen = 0
    for trajectories in cohort.values():
        for trajectory in trajectories:
            for m in trajectory.measurements:
                assert m.electrical_leukocyte_reads == 0
                seen += 1
    assert seen > 0


def test_the_compartment_does_something_when_it_is_on() -> None:
    """An extension that changes nothing when switched on is not an extension."""
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        n_electrical_loci=50,
        n_loci=150,
    )
    off = LongitudinalSimulator(base).generate_cohort()
    on = LongitudinalSimulator(
        replace(base, leukocyte_channel_fraction=0.5)
    ).generate_cohort()
    off_reads = [
        m.electrical_reads
        for trajectories in off.values()
        for t in trajectories
        for m in t.measurements
    ]
    on_reads = [
        m.electrical_reads
        for trajectories in on.values()
        for t in trajectories
        for m in t.measurements
    ]
    assert off_reads != on_reads
    assert sum(on_reads) > sum(off_reads)


def test_the_attributable_enrichment_equals_the_raw_when_off() -> None:
    """With no leukocyte compartment there is nothing to subtract."""
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        n_electrical_loci=50,
        n_loci=150,
    )
    cohort = LongitudinalSimulator(base).generate_cohort()
    for trajectories in cohort.values():
        for t in trajectories:
            assert ElectricalChannelDetector.state_enrichment_attributable(
                t.measurements
            ) == pytest.approx(
                ElectricalChannelDetector.state_enrichment(t.measurements), abs=1e-12
            )


def test_the_audit_control_reproduces_the_published_aucs(audit: dict) -> None:
    for entry in audit["control"]:
        assert entry["matches"] is True, entry
        assert entry["published_auc"] is not None, entry
        assert (
            abs(entry["recomputed_auc_raw"] - entry["published_auc"]) < 1e-9
        ), entry


def test_the_control_reproduces_the_published_auc_from_the_model() -> None:
    """The control is not a stored number; it is recomputed here."""
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT, seed=20261106, n_patients_per_arm=800
    )
    cfg = replace(
        base,
        electrical_fold_change=3.6979371667856475 - 1.0,
        state_fraction_resistant=0.3916913946587537,
        sequencing_depth=200_000,
        n_loci=150,
        n_electrical_loci=50,
    )
    outcomes, _ = collect_outcomes(cfg, target_specificity=0.98)
    mrd = [
        o
        for o in outcomes
        if o.split == "evaluation" and o.mrd_flagged
    ]
    raw = _auc([o.electrical_enrichment for o in mrd], [o.relapsed for o in mrd])
    assert abs(raw - PUBLISHED_AUC[("NSCLC", "KCNN4")]) < 1e-9


def test_a_leukocyte_background_inverts_the_raw_statistic(audit: dict) -> None:
    """The published statistic does not degrade under a leukocyte background.

    It inverts: the leukocyte contribution divided by the tumour's cfDNA share
    is inversely related to tumour burden, and relapsers carry more tumour.
    """
    operating = [
        r
        for r in audit["sweep"]
        if r["dataset"] == "NSCLC"
        and r["channel"] == "KCNN4"
        and r["tumour_share_multiplier"] == 1
    ]
    by_fraction = {r["leukocyte_fraction"]: r for r in operating}
    assert by_fraction[0.0]["auc_raw"] > 0.99
    for fraction in (0.5, 0.9, 0.99):
        assert by_fraction[fraction]["auc_raw"] < 0.01, fraction


def test_the_attributable_statistic_is_at_chance(audit: dict) -> None:
    """Correcting for the leukocyte reads does not rescue the readout either."""
    operating = [
        r
        for r in audit["sweep"]
        if r["dataset"] == "NSCLC"
        and r["channel"] == "KCNN4"
        and r["tumour_share_multiplier"] == 1
    ]
    by_fraction = {r["leukocyte_fraction"]: r for r in operating}
    assert by_fraction[0.5]["auc_attributable"] < 0.6
    assert by_fraction[0.5]["auc_attributable"] > 0.4


def test_the_reference_set_is_default_off() -> None:
    """Another extension that is on by default would move the published model."""
    assert SimulationConfig().n_leukocyte_reference_loci == 0


def test_the_reference_set_draws_reads_and_the_model_without_it_does_not() -> None:
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        n_electrical_loci=50,
        n_loci=100,
    )
    without = LongitudinalSimulator(base).generate_cohort()
    with_reference = LongitudinalSimulator(
        replace(
            base,
            n_leukocyte_reference_loci=20,
            leukocyte_channel_fraction=0.9,
        )
    ).generate_cohort()

    def reference_reads(cohort) -> list[int]:
        return [
            m.leukocyte_reference_reads
            for trajectories in cohort.values()
            for trajectory in trajectories
            for m in trajectory.measurements
        ]

    assert sum(reference_reads(without)) == 0
    assert sum(reference_reads(with_reference)) > 0


def test_the_reference_correction_equals_the_raw_without_a_reference_set() -> None:
    """With no reference set there is nothing to subtract."""
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=40,
        n_electrical_loci=50,
        n_loci=100,
    )
    cohort = LongitudinalSimulator(base).generate_cohort()
    for trajectories in cohort.values():
        for trajectory in trajectories:
            assert ElectricalChannelDetector.state_enrichment_reference_corrected(
                trajectory.measurements
            ) == pytest.approx(
                ElectricalChannelDetector.state_enrichment(trajectory.measurements),
                abs=1e-12,
            )


def test_no_panel_in_the_search_space_clears_k3() -> None:
    """The re-derivation's finding: the correction is not a budget problem.

    The search covered 200,000x to 20,000,000x with reference sets from 5 to 50
    loci, and nothing in it reached the programme's own K3 threshold. That is
    the reason the proposal asks for localisation rather than a bigger panel.
    """
    derivation_path = Path("results/leukocyte_audit/operating_point.json")
    if not derivation_path.exists():
        pytest.skip("the operating-point derivation has not been generated")
    derivation = json.loads(derivation_path.read_text())
    assert derivation["anything_clears_k3"] is False
    assert len(derivation["frontier"]) >= 6
    best = max(r["auc_reference_corrected"] for r in derivation["frontier"])
    assert best < 0.65
    # Even a perfect background subtraction does not reach it.
    best_oracle = max(r["auc_attributable"] for r in derivation["frontier"])
    assert best_oracle < 0.65


def test_the_report_states_the_finding() -> None:
    text = REPORT.read_text()
    for phrase in (
        "byte-identical",
        "inverts",
        "cannot survive",
        "upper bound",
        "QC and tumour-fraction tool",
        "localisation rate",
    ):
        assert phrase in text, phrase
