"""Tests for the Denton collaboration request.

This letter goes to the PLCO investigator whose own project is about the
programme's question, so it has to do two things at once: make the
decision-analytic case, and not overstate the plasma evidence. The gates
bind both.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DOC = Path("docs/DENTON-COLLABORATION-REQUEST.md")
SUMMARY = Path("docs/PARTNER-SUMMARY.md")
SHORTLIST = Path("docs/HOST-SHORTLIST.md")


@pytest.fixture(scope="module")
def doc() -> str:
    return DOC.read_text()


@pytest.fixture(scope="module")
def letter(doc: str) -> str:
    body = doc.split("<!-- BEGIN DENTON LETTER -->")[1]
    return body.split("<!-- END DENTON LETTER -->")[0].strip()


def test_the_letter_is_a_draft_and_says_so(doc: str) -> None:
    assert "draft, not sent" in doc
    assert "Nothing has been sent to Professor Denton" in doc
    assert "not part of the PLCO submission package" in doc


def test_the_letter_is_plain_text_and_complete(letter: str) -> None:
    assert "**" not in letter
    assert "](" not in letter
    assert "[HOST]" not in letter
    assert letter.startswith("Dear Professor Denton,")
    assert letter.rstrip().endswith("roycelam@umich.edu")
    assert len(letter) <= 8_000, len(letter)


def test_the_letter_attaches_the_partner_summary(doc: str) -> None:
    assert "PARTNER-SUMMARY.md" in doc
    assert SUMMARY.exists()


def test_the_letter_names_why_him(doc: str) -> None:
    """The subject match is the reason for the choice, and it is recorded."""
    flat = " ".join(doc.split())
    assert "PLCO-2057" in flat
    assert "Brian T. Denton" in flat
    assert "btdenton@umich.edu" in flat
    # And the alternative is on the record too.
    assert "HOST-SHORTLIST.md" in flat


def test_the_ten_tube_ask_is_exact(letter: str) -> None:
    assert (
        "Five incident lung-cancer cases and five matched cancer-free controls"
        in letter
    )
    assert "PLCO banks plasma at T0, T3, T4 and T5 and not at T1 or T2" in letter
    assert "Ten tubes do not need germline material or matched tumour" in letter
    assert (
        "Ten is not enough to estimate a recovery rate and I am not asking for "
        "one" in letter
    )
    assert "twenty minutes to talk about whether this is worth doing" in letter


def test_the_sponsorship_is_asked_for_not_asserted(letter: str) -> None:
    assert "601.42" in letter
    assert "do not hold a U-M appointment" in letter
    assert "a former student of the institution" in letter
    # It is asked for, and it is offered as his department's work.
    assert "to sponsor a standing for me at your institution" in letter


def test_the_two_unsettled_things_are_in_the_letter(letter: str) -> None:
    """A first letter that hides the gap is worse than no letter."""
    assert "the answer is outstanding" in letter
    assert "full-time employees" in letter
    assert "is by definition not employment" in letter


def test_the_evidence_is_stated_with_its_limits(letter: str) -> None:
    assert "Nothing has been measured in blood" in letter
    assert "inverts" in letter
    assert "Three of my five kill conditions have fired" in letter
    assert "was then simulated" in letter


def test_the_letter_does_not_overclaim(letter: str) -> None:
    for forbidden in (
        "we have measured the electrical signal in blood",
        "the readout works in blood",
        "demonstrates that the state can be read",
    ):
        assert forbidden not in letter.lower()


def test_what_is_not_being_asked_for_is_listed(letter: str) -> None:
    assert (
        "Not a commitment, not funding, not exclusivity, not intellectual "
        "property, not authorship" in letter
    )


def test_the_limits_section_is_bound_to_the_letter(doc: str) -> None:
    flat = " ".join(doc.split())
    for limit in (
        "does not present the programme's plasma numbers as measurements",
        "does not claim the sponsorship route is settled",
        "does not claim ten tubes will show the readout works",
        "does not ask for a partnership",
        "does not disguise what the sponsorship costs his department",
        "does not describe the requester as a member of the University",
    ):
        assert limit in flat, limit


def test_the_pilot_needs_an_eems_application(doc: str) -> None:
    """Ten tubes is not a favour to be slipped into an existing request."""
    flat = " ".join(doc.split())
    assert "an EEMS application is required for all pilot studies" in flat
    assert "2027-02-18" in flat


def test_the_recipient_is_the_chosen_one_and_the_alternative_is_on_record(
    doc: str,
) -> None:
    flat = " ".join(doc.split())
    assert "Professor Brian Denton" in flat
    assert "HOST-INVITATION.md" in flat
    assert "Why him and not Bryant" in flat
