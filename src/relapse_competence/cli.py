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

from .benchmark import (
    run_channel_allocation_sweep,
    run_depth_sweep,
    run_mrd_benchmark,
    run_screening_benchmark,
)
from .config import Regime, SimulationConfig
from .fidelity import (
    MODEL_VARIANTS,
    run_fidelity_comparison,
    run_split_model_validation,
    summarise,
)
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


def _cmd_fidelity(args: argparse.Namespace) -> int:
    """Model-fidelity comparison and split-model validation."""
    cfg = _config_from_args(args, Regime.POST_TREATMENT)

    # The comparison runs with the electrical channel exactly as the published
    # sweep ran it, so that its "published" variant reproduces the published
    # headline rather than a differently-noised cohort. The split-model
    # validation needs the channel, so it gets one; both arms of that
    # comparison use it, so the transfer is still apples to apples.
    comparison = run_fidelity_comparison(
        cfg,
        depths=tuple(int(d) for d in args.depths.split(",")),
        locus_counts=tuple(int(n) for n in args.loci.split(",")),
        target_specificity=args.target_specificity,
    )
    validation_config = (
        cfg if cfg.n_electrical_loci > 0 else replace(cfg, n_electrical_loci=50)
    )
    # The split-model validation runs at the operating point the programme
    # recommends, so its numbers can be read against the D1 headline.
    validation_config = replace(
        validation_config,
        sequencing_depth=args.split_depth,
        n_loci=args.split_loci,
    )
    validation = run_split_model_validation(
        validation_config,
        target_specificity=args.target_specificity,
        variants=MODEL_VARIANTS[1:],
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    comparison_payload = build_report(
        mode="simulated",
        config=cfg,
        payload=comparison,
        claim_scope=(
            "Simulated. Each variant turns on one fidelity extension of the "
            "published model and recomputes the headline MRD numbers. The "
            "published configuration is included as the reference, and the "
            "published numbers do not change: the extensions are default-off."
        ),
    )
    validation_payload = build_report(
        mode="simulated",
        config=validation_config,
        payload=validation,
        claim_scope=(
            "Simulated. A detector fitted on the published model is applied, "
            "without refitting, to each fidelity model; the difference "
            "bounds the performance that the published model was hiding."
        ),
    )

    comparison_path = write_report(comparison_payload, outdir / "model_fidelity.json")
    validation_path = write_report(
        validation_payload, outdir / "split_model_validation.json"
    )

    print(summarise(comparison["variants"]))
    print()
    print("split-model validation (detector fitted on the published model):")
    published = validation["published_model_published_detector"]
    print(
        f"  published model          sens={published['mrd_sensitivity']:.3f} "
        f"spec(resp)={published['mrd_specificity_vs_responders']:.3f} "
        f"spec(persist)={published['mrd_specificity_vs_persistent']:.3f} "
        f"auc(enrichment)={published['auc_electrical_enrichment_within_mrd_positive']:.3f}"
    )
    for evaluation in validation["evaluations"]:
        transfer = evaluation["variant_model_published_detector"]
        refit = evaluation["variant_model_refitted_detector"]
        print(
            f"  {evaluation['variant']:<26} transfer: sens={transfer['mrd_sensitivity']:.3f} "
            f"spec(resp)={transfer['mrd_specificity_vs_responders']:.3f} "
            f"spec(persist)={transfer['mrd_specificity_vs_persistent']:.3f}  "
            f"| refit: sens={refit['mrd_sensitivity']:.3f} "
            f"spec(resp)={refit['mrd_specificity_vs_responders']:.3f} "
            f"spec(persist)={refit['mrd_specificity_vs_persistent']:.3f} "
            f"auc(enr)={refit['auc_electrical_enrichment_within_mrd_positive']:.3f}"
        )
    print(f"wrote {comparison_path}")
    print(f"wrote {validation_path}")
    return 0


def _cmd_allocation(args: argparse.Namespace) -> int:
    cfg = _config_from_args(args, Regime.POST_TREATMENT)
    rows = run_channel_allocation_sweep(
        cfg,
        total_loci=tuple(int(x) for x in args.loci.split(",")),
        depth=args.depth,
        electrical_fractions=tuple(float(x) for x in args.fractions.split(",")),
        target_specificity=args.target_specificity,
    )
    report = build_report(
        mode="simulated",
        config=cfg,
        payload={"channel_allocation": rows},
        claim_scope=(
            "Simulated channel allocation under a fixed total read budget. "
            "Reports whether a bulk ion-channel channel refines the relapse call "
            "within the MRD-positive population, and what that costs the "
            "mutation channel."
        ),
    )
    path = write_report(report, args.out)
    header = (
        f"{'loci':>5} {'e_frac':>7} {'n_mut':>6} {'n_elec':>7} {'mrd_sens':>9} "
        f"{'mrd_spec':>9} {'lead':>6} {'|MRD+|':>7} {'ppv_base':>9} {'ppv_ref':>8} "
        f"{'auc_raw':>8} {'auc_enr':>8}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        if r["degenerate"]:
            print(
                f"{r['total_loci']:>5} {r['electrical_fraction']:>7.2f} "
                f"{r['n_mutation_loci']:>6} {r['n_electrical_loci']:>7}  "
                f"DEGENERATE - {r['degenerate_reason']}"
            )
            continue
        lead = (
            f"{r['median_lead_time_days']:.0f}"
            if r["median_lead_time_days"] is not None
            else "n/a"
        )

        def _f(value: float) -> str:
            return "n/a" if value != value else f"{value:.3f}"

        print(
            f"{r['total_loci']:>5} {r['electrical_fraction']:>7.2f} "
            f"{r['n_mutation_loci']:>6} {r['n_electrical_loci']:>7} "
            f"{r['mrd_sensitivity']:>9.3f} {r['mrd_specificity']:>9.3f} {lead:>6} "
            f"{r['n_mrd_positive_evaluation']:>7} "
            f"{_f(r['ppv_within_mrd_positive']):>9} "
            f"{_f(r['ppv_after_electrical_refinement']):>8} "
            f"{_f(r['auc_electrical_raw_within_mrd_positive']):>8} "
            f"{_f(r['auc_electrical_enrichment_within_mrd_positive']):>8}"
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

    p_alloc = sub.add_parser(
        "allocation", help="split a fixed read budget between mutation and electrical channels"
    )
    _add_common(p_alloc)
    p_alloc.add_argument("--depth", type=int, default=50_000)
    p_alloc.add_argument("--loci", default="50,200")
    p_alloc.add_argument("--fractions", default="0.0,0.25,0.5,0.75,1.0")
    p_alloc.add_argument("--out", default="results/channel_allocation.json")
    p_alloc.set_defaults(func=_cmd_allocation)

    p_screen = sub.add_parser("screening", help="sequential vs single-timepoint")
    _add_common(p_screen)
    p_screen.add_argument("--out", default="results/screening.json")
    p_screen.set_defaults(func=_cmd_screening)

    p_fidelity = sub.add_parser(
        "fidelity", help="model-fidelity comparison and split-model validation"
    )
    _add_common(p_fidelity)
    p_fidelity.add_argument("--depths", default="5000,50000,200000,500000")
    p_fidelity.add_argument("--loci", default="50,200")
    p_fidelity.add_argument("--outdir", default="results")
    p_fidelity.add_argument(
        "--split-depth",
        type=int,
        default=200_000,
        help="depth for the split-model validation",
    )
    p_fidelity.add_argument(
        "--split-loci",
        type=int,
        default=200,
        help="mutation panel size for the split-model validation",
    )
    p_fidelity.set_defaults(func=_cmd_fidelity)

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
