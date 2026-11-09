"""Tests for the gate review.

The gate review applies the programme's own killing conditions to the current
evidence. Two properties matter and are asserted here: the conditions that
cannot be evaluated are recorded as such rather than passed, and the
configuration that carries the programme's readout is named.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ARTEFACT = Path("results/gate_review/gate_review.json")
REPORT = Path("docs/GATE-REVIEW.md")


@pytest.fixture(scope="module")
def gate() -> dict:
    if not ARTEFACT.exists():
        pytest.skip("the gate review artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


def test_all_five_conditions_are_evaluated(gate: dict) -> None:
    conditions = {c["id"]: c for c in gate["conditions"]}
    assert set(conditions) == {"K1", "K2", "K3", "K4", "K5"}
    for condition in conditions.values():
        assert condition["status"] in {"fired", "not_fired", "not_evaluable"}


def test_the_unevaluable_conditions_are_not_passed(gate: dict) -> None:
    conditions = {c["id"]: c for c in gate["conditions"]}
    assert conditions["K2"]["status"] == "not_evaluable"
    assert conditions["K5"]["status"] == "not_evaluable"


def test_k4_has_fired_for_systemic_delivery(gate: dict) -> None:
    conditions = {c["id"]: c for c in gate["conditions"]}
    assert conditions["K4"]["status"] == "fired"


def test_the_named_state_candidates_survive_k1_and_k3(gate: dict) -> None:
    """The three channels that carry the programme's readout must survive."""
    for dataset, channel in (
        ("SCLC", "KCNN4"),
        ("SCLC", "PIEZO1"),
        ("NSCLC", "KCNN4"),
    ):
        verdict = next(
            v
            for v in gate["k1_k3_detail"]
            if v["dataset"] == dataset and v["channel"] == channel
        )
        assert verdict["state_candidate_in_tissue"] is True, (dataset, channel)
        assert verdict["k1_fired"] is False, (dataset, channel)
        assert verdict["k3_fired"] is False, (dataset, channel)


def test_a_candidate_that_fires_is_only_a_marginal_one(gate: dict) -> None:
    """A channel that barely clears the tissue bar cannot carry the readout."""
    for verdict in gate["k1_k3_detail"]:
        if verdict["state_candidate_in_tissue"] and verdict["k1_fired"]:
            assert verdict["abundance_fold_state_vs_tumour"] < 1.5, verdict
            assert "marginal" in REPORT.read_text().lower()


def test_piezo1_is_not_a_readout_in_nsclc(gate: dict) -> None:
    """The state does not over-express PIEZO1 in NSCLC, so it carries nothing."""
    verdict = next(
        v
        for v in gate["k1_k3_detail"]
        if v["dataset"] == "NSCLC" and v["channel"] == "PIEZO1"
    )
    assert verdict["abundance_fold_state_vs_tumour"] < 1.0
    assert verdict["k1_fired"] is True
    assert verdict["k3_fired"] is True


def test_kcnn4_is_the_readout_that_survives_in_nsclc(gate: dict) -> None:
    verdict = next(
        v
        for v in gate["k1_k3_detail"]
        if v["dataset"] == "NSCLC" and v["channel"] == "KCNN4"
    )
    assert verdict["auc_at_operating_point"] > 0.9
    assert verdict["k1_fired"] is False
    assert verdict["k3_fired"] is False


def test_the_verdicts_rest_on_a_projection_and_say_so(gate: dict) -> None:
    for condition in gate["conditions"]:
        if condition["id"] in {"K1", "K3"}:
            assert "not a plasma measurement" in condition["basis"]
    text = REPORT.read_text()
    assert "not a plasma measurement" in text or "model-based projection" in text
    assert "would change" in text.lower()


def _report_configuration_table() -> list[list[str]]:
    """Rows of the report's own configuration table, header first."""
    text = REPORT.read_text()
    anchor = "### The configurations that matter"
    assert anchor in text, "the gate review report lost its configuration table"
    rows: list[list[str]] = []
    for line in text[text.index(anchor) :].splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") and c for c in cells):
            continue
        rows.append(cells)
    return rows


def test_the_report_configuration_table_matches_the_artefact(gate: dict) -> None:
    """Every cell of the report's table must be the artefact's number.

    The check is in both directions: the report cannot quote a number the
    artefact does not hold, and it cannot call a configuration a pass where
    the artefact says the condition fires.
    """
    rows = _report_configuration_table()
    assert len(rows) > 1
    header = [c.replace("*", "").strip() for c in rows[0]]
    assert header == [
        "Dataset",
        "Channel",
        "Tissue fold",
        "State fraction",
        "Bulk elevation",
        "AUC at 200k× / 200",
        "K1",
        "K3",
    ]
    measured = {
        (m["dataset"], m["channel"]): m for m in gate["measured_parameters"]
    }
    verdicts = {(v["dataset"], v["channel"]): v for v in gate["k1_k3_detail"]}
    fired = {c["id"]: set(c.get("fired_for") or []) for c in gate["conditions"]}
    for row in rows[1:]:
        assert len(row) == len(header)
        dataset = row[0].replace("*", "").strip()
        channel = row[1].replace("*", "").strip()
        key = f"{dataset} / {channel}"
        pair = (dataset, channel)
        assert pair in measured, key
        assert pair in verdicts, key
        m = measured[pair]
        v = verdicts[pair]
        assert float(row[2].replace("*", "")) == round(
            m["abundance_fold_state_vs_tumour"], 3
        ), key
        assert float(row[3].replace("*", "")) == round(m["state_fraction"], 3), key
        assert float(row[4].replace("*", "")) == round(m["bulk_elevation"], 3), key
        assert float(row[5].replace("*", "")) == round(
            v["auc_at_operating_point"], 4
        ), key
        for condition_id in ("K1", "K3"):
            cell = row[header.index(condition_id)].replace("*", "").strip().lower()
            assert cell in {"fire", "pass"}, (key, condition_id, cell)
            assert (cell == "fire") == (key in fired[condition_id]), (
                key,
                condition_id,
                cell,
            )


def test_the_report_table_discriminates_fire_from_pass(gate: dict) -> None:
    """The table must contain both verdicts, or the check above is vacuous."""
    rows = _report_configuration_table()
    header = [c.replace("*", "").strip() for c in rows[0]]
    cells = {
        row[header.index("K1")].replace("*", "").strip().lower()
        for row in rows[1:]
    }
    assert "fire" in cells
    assert "pass" in cells
