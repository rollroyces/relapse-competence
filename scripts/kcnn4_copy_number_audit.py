#!/usr/bin/env python3
"""Is KCNN4's elevation in the relapse-competent state a copy-number effect?

The driver-versus-passenger audit found that KCNN4's expression co-allocates
with the state's transcriptional programme inside state cells, and left the
direction of causation open. One of the two ways that could go is
copy-number: if the state carries an amplification that includes KCNN4, the
channel's elevation is a consequence of the genome rather than a consequence
of the programme, and no amount of transcriptional reasoning would separate
them.

**Why the obvious statistic is the wrong one.** A gene that is
transcriptionally upregulated has its own expression raised relative to its
positional neighbours, exactly as an amplified gene does. So "KCNN4 is high
relative to its neighbours" cannot tell the two apart, and this audit does not
claim it can. What can be told apart is a *locus-specific* copy-number
event: a region of the genome that is denser in the state cells than the
genome as a whole. That is the statistic below, and it is the standard one a
copy-number caller uses -- the local density at a locus, as a log-ratio
against the cell's genome-wide baseline.

**What is computed.** For each library, and for the target locus plus a
deterministic sample of control loci spread across the genome:

- the *regional signal* at the locus: the mean expression of the fifty
  positional neighbours on either side, taken from all positioned genes so
  that the window is dense and local;
- the *log-ratio* of that signal against the cell's genome-wide baseline,
  the median over the control loci;
- the *focal statistic*: the locus's own expression relative to its
  neighbourhood, which says whether the elevation is regional or
  gene-specific, and which -- as above -- cannot separate amplification from
  regulation.

**The test.** If the state's KCNN4 region is no more copy-number-elevated
than the rest of the genome, there is no KCNN4-specific copy-number event to
explain the elevation, and the amplification explanation is not supported at
the locus level. The test is calibrated by permuting the state/tumour labels
within each library, and the control loci provide the null distribution the
target is ranked against.

    python scripts/kcnn4_copy_number_audit.py
    python scripts/kcnn4_copy_number_audit.py --permutations 200
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]

#: The deposits, and the transcriptional programme each defines. The programme
#: is not used in the statistic here; it is carried so that the same genes can
#: be reported alongside.
DATASETS: dict[str, dict] = {
    "GSE299684": {
        "datadir": "data/gse299684",
        "module": "gse299684_state_expression",
        "state_gene": "YAP1",
        "cohort": "SCLC",
    },
    "GSE353299": {
        "datadir": "data/gse353299",
        "module": "gse353299_state_expression",
        "state_gene": "KRT17",
        "cohort": "NSCLC",
    },
}

#: The locus under test, and the genes reported alongside it.
TARGET = "KCNN4"
COMPARATORS = ("PIEZO1", "KRT14", "KRT15", "CD276", "ACTB")

#: How many positional neighbours on each side of the locus.
WINDOW = 50

#: A small constant so that a zero signal does not make a ratio infinite.
PSEUDOCOUNT = 0.05


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _core(module):
    return getattr(module, "core", module)


def _manifest(datadir: Path) -> list[tuple[str, str]]:
    manifest_path = datadir / "manifest.tsv"
    if not manifest_path.exists():
        return []
    rows = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if parts and parts[0]:
            rows.append((parts[0], parts[1] if len(parts) > 1 else parts[0]))
    return rows


def _chromosome_genes(
    positions: dict[str, tuple[str, int, int]], gene_index: dict[str, int]
) -> dict[str, list[tuple[int, str]]]:
    """Every positioned gene, sorted by position, per chromosome."""
    by_chromosome: dict[str, list[tuple[int, str]]] = {}
    for gene, (chromosome, start, _) in positions.items():
        if gene not in gene_index:
            continue
        by_chromosome.setdefault(chromosome, []).append((start, gene))
    for entries in by_chromosome.values():
        entries.sort()
    return by_chromosome


def _neighbourhood(
    entries: list[tuple[int, str]], gene: str, window: int
) -> list[str]:
    """The positional neighbours of a gene, excluding the gene itself."""
    centre = next(i for i, (_, g) in enumerate(entries) if g == gene)
    low = max(0, centre - window)
    high = min(len(entries), centre + window + 1)
    return [g for _, g in entries[low:high] if g != gene]


def _local_signal(
    matrix, gene_index: dict[str, int], neighbours: list[str]
) -> np.ndarray:
    """Per-cell mean linear expression of a locus's neighbourhood.

    The mean is taken in linear space, over counts per 10,000, which is the
    same convention the repository's fold changes use: a ratio of arithmetic
    means of linear values. Taking the mean in log space instead would give
    a geometric mean, which is dominated by the low-expression neighbours and
    is not comparable with the published folds.
    """
    if not neighbours:
        return np.zeros(matrix.shape[1])
    total = np.zeros(matrix.shape[1])
    for gene in neighbours:
        total += _linear(
            np.asarray(matrix[gene_index[gene]].todense()).ravel()
        )
    return total / len(neighbours)


def _linear(values: np.ndarray) -> np.ndarray:
    """Log-normalised values back to counts per 10,000."""
    return np.expm1(values)


def _collect(dataset: str, config: dict, controls: list[str]) -> list[dict]:
    """Per library: the per-cell statistics for the target and the controls."""
    module = _load_module(config["module"])
    core = _core(module)
    datadir = REPO / config["datadir"]
    positions = core.fetch_gene_positions(REPO / "data" / "ensembl_gene_positions.tsv")
    libraries = []
    for accession, prefix in _manifest(datadir):
        gene_names, raw = core.read_sample(datadir, accession, prefix)
        gene_index = {g: i for i, g in enumerate(gene_names)}
        keep = core.qc_filter(raw, gene_names)
        if len(keep) == 0:
            continue
        raw = raw[:, keep]
        matrix = core.normalise(raw)
        labels = module.assign_cell_types(matrix, gene_index)
        state_counts = core.raw_counts(raw, gene_index, config["state_gene"])
        state_expression = core.gene_values(matrix, gene_index, config["state_gene"])
        positive, negative = module.state_masks(
            "detected", labels, state_counts, state_expression
        )
        if positive.sum() < 20 or negative.sum() < 20:
            continue
        by_chromosome = _chromosome_genes(positions, gene_index)
        wanted = [TARGET, *COMPARATORS, *controls]
        usable = []
        for gene in wanted:
            if gene not in gene_index or gene not in positions:
                continue
            chromosome = positions[gene][0]
            entries = by_chromosome.get(chromosome)
            if not entries or not any(g == gene for _, g in entries):
                continue
            neighbours = _neighbourhood(entries, gene, WINDOW)
            if len(neighbours) < 20:
                continue
            usable.append((gene, neighbours))
        if not usable:
            continue
        local = {}
        focal = {}
        for gene, neighbours in usable:
            signal = _local_signal(matrix, gene_index, neighbours)
            local[gene] = signal
            own = core.gene_values(matrix, gene_index, gene)
            denominator = _linear(signal) + PSEUDOCOUNT
            focal[gene] = np.log2((_linear(own) + PSEUDOCOUNT) / denominator)
        baseline = (
            np.median(
                np.vstack([local[gene] for gene, _ in usable if gene != TARGET]),
                axis=0,
            )
            if len(usable) > 1
            else np.zeros(matrix.shape[1])
        )
        log_ratio = {
            gene: np.log2((signal + PSEUDOCOUNT) / (baseline + PSEUDOCOUNT))
            for gene, signal in local.items()
        }
        own_linear = _linear(core.gene_values(matrix, gene_index, TARGET))
        libraries.append(
            {
                "accession": accession,
                "cohort": config["cohort"],
                "n_state": int(positive.sum()),
                "n_tumour": int(negative.sum()),
                "_state": np.flatnonzero(positive),
                "_tumour": np.flatnonzero(negative),
                "_own": own_linear,
                "_neighbourhood": local[TARGET],
                "_baseline": baseline,
                "_log_ratio": log_ratio,
                "_focal": focal,
                "_control_genes": [gene for gene, _ in usable if gene != TARGET],
            }
        )
        print(f"{accession}: {int(positive.sum())} state cells", flush=True)
    return libraries


def _fold(values: np.ndarray, state: np.ndarray, tumour: np.ndarray) -> float:
    """The ratio of means, in linear space, as the repository's folds are.

    A median would be zero for a lowly expressed gene in the tumour cells,
    because most of them do not detect it at all; the ratio of means is the
    statistic the published folds use and the one a fold can be compared
    with.
    """
    tumour_mean = float(values[tumour].mean())
    if tumour_mean <= 0:
        return float("nan")
    return float(values[state].mean() / tumour_mean)


def _delta(values: np.ndarray, state: np.ndarray, tumour: np.ndarray) -> float:
    """The difference between the state and tumour medians."""
    return float(np.median(values[state]) - np.median(values[tumour]))


def _rank_percentile(value: float, population: list[float]) -> float:
    """The percentile of a value within a population."""
    if not population:
        return float("nan")
    below = sum(1 for other in population if other < value)
    return float(below / len(population))


def _run(libraries: list[dict], permutations: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    observed = []
    for library in libraries:
        control = library["_control_genes"]
        target_delta = _delta(
            library["_log_ratio"][TARGET], library["_state"], library["_tumour"]
        )
        control_deltas = {
            gene: _delta(
                library["_log_ratio"][gene], library["_state"], library["_tumour"]
            )
            for gene in control
        }
        percentile = _rank_percentile(
            target_delta, list(control_deltas.values())
        )
        state = library["_state"]
        tumour = library["_tumour"]
        own_fold = _fold(library["_own"], state, tumour)
        neighbourhood_fold = _fold(library["_neighbourhood"], state, tumour)
        genome_fold = _fold(library["_baseline"], state, tumour)
        observed.append(
            {
                "accession": library["accession"],
                "fold_own": own_fold,
                "fold_neighbourhood": neighbourhood_fold,
                "fold_genome_baseline": genome_fold,
                "target_delta_log_ratio": target_delta,
                "control_delta_log_ratio": list(control_deltas.values()),
                "percentile_among_control_loci": percentile,
                "target_delta_focal": _delta(
                    library["_focal"][TARGET], library["_state"], library["_tumour"]
                ),
            }
        )
    # Pooled across the libraries of the dataset: the per-library fold of a
    # lowly expressed gene is extremely noisy, so the pooled ratio of means
    # is the statistic that can be compared with the published fold.
    pooled_own = np.concatenate([library["_own"] for library in libraries])
    pooled_state = np.concatenate(
        [library["_state"] for library in libraries]
    )
    offsets = []
    running = 0
    for library in libraries:
        offsets.append(running)
        running += library["_own"].shape[0]
    pooled_state = np.concatenate(
        [library["_state"] + offset for library, offset in zip(libraries, offsets, strict=False)]
    )
    pooled_tumour = np.concatenate(
        [library["_tumour"] + offset for library, offset in zip(libraries, offsets, strict=False)]
    )
    pooled = {
        "fold_own": _fold(pooled_own, pooled_state, pooled_tumour),
        "fold_neighbourhood": _fold(
            np.concatenate([library["_neighbourhood"] for library in libraries]),
            pooled_state,
            pooled_tumour,
        ),
        "fold_genome_baseline": _fold(
            np.concatenate([library["_baseline"] for library in libraries]),
            pooled_state,
            pooled_tumour,
        ),
    }

    # The permutation: the state/tumour labels are shuffled within each
    # library, so each library keeps its own cell distribution and only the
    # state association is destroyed.
    null = []
    for _ in range(permutations):
        percentiles = []
        for library in libraries:
            state = library["_state"]
            tumour = library["_tumour"]
            pool = np.concatenate([state, tumour])
            rng.shuffle(pool)
            shuffled_state = pool[: len(state)]
            shuffled_tumour = pool[len(state) :]
            target_delta = _delta(
                library["_log_ratio"][TARGET], shuffled_state, shuffled_tumour
            )
            control_deltas = [
                _delta(library["_log_ratio"][gene], shuffled_state, shuffled_tumour)
                for gene in library["_control_genes"]
            ]
            percentiles.append(
                _rank_percentile(target_delta, control_deltas)
            )
        null.append(float(np.mean(percentiles)))
    observed_mean = float(
        np.mean([entry["percentile_among_control_loci"] for entry in observed])
    )
    extreme = sum(1 for value in null if value >= observed_mean)
    # The per-library statement is the robust one. The pooled ratio of means
    # moves with the library set, because the gene's expression in tumour
    # cells is near zero in many libraries and the ratio is then dominated by
    # a few of them; the per-library comparison between the gene and its own
    # neighbourhood does not move.
    def _comparable(entry: dict) -> bool:
        """A library counts in the comparison when both folds are finite."""
        return (
            np.isfinite(entry["fold_own"])
            and np.isfinite(entry["fold_neighbourhood"])
        )

    comparable = [entry for entry in observed if _comparable(entry)]
    summary = {
        "n_libraries": len(observed),
        "n_comparable": len(comparable),
        "median_fold_own": float(np.median([e["fold_own"] for e in comparable])),
        "median_fold_neighbourhood": float(
            np.median([e["fold_neighbourhood"] for e in comparable])
        ),
        "max_fold_neighbourhood": float(
            np.max([e["fold_neighbourhood"] for e in comparable])
        ),
        "median_fold_genome_baseline": float(
            np.median([e["fold_genome_baseline"] for e in observed])
        ),
        "libraries_where_the_neighbourhood_rises_more_than_the_gene": int(
            sum(
                1
                for entry in comparable
                if entry["fold_neighbourhood"] > entry["fold_own"]
            )
        ),
    }
    return {
        "pooled": pooled,
        "summary": summary,
        "per_library": observed,
        "mean_percentile_among_control_loci": observed_mean,
        "permutation_p": float((extreme + 1) / (len(null) + 1)),
        "null_mean": float(np.mean(null)),
        "null_sd": float(np.std(null)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permutations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20261111)
    parser.add_argument("--controls", type=int, default=300)
    parser.add_argument("--outdir", default="results/kcnn4_copy_number")
    args = parser.parse_args(argv)

    outdir = REPO / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    document = {
        "audit": {
            "id": "kcnn4-copy-number-audit-2026-11",
            "generated_by": "scripts/kcnn4_copy_number_audit.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "question": (
                "Is the KCNN4 locus copy-number-elevated in the state cells, "
                "relative to the rest of the genome?"
            ),
            "limits": (
                "The proxy is positional and coarse: it reads a regional "
                "density, so it can find a broad gain that includes the "
                "locus, and it cannot find a focal amplification of the gene "
                "itself, nor separate transcriptional regulation from one."
            ),
            "window": WINDOW,
            "permutations": args.permutations,
            "seed": args.seed,
            "n_control_loci": args.controls,
        },
        "datasets": {},
    }

    rng = np.random.default_rng(args.seed)
    for dataset, config in DATASETS.items():
        if not (REPO / config["datadir"]).exists():
            print(f"{dataset}: no local copy of the deposit, skipped", flush=True)
            continue
        print(f"=== {dataset} ({config['cohort']}) ===", flush=True)
        module = _load_module(config["module"])
        core = _core(module)
        positions = core.fetch_gene_positions(
            REPO / "data" / "ensembl_gene_positions.tsv"
        )
        candidates = sorted(
            gene
            for gene in positions
            if gene not in (TARGET, *COMPARATORS)
            and positions[gene][0] not in {"MT"}
        )
        controls = [
            candidates[i]
            for i in rng.choice(
                len(candidates), size=min(args.controls, len(candidates)), replace=False
            )
        ]
        libraries = _collect(dataset, config, controls)
        if not libraries:
            continue
        document["datasets"][dataset] = {
            "cohort": config["cohort"],
            "state_gene": config["state_gene"],
            "n_libraries": len(libraries),
            "result": _run(libraries, args.permutations, args.seed),
        }

    out_path = outdir / "kcnn4_copy_number.json"
    out_path.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {out_path}")
    for dataset, payload in document["datasets"].items():
        result = payload["result"]
        print(
            f"=== {dataset} ({payload['cohort']}), {payload['n_libraries']} libraries ==="
        )
        pooled = result["pooled"]
        summary = result["summary"]
        print(
            f"  pooled: own x{pooled['fold_own']:.2f}  "
            f"neighbourhood x{pooled['fold_neighbourhood']:.2f}  "
            f"genome baseline x{pooled['fold_genome_baseline']:.2f}"
        )
        print(
            f"  per library ({summary['n_comparable']} comparable): "
            f"median own x{summary['median_fold_own']:.2f}, "
            f"median neighbourhood x{summary['median_fold_neighbourhood']:.2f} "
            f"(max x{summary['max_fold_neighbourhood']:.2f}), "
            f"median genome x{summary['median_fold_genome_baseline']:.2f}; "
            f"the neighbourhood rises more than the gene in "
            f"{summary['libraries_where_the_neighbourhood_rises_more_than_the_gene']}"
            f" of {summary['n_libraries']}"
        )
        print(
            f"  KCNN4 log-ratio change, percentile among control loci: "
            f"{result['mean_percentile_among_control_loci']:.3f} "
            f"(null {result['null_mean']:.3f} +/- {result['null_sd']:.3f}) "
            f"p={result['permutation_p']:.4g}"
        )
        for entry in result["per_library"]:
            print(
                f"    {entry['accession']}: "
                f"own x{entry['fold_own']:.2f} "
                f"neighbourhood x{entry['fold_neighbourhood']:.2f} "
                f"genome x{entry['fold_genome_baseline']:.2f} | "
                f"locus-delta={entry['target_delta_log_ratio']:+.3f} "
                f"pct={entry['percentile_among_control_loci']:.2f} "
                f"focal={entry['target_delta_focal']:+.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
