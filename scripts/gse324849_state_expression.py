#!/usr/bin/env python3
"""Does the ion-channel readout transfer to a third dataset?

This is the third state-resolved audit, and it is the first in **human** SCLC
with a therapy-resistance state: GSE324849 profiles a relapsed SCLC adrenal
metastasis from a patient treated with tarlatamab, the DLL3xCD3 bispecific
whose approval the paper's title refers to. Its central finding is that one
mode of acquired resistance is *therapeutic selection for a NEUROD1-high state
with concomitant DLL3 downregulation*.

That gives a state definition that is independent of the ion channels, and a
validation axis that is independent too: if the NEUROD1-high population is the
one the paper describes, it must have lost DLL3.

The comparison:

* GSE299684 — relapsed SCLC, YAP1+ state, PIEZO1 marks it (3.36x)
* GSE353299 — EGFR-mutant NSCLC, KRT17+ state, KCa3.1 marks it (3.70x)
* GSE324849 — relapsed SCLC after tarlatamab, NEUROD1-high state

Run
---
    python scripts/gse324849_state_expression.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]


def _load_core():
    spec = importlib.util.spec_from_file_location(
        "gse299684_state_expression", REPO / "scripts" / "gse299684_state_expression.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = _load_core()

CHANNELS = core.CHANNELS

STATE_GENE = "NEUROD1"

#: The paper's own signature for the NEUROD1-high acquired-resistance state:
#: DLL3 downregulation. None of these genes is an ion channel, so the state
#: call cannot be circular with the measurement.
STATE_VALIDATION_DOWN = ("DLL3", "ASCL1", "POU2F3")

CELL_TYPE_MARKERS: dict[str, tuple[str, ...]] = {
    "malignant": (
        "EPCAM",
        "KRT8",
        "KRT18",
        "KRT19",
        "SYP",
        "INSM1",
        "CHGA",
        "CHGB",
        "SCG2",
        "UCHL1",
        "NPY",
        "ASCL1",
        "NEUROD1",
        "POU2F3",
    ),
    "t_nk": ("CD3D", "CD3E", "TRAC", "TRBC2", "IL7R", "NKG7", "GNLY", "KLRD1"),
    "myeloid": ("LST1", "TYROBP", "CD68", "AIF1", "FCER1G", "C1QA", "C1QB", "CTSS"),
    "b_plasma": ("MS4A1", "CD79A", "CD79B", "JCHAIN", "IGHG1", "IGKC"),
    "endothelial": ("PECAM1", "VWF", "CLDN5", "EGFL7", "CDH5"),
    "fibroblast": ("COL1A1", "COL1A2", "DCN", "LUM", "COL3A1", "PDGFRB"),
}

STATE_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("detected", "NEUROD1 with at least one transcript"),
    ("two_transcripts", "NEUROD1 with at least two transcripts"),
    ("top_decile", "the top decile of NEUROD1 expression among malignant cells"),
)
PRIMARY_DEFINITION = "detected"


def read_library(directory: Path, stem: str):
    """One 10x library, in this deposit's naming (``<stem>_features.tsv.gz``)."""
    import gzip

    import scipy.io

    with gzip.open(directory / f"{stem}_features.tsv.gz", "rt") as handle:
        gene_names = [line.split("\t")[1] for line in handle if line.strip()]
    with gzip.open(directory / f"{stem}_barcodes.tsv.gz", "rt") as handle:
        n_cells = sum(1 for line in handle if line.strip())
    with gzip.open(directory / f"{stem}_matrix.mtx.gz", "rb") as handle:
        matrix = scipy.io.mmread(handle).tocsr()
    if matrix.shape != (len(gene_names), n_cells):
        raise ValueError(
            f"{stem}: matrix is {matrix.shape}, expected ({len(gene_names)}, {n_cells})"
        )
    return gene_names, matrix


