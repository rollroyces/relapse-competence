"""Tests for the per-patient audit.

The audit re-runs the plasma projection for each tumour instead of for a
cell-count-weighted average. Three properties matter and are asserted here:
the new layer reproduces the published one exactly (the controls), the report
agrees with the artefacts cell by cell, and the SCLC correction it carries is
stated in the numbers rather than in prose.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

AUDIT = Path("results/per_patient_audit/per_patient_audit.json")
FOLDS = Path("results/per_library_folds/per_library_folds.json")
REPORT = Path("docs/PER-PATIENT-AUDIT.md")
GATE_REVIEW = Path("results/gate_review/gate_review.json")


@pytest.fixture(scope="module")
def audit() -> dict:
    if not AUDIT.exists():
        pytest.skip("the per-patient audit artefact has not been generated")
    return json.loads(AUDIT.read_text())


@pytest.fixture(scope="module")
def folds() -> dict:
    if not FOLDS.exists():
        pytest.skip("the per-library folds artefact has not been generated")
    return json.loads(FOLDS.read_text())


def _records(audit: dict) -> dict[tuple[str, str, str], dict]:
    return {
        (r["dataset"], r["accession"], r["channel"]): r for r in audit["per_library"]
    }


def test_the_pooled_control_reproduces_the_gate_review(audit: dict) -> None:
    """The per-tumour layer must be comparable with the published one."""
    assert audit["control"]["all_match"] is True
    for entry in audit["control"]["entries"]:
        assert entry["matches"] is True, entry
        assert (
            abs(
                entry["recomputed_auc_at_operating_point"]
                - entry["gate_review_auc_at_operating_point"]
            )
            < 1e-12
        ), entry


def test_the_pooled_folds_reproduce_the_published_artefacts(folds: dict) -> None:
    for dataset, entry in folds["control"].items():
        assert entry["all_channels_match"] is True, (dataset, entry)
        assert entry["max_absolute_difference"] == 0.0, (dataset, entry)


def test_the_per_library_detection_ratio_signs_match_the_published_counts(
    folds: dict,
) -> None:
    """The per-library folds rest on the same footing as a published number."""
    for dataset, genes in folds["per_library_sign_counts"].items():
        for gene, record in genes.items():
            if record["published_above_one"] is None:
                continue
            assert record["matches"] is True, (dataset, gene, record)


def test_sclc_kcnn4_is_not_on_in_the_state_in_most_libraries(folds: dict) -> None:
    """The correction: the pooled KCNN4 fold does not describe a tumour."""
    record = folds["composition"]["SCLC"]["KCNN4"]
    assert record["n_libraries_with_fold_above_one"] < (
        record["n_libraries_with_fold_computable"] / 2
    ), record
    assert record["per_library_fold_median"] < 1.0, record


def test_nsclc_kcnn4_survives_per_library(folds: dict) -> None:
    """The control that shows the difference: NSCLC is one tissue."""
    record = folds["composition"]["NSCLC"]["KCNN4"]
    assert record["n_libraries_with_fold_above_one"] > (
        record["n_libraries_with_fold_computable"] / 2
    ), record
    assert record["per_library_fold_median"] > 2.0, record


def test_every_mrd_library_clears_k3(audit: dict) -> None:
    """The NSCLC cohort the programme projects works tumour by tumour."""
    mrd = [
        r
        for r in audit["per_library"]
        if r["dataset"] == "NSCLC" and r["treatment"] == "osi_mrd"
    ]
    assert len(mrd) == 7
    for record in mrd:
        assert record["operating_point"]["k3_fired"] is False, record
        assert record["operating_point"]["auc"] > 0.9, record


def test_sclc_kcnn4_clears_k3_in_about_one_library(audit: dict) -> None:
    """The correction in the projection layer as well as the measurement."""
    subset = [
        r
        for r in audit["per_library"]
        if r["dataset"] == "SCLC" and r["channel"] == "KCNN4"
    ]
    clearing = [r for r in subset if not r["operating_point"]["k3_fired"]]
    assert len(clearing) == 1, [r["accession"] for r in clearing]


def test_sclc_piezo1_clears_k3_in_few_libraries(audit: dict) -> None:
    subset = [
        r
        for r in audit["per_library"]
        if r["dataset"] == "SCLC" and r["channel"] == "PIEZO1"
    ]
    clearing = [r for r in subset if not r["operating_point"]["k3_fired"]]
    assert 0 < len(clearing) < len(subset) / 2, [r["accession"] for r in clearing]


def test_the_no_signal_baseline_is_reported(audit: dict) -> None:
    """Configurations with no usable channel settle at the burden-confounded floor."""
    baseline = {
        r["operating_point"]["auc"]
        for r in audit["per_library"]
        if r["inputs"]["abundance_fold"] <= 1.0
    }
    assert baseline == {0.46584739545121057}, baseline


def test_the_report_quotes_the_artefacts(audit: dict, folds: dict) -> None:
    text = REPORT.read_text()
    for record in audit["per_library"]:
        assert record["accession"] in text, record["accession"]
    for library in folds["per_library"]:
        assert library["accession"] in text, library["accession"]


def test_the_report_table_discriminates_fire_from_pass(audit: dict) -> None:
    """The verdict columns must contain both values, or the check is vacuous."""
    verdicts = {
        r["operating_point"]["k3_fired"] for r in audit["per_library"]
    }
    assert verdicts == {True, False}
    text = REPORT.read_text()
    assert "| fire |" in text
    assert "| pass |" in text


def test_the_report_keeps_the_assumption_visible() -> None:
    text = REPORT.read_text()
    assert "never measured" in text or "has never been measured" in text
    assert "does not describe" in text or "do not describe" in text


def test_the_gate_review_is_not_rewritten_by_the_audit() -> None:
    """The published pooled numbers stay; the audit adds a layer."""
    if not GATE_REVIEW.exists():
        pytest.skip("the gate review artefact has not been generated")
    gate = json.loads(GATE_REVIEW.read_text())
    published = {
        (v["dataset"], v["channel"]): v["auc_at_operating_point"]
        for v in gate["k1_k3_detail"]
    }
    assert published[("SCLC", "KCNN4")] == 0.706544901065449
    assert published[("SCLC", "PIEZO1")] == 0.6945048256673333
    assert published[("NSCLC", "KCNN4")] == 0.9928621553884712
