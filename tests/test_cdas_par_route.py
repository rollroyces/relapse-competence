"""Tests for the PAR-25-248 route into the PLCO biospecimens.

The route was found on 2026-11-12 by re-reading CDAS's own list of PLCO
project types: it is the only PLCO route that carries funding with it, and
its first step has a window that closes in weeks rather than months. Its
claims are about deadlines and about what the form asks for, so the tests
check that the record carries the same numbers the source does and that the
route is in the tracker rather than only in prose.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ARTEFACT = Path("results/application_tracker/application_tracker.json")
REPORT = Path("docs/DATA-ACCESS-APPLICATIONS.md")


@pytest.fixture(scope="module")
def tracker() -> dict:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


@pytest.fixture(scope="module")
def report() -> str:
    return REPORT.read_text()


def test_the_tracker_records_the_par_route(tracker: dict) -> None:
    applications = {row["Application"]: row for row in tracker["applications"]}
    assert "PLCO-PAR" in applications
    assert "PAR-25-248" in applications["PLCO-PAR"]["Access route"]
    assert applications["PLCO-PAR"]["Route verified"].startswith("yes")


def test_the_par_facts_are_recorded_with_their_sources(tracker: dict) -> None:
    facts = {row["Fact"]: row for row in tracker["external_facts"]}
    par = {name: fact for name, fact in facts.items() if "PAR-25-248" in name}
    assert len(par) == 7, sorted(par)
    for name, fact in par.items():
        assert fact["Source"], name
        assert fact["Verified on"] == "2026-11-12", name


def test_the_request_form_step_carries_its_window(tracker: dict) -> None:
    steps = [
        row
        for row in tracker["steps"]
        if row["Application"] == "PLCO-PAR"
        and "Request Form for Specimen Verification" in row["Step"]
        and "Submit" in row["Step"]
    ]
    assert len(steps) == 1
    step = steps[0]
    assert "Dec 8, 2026" in step["Step"]
    assert "Jan 8, 2027" in step["Step"]
    assert not step["Status"].startswith("done"), step["Status"]


def test_the_route_decision_is_a_step_of_its_own(tracker: dict) -> None:
    steps = [
        row
        for row in tracker["steps"]
        if row["Application"] == "PLCO-PAR" and "Choose between" in row["Step"]
    ]
    assert len(steps) == 1
    assert "cannot be run at the same time" in steps[0]["Step"]
    assert not steps[0]["Status"].startswith("done")


def test_the_exclusivity_is_a_fact_not_only_a_sentence(tracker: dict) -> None:
    facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
    assert any(
        "exclusivity" in name and "prohibited" in value
        for name, value in facts.items()
    )


def test_the_eems_deadline_row_carries_the_preliminary_window(tracker: dict) -> None:
    facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
    deadline = facts["PLCO EEMS biospecimen application deadline"]
    assert "Feb 18, 2027" in deadline
    assert "Aug 5, 2026" in deadline


def test_the_report_states_the_dates_and_the_exclusivity(report: str) -> None:
    flat = " ".join(report.replace(">", " ").split())
    assert "Dec. 8, 2026 until Jan. 8, 2027" in flat
    assert "no later than 3 weeks after it is submitted" in flat
    assert "Oct 8, 2027" in flat
    assert "prohibited from submitting an application to both" in flat
    assert "Confirmatory Letter must be included in the grant application" in flat


def test_the_report_says_no_application_has_been_submitted(report: str) -> None:
    assert "No application has been submitted" in report
