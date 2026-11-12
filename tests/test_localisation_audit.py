"""Tests for the per-molecule attribution model and the audit built on it.

The attribution model is an extension to the published model, so three things
have to hold: with it off the model is unchanged bit for bit, with it on the
attributed statistic behaves the way the assay specification says it should,
and the audit's controls reproduce the numbers the report quotes.
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

ARTEFACT = Path("results/localisation_audit/localisation_audit.json")
REPORT = Path("docs/LOCALISATION-AUDIT.md")
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
    if not ARTEFACT.exists():
        pytest.skip("the localisation audit artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


def _base(**overrides) -> SimulationConfig:
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT, seed=20261106, n_patients_per_arm=200
    )
    defaults = {
        "electrical_fold_change": 3.6979371667856475 - 1.0,
        "state_fraction_resistant": 0.3916913946587537,
        "sequencing_depth": 200_000,
        "n_loci": 150,
        "n_electrical_loci": 50,
    }
    defaults.update(overrides)
    return replace(base, **defaults)


def _aucs(config: SimulationConfig) -> tuple[float | None, float | None, float | None]:
    """The three AUCs: raw over the whole MRD+ cohort, and the two attributed
    forms over the participants the readout applies to."""
    outcomes, _ = collect_outcomes(config, target_specificity=0.98)
    mrd = [o for o in outcomes if o.split == "evaluation" and o.mrd_flagged]
    applicable = [o for o in mrd if o.has_informative_position]
    raw = _auc([o.electrical_enrichment for o in mrd], [o.relapsed for o in mrd])
    if not applicable:
        return raw, None, None
    labels = [o.relapsed for o in applicable]
    localised = _auc(
        [o.electrical_enrichment_localised for o in applicable], labels
    )
    corrected = _auc(
        [o.electrical_enrichment_localised_corrected for o in applicable], labels
    )
    return raw, localised, corrected


# --- the extension is default-off ---


def test_the_attribution_model_is_default_off() -> None:
    """An extension that is on by default would move the published numbers."""
    config = SimulationConfig()
    assert config.attribution_rate == 0.0


def test_the_golden_fixture_is_unchanged_with_the_attribution_off() -> None:
    """The guard that the extension does not move the published model.

    The committed fixture was captured on macOS, and the simulator's last-bit
    float output differs on Linux by the one or two units in the last place
    that ``exp`` and ``log`` produce differently there. So the invariant is
    the one the repository's own golden check already uses: the regenerated
    fixture must match the committed one within that platform tolerance, on
    every platform.
    """
    capture = _load_script("capture_default_model_reference", CAPTURE)
    checker = _load_script("check_default_model_reference", CHECK)
    committed = json.loads(FIXTURE.read_text())
    problems = checker.diff(committed, capture.capture())
    assert not problems, problems[:5]


def test_the_attribution_off_makes_no_extra_random_draw() -> None:
    """The platform-independent half of the guard.

    The attributable reads are drawn only when the attribution model is on, so
    with it off every measurement records no attributable reads at all.
    """
    cohort = LongitudinalSimulator(_base()).generate_cohort()
    seen = 0
    for trajectories in cohort.values():
        for trajectory in trajectories:
            assert not trajectory.has_informative_position
            assert trajectory.informative_positions == 0
            for m in trajectory.measurements:
                assert m.attributed_reads == 0
                seen += 1
    assert seen > 0


def test_the_attribution_does_something_when_it_is_on() -> None:
    """An extension that changes nothing when switched on is not an extension."""
    off = LongitudinalSimulator(_base()).generate_cohort()
    on = LongitudinalSimulator(
        _base(attribution_rate=1.0, informative_position_rate=1.0)
    ).generate_cohort()

    def attributed(cohort) -> list[int]:
        return [
            m.attributed_reads
            for trajectories in cohort.values()
            for t in trajectories
            for m in t.measurements
        ]

    def informative(cohort) -> list[bool]:
        return [
            t.has_informative_position
            for trajectories in cohort.values()
            for t in trajectories
        ]

    assert sum(attributed(off)) == 0
    assert sum(attributed(on)) > 0
    assert any(informative(on))


def test_the_attributable_reads_are_a_subset_of_the_channel_reads() -> None:
    """The attributable molecules are channel molecules, not extra ones."""
    cohort = LongitudinalSimulator(
        _base(attribution_rate=1.0, informative_position_rate=1.0)
    ).generate_cohort()
    seen = 0
    for trajectories in cohort.values():
        for trajectory in trajectories:
            for m in trajectory.measurements:
                assert m.attributed_reads <= m.electrical_reads
                seen += 1
    assert seen > 0


def test_the_attributed_statistic_is_undefined_with_the_attribution_off() -> None:
    """With no informative position there is nothing to attribute."""
    cohort = LongitudinalSimulator(_base()).generate_cohort()
    for trajectories in cohort.values():
        for trajectory in trajectories:
            assert (
                ElectricalChannelDetector.state_enrichment_localised(
                    trajectory.measurements
                )
                == 0.0
            )


# --- the mechanism behaves as the specification says ---


def test_the_attributed_statistic_ignores_the_leukocyte_compartment() -> None:
    """The structural claim: a leukocyte's channel molecule is never counted.

    The compartment cannot reach the numerator, so it cannot invert the
    attributed statistic the way it inverts the raw one.
    """
    values = []
    raws = []
    for leukocyte_fraction in (0.5, 0.9, 0.99):
        _, localised, corrected = _aucs(
            _base(
                leukocyte_channel_fraction=leukocyte_fraction,
                attribution_rate=1.0,
                informative_position_rate=1.0,
            )
        )
        values.append(corrected)
        raws.append(
            _aucs(
                _base(
                    leukocyte_channel_fraction=leukocyte_fraction,
                    attribution_rate=1.0,
                    informative_position_rate=1.0,
                )
            )[0]
        )
    assert max(values) - min(values) < 0.05
    assert max(raws) < 0.1


def test_the_raw_statistic_inverts_where_the_attributed_one_does_not() -> None:
    """The collapse the leukocyte audit found, and its way round."""
    raw_off, _, _ = _aucs(_base(leukocyte_channel_fraction=0.0))
    raw_on, localised_on, corrected_on = _aucs(
        _base(
            leukocyte_channel_fraction=0.99,
            attribution_rate=1.0,
            informative_position_rate=1.0,
        )
    )
    assert raw_off > 0.9
    assert raw_on < 0.1
    assert corrected_on > 0.8
    assert localised_on > 0.9


def test_the_attributed_statistic_measures_the_state_and_not_the_burden() -> None:
    """The control that makes the rest of the audit readable.

    With the two arms carrying the same state fraction, the floor-corrected
    statistic has to fall back to chance. If it does not, it is measuring
    burden, and the AUC it reports is not evidence about the state.
    """
    matched = _base(
        leukocyte_channel_fraction=0.99,
        attribution_rate=1.0,
        informative_position_rate=1.0,
        # Both arms carry the same state fraction, so the only thing left
        # separating them is their burden.
        state_fraction_resistant=0.10,
        state_fraction_persistent=0.10,
    )
    _, _, corrected_matched = _aucs(matched)
    _, _, corrected_realistic = _aucs(
        _base(
            leukocyte_channel_fraction=0.99,
            attribution_rate=1.0,
            informative_position_rate=1.0,
        )
    )
    assert corrected_matched is not None
    assert corrected_realistic is not None
    assert abs(corrected_matched - 0.5) < 0.1
    assert corrected_realistic > corrected_matched + 0.2


def test_the_floor_corrected_denominator_is_what_makes_that_true() -> None:
    """Without the correction the same statistic picks up burden instead.

    The sequencing-error floor sits in the denominator of both statistics but
    only in the numerator of the published one, so the raw-VAF form of the
    localised statistic acquires a separation that tracks burden.
    """
    matched = _base(
        leukocyte_channel_fraction=0.99,
        attribution_rate=1.0,
        informative_position_rate=1.0,
        state_fraction_resistant=0.10,
        state_fraction_persistent=0.10,
    )
    outcomes, _ = collect_outcomes(matched, target_specificity=0.98)
    mrd = [o for o in outcomes if o.split == "evaluation" and o.mrd_flagged]
    applicable = [o for o in mrd if o.has_informative_position]
    labels = [o.relapsed for o in applicable]
    raw_vaf = _auc([o.electrical_enrichment_localised for o in applicable], labels)
    corrected = _auc(
        [o.electrical_enrichment_localised_corrected for o in applicable], labels
    )
    assert raw_vaf is not None and corrected is not None
    assert raw_vaf > 0.85
    assert abs(corrected - 0.5) < 0.1


def test_a_participant_without_an_informative_position_is_not_measurable() -> None:
    """The specification's first stop rule is about the fraction who have one."""
    cohort = LongitudinalSimulator(
        _base(attribution_rate=1.0, informative_position_rate=0.5)
    ).generate_cohort()
    informative = [
        t.has_informative_position
        for trajectories in cohort.values()
        for t in trajectories
    ]
    assert 0.35 < sum(informative) / len(informative) < 0.65
    for trajectories in cohort.values():
        for trajectory in trajectories:
            for m in trajectory.measurements:
                if not trajectory.has_informative_position:
                    assert m.attributed_reads == 0


