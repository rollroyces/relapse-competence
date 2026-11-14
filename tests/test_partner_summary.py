"""Tests for the partner-facing one-pager.

A summary's failure mode is not a wrong number; it is a right number filed
under the wrong heading. A reader who reads "measured" and sees the
attributed AUC has been told the readout works in blood, which is the one
claim the programme has never earned. These tests therefore check the
columns, not just the presence of the numbers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SUMMARY = Path("docs/PARTNER-SUMMARY.md")


@pytest.fixture(scope="module")
def text() -> str:
    return SUMMARY.read_text()


@pytest.fixture(scope="module")
def sections(text: str) -> dict[str, str]:
    measured = text.split("## 1. MEASURED")[1].split("## 2. PROJECTED")[0]
    projected = text.split("## 2. PROJECTED")[1].split("## 3. SIMULATED")[0]
    simulated = text.split("## 3. SIMULATED")[1].split("## 4.")[0]
    kills = text.split("## 4. KILL CONDITIONS THAT HAVE FIRED")[1].split("## 5.")[0]
    return {
        "measured": measured,
        "projected": projected,
        "simulated": simulated,
        "kills": kills,
    }


def test_the_summary_exists_and_is_one_page(text: str) -> None:
    assert SUMMARY.exists()
    assert len(text) <= 8_000, len(text)
    assert "One page, written so that you can check it" in " ".join(text.split())


def test_the_three_claims_are_separated(text: str) -> None:
    for heading in (
        "## 1. MEASURED",
        "## 2. PROJECTED",
        "## 3. SIMULATED",
    ):
        assert heading in text, heading
    # The headings must say what each column is, not just be labels.
    flat = " ".join(text.split())
    assert "no model" in flat
    assert "a model over the measured inputs" in flat
    assert "never been applied to real plasma" in flat


def test_the_columns_do_not_bleed(sections: dict[str, str]) -> None:
    """A simulation under MEASURED is the one failure that matters."""
    # The attributed AUC and its control are simulated, not measured.
    assert "0.9091" not in sections["measured"]
    assert "0.5170" not in sections["measured"]
    assert "0.7848" not in sections["measured"]
    # The measured fold is not a projection.
    assert "2.97" not in sections["projected"]
    # The projections are not simulations.
    assert "0.9929" not in sections["simulated"]
    assert "0.0053" not in sections["simulated"]


def test_each_number_is_in_the_right_column(sections: dict[str, str]) -> None:
    for value, column in (
        ("2.97", "measured"),
        ("20 of 23", "measured"),
        ("7 of 7", "measured"),
        ("0.9929", "projected"),
        ("0.0053", "projected"),
        ("0.5815", "projected"),
        ("0.5111", "projected"),
        ("0.9091", "simulated"),
        ("0.5170", "simulated"),
        ("0.7848", "simulated"),
        ("0.5373", "simulated"),
        ("0.5404", "simulated"),
    ):
        assert value in sections[column], f"{value} not in {column}"


def test_the_measured_column_carries_its_provenance(sections: dict[str, str]) -> None:
    for source in ("GSE353299", "GSE299684"):
        assert source in sections["measured"], source
    assert "per-patient audit" in sections["measured"]


def test_the_kill_conditions_are_listed_with_their_status(
    sections: dict[str, str],
) -> None:
    kills = sections["kills"]
    for pid in ("K1", "K2", "K3", "K4", "K5"):
        assert pid in kills, pid
    assert kills.count("**FIRED**") == 3, kills.count("**FIRED**")
    assert kills.count("not evaluable") == 2, kills.count("not evaluable")
    # And the summary has to say what the firings changed.
    flat = " ".join(kills.split())
    assert "K3 firing is why the programme changed statistic" in flat


def test_the_ask_and_its_limits_are_stated(text: str) -> None:
    flat = " ".join(text.split())
    assert "A ten-tube feasibility pilot, and not a stratum" in flat
    assert "is not enough to estimate a recovery rate" in flat
    assert "Ten cannot settle the readout" in flat
    assert (
        "I am not asking for partnership, exclusivity, intellectual property, "
        "authorship, or a commitment" in flat
    )


def test_the_stop_rule_that_was_never_measured_is_named(text: str) -> None:
    flat = " ".join(text.split())
    assert "that rate has never been measured" in flat
    assert "70%" in flat


def test_the_disclosure_and_the_requester_s_standing_are_in_it(text: str) -> None:
    flat = " ".join(text.split())
    assert "Singlera Genomics" in flat
    assert "co-founder, equity holder and paid consultant" in flat
    assert "US62/657,544" in flat
    assert "no institutional appointment" in flat
    assert "no competing interest in any result" in flat


def test_the_summary_does_not_claim_the_readout_works(text: str) -> None:
    """The sentence a reader would quote must not exist."""
    flat = " ".join(text.split())
    for forbidden in (
        "the readout works in blood",
        "we have measured the electrical signal in blood",
        "the assay works in plasma",
        "demonstrates that the state can be read",
    ):
        assert forbidden not in flat.lower()
