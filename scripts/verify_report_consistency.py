#!/usr/bin/env python3
"""Verify that the gap audit report agrees with the audit log.

This exists because the first published version of the report claimed
"2,418 retrieved / 100% of the union / 0 errors" while the log actually held a
larger union with several records that the parser had dropped silently. A
report that asserts numbers must be checkable against the machine-generated
record that produced them.

Usage
-----
    python scripts/verify_report_consistency.py \\
        --log results/gap_audit_bioelectric/audit_log.json \\
        --report docs/GAP-AUDIT-BIOELECTRIC.md

Exit code is 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

#: Query IDs whose hit counts are asserted in the report, with the value that
#: the report must state. Kept here so the check has an independent source of
#: truth: the log, not the report.
REQUIRED_CITATIONS = [
    "42019833",  # YAP1 relapsed SCLC — the adjacent paper (G2)
    "42327581",  # CACNA1E review — the single target hit
    "39191501",  # recurrent GBM methylation, ion channel genes
    "36038893",  # ESCC mtDNA -> MMP depolarisation -> DNA methylation
    "32777557",  # gastric CDO1 methylation and mitochondrial membrane potential
    "29723302",  # thyroid SCN4B voltage-gated channel and recurrence-free survival
    "42722615",  # TTFields and PTEN predictive biomarker
    "30015269",  # electrotaxis of lung adenocarcinoma tumour-initiating cells
    "41648746",  # VOLTAGE-2 — the rejected screening artefact
]

#: Trial registrations the report must carry.
REQUIRED_TRIALS = [
    "NCT06216301",
    "NCT04892472",
    "NCT05583188",
    "NCT06739031",
    "NCT07284069",
    "NCT03954691",
]

#: Sections that must exist for the report to be considered complete.
REQUIRED_SECTIONS = [
    "## A. Topic Framing",
    "## B. Retrieval and Evidence Audit",
    "## C. Structured Gap Map",
    "## D. Pseudo-Gaps Rejected",
    "## E. Top Priority Opportunities",
    "## F. Primary Recommended Direction",
    "## G. Gap-to-Study Conversion",
    "## H. Risk Review",
    "## I. Retrieved and Verified References",
]


def fmt(value: int) -> str:
    """Render an integer the way the report writes it (with thousands separator)."""
    return f"{value:,}"


def parse_markdown_table(text: str, anchor: str) -> list[list[str]]:
    """Rows of the first markdown table that follows ``anchor``.

    The header row is returned as the first element so the caller can skip it.
    """
    if anchor not in text:
        return []
    rest = text[text.index(anchor) :]
    rows: list[list[str]] = []
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") and c for c in cells):
            continue
        rows.append(cells)
    return rows


def _num(text: str) -> float:
    """Parse the leading number out of a table cell.

    Tolerates bold, thousands separators, trailing units, and a parenthetical
    delta annotation such as "0.802 (−3.2 pp)".
    """
    cleaned = (
        text.replace("*", "")
        .replace(",", "")
        .replace("\u2212", "-")
        .replace("\u2013", "-")
        .strip()
    )
    match = re.match(r"^-?\d+(?:\.\d+)?", cleaned)
    if not match:
        raise ValueError(f"no leading number in cell: {text!r}")
    return float(match.group(0))


def _close(a: float, b: float, tol: float = 5e-4) -> bool:
    return abs(a - b) <= tol


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify report/log consistency.")
    parser.add_argument(
        "--log", default="results/gap_audit_bioelectric/audit_log.json", help="audit log path"
    )
    parser.add_argument(
        "--report", default="docs/GAP-AUDIT-BIOELECTRIC.md", help="report path"
    )
    parser.add_argument("--readme", default="README.md", help="README path")
    parser.add_argument(
        "--d1-doc", default="docs/D1-CHANNEL-ALLOCATION.md", help="D1 report path"
    )
    parser.add_argument("--sweep", default="results/mrd_sweep.json", help="MRD sweep results")
    parser.add_argument(
        "--allocation", default="results/channel_allocation.json", help="allocation results"
    )
    parser.add_argument(
        "--allocation-deep",
        default="results/channel_allocation_200k.json",
        help="allocation results at the deeper configuration",
    )
    args = parser.parse_args(argv)

    log_path = Path(args.log)
    report_path = Path(args.report)

    if not log_path.exists():
        print(f"FAIL: audit log not found: {log_path}")
        return 1
    if not report_path.exists():
        print(f"FAIL: report not found: {report_path}")
        return 1

    log = json.loads(log_path.read_text())
    report = report_path.read_text()

    checks: list[tuple[str, bool, str]] = []

    def chk(name: str, condition: bool, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    # --- structural completeness ---
    for section in REQUIRED_SECTIONS:
        chk(f"section present: {section}", section in report)

    # --- every query hit count in the log must be stated in the report ---
    for query in log["queries"]:
        hits = query["total_hits"]
        label = f"{query['query_id']} hits={hits}"
        chk(
            f"report states {label}",
            fmt(hits) in report or str(hits) in report,
            f"source={query['source']}",
        )

    # --- retrieval reconciliation: this is the check that would have caught
    # the silent-drop defect ---
    recon = log.get("retrieval_reconciliation")
    chk("audit log contains a retrieval reconciliation block", recon is not None)
    if recon:
        n_not_parsed = recon["n_not_parsed"]
        chk(
            "every PMID returned by esearch was parsed",
            n_not_parsed == 0,
            f"{n_not_parsed} unparsed: {recon['pmids_returned_by_esearch_but_not_parsed']}",
        )
        chk(
            "report states the union size",
            fmt(recon["pmids_in_union"]) in report or str(recon["pmids_in_union"]) in report,
            f"union={recon['pmids_in_union']}",
        )
        chk(
            "report states the parsed-record count",
            fmt(recon["records_parsed"]) in report or str(recon["records_parsed"]) in report,
            f"parsed={recon['records_parsed']}",
        )
        if n_not_parsed:
            chk(
                "report discloses the unparsed records",
                "not_parsed" in report or "unparsed" in report.lower(),
            )

    # --- screening counts ---
    screening = log["screening"]
    chk(
        "report states the core-hit count",
        fmt(screening["n_core_hits"]) in report or str(screening["n_core_hits"]) in report,
        f"n_core_hits={screening['n_core_hits']}",
    )
    chk(
        "report states the core+lung count",
        fmt(screening["n_core_hits_and_lung"]) in report
        or str(screening["n_core_hits_and_lung"]) in report,
        f"n_core_hits_and_lung={screening['n_core_hits_and_lung']}",
    )
    chk(
        "report states the screening coverage percentage",
        f"{screening['screening_coverage_pct']}" in report
        or f"{screening['screening_coverage_pct']:.2f}" in report,
        f"coverage={screening['screening_coverage_pct']}%",
    )

    # --- the four records that the pre-fix parser dropped must be recovered ---
    # Regression guard: if the parser ever stops handling <PubmedBookArticle>,
    # these four stop being parsed and the reconciliation check above fires.
    RECOVERED_BOOK_RECORDS = ["22787676", "31424841", "31971703", "32119350"]
    for pmid in RECOVERED_BOOK_RECORDS:
        chk(f"recovered book record {pmid} is cited in the report", pmid in report)

    # --- every core hit must be adjudicated in the report ---
    for pmid in screening["core_hit_pmids"]:
        chk(f"report adjudicates core hit {pmid}", pmid in report)

    # --- citations and registrations ---
    for pmid in REQUIRED_CITATIONS:
        chk(f"report cites {pmid}", pmid in report)
    for nct in REQUIRED_TRIALS:
        chk(f"report cites {nct}", nct in report)

    # --- the report must not repeat the withdrawn false-positive explanation ---
    # The withdrawn explanation may appear ONLY inside an explicit correction
    # notice. Any line quoting it must also mark it as wrong.
    wrong = "treatme|nac|e-naive"
    offenders = [
        line for line in report.splitlines()
        if wrong in line and not re.search(r"wrong|Wrong|Correction|correction", line)
    ]
    chk(
        "the withdrawn explanation appears only inside a correction notice",
        not offenders,
        f"offending lines: {offenders[:2]}",
    )
    chk("report names the true false-positive source 'tenacious'", "tenacious" in report)
    chk("report carries an explicit correction notice", "Correction notice" in report)

    # --- coverage limitations must stay stated ---
    chk("report states the Google Scholar limitation", "Google Scholar" in report)
    chk("report states the Web of Science limitation", "Web of Science" in report)
    chk(
        "report warns against textual diffing of runs",
        "set-wise" in report or "set-based" in report,
    )

    # --- README MRD table must match the committed sweep results ---
    sweep_path = Path(args.sweep)
    if sweep_path.exists():
        sweep_rows = json.loads(sweep_path.read_text())["results"]["sweep"]
        readme_text = Path(args.readme).read_text() if Path(args.readme).exists() else ""
        table = parse_markdown_table(readme_text, "| Depth | Loci |")
        chk("README contains the MRD table", len(table) > 1)
        if len(table) > 1:
            body = table[1:]
            chk(
                "README table row count matches the sweep",
                len(body) == len(sweep_rows),
                f"readme={len(body)} results={len(sweep_rows)}",
            )
            for row, _row in zip(body, sweep_rows, strict=False):
                depth = _num(row[0])
                loci = int(_num(row[1]))
                match = next(
                    (
                        r
                        for r in sweep_rows
                        if r["sequencing_depth"] == depth and r["n_loci"] == loci
                    ),
                    None,
                )
                chk(f"README row {depth}/{loci} exists in the results", match is not None)
                if match is None:
                    continue
                chk(
                    f"README {depth}/{loci} sensitivity matches",
                    _close(_num(row[4]), match["sensitivity"]),
                    f"readme={row[4]} results={match['sensitivity']}",
                )
                chk(
                    f"README {depth}/{loci} specificity matches",
                    _close(_num(row[6]), match["specificity"]),
                    f"readme={row[6]} results={match['specificity']}",
                )
                if match["median_lead_time_days"] is not None:
                    chk(
                        f"README {depth}/{loci} lead time matches",
                        _close(_num(row[7]), match["median_lead_time_days"], tol=1.0),
                        f"readme={row[7]} results={match['median_lead_time_days']}",
                    )
    else:
        chk("MRD sweep results file exists", False, str(sweep_path))

    # --- D1 report tables must match the committed allocation results ---
    alloc_path = Path(args.allocation)
    deep_path = Path(args.allocation_deep)
    d1_text = Path(args.d1_doc).read_text() if Path(args.d1_doc).exists() else ""
    chk("D1 report exists", bool(d1_text))
    if alloc_path.exists() and d1_text:
        alloc_rows = json.loads(alloc_path.read_text())["results"]["channel_allocation"]
        deep_rows = (
            json.loads(deep_path.read_text())["results"]["channel_allocation"]
            if deep_path.exists()
            else []
        )

        def find(rows, loci: int, fraction: float) -> dict | None:
            return next(
                (
                    r
                    for r in rows
                    if r["total_loci"] == loci
                    and abs(r["electrical_fraction"] - fraction) < 1e-9
                ),
                None,
            )

        # C.1 specificity decomposition
        base = find(deep_rows, 200, 0.0)
        if base is not None:
            chk(
                "D1 C.1 quotes the measured specificity vs responders",
                f"{base['mrd_specificity_vs_responders']:.3f}" in d1_text,
                str(base["mrd_specificity_vs_responders"]),
            )
            chk(
                "D1 C.1 quotes the measured specificity vs persistent",
                f"{base['mrd_specificity_vs_persistent']:.3f}" in d1_text,
                str(base["mrd_specificity_vs_persistent"]),
            )
            chk(
                "D1 C.1 quotes the measured persistent share of MRD+",
                f"{base['persistent_share_of_mrd_positive'] * 100:.0f}%" in d1_text,
                str(base["persistent_share_of_mrd_positive"]),
            )

        # C.4 and C.5 tables
        # section -> (loci, column index of MRD sensitivity, column index of
        # auc_enrichment or None when the table does not carry it)
        for section, loci, sens_col, auc_col in (
            ("### C.4", 200, 3, 6),
            ("### C.5", 50, 1, None),
        ):
            table = parse_markdown_table(d1_text, section)
            chk(f"D1 {section} contains a table", len(table) > 1)
            for row in table[1:]:
                try:
                    fraction = _num(row[0])
                except ValueError:
                    continue
                match = find(alloc_rows, loci, fraction)
                chk(f"D1 {section} row e_frac={fraction} exists in the results", match is not None)
                if match is None:
                    continue
                if "degenerate" in " ".join(row).lower():
                    chk(
                        f"D1 {section} e_frac={fraction} is marked degenerate and "
                        "the results agree",
                        bool(match.get("degenerate")),
                    )
                    continue
                chk(
                    f"D1 {section} e_frac={fraction} sensitivity matches",
                    _close(_num(row[sens_col]), match["mrd_sensitivity"]),
                    f"doc={row[sens_col]} results={match['mrd_sensitivity']}",
                )
                if auc_col is not None and len(row) > auc_col:
                    chk(
                        f"D1 {section} e_frac={fraction} auc_enrichment matches",
                        _close(
                            _num(row[auc_col]),
                            match["auc_electrical_enrichment_within_mrd_positive"],
                        ),
                        f"doc={row[auc_col]} "
                        f"results={match['auc_electrical_enrichment_within_mrd_positive']}",
                    )

    # --- documentation must not carry superseded numbers or designs ---
    readme_path = Path(args.readme)
    model_card = Path("MODEL_CARD.md")
    d1_doc_path = Path(args.d1_doc)

    if readme_path.exists():
        readme_text = readme_path.read_text()
        chk("README states the current audit record count", "2,427 records screened" in readme_text)
        chk("README does not state the superseded record count", "2,418 records screened" not in readme_text)
        chk("README states the current MRD headline numbers", "39 days" in readme_text)
        chk("README does not state the superseded MRD headline numbers", "41 days" not in readme_text)

    if model_card.exists():
        card = model_card.read_text()
        chk("MODEL_CARD states the current MRD sensitivity", "52.1% sensitivity" in card)
        chk("MODEL_CARD does not state the superseded MRD sensitivity", "51.5% sensitivity" not in card)
        chk("MODEL_CARD states the current MRD lead time", "39-day" in card)
        chk("MODEL_CARD does not state the superseded MRD lead time", "41-day" not in card)
        chk("MODEL_CARD carries the specificity decomposition", "not a single number" in card)
        chk("MODEL_CARD links the D1 report", "D1-CHANNEL-ALLOCATION.md" in card)

    if d1_doc_path.exists():
        chk("gap audit links the executed D1 report", "D1-CHANNEL-ALLOCATION.md" in report)
        chk(
            "gap audit no longer describes an unimplemented information-theoretic "
            "parameterisation",
            "mutual information" not in report,
        )
        chk(
            "gap audit records the biological parameterisation that was built",
            "f_state" in report,
        )

    # --- source errors must be surfaced ---
    chk("audit log records zero source errors", log.get("errors") == [], str(log.get("errors")))

    failed = [c for c in checks if not c[1]]
    for name, ok, detail in checks:
        if not ok:
            print(f"  FAIL: {name}" + (f"  ({detail})" if detail else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} consistency checks PASSED")

    if failed:
        print("\nReport and audit log disagree. Fix the report before publishing.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
