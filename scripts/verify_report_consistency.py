#!/usr/bin/env python3
"""Verify that the gap audit report agrees with the audit log.

This exists because the first published version of the report asserted a
retrieved-record count and a screening-coverage figure that the audit log did
not support, while the parser silently dropped records. A report that asserts
numbers must be checkable against the machine-generated record that produced
them.

The withdrawn wording itself is never stored in this repository. It is
recovered from git history at run time by
``scripts/audit_findings_disposition.py``, which proves each finding in both
directions and scans the whole repository for surviving copies.

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
import subprocess
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


def _close_rounded(a: float, b: float, decimals: int = 2) -> bool:
    """Comparison for a number a report rounds to ``decimals`` places."""
    return abs(a - b) <= 0.5 * 10 ** (-decimals) + 1e-9


def _close_rel(a: float, b: float, rel_tol: float = 1e-3) -> bool:
    """Relative comparison, for numbers a report rounds to 4 significant figures."""
    if a == b:
        return True
    scale = max(abs(a), abs(b))
    return abs(a - b) <= rel_tol * scale


def _git_object_exists(sha: str) -> bool:
    """Whether ``sha`` still names a commit in this repository.

    The history was rewritten on 2026-11-06, so an id printed in the report
    can stop naming anything. A reader would copy such an id straight into a
    checkout, so it is checked rather than trusted.
    """
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


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

    # --- the authoritative report must not restate a retracted claim at all.
    # The check itself is delegated to the disposition artefact, which
    # recovers the withdrawn wording from git history at run time and proves
    # both that it was present and that no copy of it survives anywhere in
    # this repository. No copy of the wording is stored here.
    disposition_path = Path("results/audit_findings_disposition.json")
    chk("audit findings disposition artefact exists", disposition_path.exists())
    if disposition_path.exists():
        disp = json.loads(disposition_path.read_text())
        chk(
            "every audited finding is dispositioned as resolved",
            disp["disposition"]["all_resolved"] is True,
            str(disp["disposition"]),
        )
        chk(
            "the disposition covers all four findings",
            len(disp["findings"]) == 4,
            str(len(disp["findings"])),
        )
        for finding in disp["findings"]:
            chk(
                f"finding {finding['id']} is resolved with evidence",
                finding["resolved"] and bool(finding["evidence"]),
            )
            chk(
                f"finding {finding['id']} records where its withdrawn wording lives",
                finding.get("withdrawn_line_number") is not None
                and bool(finding.get("withdrawn_line_sha256")),
            )
            chk(
                f"finding {finding['id']} stores no copy of its withdrawn wording",
                "withdrawn_wording" not in finding
                and "withdrawn_text" not in finding,
            )
        chk(
            "the gap audit report links the disposition artefact",
            "audit_findings_disposition.json" in report,
        )

        # The report's own disposition table must agree with the generated
        # artefact. The commits are named by subject, because a history
        # rewrite changes every id; the artefact is the source of truth for
        # which subjects each finding credits.
        disposition_table = parse_markdown_table(
            report, "| Finding | Status | Fixed in |"
        )
        chk(
            "the report carries a findings disposition table",
            len(disposition_table) > 1,
        )
        if len(disposition_table) > 1:
            by_id = {f["id"]: f for f in disp["findings"]}
            for row in disposition_table[1:]:
                cells = [c.strip() for c in row]
                if not cells:
                    continue
                finding_id = cells[0].split(" ")[0].strip()
                if finding_id not in by_id:
                    chk(
                        f"disposition table row is a known finding: {finding_id}",
                        False,
                        finding_id,
                    )
                    continue
                cited = (
                    [c.strip() for c in re.findall(r"`([^`]+)`", cells[2])]
                    if len(cells) > 2
                    else []
                )
                expected = [
                    part.strip()
                    for part in by_id[finding_id]["fixed_in"].split(";")
                    if part.strip()
                ]
                chk(
                    f"the report's fixed-in column for {finding_id} matches the artefact",
                    cited == expected,
                    f"report={cited} artefact={expected}",
                )
            chk(
                "the report's disposition table covers every finding",
                len(disposition_table) - 1 == len(disp["findings"]),
                f"{len(disposition_table) - 1} rows for {len(disp['findings'])} findings",
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

    # --- the report must carry its own revision history and provenance ---
    chk(
        "the gap audit carries a revision history section",
        "Revision history and provenance" in report,
    )
    first_published = ""
    try:
        import subprocess as _sp

        out = _sp.run(
            [
                "git",
                "-C",
                ".",
                "log",
                "--diff-filter=A",
                "--format=%H",
                "--",
                "docs/GAP-AUDIT-BIOELECTRIC.md",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = out.stdout.strip().splitlines()
        first_published = lines[-1] if lines else ""
    except Exception:  # noqa: BLE001
        first_published = ""
    chk(
        "the first published commit could be resolved from history",
        bool(first_published),
    )
    chk(
        "the revision history names the first published commit",
        bool(first_published) and first_published[:7] in report,
        f"resolved {first_published[:7]}" if first_published else "unresolved",
    )
    chk(
        "the revision history points at the machine-generated disposition",
        "audit_findings_disposition.json" in report,
    )

    # Every commit id the revision history prints must still name a commit.
    # The history was rewritten, so a stale id is exactly what a reader would
    # copy into a checkout.
    revision_table = parse_markdown_table(
        report, "| Commit | Change | Where the retracted wording now lives |"
    )
    stale_ids = []
    for row in revision_table[1:]:
        if not row:
            continue
        token = row[0].strip().strip("`")
        if not re.fullmatch(r"[0-9a-f]{7,40}", token):
            continue
        if not _git_object_exists(token):
            stale_ids.append(token)
    chk(
        "every commit id in the revision history still names a commit",
        not stale_ids,
        f"stale: {stale_ids}" if stale_ids else "",
    )

    # --- the D0 window audit must agree with its generated artefact ---
    d0_artefact_path = Path("results/d0_window_audit/d0_window_audit.json")
    d0_doc_path = Path("docs/D0-TARGET-WINDOW-AUDIT.md")
    chk("the D0 window audit artefact exists", d0_artefact_path.exists())
    chk("the D0 window audit report exists", d0_doc_path.exists())
    if d0_artefact_path.exists() and d0_doc_path.exists():
        d0 = json.loads(d0_artefact_path.read_text())
        d0_doc = d0_doc_path.read_text()
        by_symbol = {t["symbol"]: t for t in d0["targets"]}
        d0_table = parse_markdown_table(
            d0_doc, "| Target | Tier | Lung TPM | Highest non-lung tissue |"
        )
        chk("the D0 report carries a verdict table", len(d0_table) > 1)
        if len(d0_table) > 1:
            seen = set()
            for row in d0_table[1:]:
                cells = [c.strip() for c in row]
                if not cells:
                    continue
                symbol = cells[0].strip("`")
                seen.add(symbol)
                target = by_symbol.get(symbol)
                chk(f"the D0 table row for {symbol} is a known target", target is not None)
                if target is None:
                    continue
                verdict = target.get("verdict") or {}
                gtex = target.get("gtex") or {}
                chk(
                    f"the D0 verdict for {symbol} matches the artefact",
                    verdict.get("class", "") in cells[-1],
                    f"report={cells[-1]} artefact={verdict.get('class')}",
                )
                chk(
                    f"the D0 lung TPM for {symbol} matches the artefact",
                    _close_rel(_num(cells[2]), gtex.get("lung_tpm") or 0.0),
                    f"report={cells[2]} artefact={gtex.get('lung_tpm')}",
                )
                chk(
                    f"the D0 window fold for {symbol} matches the artefact",
                    _close_rel(
                        _num(cells[4]),
                        verdict.get("window_fold_vs_max_offtarget") or 0.0,
                    ),
                    f"report={cells[4]} artefact={verdict.get('window_fold_vs_max_offtarget')}",
                )
            chk(
                "the D0 table covers every audited target",
                seen == set(by_symbol),
                f"report={sorted(seen)} artefact={sorted(by_symbol)}",
            )
        chk(
            "the D0 report states the gate outcome",
            ("does not fire" in d0_doc) or ("does not fire" in d0_doc),
        )
        chk(
            "the D0 report links the research plan",
            "RESEARCH-PLAN.md" in d0_doc,
        )

    # --- the model-fidelity artefacts must agree with the published sweep ---
    fidelity_path = Path("results/model_fidelity.json")
    split_path = Path("results/split_model_validation.json")
    fidelity_doc_path = Path("docs/MODEL-FIDELITY.md")
    chk("the model fidelity artefact exists", fidelity_path.exists())
    chk("the split-model validation artefact exists", split_path.exists())
    chk("the model fidelity report exists", fidelity_doc_path.exists())
    if fidelity_path.exists() and split_path.exists():
        fidelity = json.loads(fidelity_path.read_text())
        variants = {
            v["variant"]: v for v in fidelity["results"]["variants"]
        }
        chk(
            "the fidelity comparison covers the published model and every extension",
            set(variants) == {
                "published",
                "multi_clone",
                "gompertzian",
                "site_dependent_shedding",
                "per_locus_background",
                "combined",
            },
            str(sorted(variants)),
        )
        # The published variant must reproduce the committed sweep exactly, or
        # the deltas the report quotes are not comparable with the published
        # headline.
        sweep_path = Path(args.sweep)
        if sweep_path.exists() and "published" in variants:
            sweep = json.loads(sweep_path.read_text())["results"]["sweep"]
            reference = next(
                (
                    r
                    for r in sweep
                    if r["sequencing_depth"] == 200_000 and r["n_loci"] == 200
                ),
                None,
            )
            published = (variants["published"].get("recommended_200k_200") or {})
            if reference is not None:
                chk(
                    "the fidelity comparison's published variant reproduces the "
                    "committed sweep sensitivity",
                    _close_rel(published.get("sensitivity", 0.0), reference["sensitivity"]),
                    f"fidelity={published.get('sensitivity')} sweep={reference['sensitivity']}",
                )
                chk(
                    "the fidelity comparison's published variant reproduces the "
                    "committed sweep specificity",
                    _close_rel(published.get("specificity", 0.0), reference["specificity"]),
                    f"fidelity={published.get('specificity')} sweep={reference['specificity']}",
                )
                chk(
                    "the fidelity comparison's published variant reproduces the "
                    "committed sweep lead time",
                    _close_rel(
                        published.get("median_lead_time_days") or 0.0,
                        reference["median_lead_time_days"] or 0.0,
                    ),
                    f"fidelity={published.get('median_lead_time_days')} "
                    f"sweep={reference['median_lead_time_days']}",
                )
        split = json.loads(split_path.read_text())["results"]
        evaluations = split.get("evaluations") or []
        chk(
            "the split-model validation evaluates every fidelity variant",
            {e["variant"] for e in evaluations}
            == set(variants) - {"published"},
            str(sorted(e["variant"] for e in evaluations)),
        )
        for evaluation in evaluations:
            chk(
                f"the split-model validation reports the transfer and refit "
                f"operating points for {evaluation['variant']}",
                "variant_model_published_detector" in evaluation
                and "variant_model_refitted_detector" in evaluation,
            )
    if fidelity_doc_path.exists():
        fidelity_doc = fidelity_doc_path.read_text()
        chk(
            "the model fidelity report links the generated artefact",
            "model_fidelity.json" in fidelity_doc,
        )
        chk(
            "the model fidelity report links the split-model artefact",
            "split_model_validation.json" in fidelity_doc,
        )

    # --- the GSE299684 state-expression audit must agree with its artefact ---
    gse_artefact_path = Path("results/gse299684/state_expression.json")
    gse_doc_path = Path("docs/GSE299684-STATE-EXPRESSION.md")
    chk("the GSE299684 state-expression artefact exists", gse_artefact_path.exists())
    chk("the GSE299684 state-expression report exists", gse_doc_path.exists())
    if gse_artefact_path.exists() and gse_doc_path.exists():
        gse = json.loads(gse_artefact_path.read_text())
        gse_doc = gse_doc_path.read_text()
        sweep = gse.get("state_definition_sweep") or []
        primary = next(
            (s for s in sweep if s["definition"] == gse["audit"]["primary_definition"]),
            None,
        )
        chk(
            "the GSE299684 artefact reports the state-definition sweep",
            len(sweep) >= 3,
            str(len(sweep)),
        )
        if primary is not None:
            chk(
                "the GSE299684 state call reproduces the paper's surface signature",
                primary["state_validation_passed"] == primary["state_validation_total"],
                f"{primary['state_validation_passed']}/{primary['state_validation_total']}",
            )
            gse_table = parse_markdown_table(
                gse_doc, "| Channel | Detection: state | Detection: other tumour |"
            )
            chk("the GSE299684 report carries a channel table", len(gse_table) > 1)
            by_gene = {c["gene"]: c for c in primary["channels"] if c.get("status") == "ok"}
            if len(gse_table) > 1:
                for row in gse_table[1:]:
                    cells = [c.strip() for c in row]
                    gene = cells[0].strip("`").strip("*")
                    record = by_gene.get(gene)
                    chk(
                        f"the GSE299684 table row for {gene} is an audited channel",
                        record is not None,
                        gene,
                    )
                    if record is None:
                        continue
                    chk(
                        f"the GSE299684 detection ratio for {gene} matches the artefact",
                        _close_rounded(
                            _num(cells[4]), record["detection_ratio_vs_yap1negative"]
                        ),
                        f"report={cells[4]} artefact={record['detection_ratio_vs_yap1negative']}",
                    )
                    chk(
                        f"the GSE299684 linear fold for {gene} matches the artefact",
                        _close_rounded(
                            _num(cells[5]),
                            record.get("linear_fold_vs_yap1negative") or 0.0,
                        ),
                        f"report={cells[5]} artefact={record.get('linear_fold_vs_yap1negative')}",
                    )
                chk(
                    "the GSE299684 table covers every audited channel",
                    {c.strip().strip("`").strip("*") for c in (r[0] for r in gse_table[1:])}
                    == set(by_gene),
                )
        loso = gse.get("leave_one_sample_out") or {}
        for gene in ("KCNN4", "PIEZO1"):
            record = loso.get(gene) or {}
            chk(
                f"the GSE299684 leave-one-out result for {gene} is stable in sign",
                record.get("sign_is_stable") is True,
                str(record.get("sign_is_stable")),
            )
            chk(
                f"the GSE299684 report states the leave-one-out range for {gene}",
                f"{record.get('min_ratio'):.2f}" in gse_doc
                and f"{record.get('max_ratio'):.2f}" in gse_doc,
                f"{record.get('min_ratio')}..{record.get('max_ratio')}",
            )
        # The state-validation table must carry the pooled numbers, not a
        # single library's: a validation table quoted from one sample would
        # still "reproduce" the signature and mean nothing.
        if primary is not None:
            validation_table = parse_markdown_table(
                gse_doc, "| Marker | Expected | YAP1+ | YAP1− |"
            )
            chk(
                "the GSE299684 report carries a state-validation table",
                len(validation_table) > 1,
            )
            artefact_validation = primary["state_validation"]
            for row in validation_table[1:]:
                cells = [c.strip() for c in row]
                if not cells:
                    continue
                gene = cells[0].strip("`")
                record = artefact_validation.get(gene)
                chk(
                    f"the GSE299684 validation row for {gene} is an audited marker",
                    record is not None,
                    gene,
                )
                if record is None:
                    continue
                chk(
                    f"the GSE299684 pooled validation value for {gene} (state) "
                    "matches the artefact",
                    _close_rounded(_num(cells[2]), record["mean_yap1_positive"], 3),
                    f"report={cells[2]} artefact={record['mean_yap1_positive']}",
                )
                chk(
                    f"the GSE299684 pooled validation value for {gene} (other "
                    "tumour) matches the artefact",
                    _close_rounded(_num(cells[3]), record["mean_yap1_negative"], 3),
                    f"report={cells[3]} artefact={record['mean_yap1_negative']}",
                )

        # The per-site table must match the artefact, and the libraries it
        # counts must add up to the libraries that were read.
        site_table = parse_markdown_table(gse_doc, "| Libraries | State cells |")
        chk("the GSE299684 report carries a per-site table", len(site_table) > 1)
        if len(site_table) > 1:
            artefact_sites = {
                entry["tissue"]: entry for entry in gse["per_tissue_channels"]
            }
            total_libraries = 0
            for row in site_table[1:]:
                cells = [c.strip() for c in row]
                if len(cells) < 6:
                    continue
                site = cells[0].strip("*")
                entry = artefact_sites.get(site)
                chk(
                    f"the GSE299684 site row '{site}' is an audited site",
                    entry is not None,
                    site,
                )
                if entry is None:
                    continue
                chk(
                    f"the GSE299684 library count for '{site}' matches the artefact",
                    int(cells[1]) == len(entry["samples"]),
                    f"report={cells[1]} artefact={len(entry['samples'])}",
                )
                total_libraries += len(entry["samples"])
                chk(
                    f"the GSE299684 state-cell count for '{site}' matches the artefact",
                    int(cells[2].replace(",", "")) == entry["n_yap1_positive"],
                    f"report={cells[2]} artefact={entry['n_yap1_positive']}",
                )
                for column, gene in ((4, "KCNN4"), (5, "PIEZO1")):
                    stats = entry["channels"].get(gene) or {}
                    ratio = stats.get("detection_ratio")
                    cell = cells[column].replace("*", "").replace("—", "").strip()
                    if ratio is None or not cell:
                        continue
                    chk(
                        f"the GSE299684 {gene} ratio for '{site}' matches the artefact",
                        _close_rounded(float(cell), ratio),
                        f"report={cell} artefact={ratio}",
                    )
            chk(
                "the GSE299684 per-site table accounts for every library",
                total_libraries == len(gse["per_sample"]),
                f"{total_libraries} of {len(gse['per_sample'])}",
            )

        # The prose site breakdown must add up to the libraries that were read.
        breakdown = ""
        for paragraph in gse_doc.split("\n\n"):
            if "single-cell libraries of relapsed SCLC" in paragraph:
                breakdown = paragraph
                break
        chk(
            "the GSE299684 report states the site breakdown",
            bool(breakdown),
        )
        if breakdown:
            counts = [int(n) for n in re.findall(r"\((\d+)\)", breakdown)]
            chk(
                "the GSE299684 site breakdown adds up to every library",
                sum(counts) == len(gse["per_sample"]),
                f"{sum(counts)} vs {len(gse['per_sample'])}",
            )
            lung_libraries = sum(
                len(entry["samples"])
                for entry in gse["per_tissue_channels"]
                if "lung" in entry["tissue"]
            )
            lung_match = re.search(r"lung \((\d+)", breakdown)
            chk(
                "the GSE299684 site breakdown counts the lung libraries correctly",
                lung_match is not None and int(lung_match.group(1)) == lung_libraries,
                f"report={lung_match.group(1) if lung_match else None} artefact={lung_libraries}",
            )

        # A universal claim about libraries is only allowed if the data
        # supports it: every library where a channel falls below 1 has to be
        # named in the report.
        for row in gse["per_sample_channels"]:
            stats = (row.get("channels") or {}).get("PIEZO1") or {}
            ratio = stats.get("detection_ratio")
            if ratio is not None and ratio < 1:
                chk(
                    "the GSE299684 report names the library where PIEZO1 is below 1: "
                    f"{row['accession']}",
                    row["accession"] in gse_doc,
                    row["accession"],
                )
        for gene, counts in (gse.get("per_sample_sign_counts") or {}).items():
            if gene not in ("KCNN4", "PIEZO1"):
                continue
            above = counts["samples_with_ratio_above_one"]
            below = counts["samples_with_ratio_below_one"]
            chk(
                f"the GSE299684 report states the per-library count for {gene}",
                f"{above}" in gse_doc and f"{below}" in gse_doc,
                f"{above} above, {below} below",
            )

        # The cell-calling robustness table must match the artefact, and the
        # two load-bearing claims must hold under every call: KCa3.1 does not
        # mark the state in lung, and PIEZO1 does.
        variants = gse.get("cell_call_sensitivity") or []
        chk(
            "the GSE299684 artefact reports the cell-calling sensitivity",
            len(variants) >= 3,
            str(len(variants)),
        )
        variant_table = parse_markdown_table(
            gse_doc, "| Cell call | Malignant kept | Dropped | State signature |"
        )
        chk(
            "the GSE299684 report carries a cell-calling robustness table",
            len(variant_table) > 1,
        )
        if len(variant_table) > 1:
            by_variant = {v["variant"]: v for v in variants}
            for row in variant_table[1:]:
                cells = [c.strip() for c in row]
                if len(cells) < 8:
                    continue
                match = re.match(r"`([^`]+)`", cells[0])
                name = match.group(1) if match else cells[0].strip("`* ")
                record = by_variant.get(name)
                chk(
                    f"the GSE299684 cell-call row '{name}' is an audited variant",
                    record is not None,
                    name,
                )
                if record is None:
                    continue
                chk(
                    f"the GSE299684 malignant-kept count for '{name}' matches the artefact",
                    int(cells[1].replace(",", "")) == record["n_malignant_kept"],
                    f"report={cells[1]} artefact={record['n_malignant_kept']}",
                )
                chk(
                    f"the GSE29984 the dropped count for '{name}' matches the artefact",
                    int(cells[2].replace(",", "")) == record["n_malignant_dropped"],
                    f"report={cells[2]} artefact={record['n_malignant_dropped']}",
                )
                chk(
                    f"the GSE299684 state signature for '{name}' is reproduced in full",
                    record["state_validation_passed"] == record["state_validation_total"],
                    f"{record['state_validation_passed']}/{record['state_validation_total']}",
                )
                genes = {c["gene"]: c for c in record["channels"]}
                chk(
                    f"the GSE299684 KCNN4 ratio for '{name}' matches the artefact",
                    _close_rounded(
                        _num(cells[4]), genes["KCNN4"]["detection_ratio_vs_yap1negative"]
                    ),
                    f"report={cells[4]} artefact={genes['KCNN4']['detection_ratio_vs_yap1negative']}",
                )
                chk(
                    f"the GSE299684 PIEZO1 ratio for '{name}' matches the artefact",
                    _close_rounded(
                        _num(cells[5]), genes["PIEZO1"]["detection_ratio_vs_yap1negative"]
                    ),
                    f"report={cells[5]} artefact={genes['PIEZO1']['detection_ratio_vs_yap1negative']}",
                )
            reported = set()
            for r in variant_table[1:]:
                match = re.match(r"`([^`]+)`", r[0].strip())
                if match:
                    reported.add(match.group(1))
            chk(
                "the GSE299684 cell-call table covers every audited variant",
                reported == set(by_variant),
                f"{sorted(reported)} vs {sorted(by_variant)}",
            )

        # The two claims the programme rests on, under every cell call.
        for variant in variants:
            name = variant["variant"]
            lung = [
                site
                for site in variant["per_site"]
                if "lung" in site["tissue"] and site["n_yap1_positive"] > 0
            ]
            kcnn4 = [
                site["channels"]["KCNN4"]["detection_ratio"]
                for site in lung
                if site["channels"].get("KCNN4", {}).get("detection_ratio") is not None
            ]
            piezo1 = [
                site["channels"]["PIEZO1"]["detection_ratio"]
                for site in lung
                if site["channels"].get("PIEZO1", {}).get("detection_ratio") is not None
            ]
            chk(
                f"KCa3.1 does not mark the state in lung under the '{name}' cell call",
                bool(kcnn4) and max(kcnn4) < 1.0,
                str(kcnn4),
            )
            chk(
                f"PIEZO1 marks the state in lung under the '{name}' cell call",
                bool(piezo1) and min(piezo1) > 1.0,
                str(piezo1),
            )
            loso = variant["leave_one_sample_out"]
            for gene in ("KCNN4", "PIEZO1"):
                chk(
                    f"the '{name}' cell call leaves the {gene} leave-one-out sign stable",
                    loso[gene]["sign_is_stable"] is True,
                    gene,
                )

        # The copy-number proxy's limits are recorded, not glossed over.
        cnv = gse.get("cnv_proxy_by_state") or {}
        chk(
            "the GSE299684 artefact records the copy-number proxy's limits",
            "note" in cnv and len(cnv.get("per_sample") or []) > 0,
        )
        plain = " ".join(gse_doc.replace("**", "").split())
        chk(
            "the GSE299684 report states that the copy-number proxy does not "
            "reproduce the paper's comparison",
            "does not reproduce the paper" in plain,
        )

        chk(
            "the GSE299684 report names the dataset and the paper",
            "GSE299684" in gse_doc and "42019833" in gse_doc,
        )
        chk(
            "the GSE299684 report links the generated artefact",
            "state_expression.json" in gse_doc,
        )

    # --- the GSE353299 NSCLC audit must agree with its artefact ---
    nsclc_artefact_path = Path("results/gse353299/state_expression.json")
    nsclc_doc_path = Path("docs/GSE353299-STATE-EXPRESSION.md")
    chk("the GSE353299 artefact exists", nsclc_artefact_path.exists())
    chk("the GSE353299 report exists", nsclc_doc_path.exists())
    if nsclc_artefact_path.exists() and nsclc_doc_path.exists():
        nsclc = json.loads(nsclc_artefact_path.read_text())
        nsclc_doc = nsclc_doc_path.read_text()
        nsclc_primary = next(
            s
            for s in nsclc["state_definition_sweep"]
            if s["definition"] == nsclc["audit"]["primary_definition"]
        )
        chk(
            "the GSE353299 state call is validated on the basaloid programme",
            nsclc_primary["state_validation"]["basaloid_enriched_in_state"] is True,
            str(nsclc_primary["state_validation"]),
        )
        nsclc_genes = {
            c["gene"]: c for c in nsclc_primary["channels"] if c.get("status") == "ok"
        }
        nsclc_table = parse_markdown_table(
            nsclc_doc, "| Channel | Detection: state | Detection: other tumour |"
        )
        chk("the GSE353299 report carries a channel table", len(nsclc_table) > 1)
        if len(nsclc_table) > 1:
            for row in nsclc_table[1:]:
                cells = [c.strip() for c in row]
                if len(cells) < 7:
                    continue
                gene = cells[0].strip("`* ")
                record = nsclc_genes.get(gene)
                chk(
                    f"the GSE299299 channel row for {gene} is an audited channel",
                    record is not None,
                    gene,
                )
                if record is None:
                    continue
                chk(
                    f"the GSE299299 detection ratio for {gene} matches the artefact",
                    _close_rounded(
                        _num(cells[4]), record["detection_ratio_vs_yap1negative"]
                    ),
                    f"report={cells[4]} artefact={record['detection_ratio_vs_yap1negative']}",
                )
                chk(
                    f"the GSE299299 state detection for {gene} matches the artefact",
                    _close_rounded(
                        _num(cells[1]), record["detection_yap1_positive"], 3
                    ),
                    f"report={cells[1]} artefact={record['detection_yap1_positive']}",
                )
            chk(
                "the GSE299299 table covers every audited channel",
                {c.strip().strip("`* ") for c in (r[0] for r in nsclc_table[1:])}
                == set(nsclc_genes),
            )

        # The per-timepoint table: the per-library median and range of the
        # state fraction must match the artefact.
        timepoint_table = parse_markdown_table(
            nsclc_doc, "| Libraries | Malignant cells |"
        )
        chk("the GSE353299 report carries a timepoint table", len(timepoint_table) > 1)
        if len(timepoint_table) > 1:
            by_timepoint = {e["treatment"]: e for e in nsclc["per_timepoint"]}
            for row in timepoint_table[1:]:
                cells = [c.strip() for c in row]
                if len(cells) < 4:
                    continue
                match = re.match(r"`([^`]+)`", cells[0].strip())
                key = match.group(1) if match else cells[0].strip("`* ").lower()
                record = by_timepoint.get(key)
                chk(
                    f"the GSE299299 timepoint row '{key}' is an audited timepoint",
                    record is not None,
                    key,
                )
                if record is None:
                    continue
                chk(
                    f"the GSE299299 library count for '{key}' matches the artefact",
                    int(cells[1]) == record["n_libraries"],
                    f"report={cells[1]} artefact={record['n_libraries']}",
                )
                chk(
                    f"the GSE299299 malignant count for '{key}' matches the artefact",
                    int(cells[2].replace(",", "")) == record["n_malignant"],
                    f"report={cells[2]} artefact={record['n_malignant']}",
                )
                fractions = sorted(
                    s["state_positive_fraction_of_malignant"]
                    for s in nsclc["per_sample"]
                    if s["treatment"].strip().lower() == key
                    and s["state_positive_fraction_of_malignant"] is not None
                )
                if fractions:
                    median = fractions[len(fractions) // 2]
                    chk(
                        f"the GSE299299 state fraction for '{key}' matches the artefact",
                        f"{median:.3f}" in cells[3],
                        f"report={cells[3]} artefact={median:.3f}",
                    )

        # The cross-disease table must be traceable to both artefacts.
        comparison = parse_markdown_table(nsclc_doc, "| NSCLC, KRT17+ state")
        chk("the GSE299299 report carries a cross-disease table", len(comparison) > 1)
        sclc_artefact_path = Path("results/gse299684/state_expression.json")
        if len(comparison) > 1 and sclc_artefact_path.exists():
            sclc = json.loads(sclc_artefact_path.read_text())
            sclc_primary = next(
                s
                for s in sclc["state_definition_sweep"]
                if s["definition"] == sclc["audit"]["primary_definition"]
            )
            sclc_genes = {
                c["gene"]: c for c in sclc_primary["channels"] if c.get("status") == "ok"
            }
            for row in comparison[1:]:
                cells = [c.strip() for c in row]
                if len(cells) < 3:
                    continue
                gene = cells[0].strip("`* ")
                if gene not in sclc_genes or gene not in nsclc_genes:
                    continue
                chk(
                    f"the cross-disease SCLC value for {gene} matches the SCLC artefact",
                    _close_rounded(
                        _num(cells[1]), sclc_genes[gene]["detection_ratio_vs_yap1negative"]
                    ),
                    f"report={cells[1]} artefact={sclc_genes[gene]['detection_ratio_vs_yap1negative']}",
                )
                chk(
                    f"the cross-disease NSCLC value for {gene} matches the NSCLC artefact",
                    _close_rounded(
                        _num(cells[2]),
                        nsclc_genes[gene]["detection_ratio_vs_yap1negative"],
                    ),
                    f"report={cells[2]} artefact={nsclc_genes[gene]['detection_ratio_vs_yap1negative']}",
                )

        # The robustness that carries the conclusion.
        loso = nsclc.get("leave_one_sample_out") or {}
        kcnn4 = loso.get("KCNN4") or {}
        chk(
            "the GSE299299 KCa3.1 result holds in every patient",
            kcnn4.get("n_samples_with_ratio_above_one") == len(nsclc["per_sample"]),
            str(kcnn4.get("n_samples_with_ratio_above_one")),
        )
        chk(
            "the GSE299299 KCa3.1 leave-one-out sign is stable",
            kcnn4.get("sign_is_stable") is True,
        )
        chk(
            "the GSE299299 report names the dataset and the correction",
            "GSE353299" in nsclc_doc and "42019833" not in nsclc_doc,
        )

    # --- the research plan must exist and agree with the executed results ---
    plan_path = Path("docs/RESEARCH-PLAN.md")
    chk("research plan exists", plan_path.exists())
    if plan_path.exists():
        plan = plan_path.read_text()
        chk("research plan links the gap audit", "GAP-AUDIT-BIOELECTRIC.md" in plan)
        chk("research plan links the D1 report", "D1-CHANNEL-ALLOCATION.md" in plan)
        for pid in (
            "42019833",  # YAP1+ relapsed SCLC -- the anchor
            "42327581",  # the single target-intersection record
            "41741906",  # KCNN4 in NSCLC
            "40688096",  # elexacaftor blocks KCa3.1
            "30015269",  # electrotaxis of lung tumour-initiating cells
            "38494915",  # Piezo1 as tumour suppressor -- the contraindication
        ):
            chk(f"research plan cites {pid}", pid in plan)
        for gate in ("K1", "K2", "K3", "K4", "K5"):
            chk(f"research plan defines killing condition {gate}", gate in plan)
        for stage in ("D0", "D2", "D3", "D4", "D5"):
            chk(f"research plan defines stage {stage}", f"Stage {stage}" in plan or f"### {stage}" in plan)

        # Numbers quoted in the plan must come from the committed allocation
        # results, not from memory.
        # The plan quotes the 200,000x configuration, so that is the file it
        # must agree with.
        deep_alloc_rows = []
        if deep_path.exists():
            deep_alloc_rows = json.loads(deep_path.read_text())["results"][
                "channel_allocation"
            ]
        if deep_alloc_rows:
            base = next(
                (
                    r
                    for r in deep_alloc_rows
                    if r["total_loci"] == 200 and r["electrical_fraction"] == 0.0
                ),
                None,
            )
            if base is not None:
                chk(
                    "research plan quotes the measured specificity vs persistent",
                    f"{base['mrd_specificity_vs_persistent']:.3f}" in plan,
                    str(base["mrd_specificity_vs_persistent"]),
                )
                chk(
                    "research plan quotes the measured persistent share of MRD+",
                    f"{base['persistent_share_of_mrd_positive'] * 100:.0f}%" in plan,
                    str(base["persistent_share_of_mrd_positive"]),
                )
                chk(
                    "research plan states the depth its quoted figures come from",
                    "200,000" in plan,
                )

    # --- licence metadata must agree with the licence file ---
    licence_path = Path("LICENSE")
    licence_text = licence_path.read_text() if licence_path.exists() else ""
    chk(
        "LICENSE carries the GNU Affero General Public License v3 text",
        "GNU AFFERO GENERAL PUBLIC LICENSE" in licence_text
        and "Version 3, 19 November 2007" in licence_text,
    )
    pyproject_path = Path("pyproject.toml")
    pyproject = pyproject_path.read_text() if pyproject_path.exists() else ""
    chk("pyproject declares AGPL-3.0-or-later", 'license = "AGPL-3.0-or-later"' in pyproject)
    citation_path = Path("CITATION.cff")
    citation = citation_path.read_text() if citation_path.exists() else ""
    chk("CITATION.cff declares AGPL-3.0-or-later", "license: AGPL-3.0-or-later" in citation)
    readme_path = Path(args.readme)
    readme_licence = readme_path.read_text() if readme_path.exists() else ""
    chk("README states the dual licence", "AGPL-3.0-or-later" in readme_licence)
    chk(
        "COMMERCIAL_LICENSE.md exists for the commercial option",
        Path("COMMERCIAL_LICENSE.md").exists(),
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
