"""Tests for the U-M affiliation mechanism, and for what it does not settle.

The requester's obstacle was never employment: it was institutional
membership. The University of Michigan publishes a mechanism for people who
hold no appointment, and its eligible categories name a U-M alum. These
tests bind the mechanism to its quotations, and bind the limits to the
document as well, because a document that only records what is convenient
would be worse than no document.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

MECHANISM = Path("docs/UM-AFFILIATION-MECHANISM.md")
APPLICATIONS = Path("docs/DATA-ACCESS-APPLICATIONS.md")
INVITATION = Path("docs/HOST-INVITATION.md")
INQUIRY = Path("docs/plco-cdas-submission-package/07-scoping-inquiry.md")
ARTEFACT = Path("results/application_tracker/application_tracker.json")


@pytest.fixture(scope="module")
def mechanism() -> str:
    return MECHANISM.read_text()


@pytest.fixture(scope="module")
def flat(mechanism: str) -> str:
    """Whitespace-flattened text.

    Quoted passages in the source are hard-wrapped, and a gate that compares
    a phrase containing a space against the raw file would silently miss a
    line break inside it. Flattening first is what makes the comparison
    mean what it says.
    """
    return " ".join(mechanism.split())


def test_the_mechanism_document_exists_and_says_what_it_is() -> None:
    assert MECHANISM.exists()
    text = MECHANISM.read_text()
    assert "researched and recorded" in text
    assert "2026-11-13" in text
    # It is a reading of published policy, not an action taken.
    assert "Nothing here has been submitted, requested or filed" in text


def test_the_mechanism_is_quoted_not_paraphrased(flat: str) -> None:
    """The quotations have to be the policy's words.

    The document's whole value is that the policy says this, so the
    load-bearing phrases are checked verbatim against the text.
    """
    for phrase in (
        "does not hold a U-M appointment",
        '"a U-M alum"',
        "COVERED VISITING AFFILIATE/COLLEAGUE",
        "up to two (2) years at a time (renewable)",
        "academic affiliate (e.g. research collaborator)",
        "Regular Uniqnames with UMIDs",
        "as members of the U-M community",
        "count as affiliated with U-M during the term of their sponsorship/appointment",
        "N/A = an appointment is either optional or not required",
        "Sponsored accounts",
    ):
        assert phrase in flat, phrase


def test_the_mechanism_cites_its_sources(flat: str) -> None:
    for url in (
        "spg.umich.edu/policy/601.42",
        "documentation.its.umich.edu/node/255",
        "documentation.its.umich.edu/node/256",
        "documentation.its.umich.edu/node/1251",
        "az.research.umich.edu/medschool/guidance/external-non-um-study-team-members",
        "its.umich.edu/computing/computers-software/standard-computing-services",
        "spg-60142-covered-visitors",
    ):
        assert url in flat, url


def test_the_document_states_what_the_mechanism_does_not_settle(flat: str) -> None:
    """The limits are as load-bearing as the findings.

    U-M's policy governs U-M's definition of affiliation and does not speak
    for NCI's, so a document that omitted this would be overstating.
    """
    for limit in (
        "does not establish that CDAS will accept a sponsored affiliate",
        "does not establish that the University's own arrangement is sufficient",
        "does not establish that the host will sponsor",
        "does not establish a processing time",
    ):
        assert limit in flat, limit


def test_the_library_registration_is_recorded_as_not_a_route(flat: str) -> None:
    """It is easily mistaken for one, so it is recorded as not being one."""
    assert "Register as a Researcher" in flat
    assert "Special Collections request account" in flat
    assert "not a route to any of this" in flat


def test_the_alumni_address_is_not_treated_as_a_status(flat: str) -> None:
    assert "a mailbox, not a status" in flat


def test_the_verification_gap_is_recorded(flat: str) -> None:
    """A reader who hits the same 403 needs to know where the text came from."""
    assert "403" in flat
    assert "rendered page" in flat


def test_the_applications_document_carries_the_mechanism() -> None:
    text = " ".join(APPLICATIONS.read_text().split())
    assert "SPG 601.42, Covered Visitors" in text
    assert '"a U-M alum"' in text
    assert "does not speak for NCI's" in text
    assert "UM-AFFILIATION-MECHANISM.md" in text


def test_the_fact_table_records_the_mechanism_and_its_limits() -> None:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    facts = {
        row["Fact"]: row["Value"]
        for row in json.loads(ARTEFACT.read_text())["external_facts"]
    }
    mechanism = facts.get("U-M mechanism for a researcher with no appointment", "")
    assert "SPG 601.42" in mechanism
    assert '"a U-M alum"' in mechanism
    assert "does not hold a U-M appointment" in mechanism

    identity = facts.get("U-M identity and address for a sponsored affiliate", "")
    assert "Sponsor System" in identity
    assert "Regular Uniqnames with UMIDs" in identity

    standing = facts.get("U-M research standing without an appointment", "")
    assert "count as affiliated with U-M" in standing

    limit = facts.get("What the U-M mechanism does not settle", "")
    assert "does not establish" in limit

    library = facts.get('U-M Library "Register as a Researcher"', "")
    assert "Special Collections" in library


def test_the_host_letter_names_the_mechanism_rather_than_asking_about_it() -> None:
    """A professor asked to invent a standing will not invent one."""
    text = INVITATION.read_text()
    letter = text.split("<!-- BEGIN HOST LETTER -->")[1]
    letter = letter.split("<!-- END HOST LETTER -->")[0].strip()
    assert "601.42" in letter
    assert "Covered Visitors" in letter
    assert '"a U-M alum"' in letter
    assert "who do not hold a U-M appointment" in letter
    assert "Sponsor System" in letter
    assert "uniqname with a UMID" in letter
    assert "would you and your department sponsor me" in letter
    assert "two years at a time, renewable" in letter
    assert "it is not employment" in letter
    assert "I have attached the policy references" in letter
    # The letter asks a question the host can answer with a yes or a no.
    assert "if that is not how your department does it, what is?" in letter
    # It does not claim NCI has already accepted the arrangement.
    assert "you have confirmed" not in letter
    assert "you have already accepted" not in letter


def test_message_g_puts_the_specific_arrangement_to_cdas() -> None:
    """A question that names the arrangement can be answered yes or no."""
    text = INQUIRY.read_text()
    body = text.split("<!-- BEGIN MESSAGE G -->")[1]
    body = body.split("<!-- END MESSAGE G -->")[0].strip()
    assert "601.42" in body
    assert "Covered Visitors" in body
    assert "sponsored affiliation" in body
    assert "creates no HR appointment" in body
    assert "Would a researcher holding a sponsored affiliation" in body
    # It asks; it does not assert an answer.
    assert "you have confirmed" not in body


def test_message_g_still_asks_the_original_two_questions() -> None:
    """The new question is added to the old ones, not substituted for them."""
    text = INQUIRY.read_text()
    body = text.split("<!-- BEGIN MESSAGE G -->")[1]
    body = body.split("<!-- END MESSAGE G -->")[0].strip()
    assert "approved-users list" in body
    assert "current appointment" in body
    assert "former student of the institution" in body


def test_message_g_length_is_stated_and_true() -> None:
    text = INQUIRY.read_text()
    body = text.split("<!-- BEGIN MESSAGE G -->")[1]
    body = body.split("<!-- END MESSAGE G -->")[0].strip()
    section = text.split("## 11. Message G")[-1]
    stated = re.search(r"\*\*Characters:\*\*\s*([\d,]+)", section)
    assert stated is not None
    assert stated.group(1).replace(",", "") == str(len(body))
