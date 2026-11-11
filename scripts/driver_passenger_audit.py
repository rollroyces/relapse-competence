#!/usr/bin/env python3
"""Is the electrical mark instructive, or a passenger of the transcriptional state?

The programme's readout rests on an assumption that has never been tested: that
an ion channel marks the relapse-competent state in a way that a screening
cohort's plasma could carry. Before a mechanistic collaborator can be asked to
test it, one question has to be settled with what is already in this
repository: **is the channel's elevation in state cells part of the
transcriptional programme that defines the state, or is it a separate axis
that the programme does not explain?**

Two measurements are made here, both from the public deposits already cached
in this repository and from nothing else.

1.  *Coupling, within state cells.* Within a library's state cells, does the
    channel's expression rise with the strength of the transcriptional
    programme, once cell depth is held constant? The test is stratified by
    depth decile and calibrated by permutation within each library, so the
    null is "the channel and the programme score are unrelated among these
    cells".

2.  *Coupling, across libraries.* Across libraries, does the channel's
    state-versus-tumour fold track the programme's own state-versus-tumour
    fold? Both are ratios of means over the same cells, so estimation noise
    attenuates both equally and cannot manufacture an association between
    them.

Neither measurement is causal, and the document that reads this artefact says
so. What the two can settle is whether the channel's mark is coupled to the
programme at all, which is the necessary condition for "it is simply the
programme", and the thing a perturbation experiment would then have to beat.

Two controls travel with every test. A gene that is *in* the programme score
is a power control: if the machinery cannot find it, it cannot find
anything. A housekeeping gene is a specificity control: if it shows the same
coupling as the channel, the coupling is an artefact of depth.

    python scripts/driver_passenger_audit.py
    python scripts/driver_passenger_audit.py --permutations 200
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[1]

#: The two deposits that carry a transcriptional axis independent of the ion
#: channels under test, and the axis each one defines.
DATASETS: dict[str, dict] = {
    "GSE299684": {
        "datadir": "data/gse299684",
        "module": "gse299684_state_expression",
        "state_gene": "YAP1",
        # The published surface-target signature the state call was validated
        # against: three genes up, three down. None is an ion channel.
        "programme_up": ("CD276", "TACSTD2", "ERBB2"),
        "programme_down": ("DLL3", "SEZ6", "CEACAM5"),
        "cohort": "SCLC",
        "power_control": "CD276",
        "negative_control": "ACTB",
    },
    "GSE353299": {
        "datadir": "data/gse353299",
        "module": "gse353299_state_expression",
        "state_gene": "KRT17",
        # The basaloid programme. KRT5 and KRT6A are deliberately left out:
        # they are also in this dataset's malignant marker module, so scoring
        # cells with them would be circular with the cell-type call.
        "programme_up": ("KRT14", "KRT15"),
        "programme_down": (),
        "cohort": "NSCLC",
        "power_control": "KRT14",
        "negative_control": "ACTB",
    },
}

#: The genes whose state-versus-tumour fold is the readout candidate, plus the
#: two controls. Taken from the candidate channels the D0 audit left standing.
TEST_GENES: tuple[str, ...] = (
    "KCNN4",
    "PIEZO1",
    "CACNA1E",
    "KCNA3",
    "TMEM150C",
    "STOML3",
    "PIEZO2",
    "CD276",
    "ACTB",
    "KRT14",
    "KRT15",
)


def _load_module(name: str):
    """Import one of the repository's state-expression scripts."""
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _core(module):
    """The shared helpers, whether they live in the module or in its core."""
    return getattr(module, "core", module)


def _manifest(datadir: Path) -> list[tuple[str, str]]:
    """(accession, file prefix) for every sample in the deposit."""
    manifest_path = datadir / "manifest.tsv"
    if not manifest_path.exists():
        return []
    rows = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if parts and parts[0]:
            rows.append((parts[0], parts[1] if len(parts) > 1 else parts[0]))
    return rows


