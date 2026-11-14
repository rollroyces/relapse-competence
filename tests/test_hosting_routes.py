"""Tests for the hosting routes: how the requester can be "part of the institution".

The programme's earlier reading was that the requester had to be adopted by
an institution. CDAS's own approved-project record contains a sole trader, a
visiting researcher and a chief executive as approved PIs, and the germline
route requires employment where CDAS may require only affiliation. These
tests bind that record to the facts table, and bind the stated limits as
firmly as the findings, because a document that only records what is
convenient would be worse than no document.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

HOSTING = Path("docs/HOSTING-ROUTES.md")
SHORTLIST = Path("docs/HOST-SHORTLIST.md")
APPLICATIONS = Path("docs/DATA-ACCESS-APPLICATIONS.md")
ARTEFACT = Path("results/application_tracker/application_tracker.json")


@pytest.fixture(scope="module")
def flat() -> str:
    return " ".join(HOSTING.read_text().split())


def test_the_document_exists_and_says_what_it_is() -> None:
    assert HOSTING.exists()
    text = HOSTING.read_text()
    assert "researched and recorded" in text
    assert "2026-11-13" in text
    assert "Nothing here has been sent to" in text


def test_the_precedents_are_quoted(flat: str) -> None:
    """The finding is that CDAS approved PIs in the requester's position.

    The quotations have to be CDAS's own field values, because that is the
    whole argument: the Institution field and the Position Title field.
    """
    for phrase in (
        "Deborah Goldwasser",
        "Institution: **Statistical Consultant**",
        "Hilary Robbins",
        "**Visiting researcher**",
        "Patrick Strasser",
        "Institution: **Wholomics GmbH**",
        "Position Title: **CEO**",
        "Brian Denton",
        "Position Title: **Professor**",
    ):
        assert phrase in flat, phrase


def test_the_precedents_name_their_project_ids(flat: str) -> None:
    for pid in ("NLST-43", "PLCO-380", "2026-0185", "PLCO-2057"):
        assert pid in flat, pid


def test_the_asymmetry_is_recorded(flat: str) -> None:
    """Affiliation is not employment, and the germline route needs employment.

    This is the finding that reorders the routes, so it is checked in the
    document, in the fact table, and by the exact wording of the policy.
    """
    assert "the investigators are full time employees" in flat
    assert "no sponsorship, courtesy appointment or covered-visitor status" in flat
    assert "dbGaP" in flat


def test_the_company_route_is_evidenced(flat: str) -> None:
    """Wholomics is running the requester's own experiment on PLCO."""
    for phrase in (
        "Analytical Suitability and Storage-Stability Pilot",
        "50 incident solid-tumor cases",
        "50 matched cancer-free controls",
        "T0–T2",
        "T4/T5",
        "Become a Partner",
        "for Research Use Only",
        "wholomics.com/research-partnerships/",
        "info@wholomics.com",
    ):
        assert phrase in flat, phrase


def test_the_non_employment_mechanisms_are_evidenced(flat: str) -> None:
    assert "does not include compensation or confer employee status" in flat
    assert "courtesy (unpaid) appointments" in flat
    assert "Neither holds an\napproved PLCO project" in flat or (
        "Neither holds an" in flat and "approved PLCO project" in flat
    )


def test_the_dead_source_is_recorded(flat: str) -> None:
    """A source that now 404s must not be cited as though it were live."""
    assert "now returns 404" in flat
    assert "is not cited here as though it were" in flat


def test_the_pagination_correction_is_recorded(flat: str) -> None:
    """The record said pagination needed a session. It does not."""
    assert "URL-form error" in flat
    assert "data_types=plco_data" in flat
    assert "bio_types=plco_bio_par" in flat
    assert "1-20 of 1735" in flat


def test_the_limits_are_as_firm_as_the_findings(flat: str) -> None:
    for limit in (
        "does not establish that CDAS would approve the requester today",
        "does not establish that a visiting appointment satisfies CDAS",
        "does not establish that any institution would actually extend an "
        "appointment to a researcher with no current post",
        "does not establish that Wholomics would want the requester",
        "does not establish a processing time for anything",
        "does not establish that the requester qualifies as a \"senior researcher\"",
    ):
        assert limit in flat, limit


def test_the_shortlist_no_longer_says_it_does_not_rank() -> None:
    """A stale paragraph contradicted the choice the same file records."""
    sl = " ".join(SHORTLIST.read_text().split())
    assert "It does not rank the candidates" not in sl
    assert "URL-form error" in sl
    assert "data_types=plco_data" in sl
    assert "Brian Denton" in sl
    assert "PLCO-2057" in sl


def test_the_applications_document_links_the_routes() -> None:
    text = " ".join(APPLICATIONS.read_text().split())
    assert "HOSTING-ROUTES.md" in text


def test_the_fact_table_records_the_precedents_and_the_limits() -> None:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    facts = {
        row["Fact"]: row["Value"]
        for row in json.loads(ARTEFACT.read_text())["external_facts"]
    }
    consultant = facts.get(
        "CDAS approved PI who is a self-employed consultant", ""
    )
    assert "Statistical Consultant" in consultant
    assert "NLST-43" in consultant

    visiting = facts.get(
        'CDAS approved PI whose title is "Visiting researcher", on PLCO', ""
    )
    assert "Visiting researcher" in visiting
    assert "PLCO-380" in visiting

    germline = facts.get("PLCO germline route identity requirement", "")
    assert "full time employees" in germline

    pagination = facts.get("CDAS approved-project pagination", "")
    assert "data_types=plco_data" in pagination

    pilot = facts.get("PLCO project that is the requester's own experiment", "")
    assert "100 specimens" in pilot
    assert "50 incident solid-tumour cases" in pilot
    assert "50 matched cancer-free controls" in pilot
    assert "T0-T2" in pilot


def test_the_tracker_records_the_route_decision() -> None:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    steps = json.loads(ARTEFACT.read_text())["steps"]
    chosen = [
        row
        for row in steps
        if row["Application"] == "PLCO-DATA"
        and row["Step"].startswith("Choose the route by which")
    ]
    assert len(chosen) == 1
    assert "four routes identified" in chosen[0]["Status"]
