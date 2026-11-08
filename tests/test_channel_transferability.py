"""Tests for the channel-transferability audit.

The audit's claim is a negative one with a design consequence: the ion
channels that mark the relapse-competent state in two datasets are absent
from a third tumour's malignant compartment, while the same channels are
detected in its immune compartment, and the tumour is at least as deeply
covered as the immune cells. Each part is asserted here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ARTEFACT = Path("results/gse324849/state_expression.json")
REPORT = Path("docs/CHANNEL-TRANSFERABILITY.md")


@pytest.fixture(scope="module")
def transfer() -> dict:
    if not ARTEFACT.exists():
        pytest.skip("the channel-transferability artefact has not been generated")
    return json.loads(ARTEFACT.read_text())


def test_the_third_tumour_does_not_express_either_channel(transfer: dict) -> None:
    detection = transfer["cells"]["compartment_detection"]
    for gene in ("KCNN4", "PIEZO1"):
        assert detection[gene]["malignant"] == 0, gene


def test_the_channels_are_detected_in_the_same_librarys_immune_cells(
    transfer: dict,
) -> None:
    detection = transfer["cells"]["compartment_detection"]
    for gene in ("KCNN4", "PIEZO1"):
        assert detection[gene]["immune"] > 0, gene
        assert detection[gene]["immune"] / detection[gene]["immune_total"] > 0.02, gene


def test_the_absence_is_not_a_depth_artefact(transfer: dict) -> None:
    assert (
        transfer["cells"]["median_genes_detected_malignant"]
        >= transfer["cells"]["median_genes_detected_immune"]
    )


def test_the_third_tumour_is_ascl1_subtype_and_lacks_the_state(
    transfer: dict,
) -> None:
    detection = transfer["cells"]["compartment_detection"]
    total = detection["ASCL1"]["malignant_total"]
    assert detection["ASCL1"]["malignant"] / total > 0.5
    assert detection["NEUROD1"]["malignant"] <= 2
    assert detection["POU2F3"]["malignant"] == 0


def test_the_report_states_the_deposit_defect_and_the_consequence() -> None:
    text = REPORT.read_text()
    assert "no gene annotation" in text
    assert "tumour-expression gate" in text
    assert "GSE325242" in text and "GSE324849" in text
