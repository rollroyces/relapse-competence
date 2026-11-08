"""Tests for the GSE353299 NSCLC audit.

The NSCLC audit exists to test one thing -- whether the electrical reading of
a drug-tolerant persister population crosses from relapsed SCLC to
EGFR-mutant NSCLC -- and to correct a conclusion the SCLC audit drew from a
single disease. Both are asserted here against the generated artefacts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

NSCLC_ARTEFACT = Path("results/gse353299/state_expression.json")
SCLC_ARTEFACT = Path("results/gse299684/state_expression.json")
NSCLC_REPORT = Path("docs/GSE353299-STATE-EXPRESSION.md")
SCLC_REPORT_PATH = Path("docs/GSE299684-STATE-EXPRESSION.md")
PLAN = Path("docs/RESEARCH-PLAN.md")


@pytest.fixture(scope="module")
def nsclc() -> dict:
    if not NSCLC_ARTEFACT.exists():
        pytest.skip("the GSE353299 artefact has not been generated")
    return json.loads(NSCLC_ARTEFACT.read_text())


@pytest.fixture(scope="module")
def sclc() -> dict:
    if not SCLC_ARTEFACT.exists():
        pytest.skip("the GSE299684 artefact has not been generated")
    return json.loads(SCLC_ARTEFACT.read_text())


def _primary(artefact: dict) -> dict:
    primary = artefact["audit"]["primary_definition"]
    return next(s for s in artefact["state_definition_sweep"] if s["definition"] == primary)


def _genes(entry: dict) -> dict[str, dict]:
    return {c["gene"]: c for c in entry["channels"] if c.get("status") == "ok"}


def test_the_state_call_is_validated_on_an_orthogonal_axis(nsclc: dict) -> None:
    """The gate must recover the basaloid population the dataset's title names."""
    primary = _primary(nsclc)
    assert primary["state_validation"]["basaloid_enriched_in_state"] is True
    assert (
        primary["state_validation"]["basaloid_programme_mean_state_positive"]
        > 3 * primary["state_validation"]["basaloid_programme_mean_state_negative"]
    )


def test_the_state_is_more_frequent_after_treatment(nsclc: dict) -> None:
    """The dataset's own claim: the persister population emerges with drug exposure."""
    naive = [
        s["state_positive_fraction_of_malignant"]
        for s in nsclc["per_sample"]
        if s["treatment"].strip().lower() == "treatment_naive"
        and s["state_positive_fraction_of_malignant"] is not None
    ]
    mrd = [
        s["state_positive_fraction_of_malignant"]
        for s in nsclc["per_sample"]
        if s["treatment"].strip().lower() == "osi_mrd"
        and s["state_positive_fraction_of_malignant"] is not None
    ]
    assert naive and mrd
    naive_median = sorted(naive)[len(naive) // 2]
    # Every minimal-residual-disease library is above the naive median.
    assert min(mrd) > naive_median


def test_kcnn4_marks_the_state_in_every_patient(nsclc: dict) -> None:
    genes = _genes(_primary(nsclc))
    assert genes["KCNN4"]["detection_ratio_vs_yap1negative"] > 2.0
    loso = nsclc["leave_one_sample_out"]["KCNN4"]
    assert loso["sign_is_stable"] is True
    assert loso["n_samples_with_ratio_above_one"] == len(nsclc["per_sample"])
    assert loso["min_ratio"] > 1.5


def test_the_electrical_marking_is_disease_specific(nsclc: dict, sclc: dict) -> None:
    """KCa3.1 crosses to NSCLC; Piezo1 is much weaker there than in SCLC."""
    nsclc_genes = _genes(_primary(nsclc))
    sclc_genes = _genes(_primary(sclc))
    assert nsclc_genes["KCNN4"]["detection_ratio_vs_yap1negative"] > 2.0
    assert sclc_genes["PIEZO1"]["detection_ratio_vs_yap1negative"] > 5.0
    assert (
        nsclc_genes["PIEZO1"]["detection_ratio_vs_yap1negative"]
        < sclc_genes["PIEZO1"]["detection_ratio_vs_yap1negative"] / 3
    )


def test_the_kcna3_and_cacna1e_results_hold(nsclc: dict) -> None:
    """Kv1.3 stays an immune channel; Cav2.3 stays out of lung."""
    genes = _genes(_primary(nsclc))
    assert genes["KCNA3"]["detection_ratio_vs_yap1negative"] < 1.0
    assert genes["KCNA3"]["detection_immune"] > genes["KCNA3"]["detection_yap1_positive"]
    assert genes["CACNA1E"]["detection_ratio_vs_yap1negative"] < 1.0


def test_the_state_cells_are_not_simply_harder_to_sequence(nsclc: dict) -> None:
    controls = {c["gene"]: c for c in nsclc["controls"]}
    assert (
        controls["ACTB"]["detection_yap1_positive"]
        >= controls["ACTB"]["detection_yap1_negative"]
    )


def test_the_sclc_conclusion_is_corrected_rather_than_deleted() -> None:
    """The SCLC measurement stands; the generalisation it supported does not."""
    text = SCLC_REPORT_PATH.read_text()
    assert "Not closed on expression grounds" in text
    assert "GSE353299-STATE-EXPRESSION.md" in text
    plan = PLAN.read_text()
    assert "blocked on the window, not on the target" in plan
    assert "closed for the lung indication" not in plan


def test_the_cross_disease_table_is_traceable_to_both_artefacts(
    nsclc: dict, sclc: dict
) -> None:
    """Both artefacts exist, and the report quotes both."""
    assert NSCLC_REPORT.exists()
    text = NSCLC_REPORT.read_text()
    nsclc_genes = _genes(_primary(nsclc))
    sclc_genes = _genes(_primary(sclc))
    for gene in ("KCNN4", "PIEZO1", "PIEZO2", "TMEM150C", "CACNA1E", "KCNA3", "STOML3"):
        assert gene in nsclc_genes and gene in sclc_genes
        assert f"{nsclc_genes[gene]['detection_ratio_vs_yap1negative']:.2f}" in text
