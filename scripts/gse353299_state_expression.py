#!/usr/bin/env python3
"""Does the electrical reading of the relapse-competent state survive in NSCLC?

GSE299684 established, in relapsed SCLC, that the relapse-competent state is
electrically marked: PIEZO1 is detected in 39% of state cells against 6% of
the surrounding tumour, and KCa3.1 in 31% against 9%. The programme's target
tissue, however, is lung adenocarcinoma, and the risk register lists "the
state is not present in NSCLC (only SCLC)" as a Medium-likelihood,
High-impact risk.

This script tests the same hypothesis on **GSE353299**: 25 single-cell
libraries of EGFR-mutant lung adenocarcinoma collected at three clinical
timepoints -- treatment naive, osimertinib-treated minimal residual disease,
and progression. The state here is defined by the dataset's own authors as
**KRT17+** cells (the GEO record states the study "quantify[s] the number of
KRT17+ and KRT17- cells"; the series title calls them a "keratin 17+
aberrant basaloid drug tolerant persister population").

Design notes
------------

**The state definition is orthogonal to the hypothesis.** KRT17 is a keratin;
the channels under test are an ion channel and a mechanosensitive channel.
A channel cannot define the population it is then tested in.

**The state call is validated on an axis that is also orthogonal.** The
dataset's own title calls the KRT17+ population *baserrataloid*, so the
basaloid programme (KRT5, KRT6A, KRT14) is checked to be co-expressed in the
KRT17+ cells. The paper itself could not be consulted: the deposit is dated
2026-11-06 and is not yet indexed in PubMed or Europe PMC, so the GEO record
is the source of the definition used here.

**The timepoints are the science, not just metadata.** The paper's claim is
that the persister population emerges with drug exposure. This dataset can
test that directly: the KRT17+ fraction per treatment timepoint.

Run
---
    python scripts/download_gse353299.py && \\
    python scripts/gse353299_state_expression.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]


def _load_core():
    """The shared machinery, from the SCLC script it was written with."""
    spec = importlib.util.spec_from_file_location(
        "gse299684_state_expression", REPO / "scripts" / "gse299684_state_expression.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = _load_core()

#: The candidate channels from the D0 window audit, unchanged.
CHANNELS = core.CHANNELS

#: The state gene for this dataset.
STATE_GENE = "KRT17"

#: Cell-type marker modules for lung adenocarcinoma. The neuroendocrine
#: markers of the SCLC analysis are deliberately absent: this is adenocarcinoma,
#: and the epithelium is the tumour.
CELL_TYPE_MARKERS: dict[str, tuple[str, ...]] = {
    "malignant": (
        "EPCAM",
        "KRT8",
        "KRT18",
        "KRT19",
        "KRT7",
        "KRT5",
        "KRT6A",
    ),
    "t_nk": ("CD3D", "CD3E", "TRAC", "TRBC2", "IL7R", "NKG7", "GNLY", "KLRD1"),
    "myeloid": ("LST1", "TYROBP", "CD68", "AIF1", "FCER1G", "C1QA", "C1QB", "CTSS"),
    "b_plasma": ("MS4A1", "CD79A", "CD79B", "JCHAIN", "IGHG1", "IGKC"),
    "endothelial": ("PECAM1", "VWF", "CLDN5", "EGFL7", "CDH5"),
    "fibroblast": ("COL1A1", "COL1A2", "DCN", "LUM", "COL3A1", "PDGFRB"),
}

#: The basaloid programme, which the dataset's own title names as the
#: hallmark of the KRT17+ population. None of these is an ion channel.
BASALOID_MARKERS: tuple[str, ...] = ("KRT5", "KRT6A", "KRT14", "KRT15")

#: The state definitions that are swept.
STATE_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("detected", "KRT17 with at least one transcript"),
    ("two_transcripts", "KRT17 with at least two transcripts"),
    ("top_decile", "the top decile of KRT17 expression among malignant cells"),
)
PRIMARY_DEFINITION = "detected"

#: The treatment timepoints, in clinical order. The GEO records spell them
#: "Treatment_naive", "Osi_MRD", "Osi_progression" and "Progression"; they are
#: matched case-insensitively.
TIMEPOINT_ORDER = (
    "treatment_naive",
    "osi_mrd",
    "osi_progression",
    "progression",
)


def assign_cell_types(
    matrix, gene_index: dict[str, int], min_score: float = 0.05
) -> np.ndarray:
    """Label each cell with its marker-module argmax, or ``unassigned``."""
    names = list(CELL_TYPE_MARKERS)
    scores = np.vstack(
        [core.module_scores(matrix, gene_index, CELL_TYPE_MARKERS[name]) for name in names]
    )
    best = scores.argmax(axis=0)
    best_score = scores.max(axis=0)
    labels = np.array([names[i] for i in best], dtype=object)
    labels[best_score < min_score] = "unassigned"
    return labels


def state_masks(
    definition: str,
    labels: np.ndarray,
    state_counts: np.ndarray,
    state_expression: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """(state-positive, state-negative) masks among malignant cells."""
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
    parser.add_argument("--datadir", default="data/gse353299")
    parser.add_argument("--outdir", default="results/gse353299")
    parser.add_argument(
        "--gene-positions",
        default="data/ensembl_gene_positions.tsv",
        help="cached Ensembl BioMart gene positions",
    )
    parser.add_argument("--samples", default="", help="comma-separated accessions")
    args = parser.parse_args(argv)

    datadir = Path(args.datadir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    manifest_path = datadir / "manifest.tsv"
    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 1
    manifest = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        manifest.append(
            {
                "accession": parts[0],
                "file_prefix": parts[1],
                "title": parts[2],
                "tissue": parts[3],
                "treatment": parts[4],
                "genotype": parts[5] if len(parts) > 5 else "",
                "cell_type": parts[6] if len(parts) > 6 else "",
                "filename_mismatch": len(parts) > 7 and parts[7].strip().lower() == "yes",
            }
        )
    if args.samples:
        wanted = {s.strip() for s in args.samples.split(",")}
        manifest = [m for m in manifest if m["accession"] in wanted]

    pooled: dict[str, list[np.ndarray]] = {
        "labels": [],
        "state_counts": [],
        "state_expression": [],
        "sample": [],
        "treatment": [],
    }
    for gene in CHANNELS + BASALOID_MARKERS + ("PTPRC", "ACTB", "EPCAM", "KRT8"):
        pooled[gene] = []

    per_sample: list[dict] = []
    for record in manifest:
        accession = record["accession"]
        gene_names, raw = core.read_sample(
            datadir, accession, record["file_prefix"]
        )
        gene_index = {g: i for i, g in enumerate(gene_names)}
        keep = core.qc_filter(raw, gene_names)
        if len(keep) == 0:
            print(f"{accession}: no cells passed QC", flush=True)
            continue
        raw = raw[:, keep]
        matrix = core.normalise(raw)
        labels = assign_cell_types(matrix, gene_index)
        state_counts = core.raw_counts(raw, gene_index, STATE_GENE)
        state_expression = core.gene_values(matrix, gene_index, STATE_GENE)

        pooled["labels"].append(labels)
        pooled["state_counts"].append(state_counts)
        pooled["state_expression"].append(state_expression)
        pooled["sample"].append(np.full(matrix.shape[1], accession, dtype=object))
        pooled["treatment"].append(
            np.full(matrix.shape[1], record["treatment"].strip().lower(), dtype=object)
        )
        for gene in pooled:
            if gene in ("labels", "state_counts", "state_expression", "sample", "treatment"):
                continue
            pooled[gene].append(core.gene_values(matrix, gene_index, gene))

        malignant = labels == "malignant"
        per_sample.append(
            {
                "accession": accession,
                "file_prefix": record["file_prefix"],
                "geo_title": record["title"],
                "tissue": record["tissue"],
                "treatment": record["treatment"],
                "genotype": record["genotype"],
                "cell_type_characteristic": record["cell_type"],
                "filename_mismatch": record["filename_mismatch"],
                "n_cells_qc": int(matrix.shape[1]),
                "n_malignant": int(malignant.sum()),
                "n_state_positive": int((malignant & (state_counts >= 1)).sum()),
                "state_positive_fraction_of_malignant": (
                    float((malignant & (state_counts >= 1)).sum() / malignant.sum())
                    if malignant.sum()
                    else None
                ),
                "cell_type_counts": {
                    label: int((labels == label).sum())
                    for label in sorted(set(labels.tolist()))
                },
            }
        )
        print(
            f"{accession} ({record['tissue']}, {record['treatment']}): "
            f"{matrix.shape[1]} cells, malignant={int(malignant.sum())}, "
            f"KRT17+={int((malignant & (state_counts >= 1)).sum())}",
            flush=True,
        )

    if not pooled["labels"]:
        print("no samples could be read", file=sys.stderr)
        return 1

    labels = np.concatenate(pooled["labels"])
    state_counts = np.concatenate(pooled["state_counts"])
    state_expression = np.concatenate(pooled["state_expression"])
    sample_of = np.concatenate(pooled["sample"])
    treatment_of = np.concatenate(pooled["treatment"])
    values = {
        gene: np.concatenate(parts)
        for gene, parts in pooled.items()
        if gene not in ("labels", "state_counts", "state_expression", "sample", "treatment")
    }
    immune = np.isin(labels, ["t_nk", "myeloid", "b_plasma"])
    accessions = sorted(set(sample_of.tolist()))

    # --- the sweep over state definitions ---
    sweep: list[dict] = []
    for definition, description in STATE_DEFINITIONS:
        positive, negative = state_masks(
            definition, labels, state_counts, state_expression
        )
        basaloid_pos = np.mean(
            [
                values[g][positive].mean()
                for g in BASALOID_MARKERS
                if g in values
            ]
            or [float("nan")]
        )
        basaloid_neg = np.mean(
            [values[g][negative].mean() for g in BASALOID_MARKERS if g in values]
            or [float("nan")]
        )
        rows: list[dict] = []
        pvalues: list[float] = []
        for gene in CHANNELS:
            series = values.get(gene)
            if series is None:
                rows.append({"gene": gene, "status": "not_detected_in_any_sample"})
                continue
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
                "state_validation": {
                    "basaloid_programme_mean_state_positive": float(basaloid_pos),
                    "basaloid_programme_mean_state_negative": float(basaloid_neg),
                    "basaloid_enriched_in_state": bool(basaloid_pos > basaloid_neg),
                },
                "channels": rows,
            }
        )

    positive, negative = state_masks(
        PRIMARY_DEFINITION, labels, state_counts, state_expression
    )

    # --- per timepoint and per patient ---
    per_timepoint: list[dict] = []
    for timepoint in TIMEPOINT_ORDER:
        mask = treatment_of == timepoint
        if not mask.any():
            continue
        entry: dict = {
            "treatment": timepoint,
            "n_libraries": len(set(sample_of[mask].tolist())),
            "n_cells": int(mask.sum()),
            "n_malignant": int((mask & (labels == "malignant")).sum()),
            "n_state_positive": int((mask & positive).sum()),
            "state_positive_fraction_of_malignant": (
                float((mask & positive).sum() / (mask & (labels == "malignant")).sum())
                if (mask & (labels == "malignant")).sum()
                else None
            ),
            "channels": {},
        }
        for gene in CHANNELS:
            series = values.get(gene)
            if series is None:
                continue
            stats = core.channel_statistics(
                series, mask & positive, mask & negative, mask & immune
            )
            entry["channels"][gene] = {
                "detection_state_positive": stats.get("detection_yap1_positive"),
                "detection_state_negative": stats.get("detection_yap1_negative"),
                "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
                "mannwhitney_p": stats.get("mannwhitney_p"),
            }
        per_timepoint.append(entry)

    per_patient: list[dict] = []
    for accession in accessions:
        in_sample = sample_of == accession
        row: dict = {
            "accession": accession,
            "treatment": treatment_of[in_sample][0],
            "n_state_positive": int((in_sample & positive).sum()),
            "n_state_negative": int((in_sample & negative).sum()),
            "channels": {},
        }
        for gene in CHANNELS:
            series = values.get(gene)
            if series is None:
                continue
            stats = core.channel_statistics(
                series, in_sample & positive, in_sample & negative, in_sample & immune
            )
            row["channels"][gene] = {
                "detection_state_positive": stats.get("detection_yap1_positive"),
                "detection_state_negative": stats.get("detection_yap1_negative"),
                "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
            }
        per_patient.append(row)

    leave_one_out: dict[str, dict] = {}
    for gene in CHANNELS:
        series = values.get(gene)
        if series is None:
            continue
        ratios: list[float | None] = []
        pvalues: list[float | None] = []
        for accession in accessions:
            keep = sample_of != accession
            stats = core.channel_statistics(
                series, keep & positive, keep & negative, keep & immune
            )
            ratios.append(stats.get("detection_ratio_vs_yap1negative"))
            pvalues.append(stats.get("mannwhitney_p"))
        usable = [r for r in ratios if r is not None]
        leave_one_out[gene] = {
            "detection_ratio_leaving_one_sample_out": {
                accession: ratio for accession, ratio in zip(accessions, ratios, strict=True)
            },
            "min_ratio": min(usable) if usable else None,
            "max_ratio": max(usable) if usable else None,
            "n_samples_with_ratio_above_one": sum(1 for r in usable if r > 1),
            "n_samples_with_ratio_below_one": sum(1 for r in usable if r < 1),
            "sign_is_stable": (
                all(r > 1 for r in usable) or all(r < 1 for r in usable)
            )
            if usable
            else None,
            "max_p_leaving_one_out": max(
                (p for p in pvalues if p is not None), default=None
            ),
        }

    controls = []
    for gene in ("PTPRC", "ACTB", "EPCAM", "KRT8"):
        series = values.get(gene)
        if series is None:
            continue
        controls.append(
            {"gene": gene, **core.channel_statistics(series, positive, negative, immune)}
        )

    payload = {
        "audit": {
            "id": "gse353299-state-expression-2026-11",
            "generated_by": "scripts/gse353299_state_expression.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "GSE353299",
            "description": (
                "EGFR-mutant lung adenocarcinoma, 25 single-cell libraries at "
                "treatment-naive, osimertinib MRD and progression timepoints"
            ),
            "state_definition": (
                "KRT17+ malignant cells, as the dataset's own GEO record defines "
                "them; the call is validated on the basaloid programme, which "
                "the series title names, and is independent of the channels"
            ),
            "state_definitions_swept": [d for d, _ in STATE_DEFINITIONS],
            "primary_definition": PRIMARY_DEFINITION,
            "channels": list(CHANNELS),
            "basaloid_markers": list(BASALOID_MARKERS),
        },
        "cells": {
            "n_qc_passed": int(len(labels)),
            "cell_type_counts": {
                label: int((labels == label).sum())
                for label in sorted(set(labels.tolist()))
            },
        },
        "per_sample": per_sample,
        "state_definition_sweep": sweep,
        "per_timepoint": per_timepoint,
        "per_patient": per_patient,
        "leave_one_sample_out": leave_one_out,
        "controls": controls,
    }

    (outdir / "state_expression.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print()
    print(f"cells passing QC: {len(labels)}")
    print("cell types:", payload["cells"]["cell_type_counts"])
    print()
    for entry in sweep:
        validation = entry["state_validation"]
        print(
            f"[{entry['definition']}] state+={entry['n_state_positive']} "
            f"state-={entry['n_state_negative']} | basaloid programme "
            f"{validation['basaloid_programme_mean_state_positive']:.4f} vs "
            f"{validation['basaloid_programme_mean_state_negative']:.4f} "
            f"(enriched: {validation['basaloid_enriched_in_state']})"
        )
        for row in entry["channels"]:
            if row.get("status") != "ok":
                print(f"    {row['gene']:<10} not detected in any sample")
                continue
            print(
                f"    {row['gene']:<10} det: state+={row['detection_yap1_positive']:.3f} "
                f"state-={row['detection_yap1_negative']:.3f} "
                f"immune={row['detection_immune']:.3f} "
                f"| ratio={row['detection_ratio_vs_yap1negative']} "
                f"| p={row['mannwhitney_p']:.3g} q={row['mannwhitney_p_fdr']:.3g}"
            )
        print()
    print("per timepoint (KRT17+ fraction of malignant cells):")
    for entry in per_timepoint:
        print(
            f"  {entry['treatment']:<16} libs={entry['n_libraries']:<3} "
            f"malignant={entry['n_malignant']:<6} state+={entry['n_state_positive']:<5} "
            f"fraction={entry['state_positive_fraction_of_malignant']}"
        )
    print()
    print("leave-one-patient-out:")
    for gene, record in leave_one_out.items():
        print(
            f"  {gene:<10} min={record['min_ratio']} max={record['max_ratio']} "
            f"| above: {record['n_samples_with_ratio_above_one']} "
            f"below: {record['n_samples_with_ratio_below_one']} "
            f"| sign stable: {record['sign_is_stable']} "
            f"| max p: {record['max_p_leaving_one_out']}"
        )
    print(f"\nwrote {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
