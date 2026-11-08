#!/usr/bin/env python3
"""Is the relapse-competent state electrically readable?

GSE299684 is the GEO deposit of PMID 42019833 (Stewart et al., *YAP1 Defines
an Emergent, Plastic Population of Relapsed SCLC*, J Thorac Oncol 2026) — the
anchor paper of the research plan. It holds 15 single-cell libraries of
relapsed SCLC from seven metastatic sites, and it is public. This script
answers the question the plan cannot answer on bulk tissue: **do the cells of
the relapse-competent state express the candidate channels more than the
surrounding tumour and the tumour-infiltrating immune cells?**

Design notes
------------

**The state is defined on an axis independent of the feature under test.** The
paper defines its population by YAP1 expression, and independently reports that
YAP1(+) cells lose DLL3, SEZ6 and CEACAM5 while coexpressing CD276 (B7-H3),
TACSTD2 (TROP2) and ERBB2. This script calls the population by YAP1 and then
*checks* that it reproduces the surface-target signature. Only after that
check does it look at the ion channels, so a channel cannot define the state
it is then tested in.

**The state call is swept, not fixed.** "YAP1 detected" is permissive; a cell
with one transcript is not the same as a cell with fifty. Three definitions
are run — any detection, at least two transcripts, and the top decile of
expression — and the channel result is reported under each, so that the
conclusion cannot rest on one cut.

**The comparison that matters is within the tumour.** A channel that is
expressed everywhere is not a state marker. The primary contrast is YAP1(+)
cancer cells against YAP1(-) cancer cells from the same biopsies; the
secondary one is YAP1(+) cancer cells against the immune compartment, which is
the "state-to-immune ratio" the D0 window audit asked for.

**Detection rate is reported next to the mean.** Ion channels are low
expressed in single-cell data and drop out, so the fraction of cells with at
least one count is reported alongside the mean log-normalised expression, and
the two are not allowed to disagree silently.

Run
---
    python scripts/gse299684_state_expression.py --datadir data/gse299684
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.stats import fisher_exact, mannwhitneyu

#: The candidate channels from the D0 window audit, plus the Piezo1 complex
#: regulators and the dominant on-target off-target.
CHANNELS: tuple[str, ...] = (
    "KCNN4",
    "PIEZO1",
    "CACNA1E",
    "KCNA3",
    "TMEM150C",
    "STOML3",
    "PIEZO2",
)

#: Cell-type marker modules. The malignant module deliberately mixes epithelial
#: and neuroendocrine markers: the YAP1(+) population abandons SCLC features
#: for LCNEC features, so a neuroendocrine-only rule would drop exactly the
#: cells under test.
CELL_TYPE_MARKERS: dict[str, tuple[str, ...]] = {
    "malignant": (
        "EPCAM",
        "KRT8",
        "KRT18",
        "KRT19",
        "KRT7",
        "SYP",
        "INSM1",
        "CHGA",
        "CHGB",
        "SCG2",
        "UCHL1",
        "NPY",
    ),
    "t_nk": ("CD3D", "CD3E", "TRAC", "TRBC2", "IL7R", "NKG7", "GNLY", "KLRD1"),
    "myeloid": ("LST1", "TYROBP", "CD68", "AIF1", "FCER1G", "C1QA", "C1QB", "CTSS"),
    "b_plasma": ("MS4A1", "CD79A", "CD79B", "JCHAIN", "IGHG1", "IGKC"),
    "endothelial": ("PECAM1", "VWF", "CLDN5", "EGFL7", "CDH5"),
    "fibroblast": ("COL1A1", "COL1A2", "DCN", "LUM", "COL3A1", "PDGFRB"),
}

#: The paper's surface-target signature, used to validate the state call.
#: YAP1(+) cells are expected to be higher in the first group and lower in the
#: second. None of these genes is an ion channel.
STATE_VALIDATION_UP: tuple[str, ...] = ("CD276", "TACSTD2", "ERBB2")
STATE_VALIDATION_DOWN: tuple[str, ...] = ("DLL3", "SEZ6", "CEACAM5")

#: Housekeeping and pan-immune controls, so a null result can be told apart
#: from a broken pipeline.
CONTROL_GENES: tuple[str, ...] = ("PTPRC", "ACTB", "GAPDH", "RPL13A")

YAP1_GENE = "YAP1"

#: The three state definitions that are swept.
STATE_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("detected", "YAP1 with at least one transcript"),
    ("two_transcripts", "YAP1 with at least two transcripts"),
    ("top_decile", "the top decile of YAP1 expression among malignant cells"),
)
PRIMARY_DEFINITION = "detected"

#: Copy-number proxy settings.
CNV_DIAGNOSTIC_GENES = 2000
CNV_NEIGHBOURHOOD = 50

CNV_CHROMOSOMES: frozenset[str] = frozenset(
    [str(c) for c in range(1, 23)] + ["X", "Y"]
)

USER_AGENT = "relapse-competence-gse299684/0.1"
ENSEMBL_BIOMART = "https://www.ensembl.org/biomart/martservice"


# =============================================================================
# data access
# =============================================================================
def fetch_gene_positions(cache: Path) -> dict[str, tuple[str, int, int]]:
    """Gene symbol -> (chromosome, start, end), from Ensembl BioMart."""
    if cache.exists():
        rows: dict[str, tuple[str, int, int]] = {}
        for line in cache.read_text(encoding="utf-8").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            try:
                rows[parts[1]] = (parts[2], int(parts[3]), int(parts[4]))
            except ValueError:
                continue
        return rows

    query = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query virtualSchemaName="default" formatter="TSV" header="1" uniqueRows="1" datasetConfigVersion="0.6">
  <Dataset name="hsapiens_gene_ensembl" interface="default">
    <Attribute name="ensembl_gene_id"/>
    <Attribute name="external_gene_name"/>
    <Attribute name="chromosome_name"/>
    <Attribute name="start_position"/>
    <Attribute name="end_position"/>
    <Attribute name="gene_biotype"/>
  </Dataset>
</Query>"""
    url = ENSEMBL_BIOMART + "?" + urllib.parse.urlencode({"query": query})
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        text = response.read().decode("utf-8")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")

    rows = {}
    for line in text.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) < 5 or not parts[1]:
            continue
        try:
            rows[parts[1]] = (parts[2], int(parts[3]), int(parts[4]))
        except ValueError:
            continue
    return rows


