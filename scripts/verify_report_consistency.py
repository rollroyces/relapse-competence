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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify report/log consistency.")
    parser.add_argument(
        "--log", default="results/gap_audit_bioelectric/audit_log.json", help="audit log path"
    )
    parser.add_argument(
        "--report", default="docs/GAP-AUDIT-BIOELECTRIC.md", help="report path"
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
