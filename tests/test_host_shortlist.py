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
import re
from pathlib import Path

import pytest

SHORTLIST = Path("docs/HOST-SHORTLIST.md")
INVITATION = Path("docs/HOST-INVITATION.md")
INQUIRY = Path("docs/plco-cdas-submission-package/07-scoping-inquiry.md")
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
        if re.match(
            r"\|\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\s*\|",
            line,
        )
    ]
    assert len(rows) == 20, len(rows)


def test_the_shortlist_records_the_chosen_host_and_the_order(shortlist: str) -> None:
    assert "Alex Bryant" in shortlist
    assert "University of Michigan" in shortlist
    assert "fallback order" in shortlist.lower()


def test_the_shortlist_corrects_the_filter_claim(shortlist: str) -> None:
    flat = " ".join(shortlist.split())
    assert "A correction to the record" in flat
    assert "It cannot" in flat


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


def test_the_choices_are_recorded_in_the_letters() -> None:
    """The decisions taken on 2026-11-13 have to be visible in the letters."""
    host = INVITATION.read_text()
    host_letter = host.split("<!-- BEGIN HOST LETTER -->")[1]
    host_letter = host_letter.split("<!-- END HOST LETTER -->")[0]
    assert "Professor Bryant" in host_letter
    assert "I studied at Michigan" in host_letter

    tzl_doc = Path("docs/TAIZHOU-COLLABORATION-REQUEST.md").read_text()
    tzl = tzl_doc.split("<!-- BEGIN TAIZHOU LETTER -->")[1]
    tzl = tzl.split("<!-- END TAIZHOU LETTER -->")[0]
    assert "pilot on ten aliquots" in tzl
    assert "If the archive's sponsor has to be consulted" in tzl

    laboratory = Path("docs/LABORATORY-INVITATION.md").read_text()
    assert "Held rather than sent" in laboratory
