"""Tests for the dbGaP scoping inquiry.

The germline half of the attribution set needs an institution that can
verify employment, and dbGaP's own rules are what decide that: the
investigator has to be a permanent employee of their own institution, and
the request needs an Institutional Signing Official and an IT Director who
may not be the PI. An organisation of one appears to have nobody who can
fill those two roles. That is an inference from the rules, and these tests
make sure the repository keeps calling it an inference, and that the letter
asks the question instead of asserting the answer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

DOC = Path("docs/DBGAP-SCOPING-INQUIRY.md")
ROUTES = Path("docs/HOSTING-ROUTES.md")
README = Path("README.md")
ARTEFACT = Path("results/application_tracker/application_tracker.json")

BEGIN = "<!-- BEGIN DBGAP MESSAGE -->"
END = "<!-- END DBGAP MESSAGE -->"


@pytest.fixture(scope="module")
def doc() -> str:
    if not DOC.exists():
        pytest.skip("the dbGaP scoping inquiry has not been written")
    return DOC.read_text()


@pytest.fixture(scope="module")
def message(doc: str) -> str:
    return doc.split(BEGIN)[1].split(END)[0].strip()


@pytest.fixture(scope="module")
def flat(doc: str) -> str:
    return " ".join(doc.split())


def test_the_document_is_a_draft_and_says_so(doc: str) -> None:
    assert "draft, not sent" in doc
    assert "No request has been started" in doc
    assert "not part of the PLCO submission package" in doc


def test_the_message_is_plain_text_and_complete(message: str) -> None:
    assert "**" not in message
    assert "](" not in message
    assert "[TO FILL:" not in message
    assert message.startswith("Dear dbGaP staff,")
    assert message.endswith("Royce Lam\nroycelam@umich.edu")
    assert len(message) <= 10_000


def test_the_record_states_the_message_length_and_it_is_the_length(
    flat: str, message: str
) -> None:
    stated = re.search(r"Plain text, ([\d,]+) characters", flat)
    assert stated is not None
    assert stated.group(1).replace(",", "") == str(len(message))


def test_the_message_quotes_the_rules_it_depends_on(message: str) -> None:
    """A question about a rule is only answerable if the rule is quoted."""
    for phrase in (
        "Extramural Investigators must be permanent employees of their "
        "institution",
        "PI has identified him/herself as the signing official or the IT "
        "director for the project",
        "the signing official's and IT director's emails must be from their "
        "organization",
        "institutional authority to legally bind the institution",
        "verification by the institution that the investigators are full time "
        "employees",
    ):
        assert phrase in message, phrase


def test_the_message_asks_three_numbered_questions(message: str) -> None:
    for number in ("1. ", "2. ", "3. "):
        assert f"\n{number}" in message, number
    assert "phs001286.v5.p2" in message


def test_the_message_claims_nothing_that_has_not_happened(message: str) -> None:
    """It asks, and it says that a no is an answer."""
    assert (
        "that is a complete answer and it settles the question for me"
        in message
    )
    assert "I am not asking for an exception to any rule" in message
    assert "I am not filing a request" in message
    for forbidden in (
        "you have confirmed",
        "I have registered",
        "I have submitted",
        "you have approved",
    ):
        assert forbidden not in message, forbidden


def test_the_route_is_recorded(flat: str) -> None:
    for phrase in (
        "https://dbgap.ncbi.nlm.nih.gov/classic/aa/wga.cgi?page=email",
        "dbgap-help@ncbi.nlm.nih.gov",
        "carries no bot check and no token",
        "fall 2026",
    ):
        assert phrase in flat, phrase


def test_the_fact_table_records_the_dbgap_rules() -> None:
    if not ARTEFACT.exists():
        pytest.skip("the application tracker artefact has not been generated")
    tracker = json.loads(ARTEFACT.read_text())
    facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
    rule = facts["dbGaP's own eligibility rule for an Authorized Access request"]
    assert "permanent employees of their institution" in rule
    personnel = facts["dbGaP's personnel errors on a data access request"]
    assert "signing official or the IT director" in personnel
    assert "must be from their organization" in personnel


def test_the_hosting_routes_keep_the_inference_an_inference() -> None:
    routes = " ".join(ROUTES.read_text().split())
    assert (
        "That is an inference from the rules and not a ruling" in routes
    )
    assert "DBGAP-SCOPING-INQUIRY.md" in routes


def test_the_readme_indexes_the_document() -> None:
    assert "[`docs/DBGAP-SCOPING-INQUIRY.md`](docs/DBGAP-SCOPING-INQUIRY.md)" in (
        README.read_text()
    )