def test_more_informative_positions_raise_the_attribution_rate() -> None:
    """The multi-gene fallback: more positions, more attributable molecules."""
    single = LongitudinalSimulator(
        _base(attribution_rate=0.1, informative_position_rate=1.0)
    ).generate_cohort()
    multi = LongitudinalSimulator(
        _base(
            attribution_rate=0.1,
            informative_position_rate=1.0,
            informative_positions_mean=3.0,
        )
    ).generate_cohort()

    def attributed(cohort) -> int:
        return sum(
            m.attributed_reads
            for trajectories in cohort.values()
            for t in trajectories
            for m in t.measurements
        )

    assert attributed(multi) > attributed(single)


# --- the audit's own controls ---


def test_the_audit_control_reproduces_the_published_aucs(audit: dict) -> None:
    for entry in audit["control"]:
        assert entry["matches"] is True, entry
        assert entry["published_auc"] is not None, entry
        assert (
            abs(entry["recomputed_auc_raw"] - entry["published_auc"]) < 1e-9
        ), entry


def test_the_audit_control_finds_the_attributed_statistic_undefined(
    audit: dict,
) -> None:
    """With the attribution off, no participant has an informative position."""
    for entry in audit["control"]:
        assert entry["auc_localised_with_attribution_off"] is None, entry


