#!/usr/bin/env python3
"""Per-library state fraction and per-cell channel fold.

The gate review projects the plasma readout from a *pooled* state fraction and
a *pooled* per-cell fold. Both pooled values are cell-count weighted, so a few
large libraries decide them for every patient. This script recomputes both
per library, on the same code path the published state-expression artefacts
were computed with, so the projection can be run for the tumours individually.

The pooled values are recomputed here too and written out as a **control**.
They must reproduce the published artefacts' pooled numbers exactly; if they
do not, the per-library numbers are not trustworthy and the script fails.

    python scripts/per_library_folds.py

Outputs
-------
    results/per_library_folds/per_library_folds.json
    results/per_library_folds/per_library_folds.tsv
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
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(module_name: str):
    spec = importlib.util.spec_from_file_location(
        module_name, REPO / "scripts" / f"{module_name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = _load("gse299684_state_expression")
nsclc = _load("gse353299_state_expression")

#: The immune compartments, as both state-expression scripts define them.
IMMUNE_LABELS = ("t_nk", "myeloid", "b_plasma")

#: Below this many state cells the per-library fold is not a stable estimate.
#: The rule is stated here rather than applied silently: a library that fails
#: it is still reported, with its cell count, and flagged.
MIN_STATE_CELLS_FOR_STABLE_FOLD = 30


def _channel_entry(stats: dict) -> dict:
    """The per-library part of a channel record, in a stable shape."""
    if stats.get("status") != "ok":
        return {
            "status": stats.get("status", "missing"),
            "linear_fold": None,
            "n_state_cells": 0,
            "n_other_cells": 0,
        }
    return {
        "status": "ok",
        "linear_fold": stats.get("linear_fold_vs_yap1negative"),
        "linear_mean_state": stats.get("linear_mean_yap1_positive"),
        "linear_mean_other": stats.get("linear_mean_yap1_negative"),
        "detection_state": stats.get("detection_yap1_positive"),
        "detection_other": stats.get("detection_yap1_negative"),
        "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
        "mannwhitney_p": stats.get("mannwhitney_p"),
        "n_state_cells": int(stats.get("n_yap1_positive", 0)),
        "n_other_cells": int(stats.get("n_yap1_negative", 0)),
    }


def _sclc_pass(datadir: Path) -> tuple[list[dict], dict[str, dict], dict]:
    """Per-library state fraction and fold for the relapsed-SCLC deposit."""
    manifest: list[list[str]] = []
    for line in (datadir / "manifest.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        manifest.append(
            {
                "accession": parts[0],
                "file_prefix": parts[1],
                "title": parts[2],
                "tissue": parts[3],
            }
        )

    rows: list[dict] = []
    pooled: dict[str, list[np.ndarray]] = {
        "labels": [],
        "state_counts": [],
        "state_expression": [],
    }
    for gene in core.CHANNELS:
        pooled[gene] = []

    for record in manifest:
        accession = record["accession"]
        gene_names, raw = core.read_sample(
            datadir, accession, record["file_prefix"]
        )
        gene_index = {g: i for i, g in enumerate(gene_names)}
        keep = core.qc_filter(raw, gene_names)
        if len(keep) == 0:
            continue
        raw = raw[:, keep]
        matrix = core.normalise(raw)
        labels = core.assign_cell_types(matrix, gene_index)
        state_counts = core.raw_counts(raw, gene_index, core.YAP1_GENE)
        state_expression = core.gene_values(matrix, gene_index, core.YAP1_GENE)
        positive, negative = core.state_masks(
            core.PRIMARY_DEFINITION, labels, state_counts, state_expression
        )
        immune = np.isin(labels, IMMUNE_LABELS)

        pooled["labels"].append(labels)
        pooled["state_counts"].append(state_counts)
        pooled["state_expression"].append(state_expression)

        n_malignant = int((labels == "malignant").sum())
        n_state = int(positive.sum())
        row: dict = {
            "dataset": "SCLC",
            "accession": accession,
            "label": record["tissue"],
            "treatment": None,
            "n_malignant": n_malignant,
            "n_state": n_state,
            "state_fraction": (n_state / n_malignant) if n_malignant else None,
            "state_definition": core.PRIMARY_DEFINITION,
            "channels": {},
        }
        for gene in core.CHANNELS:
            series = core.gene_values(matrix, gene_index, gene)
            pooled[gene].append(series)
            entry = _channel_entry(
                core.channel_statistics(series, positive, negative, immune)
            )
            entry["fold_stable"] = bool(
                entry["n_state_cells"] >= MIN_STATE_CELLS_FOR_STABLE_FOLD
            )
            row["channels"][gene] = entry
        rows.append(row)
        print(f"{accession}: {n_state}/{n_malignant} state cells", flush=True)

    labels = np.concatenate(pooled["labels"])
    state_counts = np.concatenate(pooled["state_counts"])
    state_expression = np.concatenate(pooled["state_expression"])
    positive, negative = core.state_masks(
        core.PRIMARY_DEFINITION, labels, state_counts, state_expression
    )
    immune = np.isin(labels, IMMUNE_LABELS)
    pooled_channels: dict[str, dict] = {}
    for gene in core.CHANNELS:
        stats = core.channel_statistics(
            np.concatenate(pooled[gene]), positive, negative, immune
        )
        pooled_channels[gene] = {
            "linear_fold": stats.get("linear_fold_vs_yap1negative"),
            "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
            "n_state_cells": int(stats.get("n_yap1_positive", 0)),
            "n_other_cells": int(stats.get("n_yap1_negative", 0)),
        }
    composition = _composition(
        rows,
        pooled,
        labels,
        positive,
        negative,
        core.CHANNELS,
        _owner_array(rows, positive, negative),
    )
    return rows, pooled_channels, composition


def _nsclc_pass(datadir: Path) -> tuple[list[dict], dict[str, dict], dict]:
    """Per-library state fraction and fold for the EGFR-mutant NSCLC deposit."""
    manifest: list[dict] = []
    for line in (datadir / "manifest.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        manifest.append(
            {
                "accession": parts[0],
                "file_prefix": parts[1],
                "title": parts[2],
                "tissue": parts[3],
                "treatment": parts[4].strip().lower(),
            }
        )

    rows: list[dict] = []
    pooled: dict[str, list[np.ndarray]] = {
        "labels": [],
        "state_counts": [],
        "state_expression": [],
    }
    for gene in nsclc.CHANNELS:
        pooled[gene] = []

    for record in manifest:
        accession = record["accession"]
        gene_names, raw = core.read_sample(
            datadir, accession, record["file_prefix"]
        )
        gene_index = {g: i for i, g in enumerate(gene_names)}
        keep = core.qc_filter(raw, gene_names)
        if len(keep) == 0:
            continue
        raw = raw[:, keep]
        matrix = core.normalise(raw)
        labels = nsclc.assign_cell_types(matrix, gene_index)
        state_counts = core.raw_counts(raw, gene_index, nsclc.STATE_GENE)
        state_expression = core.gene_values(matrix, gene_index, nsclc.STATE_GENE)
        positive, negative = nsclc.state_masks(
            nsclc.PRIMARY_DEFINITION, labels, state_counts, state_expression
        )
        immune = np.isin(labels, IMMUNE_LABELS)

        pooled["labels"].append(labels)
        pooled["state_counts"].append(state_counts)
        pooled["state_expression"].append(state_expression)

        n_malignant = int((labels == "malignant").sum())
        n_state = int(positive.sum())
        row: dict = {
            "dataset": "NSCLC",
            "accession": accession,
            "label": f"{record['tissue']} / {record['treatment']}",
            "treatment": record["treatment"],
            "n_malignant": n_malignant,
            "n_state": n_state,
            "state_fraction": (n_state / n_malignant) if n_malignant else None,
            "state_definition": nsclc.PRIMARY_DEFINITION,
            "channels": {},
        }
        for gene in nsclc.CHANNELS:
            series = core.gene_values(matrix, gene_index, gene)
            pooled[gene].append(series)
            entry = _channel_entry(
                core.channel_statistics(series, positive, negative, immune)
            )
            entry["fold_stable"] = bool(
                entry["n_state_cells"] >= MIN_STATE_CELLS_FOR_STABLE_FOLD
            )
            row["channels"][gene] = entry
        rows.append(row)
        print(
            f"{accession}: {n_state}/{n_malignant} state cells "
            f"({record['treatment']})",
            flush=True,
        )

    labels = np.concatenate(pooled["labels"])
    state_counts = np.concatenate(pooled["state_counts"])
    state_expression = np.concatenate(pooled["state_expression"])
    positive, negative = nsclc.state_masks(
        nsclc.PRIMARY_DEFINITION, labels, state_counts, state_expression
    )
    immune = np.isin(labels, IMMUNE_LABELS)
    pooled_channels: dict[str, dict] = {}
    for gene in nsclc.CHANNELS:
        stats = core.channel_statistics(
            np.concatenate(pooled[gene]), positive, negative, immune
        )
        pooled_channels[gene] = {
            "linear_fold": stats.get("linear_fold_vs_yap1negative"),
            "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
            "n_state_cells": int(stats.get("n_yap1_positive", 0)),
            "n_other_cells": int(stats.get("n_yap1_negative", 0)),
        }
    composition = _composition(
        rows,
        pooled,
        labels,
        positive,
        negative,
        nsclc.CHANNELS,
        _owner_array(rows, positive, negative),
    )
    return rows, pooled_channels, composition


def _published_pooled(root: Path) -> dict[str, dict[str, dict]]:
    """The pooled folds as published, for the control."""
    out: dict[str, dict[str, dict]] = {}
    for dataset, relative in (
        ("SCLC", "results/gse299684/state_expression.json"),
        ("NSCLC", "results/gse353299/state_expression.json"),
    ):
        artefact = json.loads((root / relative).read_text())
        primary = artefact["audit"]["primary_definition"]
        entry = next(
            s
            for s in artefact["state_definition_sweep"]
            if s["definition"] == primary
        )
        out[dataset] = {
            c["gene"]: {
                "linear_fold": c.get("linear_fold_vs_yap1negative"),
                "detection_ratio": c.get("detection_ratio_vs_yap1negative"),
            }
            for c in entry["channels"]
            if c.get("status") == "ok"
        }
    return out


def _control(recomputed: dict[str, dict[str, dict]], published: dict[str, dict[str, dict]]) -> dict:
    """Compare the recomputed pooled folds with the published ones."""
    out: dict = {}
    for dataset, channels in recomputed.items():
        entries: dict = {}
        worst = 0.0
        for gene, record in channels.items():
            reference = published.get(dataset, {}).get(gene, {})
            recomputed_fold = record["linear_fold"]
            published_fold = reference.get("linear_fold")
            difference = (
                abs(recomputed_fold - published_fold)
                if recomputed_fold is not None and published_fold is not None
                else None
            )
            if difference is not None:
                worst = max(worst, difference)
            entries[gene] = {
                "recomputed_linear_fold": recomputed_fold,
                "published_linear_fold": published_fold,
                "absolute_difference": difference,
                "matches": difference is not None and difference < 1e-9,
                "recomputed_detection_ratio": record["detection_ratio"],
                "published_detection_ratio": reference.get("detection_ratio"),
            }
        out[dataset] = {
            "channels": entries,
            "max_absolute_difference": worst,
            "all_channels_match": all(e["matches"] for e in entries.values()),
        }
    return out


def _tsv(rows: list[dict], channels: tuple[str, ...]) -> str:
    header = [
        "dataset",
        "accession",
        "label",
        "treatment",
        "n_malignant",
        "n_state",
        "state_fraction",
    ]
    for gene in channels:
        header += [
            f"{gene}_linear_fold",
            f"{gene}_n_state_cells",
            f"{gene}_detection_ratio",
            f"{gene}_fold_stable",
        ]
    lines = ["\t".join(header)]
    for row in rows:
        cells = [
            row["dataset"],
            row["accession"],
            row["label"],
            row["treatment"] or "",
            str(row["n_malignant"]),
            str(row["n_state"]),
            f"{row['state_fraction']:.6f}" if row["state_fraction"] is not None else "",
        ]
        for gene in channels:
            entry = row["channels"].get(gene, {})
            fold = entry.get("linear_fold")
            cells += [
                f"{fold:.6f}" if fold is not None else "",
                str(entry.get("n_state_cells", 0)),
                f"{entry['detection_ratio']:.6f}"
                if entry.get("detection_ratio") is not None
                else "",
                "yes" if entry.get("fold_stable") else "no",
            ]
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


def _composition(
    per_library: list[dict],
    pooled: dict[str, list[np.ndarray]],
    labels: np.ndarray,
    positive: np.ndarray,
    negative: np.ndarray,
    channels: tuple[str, ...],
    owner: np.ndarray,
) -> dict:
    """How much of the pooled fold is a between-library contrast.

    The pooled fold compares every state cell in the deposit with every
    non-state cell in it. If the channel's baseline expression differs by
    metastatic site, that comparison is not the same quantity as the
    within-tumour comparison a patient's plasma would carry. Two numbers
    expose it: the pooled fold with one library removed, and the number of
    libraries whose own fold exceeds 1.
    """
    out: dict = {}
    values = {gene: np.concatenate(pooled[gene]) for gene in channels}
    for gene in channels:
        series = values[gene]
        loo: dict[str, float] = {}
        for library in per_library:
            keep = owner != library["accession"]
            state_mask = keep & positive
            other_mask = keep & negative
            if state_mask.sum() == 0 or other_mask.sum() == 0:
                continue
            loo[library["accession"]] = float(
                np.expm1(series[state_mask]).mean() / np.expm1(series[other_mask]).mean()
            )
        per_library_folds = []
        for library in per_library:
            entry = library["channels"].get(gene, {})
            fold = entry.get("linear_fold")
            if fold is not None:
                per_library_folds.append(fold)
        above_one = sum(1 for fold in per_library_folds if fold > 1.0)
        out[gene] = {
            "leave_one_library_out_pooled_fold": loo,
            "leave_one_library_out_min": min(loo.values()) if loo else None,
            "leave_one_library_out_max": max(loo.values()) if loo else None,
            "n_libraries_with_fold_above_one": above_one,
            "n_libraries_with_fold_computable": len(per_library_folds),
            "per_library_fold_median": (
                float(np.median(per_library_folds)) if per_library_folds else None
            ),
            "per_library_fold_min": (
                float(min(per_library_folds)) if per_library_folds else None
            ),
            "per_library_fold_max": (
                float(max(per_library_folds)) if per_library_folds else None
            ),
        }
    return out


def _owner_array(
    per_library: list[dict], positive: np.ndarray, negative: np.ndarray
) -> np.ndarray:
    """Which library each cell belongs to, for the leave-one-out computation.

    The pooled arrays are concatenated in manifest order, and the rows are
    appended in the same order, so the malignant cells can be handed to their
    libraries by counting them.
    """
    counts = [int(row["n_malignant"]) for row in per_library]
    owners = np.concatenate(
        [
            np.full(count, row["accession"])
            for count, row in zip(counts, per_library, strict=False)
        ]
    )
    malignant_index = np.where(positive | negative)[0]
    owner = np.empty(len(positive), dtype=object)
    owner[malignant_index] = owners
    return owner


def _published_sign_counts(root: Path) -> dict[str, dict[str, dict]]:
    """The published per-library detection-ratio sign counts, where they exist.

    The SCLC artefact records how many libraries have a detection ratio above
    1. The NSCLC artefact does not: its ``leave_one_sample_out`` block holds
    the pooled ratio with one library removed, which is a different statistic
    and is not a per-library sign.
    """
    out: dict[str, dict[str, dict]] = {}
    sclc = json.loads((root / "results/gse299684/state_expression.json").read_text())
    out["SCLC"] = {
        gene: {
            "above_one": record["samples_with_ratio_above_one"],
            "below_one": record["samples_with_ratio_below_one"],
        }
        for gene, record in sclc["per_sample_sign_counts"].items()
    }
    out["NSCLC"] = {}
    return out


def _composition_control(
    per_library: list[dict], published_signs: dict[str, dict[str, dict]]
) -> dict:
    """The per-library detection-ratio signs, against the published counts.

    The published state-expression artefacts already record how many libraries
    have a detection ratio above 1. This recomputes that count, so the
    per-library folds rest on the same footing as a published number.
    """
    out: dict = {}
    for dataset in ("SCLC", "NSCLC"):
        subset = [r for r in per_library if r["dataset"] == dataset]
        entries: dict = {}
        for gene in core.CHANNELS:
            above = 0
            below = 0
            computable = 0
            for library in subset:
                entry = library["channels"].get(gene, {})
                ratio = entry.get("detection_ratio")
                if ratio is None:
                    continue
                computable += 1
                if ratio > 1.0:
                    above += 1
                else:
                    below += 1
            reference = published_signs.get(dataset, {}).get(gene)
            entries[gene] = {
                "recomputed_above_one": above,
                "recomputed_below_one": below,
                "n_computable": computable,
                "published_above_one": (
                    reference["above_one"] if reference else None
                ),
                "published_below_one": (
                    reference["below_one"] if reference else None
                ),
                "matches": (
                    reference is not None
                    and reference["above_one"] == above
                    and reference["below_one"] == below
                ),
            }
        out[dataset] = entries
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sclc-datadir", default="data/gse299684")
    parser.add_argument("--nsclc-datadir", default="data/gse353299")
    parser.add_argument("--outdir", default="results/per_library_folds")
    args = parser.parse_args(argv)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    sclc_rows, sclc_pooled, sclc_composition = _sclc_pass(
        Path(args.sclc_datadir)
    )
    nsclc_rows, nsclc_pooled, nsclc_composition = _nsclc_pass(
        Path(args.nsclc_datadir)
    )
    rows = sclc_rows + nsclc_rows

    published = _published_pooled(REPO)
    control = _control(
        {"SCLC": sclc_pooled, "NSCLC": nsclc_pooled}, published
    )
    signs = _composition_control(rows, _published_sign_counts(REPO))
    composition = {"SCLC": sclc_composition, "NSCLC": nsclc_composition}

    document = {
        "audit": {
            "id": "per-library-folds-2026-11",
            "generated_by": "scripts/per_library_folds.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "note": (
                "Per-library state fraction and per-cell channel fold, "
                "recomputed on the same code path as the published "
                "state-expression artefacts. The pooled values are recomputed "
                "too and reported as a control: they must reproduce the "
                "published numbers exactly, or the per-library numbers are "
                "not trustworthy."
            ),
            "state_definitions": {
                "SCLC": core.PRIMARY_DEFINITION,
                "NSCLC": nsclc.PRIMARY_DEFINITION,
            },
            "min_state_cells_for_stable_fold": MIN_STATE_CELLS_FOR_STABLE_FOLD,
        },
        "control": control,
        "per_library_sign_counts": signs,
        "composition": composition,
        "per_library": rows,
    }

    (outdir / "per_library_folds.json").write_text(
        json.dumps(document, indent=2) + "\n"
    )
    (outdir / "per_library_folds.tsv").write_text(
        _tsv(rows, core.CHANNELS)
    )

    for dataset, entry in control.items():
        status = "MATCH" if entry["all_channels_match"] else "MISMATCH"
        print(
            f"control {dataset}: {status} "
            f"(max |diff| {entry['max_absolute_difference']:.3e})"
        )
    if not all(entry["all_channels_match"] for entry in control.values()):
        print(
            "the recomputed pooled values do not reproduce the published "
            "artefacts; the per-library numbers are not trustworthy",
            file=sys.stderr,
        )
        return 1

    print(f"wrote {outdir / 'per_library_folds.json'}")
    print(f"wrote {outdir / 'per_library_folds.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
