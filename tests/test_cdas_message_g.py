"""Tests for the verified state of CDAS message G.

Message G was filled into the live CDAS contact form on 2026-11-15 and
every field was read back out of the page rather than assumed. The
repository records the message by its digest, so that the text which was
on the form can be compared with the text held here, and it records that
the form has not been submitted. These tests recompute the digest
independently of the consistency checker, and they refuse to let the
record drift into claiming a submission that has not happened.

When the message is actually sent, the state literal in the document
changes from "The submission has not been made." to "The submission was
made on <date>", the digest stays the same, and the check below moves
with it. That is the only change this file expects.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

INQUIRY = Path("docs/plco-cdas-submission-package/07-scoping-inquiry.md")

BEGIN = "<!-- BEGIN MESSAGE G -->"
END = "<!-- END MESSAGE G -->"

#: The digest of the message as it stood in the live form on 2026-11-15.
VERIFIED_DIGEST = (
    "d67fc9d3705910bea224ef4d50da71746473e3a75531328edb41526132ec25a1"
)


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
    """Section 11, flattened, so that a line break cannot hide a phrase."""
    return " ".join(inquiry.split("## 11. Message G")[-1].split())


def test_the_record_states_the_digest_of_the_message(
    section: str, message: str
) -> None:
    """The recorded digest has to be the digest of the message itself."""
    digests = re.findall(r"\b[0-9a-f]{64}\b", section)
    assert len(digests) == 1, digests
    actual = hashlib.sha256(message.encode("utf-8")).hexdigest()
    assert actual == digests[0], (actual, digests[0])


def test_the_message_is_the_one_that_was_verified(message: str) -> None:
    """Pinned, so that an edit cannot pass unnoticed."""
    assert len(message) == 2233
    assert (
        hashlib.sha256(message.encode("utf-8")).hexdigest() == VERIFIED_DIGEST
    )


def test_the_record_states_the_submission_state_exactly_once(section: str) -> None:
    pending = "The submission has not been made."
    sent = "The submission was made on "
    assert sum(1 for m in (pending, sent) if m in section) == 1
    assert pending in section
    assert "Nothing has been submitted" in section


def test_the_verified_fields_are_recorded(section: str) -> None:
    """The fields, as they were read back off the live page."""
    for phrase in (
        "roycelam@umich.edu",
        "Subject `PLCO`",
        "Topic `Data Access/Availability`",
        "`id_name`",
        "`id_phone`",
        "2026-11-15",
    ):
        assert phrase in section, phrase


def test_the_message_puts_the_three_questions_to_cdas(message: str) -> None:
    assert message.startswith("Dear CDAS team,")
    assert message.endswith("Royce Lam\nroycelam@umich.edu")
    for phrase in (
        "approved-users list",
        "current appointment",
        "601.42",
        "Covered Visitors",
        "sponsored affiliation",
        "creates no HR appointment",
    ):
        assert phrase in message, phrase


def test_the_message_claims_nothing_that_has_not_happened(message: str) -> None:
    """It asks questions; it does not report answers, or a submission."""
    for forbidden in (
        "you have confirmed",
        "you have already accepted",
        "I have submitted",
        "I submitted",
        "the form has been submitted",
    ):
        assert forbidden not in message, forbidden