def test_the_audit_state_control_separates_state_from_burden(audit: dict) -> None:
    """The control that has to hold for the audit's headline to mean anything."""
    for row in audit["state_control"]:
        assert (
            abs(row["auc_localised_corrected_matched_state"] - 0.5) < 0.1
        ), row
        assert (
            row["auc_localised_corrected_realistic"]
            > row["auc_localised_corrected_matched_state"]
        ), row


def test_the_audit_records_that_the_nscl_readout_clears_k3(audit: dict) -> None:
    rows = [
        r
        for r in audit["sweep"]
        if r["dataset"] == "NSCLC"
        and r["channel"] == "KCNN4"
        and r["leukocyte_fraction"] == 0.99
        and r["attribution_rate"] == 1.0
        and r["informative_position_rate"] == 1.0
        and r["sequencing_depth"] == 200000
    ]
    assert len(rows) == 1
    assert rows[0]["clears_k3"] is True
    assert rows[0]["auc_localised_corrected"] > 0.85


def test_the_audit_does_not_rescue_the_sclc_candidates(audit: dict) -> None:
    """The per-patient audit had already excluded them; this agrees."""
    for dataset, channel in (("SCLC", "KCNN4"), ("SCLC", "PIEZO1")):
        rows = [
            r
            for r in audit["sweep"]
            if r["dataset"] == dataset
            and r["channel"] == channel
            and r["leukocyte_fraction"] == 0.99
            and r["attribution_rate"] == 1.0
            and r["informative_position_rate"] == 1.0
            and r["sequencing_depth"] == 200000
        ]
        assert len(rows) == 1
        assert rows[0]["clears_k3"] is False, rows[0]


def test_the_report_states_the_finding() -> None:
    text = REPORT.read_text()
    for phrase in (
        "default-off",
        "byte-identical",
        "by construction",
        "the state, not the burden",
        "attribution rate",
        "informative position",
    ):
        assert phrase in text, phrase