# =============================================================================
# 10x loading
# =============================================================================
def read_sample(
    directory: Path, accession: str, prefix: str
) -> tuple[list[str], sparse.csr_matrix]:
    """One 10x triplet -> (gene symbols, genes x cells CSR matrix)."""
    import scipy.io

    with gzip.open(directory / f"{accession}_{prefix}.features.tsv.gz", "rt") as handle:
        gene_names = [line.split("\t")[1] for line in handle if line.strip()]
    with gzip.open(directory / f"{accession}_{prefix}.barcodes.tsv.gz", "rt") as handle:
        n_cells = sum(1 for line in handle if line.strip())
    with gzip.open(directory / f"{accession}_{prefix}.matrix.mtx.gz", "rb") as handle:
        matrix = scipy.io.mmread(handle).tocsr()
    if matrix.shape != (len(gene_names), n_cells):
        raise ValueError(
            f"{accession}: matrix is {matrix.shape}, expected ({len(gene_names)}, {n_cells})"
        )
    return gene_names, matrix


# =============================================================================
# QC and normalisation
# =============================================================================
def qc_filter(
    matrix: sparse.csr_matrix,
    gene_names: list[str],
    min_genes: int = 200,
    min_counts: int = 500,
    max_mito: float = 0.20,
) -> np.ndarray:
    """The indices of the cells that pass quality control."""
    counts = np.asarray(matrix.sum(axis=0)).ravel()
    n_genes = np.asarray((matrix > 0).sum(axis=0)).ravel()
    mito_idx = [i for i, g in enumerate(gene_names) if g.startswith("MT-")]
    if mito_idx:
        mito = np.asarray(matrix[mito_idx, :].sum(axis=0)).ravel()
        mito_fraction = np.divide(
            mito, counts, out=np.zeros_like(mito, dtype=float), where=counts > 0
        )
    else:
        mito_fraction = np.zeros_like(counts, dtype=float)
    keep = (n_genes >= min_genes) & (counts >= min_counts) & (mito_fraction <= max_mito)
    return np.flatnonzero(keep)


def normalise(matrix: sparse.csr_matrix, target: float = 1e4) -> sparse.csr_matrix:
    """Counts per cell to a fixed library size, then log1p."""
    counts = np.asarray(matrix.sum(axis=0)).ravel()
    scale = np.divide(
        target, counts, out=np.zeros_like(counts, dtype=float), where=counts > 0
    )
    scaled = matrix.multiply(scale).tocsr()
    scaled.data = np.log1p(scaled.data)
    return scaled


def gene_values(
    matrix: sparse.csr_matrix, gene_index: dict[str, int], gene: str
) -> np.ndarray:
    """The log-normalised expression of one gene, zeros when it is absent."""
    if gene not in gene_index:
        return np.zeros(matrix.shape[1])
    return np.asarray(matrix[gene_index[gene]].todense()).ravel()


def raw_counts(
    matrix: sparse.csr_matrix, gene_index: dict[str, int], gene: str
) -> np.ndarray:
    """The raw transcript count of one gene, zeros when it is absent."""
    if gene not in gene_index:
        return np.zeros(matrix.shape[1])
    return np.asarray(matrix[gene_index[gene]].todense()).ravel()


# =============================================================================
# cell typing
# =============================================================================
def module_scores(
    matrix: sparse.csr_matrix, gene_index: dict[str, int], markers: tuple[str, ...]
) -> np.ndarray:
    """Mean log-normalised expression of a marker set, per cell."""
    idx = [gene_index[m] for m in markers if m in gene_index]
    if not idx:
        return np.zeros(matrix.shape[1])
    return np.asarray(matrix[idx, :].sum(axis=0)).ravel() / len(idx)


def assign_cell_types(
    matrix: sparse.csr_matrix,
    gene_index: dict[str, int],
    min_score: float = 0.05,
) -> np.ndarray:
    """Label each cell with its marker-module argmax, or ``unassigned``."""
    names = list(CELL_TYPE_MARKERS)
    scores = np.vstack(
        [module_scores(matrix, gene_index, CELL_TYPE_MARKERS[name]) for name in names]
    )
    best = scores.argmax(axis=0)
    best_score = scores.max(axis=0)
    labels = np.array([names[i] for i in best], dtype=object)
    labels[best_score < min_score] = "unassigned"
    return labels


