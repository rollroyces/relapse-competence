"""Tests for the data-access application tracker.

The tracker is a statement about what has been asked for and what has not.
Two properties matter: it must not drift from the document it is generated
from, and it must not record an application as submitted that has not been.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ARTEFACT = Path("results/application_tracker/application_tracker.json")
REPORT = Path("docs/DATA-ACCESS-APPLICATIONS.md")
SCRIPT = Path("scripts/application_tracker.py")
FOLDS = Path("results/per_library_folds/per_library_folds.json")
AUDIT = Path("results/per_patient_audit/per_patient_audit.json")


def _load_script():
    spec = importlib.util.spec_from_file_location("application_tracker", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tracker_script = _load_script()


@pytest.fixture(scope="module")
def tracker() -> dict:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


@pytest.fixture(scope="module")
def document() -> dict:
    if not REPORT.exists():
        pytest.skip("the data-access applications document does not exist")
    return tracker_script.parse(REPORT.read_text())


def test_the_artefact_matches_the_document(tracker: dict, document: dict) -> None:
    """The artefact is a projection of the document, not a second source."""
    assert tracker_script._comparable(tracker) == tracker_script._comparable(document)


def test_the_tracker_covers_every_application(tracker: dict) -> None:
    applications = {row["Application"] for row in tracker["applications"]}
    assert applications == {
        "PLCO-DATA",
        "PLCO-EEMS",
        "PLCO-PAR",
        "TZL-EGA",
        "TZL-DIRECT",
    }
    assert {row["Application"] for row in tracker["steps"]} == applications


def test_every_step_has_an_owner_and_a_status(tracker: dict) -> None:
    for row in tracker["steps"]:
        assert row["Owner"].strip(), row
        assert row["Status"].strip(), row


def test_the_ega_route_is_recorded_as_unverified(tracker: dict) -> None:
    """The catalogue query found no deposit, and that has to be on the record."""
    applications = {row["Application"]: row for row in tracker["applications"]}
    assert applications["TZL-EGA"]["Route verified"].startswith("no")
    facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
    assert any(
        "matching Taizhou" in fact and value == "0" for fact, value in facts.items()
    )


def test_no_application_is_recorded_as_submitted(tracker: dict) -> None:
    """A data-access request is an institutional act.

    The tracker may record a submission once one has happened, but nothing in
    this repository may assert that one has without a record of it, and the
    document has to keep saying so while that is the case.
    """
    applications = {row["Application"]: row for row in tracker["applications"]}
    for name, row in applications.items():
        assert "submitted" not in row["Status"].lower(), (name, row)
    text = REPORT.read_text()
    assert "No application has been submitted" in text


def test_the_quoted_measurements_match_the_artefacts(tracker: dict) -> None:
    """The applications are justified by this repository's own numbers."""
    if not FOLDS.exists() or not AUDIT.exists():
        pytest.skip("the measurement artefacts are not present")
    folds = json.loads(FOLDS.read_text())
    audit = json.loads(AUDIT.read_text())
    text = REPORT.read_text()

    nsclc = folds["composition"]["NSCLC"]["KCNN4"]
    assert (
        f"{nsclc['n_libraries_with_fold_above_one']} of "
        f"{nsclc['n_libraries_with_fold_computable']}" in text
    )

    mrd = [
        r
        for r in audit["per_library"]
        if r["dataset"] == "NSCLC" and r["treatment"] == "osi_mrd"
    ]
    clearing = sum(1 for r in mrd if not r["operating_point"]["k3_fired"])
    assert clearing == len(mrd)
    assert f"{clearing} of {len(mrd)}" in text


def test_the_document_does_not_promise_post_treatment_data() -> None:
    """Neither cohort is post-treatment, and the document has to say so."""
    text = REPORT.read_text()
    assert "Neither PLCO nor TZL is a" in text
    assert "post-treatment" in text


def test_the_check_fails_when_the_document_drifts(tmp_path: Path) -> None:
    """The check has to bite, or it is not a check."""
    text = REPORT.read_text()
    altered = text.replace(
        "| PLCO-DATA | Create the CDAS account and log in with RAS | PI | not started | — |",
        "| PLCO-DATA | Create the CDAS account and log in with RAS | PI | done | — |",
    )
    assert altered != text
    parsed = tracker_script.parse(altered)
    assert parsed["steps"] != tracker_script.parse(text)["steps"]


def test_a_changed_table_shape_is_refused() -> None:
    """A table whose columns changed has to be refused, not silently read."""
    text = REPORT.read_text().replace(
        tracker_script.FACT_TABLE_ANCHOR,
        "| Fact | Value | Source |",
    )
    with pytest.raises(SystemExit):
        tracker_script.parse(text)
