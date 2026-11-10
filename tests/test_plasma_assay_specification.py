"""Tests for the plasma assay specification.

The specification exists because the leukocyte audit found that the plasma
numbers were projections of an assay that had never been written down. Two
properties matter here: the specification's numbers must be the artefacts'
numbers, and the design elements the audit forced must not be quietly dropped
from it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SPEC = Path("docs/PLASMA-ASSAY-SPECIFICATION.md")
LEUK = Path("results/leukocyte_audit/leukocyte_audit.json")
PACKAGE = Path("docs/plco-cdas-submission-package")


@pytest.fixture(scope="module")
def spec() -> str:
    if not SPEC.exists():
        pytest.skip("the assay specification has not been written")
    return SPEC.read_text()


@pytest.fixture(scope="module")
def operating() -> dict:
    if not LEUK.exists():
        pytest.skip("the leukocyte audit artefact has not been generated")
    audit = json.loads(LEUK.read_text())
    return next(
        r
        for r in audit["sweep"]
        if r["dataset"] == "NSCLC"
        and r["channel"] == "KCNN4"
        and r["tumour_share_multiplier"] == 1
        and r["leukocyte_fraction"] == 0.99
        and r["n_leukocyte_reference_loci"] == 0
    )


def test_the_specification_quotes_the_audits_own_numbers(spec: str, operating: dict) -> None:
    assert (
        f"{operating['median_tumour_cfDNA_share_relapsers']:.2e}" in spec
    )
    assert (
        f"{operating['median_tumour_cfDNA_share_non_relapsers']:.2e}" in spec
    )
    assert f"{operating['enrichment_noise_relapsers']:.1f}" in spec
    assert f"{operating['enrichment_noise_non_relapsers']:.0f}" in spec


def test_the_analyte_is_named(spec: str) -> None:
    """The channel is a transcript, so it cannot be read in cfDNA."""
    assert "cfRNA" in spec
    assert "cfDNA" in spec


def test_the_attribution_is_per_molecule(spec: str) -> None:
    """Subtraction fails; only counting tumour-derived molecules works."""
    assert "per molecule" in spec
    assert "heterozygous germline SNP" in spec
    assert "control and a normalisation check" in spec


def test_the_stop_rules_are_present_and_numbered(spec: str) -> None:
    for rule in ("S1", "S2", "S3", "S4", "S5", "S6"):
        assert f"**{rule}**" in spec, rule
    # The two thresholds that are the programme's own, not choices.
    assert "0.65" in spec
    assert "0.98" in spec


def test_the_panel_adds_up_to_the_published_operating_point(spec: str) -> None:
    """150 mutation + 38 channel + 12 leukocyte reference = 200 loci, 25%."""
    assert "150" in spec
    assert "38" in spec
    assert "12" in spec
    assert "200,000x" in spec


def test_the_package_links_the_specification() -> None:
    for name in ("01-project-details.md", "02-proposal-narrative.md"):
        path = PACKAGE / name
        if not path.exists():
            continue
        assert "PLASMA-ASSAY-SPECIFICATION.md" in path.read_text(), name


def test_the_specification_does_not_claim_the_assay_works(spec: str) -> None:
    """It is a specification, not a result."""
    assert "It does not establish that the assay works" in spec
    assert "upper bound" in spec
