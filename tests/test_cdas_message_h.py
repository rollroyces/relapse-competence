"""Tests for CDAS message H.

Message H asks the half of the question that message G does not: not what
a sponsored affiliation is worth on the approved-users list, but whether an
organisation the requester registered himself counts as an institution at
all. The answer decides whether the one route that needs nobody's permission
is open, so the message has to name the arrangement, rest on a record CDAS
publishes, and claim nothing that has not happened.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

INQUIRY = Path("docs/plco-cdas-submission-package/07-scoping-inquiry.md")

BEGIN = "<!-- BEGIN MESSAGE H -->"
END = "<!-- END MESSAGE H -->"


@pytest.fixture(scope="module")
def inquiry() -> str:
    if not INQUIRY.exists():
        pytest.skip("the scoping inquiry has not been written")
    return INQUIRY.read_text()


@pytest.fixture(scope="module")
def message(inquiry: str) -> str:
    return inquiry.split(BEGIN)[1].split(END)[0].strip()


@pytest.fixture(scope="module")
def section(inquiry: str) -> str:
    """Section 12, flattened, so that a line break cannot hide a phrase."""
    tail = inquiry.split("## 12. Message H", 1)[1]
    return " ".join(re.split(r"\n## ", tail, maxsplit=1)[0].split())


def test_the_message_is_plain_text_and_inside_the_field_limit(message: str) -> None:
    assert "**" not in message
    assert "[TO FILL:" not in message
    assert len(message) <= 10_000


def test_the_record_states_the_message_length_and_it_is_the_length(
    section: str, message: str
) -> None:
    stated = re.search(r"\*\*Characters:\*\*\s*([\d,]+)", section)
    assert stated is not None
    assert stated.group(1).replace(",", "") == str(len(message))


def test_the_message_asks_the_specific_arrangement(message: str) -> None:
    """A question that names the arrangement can be answered yes or no."""
    for phrase in (
        "NLST-43",
        "Deborah Goldwasser",
        "Statistical Consultant",
        "a personal address at gmail.com",
        "must complete all the required registrations as though "
        "they are an organization",
        "approved-users list",
        "a permanent employee of your institution",
    ):
        assert phrase in message, phrase


def test_the_message_asks_three_numbered_questions(message: str) -> None:
    for number in ("1. ", "2. ", "3. "):
        assert f"\n{number}" in message, number


def test_the_message_claims_nothing_that_has_not_happened(message: str) -> None:
    for forbidden in (
        "you have confirmed",
        "you have already accepted",
        "I have registered",
        "I have submitted",
    ):
        assert forbidden not in message, forbidden
    # And it does not ask CDAS to change what it has already said.
    assert "I am not asking you to change any of them" in message


def test_the_record_carries_the_address_but_the_message_does_not(
    section: str, message: str
) -> None:
    """The record needs it; the message does not need to republish it."""
    assert "deborah.l.goldwasser@gmail.com" in section
    assert "deborah.l.goldwasser@gmail.com" not in message


def test_the_message_is_drafted_and_not_sent(section: str) -> None:
    assert "Status: drafted, not sent" in section
    assert "drafted, not sent" in section


def test_the_sending_record_says_the_three_drafts_are_not_sent(
    inquiry: str,
) -> None:
    flat = " ".join(inquiry.split())
    assert (
        "Three more messages are drafted, and none of them has been sent"
        in flat
    )
    for message_name in ("Message F", "message G", "message H"):
        assert message_name in flat, message_name
