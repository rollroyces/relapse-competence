"""Command line entry point.

    python -m relapse_competence.cli sweep    --out results/mrd_sweep.json
    python -m relapse_competence.cli mrd      --out results/mrd_single.json
    python -m relapse_competence.cli screening --out results/screening.json
    python -m relapse_competence.cli all      --outdir results/

Every subcommand writes a JSON record stamped with ``mode: simulated`` and the
full configuration plus calibration provenance.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from .benchmark import run_depth_sweep, run_mrd_benchmark, run_screening_benchmark
from .config import Regime, SimulationConfig
from .report import build_report, write_report

__all__ = ["main"]


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--seed", type=int, default=20261106)
    parser.add_argument("--patients", type=int, default=400)
    parser.add_argument("--draws", type=int, default=12)
    parser.add_argument("--interval", type=int, default=90, help="days between draws")
    parser.add_argument(
        "--target-specificity",
        type=float,
        default=0.98,
        help="specificity bar the read threshold is selected to meet",
    )


def _config_from_args(args: argparse.Namespace, regime: Regime) -> SimulationConfig:
    return SimulationConfig(
        regime=regime,
        seed=args.seed,
        n_patients_per_arm=args.patients,
        n_draws=args.draws,
        sampling_interval_days=args.interval,
    )


def _cmd_mrd(args: argparse.Namespace) -> int:
    cfg = _config_from_args(args, Regime.POST_TREATMENT)
    result = run_mrd_benchmark(cfg, target_specificity=args.target_specificity)
    report = build_report(
        mode="simulated",
        config=cfg,
        payload={"mrd": result.as_dict()},
        claim_scope=(
            "Simulated post-treatment MRD. Figures are produced by code that "
            "executed in this run; they are not clinical measurements and not "
            "a claim about any assay."
        ),
    )
    path = write_report(report, args.out)
    print(json.dumps(result.as_dict(), indent=2))
    print(f"\nwrote {path}")
    return 0


def _cmd_sweep(args: argparse.Namespace) -> int:
    cfg = _config_from_args(args, Regime.POST_TREATMENT)
    depths = tuple(int(d) for d in args.depths.split(","))
    loci = tuple(int(n) for n in args.loci.split(","))
    results = run_depth_sweep(
        cfg,
        depths=depths,
        locus_counts=loci,
        target_specificity=args.target_specificity,
    )
    rows = [r.as_dict() for r in results]
    report = build_report(
        mode="simulated",
        config=cfg,
        payload={"sweep": rows},
        claim_scope=(
            "Simulated depth x panel-size grid. The read threshold for each "
            "configuration is selected on a held-out calibration split, not on "
            "the evaluation split."
        ),
    )
    path = write_report(report, args.out)
    header = (
        f"{'depth':>9} {'loci':>5} {'reads':>10} {'k':>5} {'sens':>6} {'sens360':>8} "
        f"{'spec':>6} {'lead_d':>7} {'minvol_cm3':>10} {'ok':>4}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        lead = (
            f"{r['median_lead_time_days']:.0f}"
            if r["median_lead_time_days"] is not None
            else "n/a"
        )
        vol = r["nominal_volume_threshold_mm3"] / 1000.0
        print(
            f"{r['sequencing_depth']:>9} {r['n_loci']:>5} {r['total_reads_per_draw']:>10} "
            f"{r['read_threshold']:>5} {r['sensitivity']:>6.3f} "
            f"{r['sensitivity_within_360d']:>8.3f} {r['specificity']:>6.3f} "
            f"{lead:>7} {vol:>10.2f} {'yes' if r['target_reached'] else 'NO':>4}"
        )
    print(f"\nwrote {path}")
    return 0


def _cmd_screening(args: argparse.Namespace) -> int:
    cfg = _config_from_args(args, Regime.SCREENING)
    payload = run_screening_benchmark(cfg)
    report = build_report(
        mode="simulated",
        config=cfg,
        payload={"screening": payload},
        claim_scope=(
            "Simulated screening regime. Compares a sequential rise detector "
            "against a single-timepoint threshold on the same simulated cohort."
        ),
    )
    path = write_report(report, args.out)
    print(json.dumps(payload, indent=2))
    print(f"\nwrote {path}")
    return 0


def _cmd_all(args: argparse.Namespace) -> int:
    outdir = Path(args.outdir)
    mrd_cfg = _config_from_args(args, Regime.POST_TREATMENT)
    screen_cfg = replace(mrd_cfg, regime=Regime.SCREENING)

    sweep = run_depth_sweep(
        mrd_cfg,
        depths=tuple(int(d) for d in args.depths.split(",")),
        locus_counts=tuple(int(n) for n in args.loci.split(",")),
        target_specificity=args.target_specificity,
    )
    screening = run_screening_benchmark(screen_cfg)

    report = build_report(
        mode="simulated",
        config=mrd_cfg,
        payload={
            "sweep": [r.as_dict() for r in sweep],
            "screening": screening,
        },
        claim_scope=(
            "Simulated. Both regimes run in this invocation; every figure "
            "originates from executed code."
        ),
    )
    path = write_report(report, outdir / "benchmark_results.json")
    print(f"wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="relapse-competence",
        description="Longitudinal cfDNA modelling for the relapse-competent state.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_mrd = sub.add_parser("mrd", help="single MRD configuration")
    _add_common(p_mrd)
    p_mrd.add_argument("--out", default="results/mrd_single.json")
    p_mrd.set_defaults(func=_cmd_mrd)

    p_sweep = sub.add_parser("sweep", help="depth x panel-size grid")
    _add_common(p_sweep)
    p_sweep.add_argument("--depths", default="5000,50000,200000,500000")
    p_sweep.add_argument("--loci", default="50,200")
    p_sweep.add_argument("--out", default="results/mrd_sweep.json")
    p_sweep.set_defaults(func=_cmd_sweep)

    p_screen = sub.add_parser("screening", help="sequential vs single-timepoint")
    _add_common(p_screen)
    p_screen.add_argument("--out", default="results/screening.json")
    p_screen.set_defaults(func=_cmd_screening)

    p_all = sub.add_parser("all", help="everything")
    _add_common(p_all)
    p_all.add_argument("--depths", default="5000,50000,200000,500000")
    p_all.add_argument("--loci", default="50,200")
    p_all.add_argument("--outdir", default="results")
    p_all.set_defaults(func=_cmd_all)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
