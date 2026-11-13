"""Tests for the Wholomics partnership enquiry.

The letter is the programme's first approach to a company that could both
employ the requester and carry a PLCO proposal, and it is the letter in
which the programme's own plasma evidence is most likely to be overstated:
every number in it is a projection or a simulation, and one of them goes
against the programme. These tests bind the ask, the evidence and the
disclosure, and they bind the section that says what the letter
deliberately does not do, because that section is a claim about the letter.
"""

from __future__ import annotations

from pathlib import Path

import pytest

LETTER_DOC = Path("docs/WHOLOMICS-PARTNERSHIP-ENQUIRY.md")
ROUTES = Path("docs/HOSTING-ROUTES.md")


@pytest.fixture(scope="module")
def doc() -> str:
    return LETTER_DOC.read_text()


@pytest.fixture(scope="module")
def letter(doc: str) -> str:
    body = doc.split("<!-- BEGIN WHOLOMICS LETTER -->")[1]
    return body.split("<!-- END WHOLOMICS LETTER -->")[0].strip()


def test_the_letter_is_a_draft_and_says_so(doc: str) -> None:
    assert "draft, not sent" in doc
    assert "Nothing has been sent to Wholomics" in doc
    assert "not part of the PLCO submission package" in doc


def test_the_letter_is_plain_text_and_complete(letter: str) -> None:
    assert "**" not in letter
    assert "](" not in letter
    assert "[HOST]" not in letter
    assert "Dear Mr Strasser" in letter
    assert letter.rstrip().endswith("roycelam@umich.edu")


def test_the_ask_is_ten_tubes_and_says_what_ten_cannot_do(letter: str) -> None:
    """The ask has to be small enough that it cannot be read as larger."""
    assert "a ten-tube pilot and not a stratum" in letter
    assert "It is not enough to estimate a recovery rate" in letter
    assert "and I am not asking for one" in letter
    # The one technical objection the recipient will have: PLCO's plasma
    # strata are not the strata their design uses.
    assert (
        "PLCO's plasma is banked at T0, T3, T4 and T5 and not at T1 or T2"
        in letter
    )


def test_the_evidence_is_stated_with_its_own_limits(letter: str) -> None:
    """Including the number that goes against the programme.

    A letter that quoted only 0.9091 would mislead, and the section that
    says what the letter does not do would be false.
    """
    assert "Every plasma number published so far is a projection" in letter
    assert "it inverts, from 0.9929 to 0.0053" in letter
    assert (
        "clears the programme's own bar at 0.9091 against a threshold of 0.65"
        in letter
    )
    assert "collapses to chance, 0.5170" in letter
    assert "That is a simulation and not a measurement" in letter
    assert "Ten tubes would not settle it" in letter


def test_the_standing_and_the_motive_are_disclosed(letter: str) -> None:
    """The commercial motive is why he is writing to a company at all."""
    assert "I hold no current institutional appointment" in letter
    assert "I am employed by nobody" in letter
    assert "no funding is attached to this work" in letter
    assert "the institution that submits it" in letter
    assert "not asking you to sponsor an unfunded interest" in letter


def test_the_singlera_disclosure_is_made(letter: str) -> None:
    assert "Singlera Genomics" in letter
    assert "co-founder, equity holder and paid consultant" in letter
    assert "The analysis code from that paper is public" in letter


def test_the_letter_does_not_overclaim(letter: str) -> None:
    """No sentence may present a simulation as a measurement."""
    for forbidden in (
        "we have measured the electrical signal in blood",
        "our measurement in plasma",
        "demonstrates that the readout works",
    ):
        assert forbidden not in letter


def test_the_limits_section_is_present_and_each_item_is_a_claim(doc: str) -> None:
    flat = " ".join(doc.split())
    for limit in (
        "does not ask for the stratum",
        "does not claim that the programme's readout works in plasma",
        "does not present the attributed statistic as the programme's own",
        "does not hide the commercial motive",
        "does not promise an exclusive arrangement",
        "does not describe the requester as a member of Wholomics",
    ):
        assert limit in flat, limit


def test_the_before_you_send_list_binds_the_decisions(doc: str) -> None:
    flat = " ".join(doc.split())
    for item in (
        "info@wholomics.com",
        "not the form",
        "no employer, no funding attached to this work",
        "whether this could be a paid collaboration",
        "ten tubes",
    ):
        assert item in flat, item


def test_the_letter_is_anchored_to_the_routes_document() -> None:
    """The letter exists because of the hosting-route finding."""
    assert ROUTES.exists()
    flat = " ".join(ROUTES.read_text().split())
    assert "Wholomics GmbH" in flat
    assert "Become a Partner" in flat
    assert "2026-0185" in flat