def _linear_means(core, matrix, gene_index, genes, mask) -> dict[str, float]:
    """Mean linear (counts per 10,000) expression of each gene over a mask."""
    out: dict[str, float] = {}
    for gene in genes:
        values = core.gene_values(matrix, gene_index, gene)
        linear = np.expm1(values[mask]) if mask.any() else np.array([])
        out[gene] = float(linear.mean()) if linear.size else float("nan")
    return out


def _mantel_haenszel_z(
    depth: np.ndarray,
    score: np.ndarray,
    outcome: np.ndarray,
    n_strata: int = 10,
) -> float | None:
    """Depth-stratified z for the outcome's odds at high versus low score.

    Cells are split into depth strata, and within each stratum into the top
    and bottom tercile of the score. The statistic is the Mantel-Haenszel
    chi-square for a 2x2 table, pooled over strata, with the continuity
    correction. Depth is held constant by construction, so a signal here is
    not a sequencing-depth effect.
    """
    n = len(depth)
    if n < 60:
        return None
    # The number of depth strata has to fit the library: a fixed ten left
    # every library below three hundred state cells contributing nothing, so
    # the whole answer came from the one largest library.
    n_strata = int(np.clip(n // 30, 3, n_strata))
    edges = np.unique(np.quantile(depth, np.linspace(0, 1, n_strata + 1)))
    if len(edges) < 3:
        return None
    strata = np.digitize(depth, edges[1:-1], right=False)
    observed = 0.0
    variance = 0.0
    used = 0
    for s in range(len(edges) - 1):
        idx = np.flatnonzero(strata == s)
        if len(idx) < 20:
            continue
        sc = score[idx]
        hi_cut = np.quantile(sc, 2.0 / 3.0)
        lo_cut = np.quantile(sc, 1.0 / 3.0)
        hi = idx[sc >= hi_cut]
        lo = idx[sc <= lo_cut]
        if len(hi) < 8 or len(lo) < 8:
            continue
        a = int(outcome[hi].sum())
        b = len(hi) - a
        c = int(outcome[lo].sum())
        d = len(lo) - c
        n_i = len(hi) + len(lo)
        r1 = a + b
        r2 = c + d
        c1 = a + c
        c2 = b + d
        if min(n_i, r1, r2, c1, c2) == 0:
            continue
        observed += a - (r1 * c1 / n_i)
        variance += (r1 * r2 * c1 * c2) / (n_i * n_i * (n_i - 1))
        used += 1
    if used == 0 or variance <= 0:
        return None
    return float((abs(observed) - 0.5) / np.sqrt(variance))


def _stouffer(zs: list[float]) -> float | None:
    if not zs:
        return None
    return float(np.sum(zs) / np.sqrt(len(zs)))


def _permutation_p(observed: float, null: list[float]) -> float:
    if not null:
        return float("nan")
    extreme = sum(1 for value in null if abs(value) >= abs(observed))
    return float((extreme + 1) / (len(null) + 1))


def _spearman_permutation(
    x: list[float], y: list[float], permutations: int, rng: np.random.Generator
) -> tuple[float, float]:
    """Spearman rho with a permutation p-value that shuffles the pairing."""
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    if len(xs) < 5:
        return float("nan"), float("nan")
    rho = float(spearmanr(xs, ys).statistic)
    null = []
    shuffled = ys.copy()
    for _ in range(permutations):
        rng.shuffle(shuffled)
        null.append(float(spearmanr(xs, shuffled).statistic))
    return rho, _permutation_p(rho, null)


def _collect(dataset: str, config: dict, outdir: Path) -> dict:
    """Everything the tests need, computed once per library."""
    module = _load_module(config["module"])
    core = _core(module)
    datadir = REPO / config["datadir"]
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
        if positive.sum() < 60 or negative.sum() < 60:
            continue
        # The stratification variable has to be the one the programme score
        # and every outcome are actually built from: the score is a mean over
        # six genes' detection, so a cell that detects more genes scores
        # higher whatever its programme is. Stratifying on total counts
        # instead left the specificity control coupled, which is how this
        # was found.
        depth = np.asarray((raw > 0).sum(axis=0)).ravel().astype(float)
        # Per-cell programme score: higher means the cell carries the
        # transcriptional programme more strongly.
        up_cells = [
            core.gene_values(matrix, gene_index, g) for g in config["programme_up"]
        ]
        down_cells = [
            core.gene_values(matrix, gene_index, g) for g in config["programme_down"]
        ]
        score = np.zeros(matrix.shape[1])
        if up_cells:
            score += np.mean(np.vstack(up_cells), axis=0)
        if down_cells:
            score -= np.mean(np.vstack(down_cells), axis=0)
        state_up = _linear_means(core, matrix, gene_index, config["programme_up"], positive)
        tumour_up = _linear_means(core, matrix, gene_index, config["programme_up"], negative)
        state_down = _linear_means(
            core, matrix, gene_index, config["programme_down"], positive
        )
        tumour_down = _linear_means(
            core, matrix, gene_index, config["programme_down"], negative
        )
        strength_terms = []
        for gene in config["programme_up"]:
            if state_up[gene] > 0 and tumour_up[gene] > 0:
                strength_terms.append(np.log2(state_up[gene] / tumour_up[gene]))
        for gene in config["programme_down"]:
            if state_down[gene] > 0 and tumour_down[gene] > 0:
                strength_terms.append(np.log2(tumour_down[gene] / state_down[gene]))
        strength = float(np.mean(strength_terms)) if strength_terms else None
        folds = {}
        for gene in TEST_GENES:
            values = core.gene_values(matrix, gene_index, gene)
            stats = core.channel_statistics(
                values, positive, negative, np.zeros(len(values), dtype=bool)
            )
            folds[gene] = {
                "linear_fold": stats.get("linear_fold_vs_yap1negative"),
                "detection_ratio": stats.get("detection_ratio_vs_yap1negative"),
                "mannwhitney_p": stats.get("mannwhitney_p"),
            }
        libraries.append(
            {
                "accession": accession,
                "cohort": config["cohort"],
                "n_state": int(positive.sum()),
                "n_tumour": int(negative.sum()),
                "state_fraction": float(positive.sum() / (positive.sum() + negative.sum())),
                "programme_strength": strength,
                "folds": folds,
                "_depth": depth[positive],
                "_score": score[positive],
                "_outcomes": {
                    gene: (core.gene_values(matrix, gene_index, gene)[positive] > 0)
                    for gene in TEST_GENES
                },
            }
        )
        print(f"{accession}: {int(positive.sum())} state cells", flush=True)
    return {"dataset": dataset, "libraries": libraries}


def _run_tests(collected: dict, config: dict, permutations: int, seed: int) -> dict:
    """The within-library and across-library tests."""
    rng = np.random.default_rng(seed)
    libraries = collected["libraries"]
    results: dict[str, dict] = {}
    for gene in TEST_GENES:
        per_library = []
        for library in libraries:
            z = _mantel_haenszel_z(
                library["_depth"],
                library["_score"],
                library["_outcomes"][gene],
            )
            per_library.append({"accession": library["accession"], "z": z})
        zs = [entry["z"] for entry in per_library if entry["z"] is not None]
        observed = _stouffer(zs)
        # The global permutation: the programme score is shuffled among the
        # state cells of each library, so each library keeps its own depth and
        # outcome distribution and only the coupling is destroyed.
        null = []
        for _ in range(permutations):
            permuted = []
            for library in libraries:
                score = library["_score"].copy()
                rng.shuffle(score)
                z = _mantel_haenszel_z(
                    library["_depth"], score, library["_outcomes"][gene]
                )
                if z is not None:
                    permuted.append(z)
            value = _stouffer(permuted)
            if value is not None:
                null.append(value)
        null_mean = float(np.mean(null)) if null else float("nan")
        null_sd = float(np.std(null)) if null else float("nan")
        effect = (
            float((observed - null_mean) / null_sd)
            if observed is not None and null and null_sd > 0
            else None
        )
        results[gene] = {
            "role": (
                "power control"
                if gene == config["power_control"]
                else "specificity control"
                if gene == config["negative_control"]
                else "candidate channel"
            ),
            "within_state_cells": {
                "n_libraries": len(zs),
                "stouffer_z": observed,
                "permutation_p": (
                    _permutation_p(observed, null) if observed is not None else float("nan")
                ),
                # The permutation null is narrow, because shuffling within a
                # library leaves that library's contribution intact, so a
                # small z can still land in the tail. The effect in units of
                # that null's spread is the honest size of the signal.
                "null_mean": null_mean,
                "null_sd": null_sd,
                "effect_in_null_sd": effect,
                "per_library_z": per_library,
            },
        }
        # Across libraries: does the channel's fold track the programme's?
        usable = [
            library
            for library in libraries
            if library["programme_strength"] is not None
            and library["folds"][gene]["linear_fold"]
        ]
        rho, rho_p = _spearman_permutation(
            [library["programme_strength"] for library in usable],
            [np.log2(library["folds"][gene]["linear_fold"]) for library in usable],
            permutations,
            rng,
        )
        results[gene]["across_libraries"] = {
            "n_libraries": len(usable),
            "spearman_rho_vs_programme_strength": rho,
            "permutation_p": rho_p,
        }
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permutations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20261111)
    parser.add_argument("--outdir", default="results/driver_passenger_audit")
    args = parser.parse_args(argv)

    outdir = REPO / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    document = {
        "audit": {
            "id": "driver-passenger-audit-2026-11",
            "generated_by": "scripts/driver_passenger_audit.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "question": (
                "Is the channel's elevation in the relapse-competent state part "
                "of the transcriptional programme that defines the state, or a "
                "separate axis?"
            ),
            "limits": (
                "No measurement here is causal. The within-library test bounds "
                "whether the channel and the programme are coupled at all; only "
                "a perturbation experiment can settle whether the channel is "
                "instructive."
            ),
            "permutations": args.permutations,
            "seed": args.seed,
        },
        "datasets": {},
    }

    for dataset, config in DATASETS.items():
        if not (REPO / config["datadir"]).exists():
            print(f"{dataset}: no local copy of the deposit, skipped", flush=True)
            continue
        print(f"=== {dataset} ({config['cohort']}) ===", flush=True)
        collected = _collect(dataset, config, outdir)
        if not collected["libraries"]:
            continue
        document["datasets"][dataset] = {
            "cohort": config["cohort"],
            "state_gene": config["state_gene"],
            "programme_up": list(config["programme_up"]),
            "programme_down": list(config["programme_down"]),
            "n_libraries": len(collected["libraries"]),
            "libraries": [
                {
                    key: value
                    for key, value in library.items()
                    if not key.startswith("_")
                }
                for library in collected["libraries"]
            ],
            "tests": _run_tests(collected, config, args.permutations, args.seed),
        }

    out_path = outdir / "driver_passenger_audit.json"
    out_path.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {out_path}")
    for dataset, payload in document["datasets"].items():
        print(f"=== {dataset} ({payload['cohort']}), {payload['n_libraries']} libraries ===")
        for gene, result in payload["tests"].items():
            within = result["within_state_cells"]
            across = result["across_libraries"]

            def _fmt(value, spec=".3f"):
                return format(value, spec) if value is not None else "n/a"

            print(
                f"  {gene:<11} {result['role']:<21} "
                f"within-state z={_fmt(within['stouffer_z'])} "
                f"p={_fmt(within['permutation_p'], '.4g')} "
                f"eff={_fmt(within['effect_in_null_sd'], '.1f')}sd "
                f"(null sd={_fmt(within['null_sd'], '.2f')})  "
                f"across-library rho={_fmt(across['spearman_rho_vs_programme_strength'])} "
                f"p={_fmt(across['permutation_p'], '.4g')} "
                f"(n={across['n_libraries']})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
