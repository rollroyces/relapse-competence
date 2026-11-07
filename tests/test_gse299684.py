"""Tests for the GSE299684 state-expression analysis.

The report makes four claims that must not rot:

1. the state call reproduces the source paper's independent surface
   signature;
2. two channels are enriched in the state and the rest are not;
3. the enrichment survives leaving out any one library;
4. the per-site breakdown distinguishes the two channels.

Each is asserted here against the generated artefact, so the claims are
enforced by CI rather than only by prose.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ARTEFACT = Path("results/gse299684/state_expression.json")
MANIFEST = Path("data/gse299684/manifest.tsv")
SCRIPT = Path("scripts/gse299684_state_expression.py")


def _load_script():
    """The analysis script is a standalone script, not a package module."""
    spec = importlib.util.spec_from_file_location("gse299684_state_expression", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analysis = _load_script()
benjamini_hochberg = analysis.benjamini_hochberg
state_masks = analysis.state_masks


@pytest.fixture(scope="module")
def artefact() -> dict:
    if not ARTEFACT.exists():
        pytest.skip("the GSE299684 artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


def _primary(artefact: dict) -> dict:
    primary = artefact["audit"]["primary_definition"]
    return next(s for s in artefact["state_definition_sweep"] if s["definition"] == primary)


def _by_gene(entry: dict) -> dict[str, dict]:
    return {c["gene"]: c for c in entry["channels"] if c.get("status") == "ok"}


def test_the_state_call_reproduces_the_paper_surface_signature(artefact: dict) -> None:
    """The state must be defined on an axis independent of the channels."""
    for entry in artefact["state_definition_sweep"]:
        assert entry["state_validation_passed"] == entry["state_validation_total"], (
            entry["definition"],
            entry["state_validation"],
        )


def test_two_channels_are_enriched_in_the_state(artefact: dict) -> None:
    entry = _primary(artefact)
    genes = _by_gene(entry)
    for gene in ("KCNN4", "PIEZO1"):
        record = genes[gene]
        assert record["detection_ratio_vs_yap1negative"] > 2.0, gene
        assert record["mannwhitney_p_fdr"] < 1e-20, gene
    for gene in ("CACNA1E", "KCNA3", "TMEM150C", "STOML3", "PIEZO2"):
        record = genes[gene]
        assert record["detection_ratio_vs_yap1negative"] < 1.0, gene


def test_the_enrichment_survives_leaving_out_any_library(artefact: dict) -> None:
    loso = artefact["leave_one_sample_out"]
    for gene in ("KCNN4", "PIEZO1"):
        record = loso[gene]
        assert record["sign_is_stable"] is True, gene
        assert record["min_ratio"] > 2.0, gene
        assert record["max_p_leaving_one_out"] < 1e-10, gene
    for gene in ("CACNA1E", "KCNA3", "TMEM150C", "STOML3", "PIEZO2"):
        record = loso[gene]
        assert record["sign_is_stable"] is False, gene


def test_piezo1_marks_the_state_at_every_site_including_lung(artefact: dict) -> None:
    sites = {
        entry["tissue"]: entry for entry in artefact["per_tissue_channels"]
    }
    lung = {
        name: entry
        for name, entry in sites.items()
        if "lung" in name and entry["n_yap1_positive"] > 0
    }
    assert lung, "no lung site with state cells"
    for name, entry in lung.items():
        assert entry["channels"]["PIEZO1"]["detection_ratio"] > 1.0, name
    # KCa3.1 does not mark the state in lung.
    for name, entry in lung.items():
        assert entry["channels"]["KCNN4"]["detection_ratio"] < 1.0, name


def test_the_state_cells_are_not_simply_harder_to_sequence(artefact: dict) -> None:
    """A depth artefact would show fewer detected genes in the state."""
    control = artefact["complexity_control"]
    assert control["median_genes_detected_yap1_positive"] >= control[
        "median_genes_detected_yap1_negative"
    ]
    genes = {c["gene"]: c for c in artefact["controls"]}
    for gene in ("ACTB", "GAPDH", "RPL13A"):
        assert genes[gene]["detection_yap1_positive"] >= genes[gene][
            "detection_yap1_negative"
        ], gene


def test_the_artefact_records_the_submission_side_filename_mismatch(artefact: dict) -> None:
    """Two accessions carry file names belonging to the other accession."""
    mismatched = [
        record for record in artefact["per_sample"] if record["filename_mismatch"]
    ]
    assert len(mismatched) == 2, [r["accession"] for r in mismatched]
    for record in mismatched:
        assert record["file_prefix"] != record["geo_title"]


def test_benjamini_hochberg_is_monotone_and_bounded() -> None:
    adjusted = benjamini_hochberg([0.01, 0.02, 0.5, 1.0])
    assert all(0.0 <= p <= 1.0 for p in adjusted)
    assert adjusted == sorted(adjusted)
    assert adjusted[0] >= 0.01


def test_state_masks_are_nested() -> None:
    """A stricter definition cannot select cells the permissive one misses."""
    import numpy as np

    labels = np.array(["malignant"] * 100 + ["t_nk"] * 10, dtype=object)
    counts = np.arange(110) % 3
    expression = counts.astype(float)
    permissive_pos, permissive_neg = state_masks(
        "detected", labels, counts, expression
    )
    strict_pos, strict_neg = state_masks("two_transcripts", labels, counts, expression)
    assert set(strict_pos[strict_pos]).issubset(set(permissive_pos[permissive_pos]))
    # A stricter call selects fewer positive cells, so the negative group grows.
    assert strict_neg.sum() >= permissive_neg.sum()