def assign_cell_types(matrix, gene_index, min_score: float = 0.05) -> np.ndarray:
    names = list(CELL_TYPE_MARKERS)
    scores = np.vstack(
        [core.module_scores(matrix, gene_index, CELL_TYPE_MARKERS[n]) for n in names]
    )
    best = scores.argmax(axis=0)
    labels = np.array([names[i] for i in best], dtype=object)
    labels[scores.max(axis=0) < min_score] = "unassigned"
    return labels


def state_masks(definition, labels, state_counts, state_expression):
    malignant = labels == "malignant"
    if definition == "detected":
        positive = malignant & (state_counts >= 1)
    elif definition == "two_transcripts":
        positive = malignant & (state_counts >= 2)
    elif definition == "top_decile":
        threshold = (
            float(np.quantile(state_expression[malignant], 0.9)) if malignant.any() else 0.0
        )
        positive = malignant & (state_expression >= threshold)
    else:
        raise ValueError(f"unknown state definition: {definition}")
    return positive, malignant & ~positive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datadir", default="data/gse324849")
    parser.add_argument("--outdir", default="results/gse324849")
    args = parser.parse_args(argv)

    datadir = Path(args.datadir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    gene_names, raw = read_library(datadir, "GSE324849")
    gene_index = {g: i for i, g in enumerate(gene_names)}
    keep = core.qc_filter(raw, gene_names)
    raw = raw[:, keep]
    matrix = core.normalise(raw)
    labels = assign_cell_types(matrix, gene_index)
    state_counts = core.raw_counts(raw, gene_index, STATE_GENE)
    state_expression = core.gene_values(matrix, gene_index, STATE_GENE)
    immune = np.isin(labels, ["t_nk", "myeloid", "b_plasma"])

    print(
        f"cells: {matrix.shape[1]} after QC "
        f"({len(keep)} of {matrix.shape[1] + (matrix.shape[1] - len(keep))} raw)"
    )
    print("cell types:", {k: int((labels == k).sum()) for k in sorted(set(labels.tolist()))})

    malignant = labels == "malignant"
    detected = np.asarray((raw > 0).sum(axis=0)).ravel()
    print()
    print("=== depth control: median genes detected per cell ===")
    print(
        f"  malignant {float(np.median(detected[malignant])):.0f} | "
        f"immune {float(np.median(detected[immune])):.0f} | "
        f"all {float(np.median(detected)):.0f}"
    )
    print()
    print("=== compartment detection (all cells) ===")
    for gene in ("NEUROD1", "DLL3", "ASCL1", "POU2F3", "SYP", "KCNN4", "PIEZO1"):
        series = core.gene_values(matrix, gene_index, gene)
        print(
            f"  {gene:<10} malignant {int((series[malignant] > 0).sum()):>5}/{int(malignant.sum()):<5} "
            f"immune {int((series[immune] > 0).sum()):>5}/{int(immune.sum()):<5}"
        )

    sweep: list[dict] = []
    for definition, description in STATE_DEFINITIONS:
        positive, negative = state_masks(
            definition, labels, state_counts, state_expression
        )
        validation: dict[str, dict] = {}
        for gene in STATE_VALIDATION_DOWN:
            series = core.gene_values(matrix, gene_index, gene)
            pos = series[positive]
            neg = series[negative]
            validation[gene] = {
                "expected_direction": "down",
                "mean_state_positive": float(pos.mean()) if len(pos) else None,
                "mean_state_negative": float(neg.mean()) if len(neg) else None,
                "direction_as_reported": bool(
                    len(pos) and len(neg) and pos.mean() < neg.mean()
                ),
                "detection_state_positive": float((pos > 0).mean()) if len(pos) else None,
                "detection_state_negative": float((neg > 0).mean()) if len(neg) else None,
            }
        rows: list[dict] = []
        pvalues: list[float] = []
        for gene in CHANNELS:
            series = core.gene_values(matrix, gene_index, gene)
            stats = core.channel_statistics(series, positive, negative, immune)
            rows.append({"gene": gene, **stats})
            if stats.get("status") == "ok":
                pvalues.append(stats["mannwhitney_p"])
        adjusted = core.benjamini_hochberg(pvalues)
        for row, q in zip(rows, adjusted, strict=False):
            if row.get("status") == "ok":
                row["mannwhitney_p_fdr"] = q
        sweep.append(
            {
                "definition": definition,
                "description": description,
                "n_state_positive": int(positive.sum()),
                "n_state_negative": int(negative.sum()),
                "state_validation": validation,
                "state_validation_passed": sum(
                    1 for v in validation.values() if v["direction_as_reported"]
                ),
                "state_validation_total": len(validation),
                "channels": rows,
            }
        )

    controls = []
    for gene in ("PTPRC", "ACTB", "EPCAM", "SYP"):
        series = core.gene_values(matrix, gene_index, gene)
        positive, negative = state_masks(
            PRIMARY_DEFINITION, labels, state_counts, state_expression
        )
        controls.append(
            {"gene": gene, **core.channel_statistics(series, positive, negative, immune)}
        )

    payload = {
        "audit": {
            "id": "gse324849-state-expression-2026-11",
            "generated_by": "scripts/gse324849_state_expression.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "GSE324849",
            "description": (
                "Human relapsed SCLC adrenal gland metastasis, patient 7373, "
                "treated with tarlatamab; 10x GEM-X 5' single-cell library"
            ),
            "state_definition": (
                "NEUROD1-high malignant cells; the call is validated against "
                "the paper's own signature for the acquired-resistance state "
                "(DLL3 downregulation), which is independent of the ion channels"
            ),
            "state_definitions_swept": [d for d, _ in STATE_DEFINITIONS],
            "primary_definition": PRIMARY_DEFINITION,
            "channels": list(CHANNELS),
        },
        "cells": {
            "n_qc_passed": int(matrix.shape[1]),
            "n_features": int(len(gene_names)),
            "median_genes_detected_malignant": (
                float(np.median(detected[malignant])) if malignant.any() else None
            ),
            "median_genes_detected_immune": (
                float(np.median(detected[immune])) if immune.any() else None
            ),
            "compartment_detection": {
                gene: {
                    "malignant": int(
                        (core.gene_values(matrix, gene_index, gene)[malignant] > 0).sum()
                    ),
                    "malignant_total": int(malignant.sum()),
                    "immune": int(
                        (core.gene_values(matrix, gene_index, gene)[immune] > 0).sum()
                    ),
                    "immune_total": int(immune.sum()),
                }
                for gene in ("NEUROD1", "DLL3", "ASCL1", "POU2F3", "SYP", "KCNN4", "PIEZO1")
            },
            "cell_type_counts": {
                label: int((labels == label).sum())
                for label in sorted(set(labels.tolist()))
            },
        },
        "state_definition_sweep": sweep,
        "controls": controls,
    }

    (outdir / "state_expression.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print()
    for entry in sweep:
        print(
            f"[{entry['definition']}] state+={entry['n_state_positive']} "
            f"state-={entry['n_state_negative']} | paper signature reproduced "
            f"{entry['state_validation_passed']}/{entry['state_validation_total']}"
        )
        for gene, record in entry["state_validation"].items():
            pos_mean = record["mean_state_positive"]
            neg_mean = record["mean_state_negative"]
            print(
                f"    {gene:<8} state+={pos_mean if pos_mean is None else round(pos_mean, 4)} "
                f"state-={neg_mean if neg_mean is None else round(neg_mean, 4)} "
                f"({'down as reported' if record['direction_as_reported'] else 'NOT down'})"
            )
        for row in entry["channels"]:
            print(
                f"    {row['gene']:<10} det: +{row['detection_yap1_positive']:.3f} "
                f"-{row['detection_yap1_negative']:.3f} "
                f"imm={row['detection_immune']:.3f} "
                f"| ratio={row['detection_ratio_vs_yap1negative']} "
                f"| linear fold={row.get('linear_fold_vs_yap1negative')} "
                f"| p={row['mannwhitney_p']:.3g} q={row['mannwhitney_p_fdr']:.3g}"
            )
        print()
    print(f"wrote {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
