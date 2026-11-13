"""Tests for message F, the draft to CDAS about the PAR route's mechanics.

Message F is not a reply and it is not sent. It is a draft that asks four
questions the published instructions do not answer, two of which decide
whether the PAR route is available on the programme's own timeline. It has to
stay honest about being unsent, and the length it claims has to be the
length of the text it claims to describe.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

INQUIRY = Path("docs/plco-cdas-submission-package/07-scoping-inquiry.md")
INVITATION = Path("docs/HOST-INVITATION.md")
ARTEFACT = Path("results/application_tracker/application_tracker.json")


@pytest.fixture(scope="module")
def inquiry() -> str:
    return INQUIRY.read_text()


@pytest.fixture(scope="module")
def message(inquiry: str) -> str:
    begin = "<!-- BEGIN MESSAGE F -->"
    end = "<!-- END MESSAGE F -->"
    assert begin in inquiry and end in inquiry
    return inquiry.split(begin)[1].split(end)[0].strip()


def test_the_draft_is_delimited_plain_and_within_the_limit(message: str) -> None:
    assert 0 < len(message) <= 10_000
    assert "**" not in message
    assert "[TO FILL:" not in message


def test_the_stated_length_is_the_length_of_the_draft(inquiry: str, message: str) -> None:
    stated = re.search(r"\*\*Characters:\*\*\s*([\d,]+)", inquiry)
    assert stated is not None
    assert stated.group(1).replace(",", "") == str(len(message))


def test_the_draft_commits_to_nothing(inquiry: str, message: str) -> None:
    assert "drafted, not sent" in inquiry
    assert "I am not filing either application yet" in message


def test_the_draft_asks_the_four_questions(message: str) -> None:
    for number in ("1.", "2.", "3.", "4."):
        assert f"\n{number} " in message, number
    assert "Request Form for Specimen Verification" in message
    assert "October 8, 2027" in message
    assert "December 8, 2026" in message


def test_the_tracker_records_the_draft_as_unsent() -> None:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    tracker = json.loads(ARTEFACT.read_text())
    steps = [
        row
        for row in tracker["steps"]
        if row["Application"] == "PLCO-PAR" and "message F" in row["Step"]
    ]
    assert len(steps) == 1
    assert "drafted, not sent" in steps[0]["Status"]
    assert not steps[0]["Status"].startswith("done")


def test_message_g_is_drafted_and_asks_the_open_question(inquiry: str) -> None:
    """Message G asks what "part of the institution" requires, and is unsent."""
    assert "Message G" in inquiry
    assert "drafted, not sent" in inquiry
    body = inquiry.split("<!-- BEGIN MESSAGE G -->")[1]
    body = body.split("<!-- END MESSAGE G -->")[0].strip()
    assert "**" not in body
    assert "[TO FILL:" not in body
    assert len(body) <= 10_000
    assert "approved-users list" in body
    assert "current appointment" in body


def test_the_state_of_message_g_is_bound_to_its_text(inquiry: str) -> None:
    body = inquiry.split("<!-- BEGIN MESSAGE G -->")[1]
    body = body.split("<!-- END MESSAGE G -->")[0].strip()
    section = inquiry.split("## 11. Message G")[-1]
    stated = re.search(r"\*\*Characters:\*\*\s*([\d,]+)", section)
    assert stated is not None
    assert stated.group(1).replace(",", "") == str(len(body))


def test_the_tracker_records_the_g_step() -> None:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    tracker = json.loads(ARTEFACT.read_text())
    steps = [
        row
        for row in tracker["steps"]
        if row["Application"] == "PLCO-DATA" and "message G" in row["Step"]
    ]
    assert len(steps) == 1
    assert "drafted, not sent" in steps[0]["Status"]


def test_the_host_letter_asks_for_the_mechanism_not_only_the_signature() -> None:
    host = INVITATION.read_text()
    letter = host.split("<!-- BEGIN HOST LETTER -->")[1]
    letter = letter.split("<!-- END HOST LETTER -->")[0]
    # The letter settles the standing question by naming the arrangement
    # rather than asking what standing would be needed.
    assert "what standing at your institution would let me reach the data" in letter
    assert "would you and your department sponsor me" in letter
    assert "The instructions allow an assistant professor" in letter
