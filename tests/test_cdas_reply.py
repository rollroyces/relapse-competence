"""Tests for the CDAS reply and what it did to the route.

The reply arrived on 2026-11-12 and it is the most consequential document in
the programme's record so far: it closed both PLCO routes for a requester
with no institutional appointment, and it produced numbers — the lung tissue
inventory and the germline route — that the applications now depend on. These
tests check that the record carries the reply faithfully, that the numbers
are the ones the source gives, and that the letters were changed to match.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ARTEFACT = Path("results/application_tracker/application_tracker.json")
REPORT = Path("docs/DATA-ACCESS-APPLICATIONS.md")
INQUIRY = Path("docs/plco-cdas-submission-package/07-scoping-inquiry.md")
INVITATION = Path("docs/HOST-INVITATION.md")


@pytest.fixture(scope="module")
def tracker() -> dict:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


@pytest.fixture(scope="module")
def inquiry() -> str:
    return INQUIRY.read_text()


@pytest.fixture(scope="module")
def report() -> str:
    return REPORT.read_text()


def _reply(text: str, tag: str) -> str:
    begin = f"<!-- BEGIN REPLY {tag} -->"
    end = f"<!-- END REPLY {tag} -->"
    assert begin in text and end in text, tag
    return text.split(begin)[1].split(end)[0].strip()


def test_the_reply_record_carries_the_three_answers(inquiry: str) -> None:
    for tag in ("B", "C", "D"):
        body = _reply(inquiry, tag)
        assert len(body) > 40, tag
        assert "**" not in body, tag


def test_the_reply_record_names_the_people_and_the_tickets(inquiry: str) -> None:
    flat = " ".join(inquiry.split())
    assert "Dayanna Sorto" in flat
    assert "Shannon Merkle" in flat
    assert "#1563" in flat
    assert "#1565" in flat


def test_the_reply_record_says_which_inquiry_is_outstanding(inquiry: str) -> None:
    assert "Message A has not been answered" in inquiry
    assert "Message E must not be sent" in inquiry


def test_the_report_quotes_the_reply_verbatim(inquiry: str, report: str) -> None:
    """A paraphrase in the report must not be able to stand for the reply."""
    flat_report = " ".join(report.replace(">", " ").split())
    for tag, sentence in (
        (
            "C",
            "you will need to find a professor to submit this data request and "
            "you must be part of the institution to be able to have access to "
            "CDAS data",
        ),
        (
            "D",
            "An MTA is required so we would need to be employed by a private "
            "company, a academic or research institution capable of executing "
            "that MTA.",
        ),
        (
            "B",
            "These are from primary lung tumors. To date, nothing has been done "
            "with the lung tissue so no markers exist.",
        ),
    ):
        assert sentence in _reply(inquiry, tag), tag
        assert sentence in flat_report, tag


def test_the_tissue_counts_are_the_published_ones(tracker: dict) -> None:
    facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
    selected = facts["PLCO lung tissue participants selected"]
    assert "1,030" in selected
    assert "434" in selected
    assert "433" in selected
    histology = facts["PLCO lung tissue by histology, with tumour cores"]
    assert "small cell 7" in histology
    overlap = facts["PLCO lung tissue participants also in the GWAS"]
    assert "348" in overlap and "347" in overlap


def test_the_germline_route_is_recorded_as_a_separate_application(tracker: dict) -> None:
    facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
    germline = facts["PLCO germline genotyping route"]
    assert "phs001286.v5.p2" in germline
    assert "dbGaP" in germline
    steps = [row["Step"] for row in tracker["steps"]]
    assert any("phs001286.v5.p2" in step for step in steps)
    assert any("whole-exome profiling" in step for step in steps)


def test_the_tracker_records_that_message_e_is_moot(tracker: dict) -> None:
    step = next(
        row
        for row in tracker["steps"]
        if row["Application"] == "PLCO-EEMS"
        and "biospecimen eligibility questions" in row["Step"]
    )
    assert "E is moot" in step["Status"]
    assert step["Status"].startswith("done")


def test_the_tracker_carries_the_corrected_deadlines(tracker: dict) -> None:
    steps = [row for row in tracker["steps"] if row["Application"] == "PLCO-EEMS"]
    final = next(row for row in steps if "EEMS final application" in row["Step"])
    assert "Apr 1, 2027" in final["Step"]
    deadline = next(
        row for row in steps if "Confirm the EEMS preliminary" in row["Step"]
    )
    assert "2027-02-18" in deadline["Status"]


def test_the_host_invitation_asks_for_a_standing_not_only_a_signature() -> None:
    text = INVITATION.read_text()
    letter = text.split("<!-- BEGIN HOST LETTER -->")[1]
    letter = letter.split("<!-- END HOST LETTER -->")[0].strip()
    assert len(letter) <= 6_000, len(letter)
    assert "](" not in letter, "the letter is pasted as plain text"
    assert "standing at your institution" in letter
    assert "PAR-25-248" in letter
    assert "[HOST]" in letter
