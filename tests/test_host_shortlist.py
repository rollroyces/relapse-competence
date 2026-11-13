"""Tests for the host shortlist.

The shortlist is where the programme's remaining PLCO dependency becomes
concrete: CDAS wants a professor who will also give the requester a standing
at their institution, and CDAS publishes every approved PLCO project with
its Principal Investigator and institution. The list is a record of a public
source, so the tests check that the record carries what the source says and
that nothing in it pretends to have been done.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SHORTLIST = Path("docs/HOST-SHORTLIST.md")
INVITATION = Path("docs/HOST-INVITATION.md")
README = Path("README.md")
ARTEFACT = Path("results/application_tracker/application_tracker.json")


@pytest.fixture(scope="module")
def shortlist() -> str:
    if not SHORTLIST.exists():
        pytest.skip("the host shortlist has not been written")
    return SHORTLIST.read_text()


def test_the_shortlist_lists_twenty_approved_projects(shortlist: str) -> None:
    rows = [
        line
        for line in shortlist.splitlines()
        if line.startswith("| ")
        and "Principal Investigator" not in line
        and not line.startswith("|---")
    ]
    assert len(rows) == 20, len(rows)


def test_the_shortlist_records_the_companies(shortlist: str) -> None:
    for company in (
        "Wholomics GmbH",
        "Pictor Labs",
        "AIRA Matrix",
        "Artera Inc.",
        "InfotechSoft",
    ):
        assert company in shortlist, company


def test_the_shortlist_records_the_requesters_own_institution(shortlist: str) -> None:
    assert "University of Michigan" in shortlist


def test_the_shortlist_claims_nothing_has_been_sent(shortlist: str) -> None:
    assert "Nothing has been sent to anyone" in shortlist
    assert "not an approach" in shortlist


def test_the_shortlist_is_linked_from_the_letter_and_the_readme(shortlist: str) -> None:
    assert "HOST-SHORTLIST.md" in INVITATION.read_text()
    assert "HOST-SHORTLIST.md" in README.read_text()


def test_the_tracker_records_the_shortlist_step() -> None:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    tracker = json.loads(ARTEFACT.read_text())
    steps = [
        row["Step"]
        for row in tracker["steps"]
        if row["Application"] == "PLCO-DATA"
    ]
    assert any("host shortlist" in step for step in steps)
    facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
    assert any(
        "company as Principal Investigator" in name and "Wholomics" in value
        for name, value in facts.items()
    )
