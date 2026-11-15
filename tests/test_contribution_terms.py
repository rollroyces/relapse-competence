"""Tests for the contribution terms.

The requester's worry is that a contribution without an institutional
appointment goes unrecorded. The answer is that PLCO contributions are
recorded in an application, and the application is public. These tests bind
that mechanism to the verified record, and bind the limits as firmly as the
findings.
"""

from __future__ import annotations

from pathlib import Path

import pytest

TERMS = Path("docs/CONTRIBUTION-TERMS.md")
ROUTES = Path("docs/HOSTING-ROUTES.md")
SUMMARY = Path("docs/PARTNER-SUMMARY.md")


@pytest.fixture(scope="module")
def flat() -> str:
    return " ".join(TERMS.read_text().split())


def test_the_document_exists_and_says_what_it_is(flat: str) -> None:
    assert TERMS.exists()
    assert "a plan, not an agreement" in flat
    assert "Nothing has been filed, submitted or agreed with anyone" in flat


def test_the_three_records_are_set_out(flat: str) -> None:
    for record in (
        "The collaborators line on the approved-project page",
        "the abstract of your research proposal and your contact information",
        "You must list all members of your investigative team and upload an "
        "NIH biosketch for each member",
    ):
        assert record in flat, record


def test_the_published_collaborator_record_is_verified(flat: str) -> None:
    """The claim rests on live pages, so the examples are named."""
    for project in ("PLCO-2057", "PLCO-380", "NLST-621", "2026-0185", "NLST-43"):
        assert project in flat, project
    assert "Viswanath Nagarajan" in flat
    assert "Stephen Duffy" in flat
    assert "Gary Gao" in flat
    # And the counter-example: solo applications publish no collaborators.
    assert "publishes none" in flat


def test_the_rule_is_to_settle_contribution_at_filing(flat: str) -> None:
    assert "settle it at filing, not after the result" in flat
    assert (
        "because that is the moment the names are recorded and published" in flat
    )


def test_the_draft_contribution_statement_has_both_columns(flat: str) -> None:
    for role in (
        "Conceptualization",
        "Methodology",
        "Software",
        "Formal analysis",
        "Investigation",
        "Data curation",
        "Writing – original draft",
    ):
        assert role in flat, role
    assert "The requester" in flat
    assert "The partner" in flat
    # And the roles he does not hold are left blank, deliberately.
    assert "He holds no funding, supervises nobody" in flat


def test_the_biosketch_route_is_recorded_as_open(flat: str) -> None:
    assert (
        "the biosketch route is open to a researcher with no appointment" in flat
    )
    assert "you CANNOT create your own eRA Commons account" in flat
    assert "There is NO cost associated with ANY of these registrations" in flat
    assert "at least six weeks prior to a deadline" in flat


def test_the_limits_are_as_firm_as_the_findings(flat: str) -> None:
    for limit in (
        "does not claim the requester will be an author of anything",
        "does not treat a collaborators line as equivalent to authorship",
        "does not put a name against a role the requester does not hold",
        "does not presume any route will be accepted",
    ):
        assert limit in flat, limit


def test_the_html_entity_trap_is_recorded(flat: str) -> None:
    """The same extractor error twice is worth a paragraph."""
    assert "HTML numeric entities" in flat
    assert "found by a mutation test" in flat


def test_each_letter_asks_to_be_named_and_still_refuses_authorship() -> None:
    """The two have to travel together or the ask is dishonest."""
    for path, marker in (
        ("docs/DENTON-COLLABORATION-REQUEST.md", "Denton letter"),
        ("docs/WHOLOMICS-PARTNERSHIP-ENQUIRY.md", "Wholomics letter"),
        ("docs/HOST-INVITATION.md", "host letter"),
    ):
        text = " ".join(Path(path).read_text().split())
        assert "that the application name me" in text, marker
        assert (
            "while a paper's author list is settled by the paper's own "
            "conventions" in text
        ), marker
    tzl = " ".join(Path("docs/TAIZHOU-COLLABORATION-REQUEST.md").read_text().split())
    assert "how the contribution would be recorded" in tzl
    assert "agree the roles in writing while the collaboration is still a proposal" in tzl


def test_the_routes_document_records_the_registration_route() -> None:
    flat = " ".join(ROUTES.read_text().split())
    assert "you CANNOT create your own eRA Commons account" in flat
    assert "There is NO cost associated with ANY of these registrations" in flat
    assert (
        "None of this requires a sponsor, a host, a grant or a signature" in flat
    )
    assert (
        "It does not settle whether CDAS accepts such an organisation" in flat
    )


def test_the_partner_summary_is_where_the_evidence_is_split() -> None:
    """The contribution terms point at the summary rather than restating it."""
    flat = " ".join(TERMS.read_text().split())
    assert "PARTNER-SUMMARY.md" in flat
    assert SUMMARY.exists()
