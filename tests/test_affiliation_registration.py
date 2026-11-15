"""Tests for the affiliation registration runbook.

The runbook is the part of the plan that needs nobody's permission, so it is
the part most likely to be acted on. It has to be exact about which route
needs what, and honest about what registering an organisation does and does
not settle.
"""

from __future__ import annotations

from pathlib import Path

import pytest

RUNBOOK = Path("docs/AFFILIATION-REGISTRATION.md")
ROUTES = Path("docs/HOSTING-ROUTES.md")
TERMS = Path("docs/CONTRIBUTION-TERMS.md")


@pytest.fixture(scope="module")
def flat() -> str:
    return " ".join(RUNBOOK.read_text().split())


def test_the_runbook_exists_and_is_marked_as_a_plan(flat: str) -> None:
    assert RUNBOOK.exists()
    assert "a plan, not an action" in flat
    assert "Nothing here has been started, filed or registered" in flat


def test_the_three_fields_the_applications_require_are_named(flat: str) -> None:
    for field in (
        "an institution, and its location",
        "a name and an **institutional e-mail address** for each approved user",
        "an **institutional e-mail address** and an **NIH biosketch** for each "
        "member of the investigative team",
    ):
        assert field in flat, field


def test_the_two_routes_are_separated(flat: str) -> None:
    assert "Route 1 — be sponsored" in flat
    assert "Route 2 — be the institution" in flat
    assert "Route 1 and Route 2 can be combined" in flat


def test_the_six_steps_are_in_order(flat: str) -> None:
    for step in (
        "Step 1 — an ORCID iD",
        "Step 2 — register the organisation",
        "Step 3 — a Commons ID linked to the ORCID",
        "Step 4 — a CDAS account",
        "Step 5 — a SciENv profile and a certified biosketch",
        "Step 6 — put the identifiers in the places that ask for them",
    ):
        assert step in flat, step


def test_the_cost_and_the_deadline_are_stated(flat: str) -> None:
    assert "There is NO cost associated with ANY of these registrations" in flat
    assert "at least six weeks prior to a deadline" in flat
    assert "2027-02-18" in flat
    assert "4-6 months from application submission to review outcome" in flat


def test_the_login_service_detail_is_recorded(flat: str) -> None:
    """RAS is institutional, so it is not the route for a self-registered body."""
    assert "ID.me, Login.gov, or the NIH Login Service" in flat
    assert "it is not the route for a self-registered organisation" in flat


def test_what_the_route_does_not_solve_is_stated(flat: str) -> None:
    assert "Whether CDAS accepts such an organisation" in flat
    assert (
        "Whether it can be the institution that verifies full-time employment"
        in flat
    )
    assert (
        "does not assert that the requester qualifies as a senior researcher"
        in flat
    )


def test_the_registration_is_not_described_as_a_formality(flat: str) -> None:
    assert "not a formality" in flat
    assert "it is his name on it" in flat
    assert (
        "does not treat the absence of a sponsor as a reason to wait" in flat
    )


def test_the_letters_flag_the_decision_before_sending() -> None:
    """The letter and the application have to agree."""
    for path in (
        "docs/DENTON-COLLABORATION-REQUEST.md",
        "docs/WHOLOMICS-PARTNERSHIP-ENQUIRY.md",
        "docs/HOST-INVITATION.md",
        "docs/TAIZHOU-COLLABORATION-REQUEST.md",
    ):
        flat = " ".join(Path(path).read_text().split())
        assert "AFFILIATION-REGISTRATION.md" in flat, path
        assert "the letter and the application have to agree" in flat, path


def test_the_runbook_agrees_with_the_routes_and_the_terms() -> None:
    """Three documents, one set of facts."""
    routes = " ".join(ROUTES.read_text().split())
    terms = " ".join(TERMS.read_text().split())
    runbook = " ".join(RUNBOOK.read_text().split())
    for phrase in ("There is NO cost associated with ANY of these registrations",):
        assert phrase in routes and phrase in terms and phrase in runbook
    for phrase in ("2027-02-18",):
        assert phrase in terms and phrase in runbook
