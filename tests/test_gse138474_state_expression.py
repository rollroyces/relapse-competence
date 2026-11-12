"""Tests for the treatment-naive SCLC comparator and the audit built on it.

The audit answers one of the two routes the gate review names for K2: whether
a treatment-naive SCLC cohort carries the relapse-competent state before
therapy. Its conclusion is a negative one, and a negative conclusion is only
worth anything if the arithmetic that produced it can be re-derived, so
these tests recompute the numbers from the artefacts rather than restating
them.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest

ARTEFACT = Path("results/gse138474/state_expression.json")
TABLE = Path("results/gse138474/state_expression.tsv")
REPORT = Path("docs/GSE138474-TREATMENT-NAIVE-SCLC.md")
SCRIPT = Path("scripts/gse138474_state_expression.py")
RELAPSED = Path("results/gse299684/state_expression.json")

PRIMARY = "detected"


@pytest.fixture(scope="module")
def audit() -> dict:
    if not ARTEFACT.exists():
        pytest.skip("the treatment-naive SCLC artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


@pytest.fixture(scope="module")
def relapsed() -> dict:
    if not RELAPSED.exists():
        pytest.skip("the relapsed-cohort artefact has not been generated")
    return json.loads(RELAPSED.read_text())


def _solid_tissue(audit: dict) -> list[dict]:
    return [lib for lib in audit["libraries"] if lib["compartment"] == "pdx"]


def test_the_artefact_records_the_dataset_and_the_state_gene(audit: dict) -> None:
    assert audit["dataset"]["accession"] == "GSE138474"
    assert audit["dataset"]["organism"] == "Homo sapiens"
    assert audit["dataset"]["state_gene"] == "YAP1"
    assert audit["dataset"]["primary_definition"] == PRIMARY


def test_every_library_carries_its_treatment_label(audit: dict) -> None:
    labels = {lib["treatment"] for lib in audit["libraries"]}
    assert "untreated" in labels
    assert "vehicle-treated" in labels
    assert any("relapsed" in label for label in labels)


def test_the_arms_partition_the_solid_tissue_libraries(audit: dict) -> None:
    solid = _solid_tissue(audit)
    arms = audit["arms"][PRIMARY]["arms"]
    counted = sum(arms[arm]["n_libraries"] for arm in ("untreated", "vehicle", "relapsed"))
    assert counted == len(solid)


def test_the_circulating_tumour_cell_series_is_reported_separately(audit: dict) -> None:
    arms = audit["arms"][PRIMARY]["arms"]
    circulating = [lib for lib in audit["libraries"] if lib["compartment"] == "ctc"]
    assert circulating, "the deposit has a circulating tumour cell series"
    assert arms["ctc_all"]["n_libraries"] == len(circulating)


def test_the_arm_medians_are_recomputable_from_the_libraries(audit: dict) -> None:
    arms = audit["arms"][PRIMARY]["arms"]
    for arm in ("untreated", "vehicle", "relapsed"):
        values = [
            lib["state_definitions"][PRIMARY]["state_fraction"]
            for lib in _solid_tissue(audit)
            if lib["arm"] == arm
        ]
        assert arms[arm]["n_libraries"] == len(values)
        assert arms[arm]["median_state_fraction"] == pytest.approx(
            statistics.median(values)
        )


def test_the_state_fraction_is_yap1_positive_over_malignant(audit: dict) -> None:
    for lib in audit["libraries"]:
        entry = lib["state_definitions"][PRIMARY]
        assert entry["n_yap1_positive"] + entry["n_yap1_negative"] == entry["n_malignant"]
        if entry["n_malignant"]:
            assert entry["state_fraction"] == pytest.approx(
                entry["n_yap1_positive"] / entry["n_malignant"]
            )


def test_the_threshold_is_half_the_relapsed_cohorts_pooled_fraction(
    audit: dict, relapsed: dict
) -> None:
    sweep = relapsed["state_definition_sweep"]
    primary = next(entry for entry in sweep if entry["definition"] == PRIMARY)
    pooled = primary["n_yap1_positive"] / (
        primary["n_yap1_positive"] + primary["n_yap1_negative"]
    )
    assert pooled == pytest.approx(0.10402781802376122)
    assert audit["decision"]["threshold"] == pytest.approx(pooled / 2)


def test_the_decision_follows_from_the_arms(audit: dict) -> None:
    arms = audit["arms"][PRIMARY]["arms"]
    decision = audit["decision"]
    untreated = arms["untreated"]["median_state_fraction"]
    relapsed = arms["relapsed"]["median_state_fraction"]
    threshold = decision["threshold"]
    present = untreated >= threshold
    assert decision["k2_route_taken"] is present
    assert decision["relapsed_arm_carries_the_state"] is (relapsed >= threshold)
    if not present and relapsed < threshold:
        assert decision["route_evaluable"] is False
        assert "not evaluable" in decision["status"]
    else:
        assert decision["route_evaluable"] is True


def test_the_cohort_cannot_answer_the_route_in_either_arm(audit: dict) -> None:
    """The negative result is a statement about the cohort, not about biology."""
    arms = audit["arms"][PRIMARY]["arms"]
    threshold = audit["decision"]["threshold"]
    assert arms["untreated"]["median_state_fraction"] < threshold
    assert arms["relapsed"]["median_state_fraction"] < threshold


def test_the_depth_is_comparable_with_the_relapsed_cohort(audit: dict) -> None:
    """The complexity control: a shallower library would find less state."""
    depths = [
        lib["complexity"]["median_genes_detected"]
        for lib in _solid_tissue(audit)
        if lib["complexity"]["median_genes_detected"]
    ]
    median = statistics.median(depths)
    assert median > 2500, f"the solid-tissue libraries are too shallow ({median})"


def test_the_top_decile_definition_is_flagged_as_degenerate(audit: dict) -> None:
    """With a rare state the 90th percentile is zero and the rule selects all."""
    for lib in audit["libraries"]:
        entry = lib["state_definitions"]["top_decile"]
        if entry.get("degenerate_zero_threshold"):
            assert entry["state_fraction"] == pytest.approx(1.0)
            break
    else:
        pytest.fail("no library reported a degenerate top-decile threshold")


def test_the_deposit_defects_are_recorded_not_resolved_silently(audit: dict) -> None:
    formats = {lib["accession"]: lib["matrix_format"] for lib in audit["libraries"]}
    assert "dense_tsv" in formats.values(), "the dense library is not recorded"
    names = {
        lib["accession"]: lib["deposited_file_name"] for lib in audit["libraries"]
    }
    assert "GSM4104165_SC68_veh.LB19002.matrix.tar.gz" == names["GSM4104165"]
    assert audit["libraries"][0]["title"] == "SC16.LB17028"


def test_the_script_matches_the_deposits_member_names(audit: dict) -> None:
    source = SCRIPT.read_text()
    for member in ("barcodes.tsv", "barcodes.txt", "genes.tsv", "matrix.mtx", "matrix.txt"):
        assert member in source


def test_the_table_and_the_artefact_agree(audit: dict) -> None:
    if not TABLE.exists():
        pytest.skip("the per-library table has not been written")
    rows = TABLE.read_text().strip().split("\n")[1:]
    assert len(rows) == len(audit["libraries"])
    by_accession = {lib["accession"]: lib for lib in audit["libraries"]}
    for row in rows:
        fields = row.split("\t")
        library = by_accession[fields[0]]
        entry = library["state_definitions"][PRIMARY]
        assert int(fields[8]) == entry["n_malignant"]
        assert int(fields[9]) == entry["n_yap1_positive"]
        assert float(fields[10]) == pytest.approx(entry["state_fraction"], abs=1e-6)


def test_the_report_states_the_numbers_the_artefact_records(audit: dict) -> None:
    if not REPORT.exists():
        pytest.skip("the report has not been written")
    text = REPORT.read_text()
    decision = audit["decision"]
    arms = audit["arms"][PRIMARY]["arms"]
    assert decision["status"] in text
    assert f"{arms['untreated']['median_state_fraction']:.5f}" in text
    assert f"{arms['relapsed']['median_state_fraction']:.5f}" in text
    assert "GSE138474" in text
    assert "0.104" in text


def test_the_gate_review_does_not_claim_k2_was_evaluated(audit: dict) -> None:
    review = Path("docs/GATE-REVIEW.md").read_text()
    row = next(line for line in review.splitlines() if line.startswith("| **K2**"))
    assert "not evaluable" in row