# =============================================================================
# copy-number proxy
# =============================================================================
def diagnostic_genes(
    positions: dict[str, tuple[str, int, int]], gene_index: dict[str, int], budget: int
) -> list[str]:
    """Genes spread across the chromosomes, for the copy-number proxy.

    Taking every k-th gene per chromosome keeps the set unbiased: taking the
    first N alphabetically would concentrate it on a few chromosomes.
    """
    by_chromosome: dict[str, list[tuple[int, str]]] = {}
    for gene, (chromosome, start, _) in positions.items():
        if chromosome not in CNV_CHROMOSOMES or gene not in gene_index:
            continue
        by_chromosome.setdefault(chromosome, []).append((start, gene))
    for entries in by_chromosome.values():
        entries.sort()

    chromosomes = sorted(by_chromosome, key=lambda c: (len(c), c))
    per_chromosome = max(1, budget // max(len(chromosomes), 1))
    chosen: list[str] = []
    for chromosome in chromosomes:
        entries = by_chromosome[chromosome]
        if not entries:
            continue
        step = max(1, len(entries) // per_chromosome)
        chosen.extend(gene for _, gene in entries[::step][:per_chromosome])
    return chosen[:budget]


def cnv_diversity(
    matrix: sparse.csr_matrix,
    gene_index: dict[str, int],
    positions: dict[str, tuple[str, int, int]],
    genes: list[str],
    neighbourhood: int = CNV_NEIGHBOURHOOD,
) -> np.ndarray:
    """Per-cell dispersion of the positionally smoothed expression.

    A simplified copy-number proxy: the expression of a gene is replaced by
    the mean of its positional neighbours on the same chromosome, which
    cancels gene-specific expression and leaves the chromosomal signal. The
    dispersion of that signal across genes is what separates malignant from
    non-malignant cells — the same idea the paper used to call cancer cells.
    """
    by_chromosome: dict[str, list[tuple[int, str]]] = {}
    for gene in genes:
        chromosome, start, _ = positions[gene]
        by_chromosome.setdefault(chromosome, []).append((start, gene))
    for entries in by_chromosome.values():
        entries.sort()

    rows: list[int] = []
    columns: list[int] = []
    weights: list[float] = []
    for row, gene in enumerate(genes):
        chromosome, start, _ = positions[gene]
        entries = by_chromosome[chromosome]
        centre = next(i for i, (_, g) in enumerate(entries) if g == gene)
        low = max(0, centre - neighbourhood)
        high = min(len(entries), centre + neighbourhood + 1)
        neighbours = [g for _, g in entries[low:high] if g != gene]
        if len(neighbours) < 10:
            continue
        weight = 1.0 / len(neighbours)
        for neighbour in neighbours:
            if neighbour in gene_index:
                rows.append(row)
                columns.append(gene_index[neighbour])
                weights.append(weight)
    if not rows:
        return np.zeros(matrix.shape[1])

    smoothing = sparse.csr_matrix(
        (weights, (rows, columns)), shape=(len(genes), matrix.shape[0])
    )
    smoothed = np.asarray((smoothing @ matrix).todense())
    return smoothed.var(axis=0)


# =============================================================================
# statistics
# =============================================================================
def benjamini_hochberg(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values."""
    if not pvalues:
        return []
    order = np.argsort(pvalues)
    adjusted = np.empty(len(pvalues))
    m = len(pvalues)
    running = 1.0
    for rank in range(m - 1, -1, -1):
        index = order[rank]
        running = min(running, pvalues[index] * m / (rank + 1))
        adjusted[index] = min(1.0, running)
    return [float(v) for v in adjusted]


def state_masks(
    definition: str,
    labels: np.ndarray,
    yap1_counts: np.ndarray,
    yap1_expression: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """(YAP1-positive, YAP1-negative) masks among malignant cells."""
    malignant = labels == "malignant"
    if definition == "detected":
        positive = malignant & (yap1_counts >= 1)
    elif definition == "two_transcripts":
        positive = malignant & (yap1_counts >= 2)
    elif definition == "top_decile":
        threshold = (
            float(np.quantile(yap1_expression[malignant], 0.9)) if malignant.any() else 0.0
        )
        positive = malignant & (yap1_expression >= threshold)
    else:
        raise ValueError(f"unknown state definition: {definition}")
    negative = malignant & ~positive
    return positive, negative


def channel_statistics(
    values: np.ndarray, positive: np.ndarray, negative: np.ndarray, immune: np.ndarray
) -> dict:
    """The state-versus-tumour and state-versus-immune contrast for one gene."""
    pos = values[positive]
    neg = values[negative]
    imm = values[immune]
    if len(pos) == 0 or len(neg) == 0:
        return {"status": "empty_group"}
    stat = mannwhitneyu(pos, neg, alternative="two-sided")
    det_pos = float((pos > 0).mean())
    det_neg = float((neg > 0).mean())
    det_imm = float((imm > 0).mean()) if len(imm) else float("nan")
    try:
        odds, fisher_p = fisher_exact(
            [
                [int((pos > 0).sum()), int((pos <= 0).sum())],
                [int((neg > 0).sum()), int((neg <= 0).sum())],
            ]
        )
    except ValueError:
        odds, fisher_p = float("nan"), float("nan")
    # The mean of log-normalised values is not a fold change: the fold that
    # can be compared with a simulator's fold assumption is the ratio of the
    # means in linear (counts per 10,000) space, which is what expm1 undoes.
    linear_pos = np.expm1(pos)
    linear_neg = np.expm1(neg)
    linear_imm = np.expm1(imm) if len(imm) else np.array([])
    return {
        "status": "ok",
        "mean_yap1_positive": float(pos.mean()),
        "mean_yap1_negative": float(neg.mean()),
        "mean_immune": float(imm.mean()) if len(imm) else None,
        "linear_mean_yap1_positive": float(linear_pos.mean()),
        "linear_mean_yap1_negative": float(linear_neg.mean()),
        "linear_mean_immune": float(linear_imm.mean()) if len(imm) else None,
        "linear_fold_vs_yap1negative": (
            float(linear_pos.mean() / linear_neg.mean()) if linear_neg.mean() > 0 else None
        ),
        "linear_fold_vs_immune": (
            float(linear_pos.mean() / linear_imm.mean())
            if len(imm) and linear_imm.mean() > 0
            else None
        ),
        "detection_yap1_positive": det_pos,
        "detection_yap1_negative": det_neg,
        "detection_immune": det_imm,
        "detection_ratio_vs_yap1negative": (det_pos / det_neg if det_neg > 0 else None),
        "fold_mean_vs_yap1negative": (
            float(pos.mean() / neg.mean()) if neg.mean() > 0 else None
        ),
        "fold_mean_vs_immune": (
            float(pos.mean() / imm.mean()) if len(imm) and imm.mean() > 0 else None
        ),
        "mannwhitney_p": float(stat.pvalue),
        "fisher_p_detection": float(fisher_p),
        "odds_ratio_detection": float(odds),
        "n_yap1_positive": int(len(pos)),
        "n_yap1_negative": int(len(neg)),
        "n_immune": int(len(imm)),
    }


# =============================================================================
# main
# =============================================================================
def _definition_entry(
    definition: str,
    description: str,
    labels: np.ndarray,
    yap1_counts: np.ndarray,
    yap1_expression: np.ndarray,
    values: dict[str, np.ndarray],
    immune: np.ndarray,
) -> dict:
    """The state-validation and channel analysis for one state definition."""
    positive, negative = state_masks(definition, labels, yap1_counts, yap1_expression)
    validation: dict[str, dict] = {}
    for gene in STATE_VALIDATION_UP + STATE_VALIDATION_DOWN:
        series = values.get(gene)
        if series is None:
            continue
        pos = series[positive]
        neg = series[negative]
        expected = "up" if gene in STATE_VALIDATION_UP else "down"
        observed = (
            pos.mean() > neg.mean() if expected == "up" else pos.mean() < neg.mean()
        )
        validation[gene] = {
            "expected_direction": expected,
            "mean_yap1_positive": float(pos.mean()),
            "mean_yap1_negative": float(neg.mean()),
            "direction_as_reported": bool(observed),
            "detection_yap1_positive": float((pos > 0).mean()),
            "detection_yap1_negative": float((neg > 0).mean()),
        }
    rows: list[dict] = []
    pvalues: list[float] = []
    for gene in CHANNELS:
        series = values.get(gene)
        if series is None:
            rows.append({"gene": gene, "status": "not_detected_in_any_sample"})
            continue
        stats = channel_statistics(series, positive, negative, immune)
        rows.append({"gene": gene, **stats})
        if stats.get("status") == "ok":
            pvalues.append(stats["mannwhitney_p"])
    adjusted = benjamini_hochberg(pvalues)
    for row, q in zip(rows, adjusted, strict=False):
        if row.get("status") == "ok":
            row["mannwhitney_p_fdr"] = q
    return {
        "definition": definition,
        "description": description,
        "n_yap1_positive": int(positive.sum()),
        "n_yap1_negative": int(negative.sum()),
        "state_validation": validation,
        "state_validation_passed": sum(
            1 for v in validation.values() if v["direction_as_reported"]
        ),
        "state_validation_total": len(validation),
        "channels": rows,
    }


def _leave_one_out(
    values: dict[str, np.ndarray],
    positive: np.ndarray,
    negative: np.ndarray,
    immune: np.ndarray,
    sample_of: np.ndarray,
    accessions: list[str],
) -> dict[str, dict]:
    """The detection ratio with each library removed in turn."""
    loso: dict[str, dict] = {}
    for gene in CHANNELS:
        series = values.get(gene)
        if series is None:
            continue
        ratios: list[float | None] = []
        pvalues: list[float | None] = []
        for accession in accessions:
            keep = sample_of != accession
            stats = channel_statistics(
                series, keep & positive, keep & negative, keep & immune
            )
            ratios.append(stats.get("detection_ratio_vs_yap1negative"))
            pvalues.append(stats.get("mannwhitney_p"))
        usable = [r for r in ratios if r is not None]
        loso[gene] = {
            "detection_ratio_leaving_one_sample_out": {
                accession: ratio
                for accession, ratio in zip(accessions, ratios, strict=True)
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
    return loso


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datadir", default="data/gse299684")
    parser.add_argument("--outdir", default="results/gse299684")
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
        accession = parts[0]
        prefix = parts[1] if len(parts) > 1 else accession
        title = parts[2] if len(parts) > 2 else prefix
        tissue = parts[3] if len(parts) > 3 else ""
        mismatch = len(parts) > 4 and parts[4].strip().lower() == "yes"
        manifest.append((accession, prefix, title, tissue, mismatch))
    if args.samples:
        wanted = {s.strip() for s in args.samples.split(",")}
        manifest = [m for m in manifest if m[0] in wanted]

    positions = fetch_gene_positions(Path(args.gene_positions))

    tracked = CHANNELS + CONTROL_GENES + STATE_VALIDATION_UP + STATE_VALIDATION_DOWN
    pooled: dict[str, list[np.ndarray]] = {
        "labels": [],
        "yap1_counts": [],
        "yap1_expression": [],
        "diversity": [],
        "sample": [],
        "detected_genes": [],
        "ptprc": [],
        "cnv_pass": [],
    }
    for gene in tracked:
        pooled[gene] = []

    per_sample: list[dict] = []
    for accession, prefix, title, tissue, mismatch in manifest:
        gene_names, raw = read_sample(datadir, accession, prefix)
        gene_index = {g: i for i, g in enumerate(gene_names)}
        keep = qc_filter(raw, gene_names)
        if len(keep) == 0:
            print(f"{accession}: no cells passed QC", flush=True)
            continue
        raw = raw[:, keep]
        matrix = normalise(raw)

        labels = assign_cell_types(matrix, gene_index)
        genes = diagnostic_genes(positions, gene_index, CNV_DIAGNOSTIC_GENES)
        diversity = cnv_diversity(matrix, gene_index, positions, genes)
        yap1_counts = raw_counts(raw, gene_index, YAP1_GENE)
        yap1_expression = gene_values(matrix, gene_index, YAP1_GENE)
        detected_genes = np.asarray((raw > 0).sum(axis=0)).ravel()
        ptprc_counts = raw_counts(raw, gene_index, "PTPRC")
        # A malignant call that looks non-malignant by the copy-number proxy
        # is the kind of cell the marker module gets wrong.
        reference = np.isin(
            labels, ["t_nk", "myeloid", "b_plasma", "endothelial", "fibroblast"]
        )
        if reference.any():
            threshold = float(np.quantile(diversity[reference], 0.9))
        else:
            threshold = 0.0
        cnv_pass = diversity >= threshold

        pooled["labels"].append(labels)
        pooled["yap1_counts"].append(yap1_counts)
        pooled["yap1_expression"].append(yap1_expression)
        pooled["diversity"].append(diversity)
        pooled["sample"].append(np.full(matrix.shape[1], accession, dtype=object))
        pooled["detected_genes"].append(detected_genes)
        pooled["ptprc"].append(ptprc_counts)
        pooled["cnv_pass"].append(cnv_pass)
        for gene in tracked:
            pooled[gene].append(gene_values(matrix, gene_index, gene))

        immune_mask = np.isin(labels, ["t_nk", "myeloid", "b_plasma"])
        per_sample.append(
            {
                "accession": accession,
                "file_prefix": prefix,
                "geo_title": title,
                "filename_mismatch": bool(mismatch),
                "tissue": tissue,
                "n_cells_raw": int(raw.shape[1]),
                "n_cells_qc": int(matrix.shape[1]),
                "n_features": int(len(gene_names)),
                "cell_type_counts": {
                    label: int((labels == label).sum())
                    for label in sorted(set(labels.tolist()))
                },
                "n_malignant": int((labels == "malignant").sum()),
                "n_yap1_positive_malignant": int(
                    ((labels == "malignant") & (yap1_counts >= 1)).sum()
                ),
                "median_cnv_diversity_malignant": (
                    float(np.median(diversity[labels == "malignant"]))
                    if (labels == "malignant").any()
                    else None
                ),
                "median_cnv_diversity_immune": (
                    float(np.median(diversity[immune_mask])) if immune_mask.any() else None
                ),
            }
        )
        print(
            f"{accession} ({tissue}): {matrix.shape[1]} cells, "
            f"malignant={int((labels == 'malignant').sum())}, "
            f"YAP1+={int(((labels == 'malignant') & (yap1_counts >= 1)).sum())}",
            flush=True,
        )

    if not pooled["labels"]:
        print("no samples could be read", file=sys.stderr)
        return 1

    labels = np.concatenate(pooled["labels"])
    yap1_counts = np.concatenate(pooled["yap1_counts"])
    yap1_expression = np.concatenate(pooled["yap1_expression"])
    diversity = np.concatenate(pooled["diversity"])
    sample_of = np.concatenate(pooled["sample"])
    detected_genes = np.concatenate(pooled["detected_genes"])
    ptprc_counts = np.concatenate(pooled["ptprc"])
    cnv_pass = np.concatenate(pooled["cnv_pass"])
    values = {
        gene: np.concatenate(parts)
        for gene, parts in pooled.items()
        if gene
        not in (
            "labels",
            "yap1_counts",
            "yap1_expression",
            "diversity",
            "sample",
            "detected_genes",
            "ptprc",
            "cnv_pass",
        )
    }
    immune = np.isin(labels, ["t_nk", "myeloid", "b_plasma"])

    tissue_of = {record["accession"]: record["tissue"] for record in per_sample}

    # --- the sweep over state definitions ---
    sweep: list[dict] = []
    for definition, description in STATE_DEFINITIONS:
        sweep.append(
            _definition_entry(
                definition,
                description,
                labels,
                yap1_counts,
                yap1_expression,
                values,
                immune,
            )
        )

    # --- per-sample and per-tissue consistency, at the primary definition ---
    positive, negative = state_masks(PRIMARY_DEFINITION, labels, yap1_counts, yap1_expression)
    per_sample_channels: list[dict] = []
    for accession in sorted(set(sample_of.tolist())):
        in_sample = sample_of == accession
        row: dict = {
            "accession": accession,
            "tissue": tissue_of.get(accession, ""),
            "n_yap1_positive": int((in_sample & positive).sum()),
            "n_yap1_negative": int((in_sample & negative).sum()),
            "channels": {},
        }
        for gene in CHANNELS:
            series = values.get(gene)
            if series is None:
                continue
            stats = channel_statistics(series, in_sample & positive, in_sample & negative, in_sample & immune)
            row["channels"][gene] = {
                "detection_yap1_positive": stats.get("detection_yap1_positive"),
                "detection_yap1_negative": stats.get("detection_yap1_negative"),
                "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
                "mannwhitney_p": stats.get("mannwhitney_p"),
            }
        per_sample_channels.append(row)

    per_tissue: dict[str, dict] = {}
    for accession, tissue in tissue_of.items():
        entry = per_tissue.setdefault(
            tissue,
            {
                "tissue": tissue,
                "samples": [],
                "n_yap1_positive": 0,
                "n_yap1_negative": 0,
                "channels": {},
            },
        )
        entry["samples"].append(accession)
        entry["n_yap1_positive"] += int(((sample_of == accession) & positive).sum())
        entry["n_yap1_negative"] += int(((sample_of == accession) & negative).sum())
    for entry in per_tissue.values():
        mask = np.isin(sample_of, entry["samples"])
        for gene in CHANNELS:
            series = values.get(gene)
            if series is None:
                continue
            stats = channel_statistics(series, mask & positive, mask & negative, mask & immune)
            entry["channels"][gene] = {
                "detection_yap1_positive": stats.get("detection_yap1_positive"),
                "detection_yap1_negative": stats.get("detection_yap1_negative"),
                "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
                "mannwhitney_p": stats.get("mannwhitney_p"),
            }

    # --- leave-one-sample-out: is the pooled effect carried by one library? ---
    accessions = sorted(set(sample_of.tolist()))
    positive, negative = state_masks(
        PRIMARY_DEFINITION, labels, yap1_counts, yap1_expression
    )
    loso = _leave_one_out(values, positive, negative, immune, sample_of, accessions)

    # --- per-sample sign counts at the primary definition ---
    per_sample_signs: dict[str, dict] = {}
    for gene in CHANNELS:
        above = 0
        below = 0
        for row in per_sample_channels:
            stats = row["channels"].get(gene) or {}
            ratio = stats.get("detection_ratio")
            if ratio is None:
                continue
            if ratio > 1:
                above += 1
            elif ratio < 1:
                below += 1
        per_sample_signs[gene] = {
            "samples_with_ratio_above_one": above,
            "samples_with_ratio_below_one": below,
        }

    # --- cell-calling sensitivity -------------------------------------------
    # The malignant call decides which cells the contrast is made on, so the
    # conclusion is recomputed under three stricter calls. The published
    # numbers stay as they are: this shows the conclusion does not depend on
    # the call, rather than moving the result.
    malignant_base = labels == "malignant"
    cell_call_variants: list[dict] = []
    for variant_name, variant_description, keep in (
        (
            "primary",
            "marker module only (the published call)",
            malignant_base,
        ),
        (
            "cnv_tightened",
            "marker module, minus the malignant calls whose copy-number proxy "
            "looks non-malignant",
            malignant_base & cnv_pass,
        ),
        (
            "ptprc_filtered",
            "marker module, minus the malignant calls that express the "
            "pan-immune gene PTPRC",
            malignant_base & (ptprc_counts == 0),
        ),
        (
            "cnv_and_ptprc",
            "both filters at once",
            malignant_base & cnv_pass & (ptprc_counts == 0),
        ),
    ):
        variant_labels = labels.copy()
        variant_labels[malignant_base & ~keep] = "unassigned"
        entry = _definition_entry(
            PRIMARY_DEFINITION,
            variant_description,
            variant_labels,
            yap1_counts,
            yap1_expression,
            values,
            immune,
        )
        variant_positive, variant_negative = state_masks(
            PRIMARY_DEFINITION, variant_labels, yap1_counts, yap1_expression
        )
        variant_loso = _leave_one_out(
            values, variant_positive, variant_negative, immune, sample_of, accessions
        )
        sites: dict[str, dict] = {}
        for accession, tissue in tissue_of.items():
            in_sample = sample_of == accession
            entry_site = sites.setdefault(
                tissue,
                {
                    "tissue": tissue,
                    "samples": [],
                    "n_yap1_positive": 0,
                    "n_yap1_negative": 0,
                    "channels": {},
                },
            )
            entry_site["samples"].append(accession)
            entry_site["n_yap1_positive"] += int(
                (in_sample & variant_positive).sum()
            )
            entry_site["n_yap1_negative"] += int(
                (in_sample & variant_negative).sum()
            )
        for site_entry in sites.values():
            mask = np.isin(sample_of, site_entry["samples"])
            for gene in ("KCNN4", "PIEZO1"):
                series = values.get(gene)
                if series is None:
                    continue
                stats = channel_statistics(
                    series,
                    mask & variant_positive,
                    mask & variant_negative,
                    mask & immune,
                )
                site_entry["channels"][gene] = {
                    "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
                    "detection_yap1_positive": stats.get("detection_yap1_positive"),
                    "detection_yap1_negative": stats.get("detection_yap1_negative"),
                }
        cell_call_variants.append(
            {
                "variant": variant_name,
                "description": variant_description,
                "n_malignant_kept": int(keep.sum()),
                "n_malignant_dropped": int((malignant_base & ~keep).sum()),
                "state_validation_passed": entry["state_validation_passed"],
                "state_validation_total": entry["state_validation_total"],
                "channels": entry["channels"],
                "leave_one_sample_out": variant_loso,
                "per_site": list(sites.values()),
            }
        )

    # The copy-number proxy separates malignant from non-malignant cells well
    # enough to call them, but it does not reproduce the paper's finer
    # copy-number-diversity comparison between YAP1(+) and YAP1(-) cells.
    cnv_by_state: dict[str, object] = {
        "note": (
            "The proxy is the dispersion of a coarsely positionally smoothed "
            "expression signal. It separates malignant from non-malignant "
            "cells well enough to filter the call, but it does not reproduce "
            "the paper's copy-number-diversity comparison between YAP1(+) and "
            "YAP1(-) cells, which is a finer metric than this proxy computes."
        ),
        "per_sample": [],
    }
    for accession in accessions:
        in_sample = sample_of == accession
        pos = in_sample & (labels == "malignant") & (yap1_counts >= 1)
        neg = in_sample & (labels == "malignant") & (yap1_counts == 0)
        if pos.sum() < 5 or neg.sum() < 5:
            continue
        cnv_by_state["per_sample"].append(
            {
                "accession": accession,
                "median_diversity_yap1_positive": float(np.median(diversity[pos])),
                "median_diversity_yap1_negative": float(np.median(diversity[neg])),
                "n_yap1_positive": int(pos.sum()),
                "n_yap1_negative": int(neg.sum()),
                "yap1_higher": bool(
                    np.median(diversity[pos]) > np.median(diversity[neg])
                ),
            }
        )

    control_rows = []
    for gene in CONTROL_GENES:
        series = values.get(gene)
        if series is None:
            continue
        control_rows.append({"gene": gene, **channel_statistics(series, positive, negative, immune)})

    payload = {
        "audit": {
            "id": "gse299684-state-expression-2026-11",
            "generated_by": "scripts/gse299684_state_expression.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "GSE299684",
            "paper": "PMID 42019833 (Stewart et al., J Thorac Oncol 2026)",
            "state_definition": (
                "YAP1-based, with the call validated against the paper's "
                "surface-target signature (CD276, TACSTD2, ERBB2 up; DLL3, SEZ6, "
                "CEACAM5 down), an axis independent of the ion channels under test"
            ),
            "state_definitions_swept": [d for d, _ in STATE_DEFINITIONS],
            "primary_definition": PRIMARY_DEFINITION,
            "channels": list(CHANNELS),
            "controls": list(CONTROL_GENES),
            "qc": {
                "min_genes_per_cell": 200,
                "min_counts_per_cell": 500,
                "max_mito_fraction": 0.20,
                "normalisation": "counts per 10,000 per cell, then log1p",
            },
        },
        "cells": {
            "n_qc_passed": int(len(labels)),
            "cell_type_counts": {
                label: int((labels == label).sum())
                for label in sorted(set(labels.tolist()))
            },
            "median_cnv_diversity": {
                label: (
                    float(np.median(diversity[labels == label]))
                    if (labels == label).any()
                    else None
                )
                for label in sorted(set(labels.tolist()))
            },
        },
        "per_sample": per_sample,
        "complexity_control": {
            "median_genes_detected_yap1_positive": (
                float(np.median(detected_genes[positive])) if positive.any() else None
            ),
            "median_genes_detected_yap1_negative": (
                float(np.median(detected_genes[negative])) if negative.any() else None
            ),
            "median_genes_detected_immune": (
                float(np.median(detected_genes[immune])) if immune.any() else None
            ),
            "note": (
                "A state that is simply harder to sequence would show fewer "
                "detected genes everywhere; the housekeeping controls in "
                "'controls' are the direct check"
            ),
        },
        "leave_one_sample_out": loso,
        "cell_call_sensitivity": cell_call_variants,
        "cnv_proxy_by_state": cnv_by_state,
        "per_sample_sign_counts": per_sample_signs,
        "state_definition_sweep": sweep,
        "per_sample_channels": per_sample_channels,
        "per_tissue_channels": list(per_tissue.values()),
        "controls": control_rows,
    }

    (outdir / "state_expression.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "gene\tmean_yap1_pos\tmean_yap1_neg\tmean_immune\tdet_yap1_pos\t"
        "det_yap1_neg\tdet_immune\tdet_ratio_vs_neg\tfold_mean_vs_neg\t"
        "fold_mean_vs_immune\tlinear_fold_vs_neg\tlinear_fold_vs_immune\t"
        "p_mwu\tp_fisher\tp_fdr"
    ]
    primary = next(s for s in sweep if s["definition"] == PRIMARY_DEFINITION)
    for row in primary["channels"]:
        if row.get("status") != "ok":
            lines.append(f"{row['gene']}\tnot_detected")
            continue
        lines.append(
            "\t".join(
                [
                    row["gene"],
                    f"{row['mean_yap1_positive']:.5f}",
                    f"{row['mean_yap1_negative']:.5f}",
                    f"{row['mean_immune']:.5f}" if row["mean_immune"] is not None else "",
                    f"{row['detection_yap1_positive']:.4f}",
                    f"{row['detection_yap1_negative']:.4f}",
                    f"{row['detection_immune']:.4f}",
                    f"{row['detection_ratio_vs_yap1negative']:.4f}"
                    if row["detection_ratio_vs_yap1negative"] is not None
                    else "",
                    f"{row['fold_mean_vs_yap1negative']:.4f}"
                    if row["fold_mean_vs_yap1negative"] is not None
                    else "",
                    f"{row['fold_mean_vs_immune']:.4f}"
                    if row["fold_mean_vs_immune"] is not None
                    else "",
                    f"{row['linear_fold_vs_yap1negative']:.4f}"
                    if row.get("linear_fold_vs_yap1negative") is not None
                    else "",
                    f"{row['linear_fold_vs_immune']:.4f}"
                    if row.get("linear_fold_vs_immune") is not None
                    else "",
                    f"{row['mannwhitney_p']:.3e}",
                    f"{row['fisher_p_detection']:.3e}",
                    f"{row['mannwhitney_p_fdr']:.3e}",
                ]
            )
        )
    (outdir / "state_expression.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print()
    print(f"cells passing QC: {len(labels)}")
    print("cell types:", payload["cells"]["cell_type_counts"])
    print()
    for entry in sweep:
        print(
            f"[{entry['definition']}] YAP1+={entry['n_yap1_positive']} "
            f"YAP1-={entry['n_yap1_negative']} | state signature reproduces "
            f"{entry['state_validation_passed']}/{entry['state_validation_total']}"
        )
        for gene, record in entry["state_validation"].items():
            if not record["direction_as_reported"]:
                print(
                    f"    {gene}: expected {record['expected_direction']}, "
                    f"observed YAP1+ {record['mean_yap1_positive']:.4f} vs "
                    f"YAP1- {record['mean_yap1_negative']:.4f}"
                )
        for row in entry["channels"]:
            if row.get("status") != "ok":
                print(f"    {row['gene']:<10} not detected in any sample")
                continue
            print(
                f"    {row['gene']:<10} det: pos={row['detection_yap1_positive']:.3f} "
                f"neg={row['detection_yap1_negative']:.3f} "
                f"imm={row['detection_immune']:.3f} "
                f"| det ratio vs neg={row['detection_ratio_vs_yap1negative']} "
                f"| fold vs immune={row['fold_mean_vs_immune']} "
                f"| p={row['mannwhitney_p']:.3g} q={row['mannwhitney_p_fdr']:.3g}"
            )
        print()
    print("cell-calling sensitivity (KCNN4 / PIEZO1 detection ratio vs other tumour):")
    for variant in cell_call_variants:
        genes = {c["gene"]: c for c in variant["channels"] if c.get("status") == "ok"}
        loso_variant = variant["leave_one_sample_out"]
        lung = [
            s
            for s in variant["per_site"]
            if "lung" in s["tissue"] and s["n_yap1_positive"] > 0
        ]
        lung_kcnn4 = [
            s["channels"]["KCNN4"]["detection_ratio"]
            for s in lung
            if s["channels"].get("KCNN4", {}).get("detection_ratio") is not None
        ]
        lung_piezo1 = [
            s["channels"]["PIEZO1"]["detection_ratio"]
            for s in lung
            if s["channels"].get("PIEZO1", {}).get("detection_ratio") is not None
        ]
        print(
            f"  {variant['variant']:<16} kept={variant['n_malignant_kept']:<6} "
            f"dropped={variant['n_malignant_dropped']:<6} "
            f"signature={variant['state_validation_passed']}/{variant['state_validation_total']} "
            f"KCNN4={genes['KCNN4']['detection_ratio_vs_yap1negative']:.3f} "
            f"PIEZO1={genes['PIEZO1']['detection_ratio_vs_yap1negative']:.3f} "
            f"| lung KCNN4 max={max(lung_kcnn4) if lung_kcnn4 else None} "
            f"PIEZO1 min={min(lung_piezo1) if lung_piezo1 else None} "
            f"| loso KCNN4 sign stable={loso_variant['KCNN4']['sign_is_stable']} "
            f"PIEZO1 sign stable={loso_variant['PIEZO1']['sign_is_stable']}"
        )
    print()
    print("leave-one-sample-out (detection ratio, state vs other tumour):")
    for gene, record in loso.items():
        print(
            f"  {gene:<10} min={record['min_ratio']} max={record['max_ratio']} "
            f"| samples with ratio>1: {record['n_samples_with_ratio_above_one']} "
            f"below: {record['n_samples_with_ratio_below_one']} "
            f"| sign stable: {record['sign_is_stable']} "
            f"| max p: {record['max_p_leaving_one_out']}"
        )
    print()
    print(f"wrote {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
