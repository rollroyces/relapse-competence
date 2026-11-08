"""Tests for the plasma-readability audit.

The audit's claim is that the simulator's assumed electrical fold and state
fraction are not one number but a disease- and channel-specific pair, and that
the published D1 enrichment AUC holds for one of the four measured cases and
not the others. Each of those is asserted here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PLASMA = Path("results/plasma_readability/plasma_readability.json")
D1 = Path("results/channel_allocation_200k.json")
NSCLC = Path("results/gse353299/state_expression.json")
SCLC = Path("results/gse299684/state_expression.json")


@pytest.fixture(scope="module")
def plasma() -> dict:
    if not PLASMA.exists():
        pytest.skip("the plasma-readability artefact has not been generated")
    return json.loads(PLASMA.read_text())


def _sweeps(plasma: dict) -> dict:
    return {
        (s["dataset"], s["channel"]): s
        for s in plasma["sweeps"]
        if s["electrical_fraction"] == 0.25
    }


def test_the_control_reproduces_the_published_d1_row(plasma: dict) -> None:
    """Otherwise the other rows are not attributable to the measurements."""
    if not D1.exists():
        pytest.skip("the D1 allocation artefact is missing")
    published = [
        r
        for r in json.loads(D1.read_text())["results"]["channel_allocation"]
        if r["total_loci"] == 200 and r["electrical_fraction"] == 0.25
    ][0]
    control = _sweeps(plasma)[("simulator default", "assumed")]
    assert abs(
        control["auc_electrical_enrichment_within_mrd_positive"]
        - published["auc_electrical_enrichment_within_mrd_positive"]
    ) < 5e-4
    assert abs(control["mrd_sensitivity"] - published["mrd_sensitivity"]) < 5e-4


def test_the_readout_is_stronger_in_nsclc_and_weaker_in_sclc(plasma: dict) -> None:
    sweeps = _sweeps(plasma)
    control = sweeps[("simulator default", "assumed")][
        "auc_electrical_enrichment_within_mrd_positive"
    ]
    assert (
        sweeps[("NSCLC", "KCNN4")]["auc_electrical_enrichment_within_mrd_positive"]
        > control
    )
    for key in (("SCLC", "KCNN4"), ("SCLC", "PIEZO1")):
        assert sweeps[key]["auc_electrical_enrichment_within_mrd_positive"] < control


def test_the_nsclc_piezo1_plasma_readout_is_at_chance(plasma: dict) -> None:
    """A good tissue marker that carries no bulk signal."""
    sweeps = _sweeps(plasma)
    assert sweeps[("NSCLC", "PIEZO1")]["auc_electrical_enrichment_within_mrd_positive"] < 0.6


def test_the_plasma_inputs_trace_to_the_two_state_audits(plasma: dict) -> None:
    """The folds are not invented here: they come from the state audits."""
    if not (NSCLC.exists() and SCLC.exists()):
        pytest.skip("the state-expression artefacts are missing")

    def _fold(path: Path, gene: str) -> float:
        artefact = json.loads(path.read_text())
        primary = artefact["audit"]["primary_definition"]
        entry = next(
            s for s in artefact["state_definition_sweep"] if s["definition"] == primary
        )
        record = next(c for c in entry["channels"] if c["gene"] == gene)
        return record["linear_fold_vs_yap1negative"]

    measured = {(m["dataset"], m["channel"]): m for m in plasma["measured"]}
    assert measured[("NSCLC", "KCNN4")]["abundance_fold_state_vs_tumour"] == pytest.approx(
        _fold(NSCLC, "KCNN4"), rel=1e-9
    )
    assert measured[("SCLC", "PIEZO1")]["abundance_fold_state_vs_tumour"] == pytest.approx(
        _fold(SCLC, "PIEZO1"), rel=1e-9
    )


def test_the_bulk_elevation_formula_is_what_the_report_claims(plasma: dict) -> None:
    for entry in plasma["measured"]:
        if entry.get("control"):
            continue
        expected = 1.0 + entry["state_fraction"] * (
            entry["abundance_fold_state_vs_tumour"] - 1.0
        )
        assert entry["bulk_elevation_with_measured_values"] == pytest.approx(
            expected, rel=1e-9
        )
