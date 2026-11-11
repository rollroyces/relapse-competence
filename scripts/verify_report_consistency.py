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


def _num_or_none(text: str) -> float | None:
    """``_num`` that reports a missing or unparsable cell as ``None``.

    A cell that cannot be read is a failed check, not a crashed verifier, so
    the caller can name the cell that drifted.
    """
    try:
        return _num(text)
    except ValueError:
        return None


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

    # --- the plasma-readability audit must agree with its artefact ---
    plasma_artefact_path = Path("results/plasma_readability/plasma_readability.json")
    plasma_doc_path = Path("docs/PLASMA-READABILITY.md")
    chk("the plasma-readability artefact exists", plasma_artefact_path.exists())
    chk("the plasma-readability report exists", plasma_doc_path.exists())
    if plasma_artefact_path.exists() and plasma_doc_path.exists():
        plasma = json.loads(plasma_artefact_path.read_text())
        plasma_doc = plasma_doc_path.read_text()
        sweeps = {
            (s["dataset"], s["channel"]): s
            for s in plasma["sweeps"]
            if s["electrical_fraction"] == 0.25
        }

        # The control must reproduce the published D1 row exactly: that is what
        # makes the other rows attributable to the measurements.
        d1_path = Path("results/channel_allocation_200k.json")
        if d1_path.exists() and ("simulator default", "assumed") in sweeps:
            d1_rows = [
                r
                for r in json.loads(d1_path.read_text())["results"]["channel_allocation"]
                if r["total_loci"] == 200 and r["electrical_fraction"] == 0.25
            ]
            control = sweeps[("simulator default", "assumed")]
            if d1_rows:
                published = d1_rows[0]
                chk(
                    "the plasma-readability control reproduces the published D1 "
                    "enrichment AUC",
                    _close_rounded(
                        control["auc_electrical_enrichment_within_mrd_positive"],
                        published["auc_electrical_enrichment_within_mrd_positive"],
                        3,
                    ),
                    f"control={control['auc_electrical_enrichment_within_mrd_positive']} "
                    f"published={published['auc_electrical_enrichment_within_mrd_positive']}",
                )
                chk(
                    "the plasma-readability control reproduces the published D1 "
                    "MRD sensitivity",
                    _close_rounded(
                        control["mrd_sensitivity"], published["mrd_sensitivity"], 3
                    ),
                )
                chk(
                    "the plasma-readability control reproduces the published D1 "
                    "PPV within MRD+",
                    _close_rounded(
                        control["ppv_within_mrd_positive"],
                        published["ppv_within_mrd_positive"],
                        3,
                    ),
                )

        # The report's sweep table must match the artefact.
        sweep_table = parse_markdown_table(
            plasma_doc, "| Configuration | Bulk elevation | Enrichment AUC within MRD+ |"
        )
        chk("the plasma-readability report carries a sweep table", len(sweep_table) > 1)
        if len(sweep_table) > 1:
            for row in sweep_table[1:]:
                cells = [c.strip() for c in row]
                if len(cells) < 4:
                    continue
                label = cells[0].replace("*", "")
                lowered = label.lower()
                # Explicit matching: "SCLC" is a substring of "NSCLC", so a
                # substring search would pair the wrong rows.
                key = None
                if "control" in lowered:
                    key = ("simulator default", "assumed")
                else:
                    dataset = "NSCLC" if "nsclc" in lowered else "SCLC"
                    channel = "KCNN4" if "kcnn4" in lowered else "PIEZO1"
                    if (dataset, channel) in sweeps:
                        key = (dataset, channel)
                chk(
                    f"the plasma-readability row '{label}' is an audited configuration",
                    key is not None,
                    label,
                )
                if key is None:
                    continue
                record = sweeps[key]
                chk(
                    f"the plasma-readability bulk elevation for '{label}' matches "
                    "the artefact",
                    _close_rounded(
                        _num(cells[1]), record["bulk_elevation_used"], 2
                    ),
                    f"report={cells[1]} artefact={record['bulk_elevation_used']}",
                )
                chk(
                    f"the plasma-readability enrichment AUC for '{label}' matches "
                    "the artefact",
                    _close_rounded(
                        _num(cells[2]),
                        record["auc_electrical_enrichment_within_mrd_positive"],
                        3,
                    ),
                    f"report={cells[2]} "
                    f"artefact={record['auc_electrical_enrichment_within_mrd_positive']}",
                )

        # The findings the report rests on.
        control_auc = (
            sweeps[("simulator default", "assumed")][
                "auc_electrical_enrichment_within_mrd_positive"
            ]
            if ("simulator default", "assumed") in sweeps
            else None
        )
        nsclc_kcnn4 = sweeps.get(("NSCLC", "KCNN4"))
        nsclc_piezo1 = sweeps.get(("NSCLC", "PIEZO1"))
        sclc_kcnn4 = sweeps.get(("SCLC", "KCNN4"))
        sclc_piezo1 = sweeps.get(("SCLC", "PIEZO1"))
        if control_auc is not None and nsclc_kcnn4 is not None:
            chk(
                "the measured NSCLC state fraction improves on the simulator's "
                "assumption",
                nsclc_kcnn4["auc_electrical_enrichment_within_mrd_positive"]
                > control_auc,
                f"{nsclc_kcnn4['auc_electrical_enrichment_within_mrd_positive']} "
                f"vs {control_auc}",
            )
        if control_auc is not None and sclc_kcnn4 is not None and sclc_piezo1 is not None:
            chk(
                "the measured SCLC state fraction weakens the electrical readout",
                max(
                    sclc_kcnn4["auc_electrical_enrichment_within_mrd_positive"],
                    sclc_piezo1["auc_electrical_enrichment_within_mrd_positive"],
                )
                < control_auc,
            )
        if nsclc_piezo1 is not None:
            chk(
                "the NSCLC PIEZO1 plasma readout is at chance, as the abundance "
                "fold predicts",
                nsclc_piezo1["auc_electrical_enrichment_within_mrd_positive"] < 0.6,
                str(nsclc_piezo1["auc_electrical_enrichment_within_mrd_positive"]),
            )
        chk(
            "the plasma-readability report distinguishes the two metrics",
            "Detection rate" in plasma_doc and "Abundance fold" in plasma_doc,
        )
        chk(
            "the plasma-readability report flags the refinement-PPV artefact",
            "artefact" in plasma_doc.lower(),
        )

    # --- the channel-transferability audit must agree with its artefact ---
    transfer_artefact_path = Path("results/gse324849/state_expression.json")
    transfer_doc_path = Path("docs/CHANNEL-TRANSFERABILITY.md")
    chk("the channel-transferability artefact exists", transfer_artefact_path.exists())
    chk("the channel-transferability report exists", transfer_doc_path.exists())
    if transfer_artefact_path.exists() and transfer_doc_path.exists():
        transfer = json.loads(transfer_artefact_path.read_text())
        transfer_doc = transfer_doc_path.read_text()
        detection = transfer["cells"]["compartment_detection"]
        malignant = detection["KCNN4"]["malignant_total"]
        for gene in ("KCNN4", "PIEZO1"):
            chk(
                f"the {gene} channel is absent from the third dataset's tumour",
                detection[gene]["malignant"] == 0,
                f"{detection[gene]['malignant']}/{malignant}",
            )
            chk(
                f"the {gene} channel is detected in the immune compartment of "
                "the third dataset",
                detection[gene]["immune"] > 0,
                f"{detection[gene]['immune']}/{detection[gene]['immune_total']}",
            )
        chk(
            "the third dataset's tumour is ASCL1-subtype",
            detection["ASCL1"]["malignant"] / max(detection["ASCL1"]["malignant_total"], 1)
            > 0.5,
            f"{detection['ASCL1']['malignant']}/{detection['ASCL1']['malignant_total']}",
        )
        chk(
            "the third dataset's tumour is covered at least as deeply as its "
            "immune compartment, so the channel absence is not a depth artefact",
            (transfer["cells"]["median_genes_detected_malignant"] or 0)
            >= (transfer["cells"]["median_genes_detected_immune"] or 0),
            f"malignant={transfer['cells']['median_genes_detected_malignant']} "
            f"immune={transfer['cells']['median_genes_detected_immune']}",
        )
        chk(
            "the third dataset does not contain the paper's NEUROD1-high state",
            detection["NEUROD1"]["malignant"] <= 2,
            str(detection["NEUROD1"]["malignant"]),
        )
        chk(
            "the channel-transferability report states the GSE325242 deposit defect",
            "no gene annotation" in transfer_doc,
        )
        chk(
            "the channel-transferability report states the tumour-specific "
            "consequence",
            "tumour-expression gate" in transfer_doc,
        )
        for gene, count in (
            ("KCNN4", detection["KCNN4"]["malignant"]),
            ("PIEZO1", detection["PIEZO1"]["malignant"]),
            ("ASCL1", detection["ASCL1"]["malignant"]),
        ):
            chk(
                f"the channel-transferability report quotes the {gene} tumour count",
                f"{count} / {malignant}" in transfer_doc,
                f"{count} / {malignant}",
            )

    # --- the README's headline numbers must match the artefacts ---
    readme_path = Path("README.md")
    if readme_path.exists():
        readme = readme_path.read_text()
        sclc_path = Path("results/gse299684/state_expression.json")
        nsclc_path = Path("results/gse353299/state_expression.json")
        plasma_path = Path("results/plasma_readability/plasma_readability.json")
        if sclc_path.exists() and nsclc_path.exists() and plasma_path.exists():
            sclc = json.loads(sclc_path.read_text())
            nsclc = json.loads(nsclc_path.read_text())
            plasma = json.loads(plasma_path.read_text())

            def _primary(artefact: dict) -> dict:
                name = artefact["audit"]["primary_definition"]
                return next(
                    s for s in artefact["state_definition_sweep"] if s["definition"] == name
                )

            def _genes(artefact: dict) -> dict:
                return {
                    c["gene"]: c
                    for c in _primary(artefact)["channels"]
                    if c.get("status") == "ok"
                }

            sclc_genes = _genes(sclc)
            nsclc_genes = _genes(nsclc)
            chk(
                "the README quotes the SCLC PIEZO1 detection ratio",
                f"{sclc_genes['PIEZO1']['detection_ratio_vs_yap1negative']:.2f}" in readme,
            )
            chk(
                "the README quotes the NSCLC KCNN4 detection ratio",
                f"{nsclc_genes['KCNN4']['detection_ratio_vs_yap1negative']:.2f}" in readme,
            )
            sweeps = {
                (s["dataset"], s["channel"]): s
                for s in plasma["sweeps"]
                if s["electrical_fraction"] == 0.25
            }
            for key, label in (
                (("simulator default", "assumed"), "0.9312"),
                (("NSCLC", "KCNN4"), "0.9929"),
                (("SCLC", "PIEZO1"), "0.6945"),
                (("NSCLC", "PIEZO1"), "0.4658"),
            ):
                if key in sweeps:
                    chk(
                        f"the README quotes the plasma enrichment AUC for {key[0]} {key[1]}",
                        label in readme,
                        label,
                    )

            # The gate yield: how many of the measured tumours express the
            # channels at all.
            def _library_rows(artefact: dict) -> list[dict]:
                rows = []
                for key in ("per_sample_channels", "per_patient"):
                    rows.extend(artefact.get(key, []))
                return rows

            def _detection(record: dict, gene: str) -> float | None:
                entry = (record.get("channels") or {}).get(gene) or {}
                pos = entry.get(
                    "detection_state_positive", entry.get("detection_yap1_positive")
                )
                neg = entry.get(
                    "detection_state_negative", entry.get("detection_yap1_negative")
                )
                if pos is None and neg is None:
                    return None
                return max(pos or 0.0, neg or 0.0)

            measurable = []
            for artefact in (sclc, nsclc):
                for record in _library_rows(artefact):
                    if any(
                        _detection(record, gene) is not None
                        for gene in ("PIEZO1", "KCNN4")
                    ):
                        measurable.append(record)
            transfer_path = Path("results/gse324849/state_expression.json")
            if transfer_path.exists():
                transfer = json.loads(transfer_path.read_text())
                detection = transfer["cells"]["compartment_detection"]
                measurable.append(
                    {
                        "channels": {
                            gene: {
                                "detection_state_positive": detection[gene]["malignant"]
                                / max(detection[gene]["malignant_total"], 1),
                                "detection_state_negative": 0.0,
                            }
                            for gene in ("PIEZO1", "KCNN4")
                        }
                    }
                )
            piezo1_positive = sum(
                1 for r in measurable if (_detection(r, "PIEZO1") or 0) > 0
            )
            kcnn4_positive = sum(
                1 for r in measurable if (_detection(r, "KCNN4") or 0) > 0
            )
            chk(
                "the README quotes the PIEZO1 gate yield",
                f"{piezo1_positive} of the {len(measurable)}" in readme
                or f"{piezo1_positive} ({piezo1_positive / len(measurable):.1%})" in readme,
                f"{piezo1_positive}/{len(measurable)}",
            )
            chk(
                "the README quotes the KCa3.1 gate yield",
                f"{kcnn4_positive} ({kcnn4_positive / len(measurable):.1%})" in readme,
                f"{kcnn4_positive}/{len(measurable)}",
            )
            chk(
                "the README distinguishes simulated figures from public-data "
                "measurements",
                "public-data audits" in readme or "public deposits" in readme,
            )
            # The per-patient audit's numbers, as the README carries them.
            readme_audit_artefact = Path(
                "results/per_patient_audit/per_patient_audit.json"
            )
            readme_folds_artefact = Path(
                "results/per_library_folds/per_library_folds.json"
            )
            if readme_audit_artefact.exists() and readme_folds_artefact.exists():
                audit_data = json.loads(readme_audit_artefact.read_text())
                chk(
                    "the README links the per-patient audit",
                    "docs/PER-PATIENT-AUDIT.md" in readme,
                )
                for summary in audit_data["summaries"]:
                    if summary["dataset"] == "NSCLC" and summary["channel"] != "KCNN4":
                        continue
                    label = f"{summary['dataset']} / {summary['channel']}"
                    chk(
                        f"the README quotes the {label} per-tumour fold yield",
                        f"{summary['n_fold_above_one']} of "
                        f"{summary['n_fold_computable']}" in readme,
                        f"{summary['n_fold_above_one']}/{summary['n_fold_computable']}",
                    )
                    chk(
                        f"the README quotes the {label} per-tumour K3 yield",
                        f"{summary['n_clearing_k3']} of {summary['n_libraries']}" in readme,
                        f"{summary['n_clearing_k3']}/{summary['n_libraries']}",
                    )
                mrd = [
                    r
                    for r in audit_data["per_library"]
                    if r["dataset"] == "NSCLC" and r["treatment"] == "osi_mrd"
                ]
                if mrd:
                    lowest = min(r["operating_point"]["auc"] for r in mrd)
                    highest = max(r["operating_point"]["auc"] for r in mrd)
                    chk(
                        "the README quotes the NSCLC per-patient AUC range",
                        f"{lowest:.3f}" in readme and f"{highest:.3f}" in readme,
                        f"{lowest:.3f}-{highest:.3f}",
                    )
                    chk(
                        "the README says every NSCLC residual-disease library clears",
                        f"all {len(mrd)}" in readme,
                    )
                chk(
                    "the README quotes the share of SCLC state cells in three libraries",
                    "86.4%" in readme,
                )
            chk(
                "the README links the data-access applications",
                "docs/DATA-ACCESS-APPLICATIONS.md" in readme,
            )
            roadmap = Path("docs/ROADMAP.md")
            if roadmap.exists():
                chk(
                    "the roadmap links the data-access applications",
                    "DATA-ACCESS-APPLICATIONS.md" in roadmap.read_text(),
                )
            datasets_doc = Path("docs/DATASETS.md")
            if datasets_doc.exists():
                chk(
                    "the dataset survey links the data-access applications",
                    "DATA-ACCESS-APPLICATIONS.md" in datasets_doc.read_text(),
                )
            chk(
                "the README states that the measurements are correlational",
                "not a mechanism" in readme,
            )

    # --- the driver-versus-passenger audit must agree with its artefact ---
    dpa_artefact = Path(
        "results/driver_passenger_audit/driver_passenger_audit.json"
    )
    dpa_doc = Path("docs/KCNN4-DRIVER-OR-PASSENGER.md")
    chk("the driver-passenger audit artefact exists", dpa_artefact.exists())
    chk("the driver-passenger audit document exists", dpa_doc.exists())
    if dpa_artefact.exists() and dpa_doc.exists():
        dpa = json.loads(dpa_artefact.read_text())
        dpa_text = dpa_doc.read_text()
        nsclc = dpa["datasets"].get("GSE353299", {})

        def _within(gene: str, dataset: dict) -> dict:
            return (
                dataset.get("tests", {})
                .get(gene, {})
                .get("within_state_cells", {})
            )

        # The cohort the document quotes has to be one where the controls
        # hold: a specificity control that fails makes every number in that
        # cohort unreadable, which is why one cohort is set aside.
        actb = _within("ACTB", nsclc)
        krt14 = _within("KRT14", nsclc)
        kcnn4 = _within("KCNN4", nsclc)
        chk(
            "the specificity control holds in the cohort the document quotes",
            actb.get("permutation_p", 1.0) > 0.05,
            str(actb.get("permutation_p")),
        )
        chk(
            "the power control holds in the cohort the document quotes",
            krt14.get("permutation_p", 1.0) < 0.05,
            str(krt14.get("permutation_p")),
        )
        chk(
            "KCNN4 is coupled to the programme in that cohort",
            kcnn4.get("permutation_p", 1.0) < 0.05,
            str(kcnn4.get("permutation_p")),
        )
        for label, entry in (
            ("KCNN4", kcnn4),
            ("the power control", krt14),
            ("the specificity control", actb),
        ):
            value = entry.get("stouffer_z")
            if value is None:
                continue
            chk(
                f"the driver-passenger document quotes {label}'s z-score {value:.2f}",
                f"{value:.2f}" in dpa_text,
            )
        sCLC = dpa["datasets"].get("GSE299684", {})
        sactb = _within("ACTB", sCLC)
        chk(
            "the SCLC cohort's specificity control fails, as the document says",
            sactb.get("permutation_p", 1.0) < 0.05,
            str(sactb.get("permutation_p")),
        )
        chk(
            "the document records the SCLC cohort as uninterpretable",
            "not interpretable" in dpa_text,
        )
        chk(
            "the document states the result is not causal",
            "Not settled" in dpa_text
            and "Causation, and the reason matters" in dpa_text,
        )
        chk(
            "the document states the falsifiable perturbation test",
            "knocking KCNN4 down" in dpa_text,
        )
        spec_path = Path("docs/PLASMA-ASSAY-SPECIFICATION.md")
        if spec_path.exists():
            spec_text = spec_path.read_text()
            chk(
                "the assay specification records that the channel may be a "
                "shadow of the transcriptional programme",
                "KCNN4-DRIVER-OR-PASSENGER.md" in spec_text
                and "shadow of the" in spec_text,
            )
            chk(
                "the assay specification says the premise is conditional on the "
                "perturbation experiment",
                "conditional on that experiment" in spec_text,
            )
        # The question a laboratory is asked has to be a question: named
        # propositions, a named perturbation, a prediction that can fail, and
        # a stated consequence for each outcome. Without those it is a
        # request for attention.
        pq_doc = Path("docs/PERTURBATION-QUESTION.md")
        chk("the perturbation question exists", pq_doc.exists())
        if pq_doc.exists():
            pq = pq_doc.read_text()
            for proposition in ("**P1**", "**P2**", "**P3**"):
                chk(
                    f"the perturbation question states {proposition}",
                    proposition in pq,
                )
            chk(
                "the perturbation question names the perturbation",
                "Knock KCNN4 down" in pq,
            )
            chk(
                "the perturbation question states a prediction that can fail",
                "collapses" in pq and "leaves both intact" in pq,
            )
            chk(
                "the perturbation question states a consequence for each outcome",
                "instructive" in pq and "passenger" in pq,
            )
            chk(
                "the perturbation question records that the direction is not settled",
                "direction not settled" in pq,
            )
            chk(
                "the perturbation question names the model obstacle",
                "not identified a cell line or a patient-derived model" in pq,
            )
            chk(
                "the perturbation question carries the deadline",
                "18 February" in pq,
            )
            chk(
                "the perturbation question quotes the measurement it rests on",
                "6.8 null standard deviations" in pq,
            )
            chk(
                "the perturbation question does not claim the channel is a passenger",
                "does not claim the channel is a passenger" in pq,
            )
            chk(
                "the host invitation points at the perturbation question",
                "PERTURBATION-QUESTION.md"
                in Path("docs/HOST-INVITATION.md").read_text(),
            )

        # The copy-number audit: the broad routes are excluded, and the
        # document has to say which routes those are.
        cn_artefact = Path(
            "results/kcnn4_copy_number/kcnn4_copy_number.json"
        )
        cn_doc = Path("docs/KCNN4-COPY-NUMBER.md")
        chk("the copy-number audit artefact exists", cn_artefact.exists())
        chk("the copy-number audit document exists", cn_doc.exists())
        if cn_artefact.exists() and cn_doc.exists():
            cn = json.loads(cn_artefact.read_text())
            cn_text = cn_doc.read_text()
            nsclc_cn = cn["datasets"].get("GSE353299", {})
            summary = nsclc_cn.get("result", {}).get("summary", {})
            chk(
                "the copy-number audit's per-library summary is present",
                summary.get("n_comparable", 0) >= 10,
                str(summary.get("n_comparable")),
            )
            chk(
                "the neighbourhood does not rise with the gene",
                summary.get("median_fold_neighbourhood", 99) < 2.0
                and summary.get("median_fold_own", 0) > 2.0,
                f"own {summary.get('median_fold_own')}, "
                f"neighbourhood {summary.get('median_fold_neighbourhood')}",
            )
            chk(
                "the document quotes the neighbourhood and gene folds",
                f"\u00d7{summary.get('median_fold_neighbourhood', 0):.2f}" in cn_text
                and f"\u00d7{summary.get('median_fold_own', 0):.2f}" in cn_text,
            )
            chk(
                "the copy-number locus test is not significant",
                nsclc_cn.get("result", {}).get("permutation_p", 0.0) > 0.05,
                str(nsclc_cn.get("result", {}).get("permutation_p")),
            )
            for phrase in (
                "Ruled out",
                "Not ruled out",
                "needs DNA",
                "focal amplification",
            ):
                chk(
                    f"the copy-number document states {phrase!r}",
                    phrase in cn_text,
                )
            chk(
                "the copy-number document points at the scoping inquiry",
                "whole-exome sequencing" in cn_text,
            )
            chk(
                "the perturbation question records the narrowed P3",
                "Narrowed, not closed" in pq,
            )

    # --- the gate review must agree with its artefact ---
    gate_artefact_path = Path("results/gate_review/gate_review.json")
    gate_doc_path = Path("docs/GATE-REVIEW.md")
    chk("the gate review artefact exists", gate_artefact_path.exists())
    chk("the gate review report exists", gate_doc_path.exists())
    if gate_artefact_path.exists() and gate_doc_path.exists():
        gate = json.loads(gate_artefact_path.read_text())
        gate_doc = gate_doc_path.read_text()
        conditions = {c["id"]: c for c in gate["conditions"]}
        chk(
            "the gate review covers all five killing conditions",
            set(conditions) == {"K1", "K2", "K3", "K4", "K5"},
            str(sorted(conditions)),
        )
        for condition_id in ("K1", "K2", "K3", "K4", "K5"):
            chk(
                f"the gate review report states the {condition_id} verdict",
                condition_id in gate_doc,
            )
        # A condition that cannot be evaluated must be recorded as such, never
        # silently passed.
        for condition_id in ("K2", "K5"):
            chk(
                f"the {condition_id} condition is recorded as not evaluable",
                conditions.get(condition_id, {}).get("status") == "not_evaluable",
                str(conditions.get(condition_id, {}).get("status")),
            )
            chk(
                f"the gate review report does not pass {condition_id} silently",
                "not evaluable" in gate_doc.lower(),
            )
        chk(
            "the K4 condition fired for the systemic-drug reading",
            conditions.get("K4", {}).get("status") == "fired",
            str(conditions.get("K4", {}).get("status")),
        )
        # The headline has to agree with the verdicts table. A document whose
        # first line says one condition has fired while the table below says
        # three is exactly the drift a reader cannot see, and this one sat
        # here because the table was updated and the prose was not.
        fired = sum(
            1 for c in conditions.values() if c.get("status") == "fired"
        )
        untested = sum(
            1 for c in conditions.values() if c.get("status") == "not_evaluable"
        )
        words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
        chk(
            "the gate review headline counts the conditions that have fired",
            f"{words[fired]} conditions have fired" in gate_doc,
            f"{fired} fired",
        )
        chk(
            "the gate review headline counts the conditions that cannot be tested",
            f"{words[untested]} cannot yet be tested" in gate_doc,
            f"{untested} not evaluable",
        )
        # And the qualification that changed the plasma arm has to be in the
        # document, not only in the audit it came from.
        chk(
            "the gate review records the leukocyte-audit qualification",
            "no leukocyte compartment" in gate_doc
            and "LEUKOCYTE-AUDIT.md" in gate_doc,
        )
        # The two documents a reader meets first must not carry the
        # pre-audit framing, where a plasma readout was named as surviving.
        # They each contradicted their own leukocyte-audit section.
        for path, name in (
            (Path("README.md"), "the README"),
            (Path("docs/ROADMAP.md"), "the roadmap"),
        ):
            if path.exists():
                text = path.read_text()
                chk(
                    f"{name} does not present the pre-audit readout as surviving",
                    "readout is now named" not in text,
                )
        if Path("README.md").exists():
            chk(
                "the README states that K3 has fired",
                "K1, K3 and K4 have fired" in Path("README.md").read_text(),
            )
        # The per-configuration numbers in the report must match the artefact.
        for verdict in gate["k1_k3_detail"]:
            label = f"{verdict['dataset']} / {verdict['channel']}"
            auc = f"{verdict['auc_at_operating_point']:.4f}"
            chk(
                f"the gate review report quotes the {label} enrichment AUC",
                auc in gate_doc,
                f"{label} {auc}",
            )
        for condition in gate["conditions"]:
            for fired in condition.get("fired_for") or []:
                dataset, _, channel = fired.partition(" / ")
                chk(
                    f"the gate review report names {fired} as firing for {condition['id']}",
                    dataset in gate_doc and channel in gate_doc,
                    fired,
                )
        chk(
            "the gate review states that K1 and K3 rest on a model-based "
            "projection rather than a plasma measurement",
            "not a plasma measurement" in gate_doc
            or "model-based projection" in gate_doc,
        )
        chk(
            "the gate review says what would change each verdict",
            "would change" in gate_doc.lower(),
        )
        chk(
            "the gate review points at the full configuration matrix",
            "gate_matrix.tsv" in gate_doc,
        )
        # The report's own configuration table must agree with the artefact in
        # both directions: every number, and every fire/pass verdict. A report
        # that calls a configuration a pass where the artefact says it fires is
        # the drift this repository exists to prevent, and the earlier
        # "is the number present somewhere" check does not catch it.
        table = parse_markdown_table(
            gate_doc, "### The configurations that matter"
        )
        chk(
            "the gate review report has the configuration table",
            len(table) > 1,
            f"{len(table)} rows",
        )
        if len(table) > 1:
            header = [c.replace("*", "").strip() for c in table[0]]
            expected_header = [
                "Dataset",
                "Channel",
                "Tissue fold",
                "State fraction",
                "Bulk elevation",
                "AUC at 200k× / 200",
                "K1",
                "K3",
            ]
            chk(
                "the gate review configuration table has the expected columns",
                header == expected_header,
                str(header),
            )
            if header == expected_header:
                measured = {
                    (m["dataset"], m["channel"]): m
                    for m in gate["measured_parameters"]
                }
                verdicts = {
                    (v["dataset"], v["channel"]): v
                    for v in gate["k1_k3_detail"]
                }
                fired = {
                    c["id"]: set(c.get("fired_for") or [])
                    for c in gate["conditions"]
                }
                for row in table[1:]:
                    if len(row) != len(header):
                        continue
                    dataset = row[0].replace("*", "").strip()
                    channel = row[1].replace("*", "").strip()
                    key = f"{dataset} / {channel}"
                    pair = (dataset, channel)
                    chk(
                        f"the gate review table's {key} is recorded in the artefact",
                        pair in measured and pair in verdicts,
                        key,
                    )
                    if pair not in measured or pair not in verdicts:
                        continue
                    m = measured[pair]
                    v = verdicts[pair]
                    for name, value, decimals in (
                        ("Tissue fold", m["abundance_fold_state_vs_tumour"], 3),
                        ("State fraction", m["state_fraction"], 3),
                        ("Bulk elevation", m["bulk_elevation"], 3),
                    ):
                        cell = _num_or_none(row[header.index(name)])
                        chk(
                            f"the gate review table's {key} {name} matches the artefact",
                            cell is not None
                            and _close_rounded(cell, value, decimals),
                            f"{row[header.index(name)]} vs {value}",
                        )
                    auc_cell = _num_or_none(row[header.index("AUC at 200k× / 200")])
                    chk(
                        f"the gate review table's {key} AUC matches the artefact",
                        auc_cell is not None
                        and _close_rounded(
                            auc_cell, v["auc_at_operating_point"], 4
                        ),
                        f"{row[header.index('AUC at 200k× / 200')]} "
                        f"vs {v['auc_at_operating_point']}",
                    )
                    for condition_id in ("K1", "K3"):
                        cell = row[header.index(condition_id)]
                        cell = cell.replace("*", "").strip().lower()
                        artefact_fires = key in fired.get(condition_id, set())
                        chk(
                            f"the gate review table's {key} {condition_id} verdict "
                            "matches the artefact",
                            (cell == "fire") == artefact_fires,
                            f"report says {cell!r}, artefact fires={artefact_fires}",
                        )

    # --- the per-patient audit must agree with its artefacts, cell by cell ---
    audit_artefact = Path("results/per_patient_audit/per_patient_audit.json")
    folds_artefact = Path("results/per_library_folds/per_library_folds.json")
    audit_doc = Path("docs/PER-PATIENT-AUDIT.md")
    chk("the per-patient audit artefact exists", audit_artefact.exists())
    chk("the per-library folds artefact exists", folds_artefact.exists())
    chk("the per-patient audit report exists", audit_doc.exists())
    if (
        audit_artefact.exists()
        and folds_artefact.exists()
        and audit_doc.exists()
    ):
        audit = json.loads(audit_artefact.read_text())
        folds = json.loads(folds_artefact.read_text())
        text = audit_doc.read_text()

        def _cell_number(cell: str) -> float | None:
            return _num_or_none(cell)

        def _cell_is_na(cell: str) -> bool:
            return cell.replace("*", "").strip().lower() in {"n/a", "na", "-"}

        def _check_number(
            label: str, cell: str, expected: float | None, decimals: int
        ) -> None:
            if expected is None:
                chk(
                    f"the per-patient audit reports {label} as not available",
                    _cell_is_na(cell),
                    cell,
                )
                return
            value = _cell_number(cell)
            chk(
                f"the per-patient audit's {label} matches the artefact",
                value is not None
                and _close_rounded(value, expected, decimals),
                f"{cell} vs {expected}",
            )

        def _check_integer(label: str, cell: str, expected: int) -> None:
            value = _cell_number(cell)
            chk(
                f"the per-patient audit's {label} matches the artefact",
                value is not None and int(round(value)) == expected,
                f"{cell} vs {expected}",
            )

        def _check_text(label: str, cell: str, expected: str) -> None:
            cleaned = cell.replace("*", "").strip()
            chk(
                f"the per-patient audit's {label} matches the artefact",
                cleaned == expected,
                f"{cleaned!r} vs {expected!r}",
            )

        # --- table 1: the measurement layer ---
        libraries = {
            (row["dataset"], row["accession"]): row
            for row in folds["per_library"]
        }
        table = parse_markdown_table(text, "## 2. The measurement layer")
        chk(
            "the per-patient audit has the measurement table",
            len(table) > 1,
            f"{len(table)} rows",
        )
        seen_libraries: set[tuple[str, str]] = set()
        if len(table) > 1:
            header = [c.replace("*", "").strip() for c in table[0]]
            expected_header = [
                "Dataset",
                "Library",
                "Site",
                "State cells",
                "State fraction",
                "KCNN4 fold",
                "PIEZO1 fold",
            ]
            chk(
                "the per-patient audit measurement table has the expected columns",
                header == expected_header,
                str(header),
            )
            if header == expected_header:
                for row in table[1:]:
                    if len(row) != len(header):
                        continue
                    dataset = row[0].replace("*", "").strip()
                    accession = row[1].replace("*", "").strip()
                    key = (dataset, accession)
                    seen_libraries.add(key)
                    chk(
                        f"the per-patient audit table's {dataset} / {accession} is "
                        "in the folds artefact",
                        key in libraries,
                        str(key),
                    )
                    if key not in libraries:
                        continue
                    library = libraries[key]
                    _check_text(
                        f"{dataset} / {accession} site",
                        row[2],
                        library["label"],
                    )
                    _check_integer(
                        f"{dataset} / {accession} state cells", row[3], library["n_state"]
                    )
                    _check_number(
                        f"{dataset} / {accession} state fraction",
                        row[4],
                        library["state_fraction"],
                        4,
                    )
                    for column, gene in (("KCNN4 fold", "KCNN4"), ("PIEZO1 fold", "PIEZO1")):
                        entry = library["channels"].get(gene, {})
                        _check_number(
                            f"{dataset} / {accession} {gene} fold",
                            row[header.index(column)],
                            entry.get("linear_fold"),
                            3,
                        )
                chk(
                    "the per-patient audit measurement table covers every library",
                    seen_libraries == set(libraries),
                    f"{len(seen_libraries)} of {len(libraries)}",
                )

        # --- table 2: the projection at the operating point ---
        records = {
            (r["dataset"], r["accession"], r["channel"]): r
            for r in audit["per_library"]
        }
        table = parse_markdown_table(text, "## 3. The projection layer")
        chk(
            "the per-patient audit has the projection table",
            len(table) > 1,
            f"{len(table)} rows",
        )
        seen_records: set[tuple[str, str, str]] = set()
        if len(table) > 1:
            header = [c.replace("*", "").strip() for c in table[0]]
            expected_header = [
                "Dataset",
                "Library",
                "Channel",
                "Fold",
                "State fraction",
                "AUC",
                "K1",
                "K3",
                "MRD sensitivity",
                "Specificity",
                "PPV",
                "AUC min (sweep)",
                "AUC max (sweep)",
            ]
            chk(
                "the per-patient audit projection table has the expected columns",
                header == expected_header,
                str(header),
            )
            if header == expected_header:
                for row in table[1:]:
                    if len(row) != len(header):
                        continue
                    dataset = row[0].replace("*", "").strip()
                    accession = row[1].replace("*", "").strip()
                    channel = row[2].replace("*", "").strip()
                    key = (dataset, accession, channel)
                    seen_records.add(key)
                    label = f"{dataset} / {accession} / {channel}"
                    chk(
                        f"the per-patient audit table's {label} is in the artefact",
                        key in records,
                        str(key),
                    )
                    if key not in records:
                        continue
                    record = records[key]
                    inputs = record["inputs"]
                    operating = record["operating_point"]
                    sweep = record["persistent_sensitivity"]
                    _check_number(
                        f"{label} fold", row[3], inputs["abundance_fold"], 3
                    )
                    _check_number(
                        f"{label} state fraction",
                        row[4],
                        inputs["state_fraction"],
                        4,
                    )
                    _check_number(f"{label} AUC", row[5], operating["auc"], 4)
                    _check_text(
                        f"{label} K1 verdict",
                        row[6],
                        "fire" if operating["k1_fired"] else "pass",
                    )
                    _check_text(
                        f"{label} K3 verdict",
                        row[7],
                        "fire" if operating["k3_fired"] else "pass",
                    )
                    _check_number(
                        f"{label} MRD sensitivity",
                        row[8],
                        operating["mrd_sensitivity"],
                        4,
                    )
                    _check_number(
                        f"{label} specificity",
                        row[9],
                        operating["mrd_specificity_vs_responders"],
                        4,
                    )
                    _check_number(
                        f"{label} PPV",
                        row[10],
                        operating["ppv_within_mrd_positive"],
                        4,
                    )
                    _check_number(
                        f"{label} AUC sweep minimum",
                        row[11],
                        min(entry["auc"] for entry in sweep),
                        4,
                    )
                    _check_number(
                        f"{label} AUC sweep maximum",
                        row[12],
                        max(entry["auc"] for entry in sweep),
                        4,
                    )
                chk(
                    "the per-patient audit projection table covers every record",
                    seen_records == set(records),
                    f"{len(seen_records)} of {len(records)}",
                )

        # --- table 3: the full depth x panel-size grid ---
        depths = audit["audit"]["depths"]
        loci = audit["audit"]["loci"]
        table = parse_markdown_table(text, "## 4. The full depth")
        chk(
            "the per-patient audit has the full grid table",
            len(table) > 1,
            f"{len(table)} rows",
        )
        if len(table) > 1:
            header = [c.replace("*", "").strip() for c in table[0]]
            expected_header = ["Dataset", "Library", "Channel"] + [
                f"{depth // 1000}k/{locus}" for depth in depths for locus in loci
            ]
            chk(
                "the per-patient audit grid table has the expected columns",
                header == expected_header,
                str(header),
            )
            if header == expected_header:
                seen_grid: set[tuple[str, str, str]] = set()
                for row in table[1:]:
                    if len(row) != len(header):
                        continue
                    key = (
                        row[0].replace("*", "").strip(),
                        row[1].replace("*", "").strip(),
                        row[2].replace("*", "").strip(),
                    )
                    seen_grid.add(key)
                    label = " / ".join(key)
                    chk(
                        f"the per-patient audit grid's {label} is in the artefact",
                        key in records,
                        str(key),
                    )
                    if key not in records:
                        continue
                    grid = records[key]["grid"]
                    index = 3
                    for depth in depths:
                        for locus in loci:
                            cell = next(
                                g
                                for g in grid
                                if g["sequencing_depth"] == depth
                                and g["total_loci"] == locus
                            )
                            _check_number(
                                f"{label} AUC at {depth}x/{locus} loci",
                                row[index],
                                cell["auc"],
                                4,
                            )
                            index += 1
                chk(
                    "the per-patient audit grid table covers every record",
                    seen_grid == set(records),
                    f"{len(seen_grid)} of {len(records)}",
                )

        # --- table 4: the summary by configuration ---
        summaries = {
            (s["dataset"], s["channel"]): s for s in audit["summaries"]
        }
        table = parse_markdown_table(text, "## 5. What the configurations say")
        chk(
            "the per-patient audit has the summary table",
            len(table) > 1,
            f"{len(table)} rows",
        )
        seen_summaries: set[tuple[str, str]] = set()
        if len(table) > 1:
            header = [c.replace("*", "").strip() for c in table[0]]
            expected_header = [
                "Dataset",
                "Channel",
                "Libraries",
                "Fold computable",
                "Fold > 1",
                "Clears K3",
                "Fires K1",
                "AUC min",
                "AUC median",
                "AUC max",
                "State fraction median",
            ]
            chk(
                "the per-patient audit summary table has the expected columns",
                header == expected_header,
                str(header),
            )
            if header == expected_header:
                for row in table[1:]:
                    if len(row) != len(header):
                        continue
                    key = (
                        row[0].replace("*", "").strip(),
                        row[1].replace("*", "").strip(),
                    )
                    seen_summaries.add(key)
                    label = " / ".join(key)
                    chk(
                        f"the per-patient audit summary's {label} is in the artefact",
                        key in summaries,
                        str(key),
                    )
                    if key not in summaries:
                        continue
                    summary = summaries[key]
                    aucs = summary["auc_at_operating_point"]
                    for column, expected in (
                        ("Libraries", summary["n_libraries"]),
                        ("Fold computable", summary["n_fold_computable"]),
                        ("Fold > 1", summary["n_fold_above_one"]),
                        ("Clears K3", summary["n_clearing_k3"]),
                        ("Fires K1", summary["n_firing_k1"]),
                    ):
                        _check_integer(
                            f"{label} {column}", row[header.index(column)], expected
                        )
                    _check_number(
                        f"{label} AUC min", row[header.index("AUC min")], aucs["min"], 4
                    )
                    _check_number(
                        f"{label} AUC median",
                        row[header.index("AUC median")],
                        aucs["median"],
                        4,
                    )
                    _check_number(
                        f"{label} AUC max", row[header.index("AUC max")], aucs["max"], 4
                    )
                    _check_number(
                        f"{label} state fraction median",
                        row[header.index("State fraction median")],
                        summary["state_fraction"]["median"],
                        4,
                    )
                chk(
                    "the per-patient audit summary table covers every configuration",
                    seen_summaries == set(summaries),
                    f"{len(seen_summaries)} of {len(summaries)}",
                )

        # --- table 5: the pooled fold against the per-library folds ---
        composition = folds["composition"]
        pooled = {
            (dataset, gene): record
            for dataset, genes in folds["control"].items()
            for gene, record in genes["channels"].items()
        }
        table = parse_markdown_table(text, "## 6. Why the pooled numbers")
        chk(
            "the per-patient audit has the composition table",
            len(table) > 1,
            f"{len(table)} rows",
        )
        seen_composition: set[tuple[str, str]] = set()
        if len(table) > 1:
            header = [c.replace("*", "").strip() for c in table[0]]
            expected_header = [
                "Dataset",
                "Channel",
                "Pooled fold",
                "Per-library fold median",
                "Per-library fold min",
                "Per-library fold max",
                "Libraries with fold > 1",
                "Pooled fold with one library removed: min",
                "max",
            ]
            chk(
                "the per-patient audit composition table has the expected columns",
                header == expected_header,
                str(header),
            )
            if header == expected_header:
                for row in table[1:]:
                    if len(row) != len(header):
                        continue
                    key = (
                        row[0].replace("*", "").strip(),
                        row[1].replace("*", "").strip(),
                    )
                    seen_composition.add(key)
                    label = " / ".join(key)
                    chk(
                        f"the per-patient audit composition's {label} is in the artefact",
                        key[1] in composition.get(key[0], {}),
                        str(key),
                    )
                    if key[1] not in composition.get(key[0], {}):
                        continue
                    record = composition[key[0]][key[1]]
                    _check_number(
                        f"{label} pooled fold",
                        row[2],
                        pooled[key]["published_linear_fold"],
                        4,
                    )
                    _check_number(
                        f"{label} per-library fold median",
                        row[3],
                        record["per_library_fold_median"],
                        4,
                    )
                    _check_number(
                        f"{label} per-library fold min",
                        row[4],
                        record["per_library_fold_min"],
                        4,
                    )
                    _check_number(
                        f"{label} per-library fold max",
                        row[5],
                        record["per_library_fold_max"],
                        4,
                    )
                    _check_text(
                        f"{label} libraries with fold above one",
                        row[6],
                        f"{record['n_libraries_with_fold_above_one']}/"
                        f"{record['n_libraries_with_fold_computable']}",
                    )
                    _check_number(
                        f"{label} leave-one-out pooled fold minimum",
                        row[7],
                        record["leave_one_library_out_min"],
                        4,
                    )
                    _check_number(
                        f"{label} leave-one-out pooled fold maximum",
                        row[8],
                        record["leave_one_library_out_max"],
                        4,
                    )
                expected_composition = {
                    (dataset, gene)
                    for dataset, genes in composition.items()
                    for gene in genes
                }
                chk(
                    "the per-patient audit composition table covers every channel",
                    seen_composition == expected_composition,
                    f"{len(seen_composition)} of {len(expected_composition)}",
                )

        # --- the controls, and the prose that quotes them ---
        control = audit["control"]
        chk(
            "the per-patient audit's pooled control reproduces the gate review",
            control["all_match"] is True,
            str(control["all_match"]),
        )
        for entry in control["entries"]:
            _check_number(
                f"the control AUC for {entry['dataset']} / {entry['channel']}",
                f"{entry['recomputed_auc_at_operating_point']:.6f}",
                entry["recomputed_auc_at_operating_point"],
                6,
            )
        for entry in folds["control"].values():
            chk(
                "the per-library folds' pooled control reproduces the published "
                "state-expression artefacts",
                entry["all_channels_match"] is True,
                str(entry["all_channels_match"]),
            )
        for dataset, genes in folds["per_library_sign_counts"].items():
            for gene, record in genes.items():
                if record["published_above_one"] is None:
                    continue
                chk(
                    f"the per-library detection-ratio signs for {dataset} / {gene} "
                    "reproduce the published counts",
                    record["matches"] is True,
                    str(record),
                )
        for claim in (
            "0.706545",
            "0.694505",
            "0.992862",
            "0.4658",
            "2,482",
            "2,872",
            "86.4%",
            "0.0093",
            "0.2421",
            "0.0091",
            "0.5888",
            "1.3702",
            "2.8122",
            "2.8094",
            "6.2977",
            "0.9491",
            "0.9991",
            "0.583",
            "2.267",
            "3.310",
        ):
            chk(
                f"the per-patient audit report quotes {claim}",
                claim in text,
            )
        chk(
            "the per-patient audit says the pooled number may not describe a patient",
            "does not describe a patient" in text
            or "not describe a patient" in text
            or "do not describe a patient" in text,
        )
        chk(
            "the per-patient audit keeps the projection's assumption visible",
            "never measured" in text or "has never been measured" in text,
        )

    # --- the data-access applications must agree with their artefacts ---
    tracker_artefact = Path("results/application_tracker/application_tracker.json")
    tracker_doc = Path("docs/DATA-ACCESS-APPLICATIONS.md")
    chk("the application tracker artefact exists", tracker_artefact.exists())
    chk("the data-access applications document exists", tracker_doc.exists())
    if tracker_artefact.exists() and tracker_doc.exists():
        tracker = json.loads(tracker_artefact.read_text())
        tracker_text = tracker_doc.read_text()

        applications = {
            row["Application"]: row for row in tracker["applications"]
        }
        chk(
            "the tracker covers both applications",
            {"PLCO-DATA", "PLCO-EEMS", "TZL-EGA", "TZL-DIRECT"} == set(applications),
            str(sorted(applications)),
        )
        chk(
            "the tracker records every step of both applications",
            len(tracker["steps"]) >= 20,
            str(len(tracker["steps"])),
        )
        chk(
            "the tracker records the shared prerequisites",
            len(tracker["prerequisites"]) >= 8,
            str(len(tracker["prerequisites"])),
        )
        for application in ("PLCO-DATA", "PLCO-EEMS", "TZL-EGA", "TZL-DIRECT"):
            chk(
                f"the tracker document names {application}",
                application in tracker_text,
            )

        # The route finding is load-bearing: if the EGA deposit turns up, the
        # document has to change, and this check has to change with it.
        chk(
            "the document states that the EGA route is unverified",
            applications["TZL-EGA"]["Route verified"].startswith("no"),
            applications["TZL-EGA"]["Route verified"],
        )
        chk(
            "the document says the EGA catalogue holds no Taizhou deposit",
            "10,814" in tracker_text and "21,922" in tracker_text,
        )
        facts = {row["Fact"]: row["Value"] for row in tracker["external_facts"]}
        chk(
            "the tracker records that no EGA record matches the study",
            any(
                "matching Taizhou" in fact and value == "0"
                for fact, value in facts.items()
            ),
            str(facts),
        )

        # Neither application has been submitted, and the document has to say
        # so: a data-access request is an institutional act, and the record
        # of it belongs to the person who makes it.
        chk(
            "the document states that neither application has been submitted",
            "Neither application has been submitted" in tracker_text,
        )
        chk(
            "the document states that neither cohort is post-treatment",
            "Neither PLCO nor TZL is a" in tracker_text,
        )

        # The scoping inquiry is the one thing that has been sent, and the
        # tracker has to say so, with the same date the sending record
        # carries and the same absence of a reference number.
        steps = {
            (row["Application"], row["Step"]): row for row in tracker["steps"]
        }
        inquiry_step = steps.get(
            ("PLCO-DATA", "Send the scoping inquiry to CDAS (subject: PLCO)")
        )
        chk(
            "the tracker records the scoping inquiry as sent",
            inquiry_step is not None and inquiry_step["Status"].startswith("done"),
            inquiry_step["Status"] if inquiry_step else "missing",
        )
        chk(
            "the tracker dates the scoping inquiry",
            inquiry_step is not None and "2026-11-11" in inquiry_step["Status"],
            inquiry_step["Status"] if inquiry_step else "missing",
        )
        chk(
            "the tracker says the form issued no inquiry number",
            inquiry_step is not None and "no inquiry number" in inquiry_step["Status"],
            inquiry_step["Status"] if inquiry_step else "missing",
        )
        chk(
            "the document records that the scoping inquiry was sent",
            "the scoping inquiry, on 2026-11-11" in tracker_text,
        )
        fact_rows = {row["Fact"]: row for row in tracker["external_facts"]}
        chk(
            "the tracker records that the contact form issues no inquiry number",
            any(
                "inquiry reference number" in fact
                and fact_rows[fact]["Value"].startswith("none")
                and fact_rows[fact]["Verified on"] == "2026-11-11"
                for fact in fact_rows
            ),
            str(sorted(fact_rows)),
        )
        chk(
            "the tracker records that three scoping inquiries were sent",
            any(
                "Scoping inquiries sent to CDAS" in fact
                and fact_rows[fact]["Value"].startswith("3")
                and fact_rows[fact]["Verified on"] == "2026-11-11"
                for fact in fact_rows
            ),
            str(sorted(fact_rows)),
        )
        # The EEMS route is the one that does not require an institutional
        # PI, and its deadline means something different from the one the
        # tracker used to state. Both are load-bearing, so both are checked.
        chk(
            "the tracker says the EEMS preliminary application is rolling",
            any(
                "rolling" in step["Status"]
                for step in tracker["steps"]
                if step["Step"] == "Confirm the EEMS preliminary application deadline"
            ),
            str(
                [
                    step["Status"]
                    for step in tracker["steps"]
                    if step["Step"]
                    == "Confirm the EEMS preliminary application deadline"
                ]
            ),
        )
        chk(
            "the tracker has a separate final-application step for Feb 18",
            any(
                "final application" in step["Step"]
                and "2026-11-11" not in step["Status"]
                for step in tracker["steps"]
            )
            and any(
                "Feb 18" in step["Step"] for step in tracker["steps"]
            ),
            str([step["Step"] for step in tracker["steps"]]),
        )
        # The document is line-wrapped, so the phrases are matched against a
        # whitespace-normalised copy: a rule that is quoted correctly but
        # broken across two lines is still there.
        flat = " ".join(tracker_text.split())
        for phrase in (
            "your own source of funding",
            "entire scientific community",
            "accepted on a rolling basis",
            "higher bar for approval",
            "before they are provided with phenotype data",
        ):
            chk(
                f"the data-access document records the EEMS rule {phrase!r}",
                phrase in flat,
            )
        for figure in ("2.9 million", "435 PLCO cases", "3,773 cores", "446 NLST-LSS"):
            chk(
                f"the data-access document records the PLCO specimen figure "
                f"{figure!r}",
                figure in flat,
            )
        # Where the pool of people who can be the PI comes from has to be
        # recorded, because it is what turns "find a host" from a vague
        # intention into a list that can be worked through.
        chk(
            "the data-access document records where the host pool comes from",
            "approved-projects/plco/" in flat
            and "bio_types=plco_bio_eems" in flat,
        )
        chk(
            "the data-access document records the pilot precedent",
            "Analytical Suitability and Storage-Stability Pilot" in flat,
        )
        # A collaborator named on the application is a smaller ask than a
        # host PI, and it is the form to aim for when the collaboration is
        # scientific rather than administrative.
        chk(
            "the data-access document records that a collaborator need not be the PI",
            "Investigative Team" in flat and "recuse" in flat,
        )

        # The host invitation is outbound correspondence rather than a
        # submission document, so it is checked here instead of in the
        # package checker. It has to say what it is, and the figures it
        # quotes have to be this repository's own.
        host_invitation = Path("docs/HOST-INVITATION.md")
        chk("the host invitation document exists", host_invitation.exists())
        if host_invitation.exists():
            invitation = host_invitation.read_text()
            chk(
                "the host invitation is marked as a draft, not sent",
                "draft, not sent" in invitation,
            )
            begin = "<!-- BEGIN HOST LETTER -->"
            end = "<!-- END HOST LETTER -->"
            chk(
                "the host invitation delimits the letter",
                begin in invitation and end in invitation,
            )
            if begin in invitation and end in invitation:
                letter = invitation.split(begin)[1].split(end)[0].strip()
                chk("the host invitation is plain text", "**" not in letter)
                chk(
                    "the host invitation has one placeholder, the host's name",
                    letter.count("[HOST]") == 1,
                    str(letter.count("[HOST]")),
                )
                chk(
                    "the host invitation is short enough to read",
                    len(letter) <= 6_000,
                    str(len(letter)),
                )
                # The letter has to tell the recipient what they would be
                # taking on, and has to be honest about the requester's
                # standing, or it wastes the one thing a professor gives a
                # stranger: their attention.
                for phrase in (
                    "Principal Investigator",
                    "Register on CDAS",
                    "submit the proposal",
                    "renewal",
                    "close-out",
                    "DocuSign",
                    "18 February",
                    "one to four weeks",
                    "I hold no current institutional appointment",
                ):
                    chk(
                        f"the host invitation tells the PI about {phrase!r}",
                        phrase in letter,
                    )
                for figure in ("2.97", "20 of 23", "7 of 7", "155,000"):
                    chk(
                        f"the host invitation quotes the repository's figure "
                        f"{figure!r}",
                        figure in letter,
                    )

        # The numbers the applications are justified by are this repository's
        # own measurements, and they have to match those artefacts.
        folds_path = Path("results/per_library_folds/per_library_folds.json")
        if folds_path.exists() and audit_artefact.exists():
            folds_data = json.loads(folds_path.read_text())
            nsclc = folds_data["composition"]["NSCLC"]["KCNN4"]
            chk(
                "the document quotes the NSCLC within-tumour fold yield",
                f"{nsclc['n_libraries_with_fold_above_one']} of "
                f"{nsclc['n_libraries_with_fold_computable']}" in tracker_text,
                f"{nsclc['n_libraries_with_fold_above_one']}/"
                f"{nsclc['n_libraries_with_fold_computable']}",
            )
            mrd = [
                r
                for r in audit["per_library"]
                if r["dataset"] == "NSCLC" and r["treatment"] == "osi_mrd"
            ]
            clearing = sum(
                1 for r in mrd if not r["operating_point"]["k3_fired"]
            )
            chk(
                "the document quotes the residual-disease libraries that clear K3",
                f"{clearing} of {len(mrd)}" in tracker_text,
                f"{clearing}/{len(mrd)}",
            )
            chk(
                "the document does not claim a residual-disease library fails",
                "7 of 7" in tracker_text
                or f"{clearing} of {len(mrd)}" in tracker_text,
            )

    # --- the PLCO CDAS submission package must agree with its artefacts ---
    package = Path("docs/plco-cdas-submission-package")
    package_files = (
        "README.md",
        "01-project-details.md",
        "02-proposal-narrative.md",
        "03-pi-cover-sheet.md",
        "04-signing-official-letter.md",
        "05-documents-checklist.md",
        "06-submission-runbook.md",
        "07-scoping-inquiry.md",
    )
    for name in package_files:
        chk(f"the submission package carries {name}", (package / name).exists())
    if all((package / name).exists() for name in package_files):
        details = (package / "01-project-details.md").read_text()
        narrative = (package / "02-proposal-narrative.md").read_text()
        cover = (package / "03-pi-cover-sheet.md").read_text()
        letter = (package / "04-signing-official-letter.md").read_text()
        package_text = "\n".join(
            (package / name).read_text() for name in package_files
        )

        # CDAS caps the project description at 500 words.
        if "<!-- BEGIN PROJECT DESCRIPTION -->" in details and (
            "<!-- END PROJECT DESCRIPTION -->" in details
        ):
            description = details.split("<!-- BEGIN PROJECT DESCRIPTION -->")[1].split(
                "<!-- END PROJECT DESCRIPTION -->"
            )[0]
            word_count = len(description.split())
            chk(
                "the submission package's project description is within CDAS's "
                "500-word cap",
                word_count <= 500,
                str(word_count),
            )
        else:
            chk(
                "the submission package marks out the project description",
                False,
                "the description markers are missing",
            )

        # Both documents that someone signs have to carry a signature block.
        chk(
            "the PI cover sheet carries a signature block",
            "## 4. Signature" in cover and "Principal Investigator" in cover,
        )
        chk(
            "the Signing Official letter carries a signature block",
            "## 5. Signature" in letter and "Signing Official" in letter,
        )

        # The package's justification is this repository's own measurements.
        folds_path = Path("results/per_library_folds/per_library_folds.json")
        if folds_path.exists():
            folds_data = json.loads(folds_path.read_text())
            nsclc = folds_data["composition"]["NSCLC"]["KCNN4"]
            chk(
                "the submission package quotes the NSCLC within-tumour fold yield",
                f"{nsclc['n_libraries_with_fold_above_one']} of "
                f"{nsclc['n_libraries_with_fold_computable']}" in narrative,
            )
        gate_path = Path("results/gate_review/gate_review.json")
        if gate_path.exists():
            gate = json.loads(gate_path.read_text())
            chk(
                "the submission package quotes the pre-specified thresholds",
                f"{gate['audit']['k1_auc_threshold']:.2f}" in package_text
                and f"{gate['audit']['k3_auc_threshold']:.2f}" in package_text,
            )
            chk(
                "the submission package quotes the electrical-channel allocation",
                f"{gate['audit']['electrical_fraction']:.0%}" in package_text,
            )

        # The constraints that shape the package must not be quietly dropped.
        for phrase in (
            "500 words",
            "Limited Data Set",
            "published on the CDAS website",
            "professor",
            "12 months",
            "DocuSign",
            "separate project proposal",
            "10,000 characters",
            "leave it empty",
            "Data Access/Availability",
            "Biospecimen Availability",
        ):
            chk(
                f"the submission package states {phrase!r}",
                phrase in package_text,
            )
        chk(
            "the submission package does not read as if it had been submitted",
            "Signed" not in cover.split("## 4. Signature")[0],
        )

        # The assay design the leukocyte audit forced: the channel transcript
        # has to be localised to the tumour, and both the proposal's summary
        # and its narrative have to say so.
        details_text = (package / "01-project-details.md").read_text()
        narrative_text = (package / "02-proposal-narrative.md").read_text()
        for phrase in (
            "somatic variant",
            "leukocyte reference",
            "tumour cfDNA fraction",
            "tumour-attributable",
        ):
            chk(
                f"the submission package's project details carry {phrase!r}",
                phrase in details_text,
            )
            chk(
                f"the submission package's narrative carries {phrase!r}",
                phrase in narrative_text,
            )
        chk(
            "the proposal states that the raw enrichment is a secondary analysis",
            "secondary" in narrative_text,
        )
        chk(
            "the proposal states that the projection is an upper bound",
            "upper bound" in narrative_text,
        )
        chk(
            "the matched primary tumour is a required element, not an optional one",
            "required, not optional" in details_text
            or "required, not optional" in narrative_text,
        )

        readme_path = Path("README.md")
        if readme_path.exists():
            chk(
                "the README links the submission package",
                "plco-cdas-submission-package" in readme_path.read_text(),
            )
        roadmap_path = Path("docs/ROADMAP.md")
        if roadmap_path.exists():
            chk(
                "the roadmap links the submission package",
                "plco-cdas-submission-package" in roadmap_path.read_text(),
            )

    # --- the leukocyte audit must agree with its artefacts ---
    leuk_artefact = Path("results/leukocyte_audit/leukocyte_audit.json")
    leuk_doc = Path("docs/LEUKOCYTE-AUDIT.md")
    chk("the leukocyte audit artefact exists", leuk_artefact.exists())
    chk("the leukocyte audit report exists", leuk_doc.exists())
    if leuk_artefact.exists() and leuk_doc.exists():
        leuk = json.loads(leuk_artefact.read_text())
        leuk_text = leuk_doc.read_text()

        # The control: the audit's own code path has to reproduce the
        # published AUCs, or the sweep is not comparable with them.
        for entry in leuk["control"]:
            chk(
                f"the leukocyte audit's control reproduces the published "
                f"{entry['dataset']}/{entry['channel']} AUC",
                entry["matches"] is True,
                str(entry),
            )

        # The operating-point table.
        operating = parse_markdown_table(
            leuk_text, "### At the published operating point"
        )
        chk(
            "the leukocyte audit report has the operating-point table",
            len(operating) > 1,
            f"{len(operating)} rows",
        )
        if len(operating) > 1:
            header = [c.replace("*", "").strip() for c in operating[0]]
            expected_header = [
                "Configuration",
                "Leukocyte background",
                "Measured tumour share",
                "MRD-positive",
                "Raw AUC",
                "Oracle-corrected AUC",
            ]
            chk(
                "the leukocyte audit operating-point table has the expected "
                "columns",
                header == expected_header,
                str(header),
            )
            if header == expected_header:
                # The operating-point table is the one without a reference
                # set, so the rows it is checked against are those.
                by_key = {
                    (f"{r['dataset']} / {r['channel']}", r["leukocyte_fraction"]): r
                    for r in leuk["sweep"]
                    if r["tumour_share_multiplier"] == 1
                    and r["n_leukocyte_reference_loci"] == 0
                }
                seen = set()
                for row in operating[1:]:
                    cells = [c.replace("*", "").strip() for c in row]
                    if len(cells) != len(expected_header):
                        continue
                    label = cells[0]
                    fraction = float(cells[1])
                    seen.add((label, fraction))
                    record = by_key.get((label, fraction))
                    if record is None:
                        chk(
                            f"the leukocyte audit table's {label} is in the artefact",
                            False,
                            label,
                        )
                        continue
                    chk(
                        f"the leukocyte audit table's {label} leukocyte background "
                        "matches the artefact",
                        abs(float(cells[1]) - record["leukocyte_fraction"]) < 1e-9,
                        cells[1],
                    )
                    chk(
                        f"the leukocyte audit table's {label} raw AUC matches the "
                        "artefact",
                        abs(float(cells[4]) - record["auc_raw"]) < 5e-5,
                        cells[4],
                    )
                    chk(
                        f"the leukocyte audit table's {label} attributable AUC "
                        "matches the artefact",
                        abs(float(cells[5]) - record["auc_attributable"]) < 5e-5,
                        cells[5],
                    )
                chk(
                    "the leukocyte audit operating-point table covers every "
                    "configuration",
                    seen == set(by_key),
                    str(sorted(str(k) for k in seen)),
                )

        # The sweep table, cell by cell.
        sweep = parse_markdown_table(leuk_text, "## 5. The sweep, with the reference set")
        chk(
            "the leukocyte audit report has the sweep table",
            len(sweep) > 1,
            f"{len(sweep)} rows",
        )
        if len(sweep) > 1:
            records = [
                r
                for r in leuk["sweep"]
                if r["dataset"] == "NSCLC" and r["channel"] == "KCNN4"
            ]
            chk(
                "the leukocyte audit sweep table has a row for every NSCLC "
                "configuration",
                len(sweep) - 1 == len(records),
                f"{len(sweep) - 1} rows for {len(records)} records",
            )
            for row, record in zip(sweep[1:], records, strict=False):
                cells = [c.replace("*", "").strip() for c in row]
                if len(cells) < 8:
                    continue
                chk(
                    f"the leukocyte audit sweep row for x{record['tumour_share_multiplier']} "
                    f"leuk={record['leukocyte_fraction']:.2f} has the right "
                    "leukocyte background",
                    abs(float(cells[1]) - record["leukocyte_fraction"]) < 1e-9,
                    cells[1],
                )
                chk(
                    f"the leukocyte audit sweep row for x{record['tumour_share_multiplier']} "
                    f"leuk={record['leukocyte_fraction']:.2f} has the right "
                    "reference-set size",
                    abs(float(cells[2]) - record["n_leukocyte_reference_loci"])
                    < 1e-9,
                    cells[2],
                )
                chk(
                    f"the leukocyte audit sweep row for x{record['tumour_share_multiplier']} "
                    f"leuk={record['leukocyte_fraction']:.2f} has the right raw AUC",
                    abs(float(cells[5]) - record["auc_raw"]) < 5e-5,
                    cells[5],
                )
                chk(
                    f"the leukocyte audit sweep row for x{record['tumour_share_multiplier']} "
                    f"leuk={record['leukocyte_fraction']:.2f} has the right "
                    "oracle-corrected AUC",
                    abs(float(cells[6]) - record["auc_attributable"]) < 5e-5,
                    cells[6],
                )
                chk(
                    f"the leukocyte audit sweep row for x{record['tumour_share_multiplier']} "
                    f"leuk={record['leukocyte_fraction']:.2f} has the right "
                    "reference-corrected AUC",
                    abs(float(cells[7]) - record["auc_reference_corrected"]) < 5e-5,
                    cells[7],
                )

        # The tissue table, against the state-expression artefacts.
        tissue = parse_markdown_table(leuk_text, "## 2. The measurement")
        chk(
            "the leukocyte audit report has the tissue table",
            len(tissue) > 1,
            f"{len(tissue)} rows",
        )
        if len(tissue) > 1:
            for row in tissue[1:]:
                cells = [c.replace("*", "").strip() for c in row]
                if len(cells) < 6:
                    continue
                dataset, _, gene = cells[0].partition(" / ")
                path = Path(
                    "results/gse299684/state_expression.json"
                    if dataset == "SCLC"
                    else "results/gse353299/state_expression.json"
                )
                if not path.exists():
                    continue
                artefact = json.loads(path.read_text())
                primary = artefact["audit"]["primary_definition"]
                sweep_entry = next(
                    s
                    for s in artefact["state_definition_sweep"]
                    if s["definition"] == primary
                )
                channel = next(
                    c for c in sweep_entry["channels"] if c["gene"] == gene
                )
                chk(
                    f"the leukocyte audit tissue row for {dataset}/{gene} has the "
                    "right state-cell level",
                    abs(float(cells[1]) - channel["linear_mean_yap1_positive"])
                    < 5e-5,
                    cells[1],
                )
                chk(
                    f"the leukocyte audit tissue row for {dataset}/{gene} has the "
                    "right immune level",
                    abs(float(cells[3]) - channel["linear_mean_immune"]) < 5e-5,
                    cells[3],
                )
                chk(
                    f"the leukocyte audit tissue row for {dataset}/{gene} has the "
                    "right state-to-immune ratio",
                    abs(
                        float(cells[5])
                        - channel["linear_mean_yap1_positive"]
                        / channel["linear_mean_immune"]
                    )
                    < 5e-3,
                    cells[5],
                )

        # The claims the document makes, which the artefact has to support.
        for claim in (
            "byte-identical",
            "cannot survive",
            "inverts",
            "upper bound",
            "QC and tumour-fraction tool",
            "reference-corrected",
            "localisation rate",
        ):
            chk(
                f"the leukocyte audit report states that the readout {claim!r}",
                claim in leuk_text,
            )
        operating_rows = [
            r
            for r in leuk["sweep"]
            if r["dataset"] == "NSCLC"
            and r["channel"] == "KCNN4"
            and r["tumour_share_multiplier"] == 1
        ]
        by_fraction = {r["leukocyte_fraction"]: r for r in operating_rows}
        chk(
            "the leukocyte audit report quotes the published NSCLC AUC",
            f"{by_fraction[0.0]['auc_raw']:.4f}" in leuk_text,
        )
        chk(
            "the leukocyte audit report quotes the inverted NSCLC AUC",
            f"{by_fraction[0.5]['auc_raw']:.4f}" in leuk_text,
        )
        chk(
            "the leukocyte audit report quotes the attributable NSCLC AUC",
            f"{by_fraction[0.5]['auc_attributable']:.4f}" in leuk_text,
        )
        chk(
            "the leukocyte audit report links the per-patient audit",
            "PER-PATIENT-AUDIT.md" in leuk_text,
        )
        # The re-derived operating point: nothing in the search space clears K3.
        derivation_path = Path("results/leukocyte_audit/operating_point.json")
        chk(
            "the operating-point derivation artefact exists",
            derivation_path.exists(),
        )
        if derivation_path.exists():
            derivation = json.loads(derivation_path.read_text())
            chk(
                "the derivation searched a panel space rather than one point",
                len(derivation["frontier"]) >= 6,
                str(len(derivation["frontier"])),
            )
            chk(
                "the derivation reports whether anything clears K3",
                "anything_clears_k3" in derivation,
            )
            frontier_table = parse_markdown_table(
                leuk_text, "## 6. The re-derived operating point"
            )
            chk(
                "the leukocyte audit report has the frontier table",
                len(frontier_table) - 1 == len(derivation["frontier"]),
                f"{len(frontier_table) - 1} rows for "
                f"{len(derivation['frontier'])} frontier rows",
            )
            if len(frontier_table) - 1 == len(derivation["frontier"]):
                for row, record in zip(
                    frontier_table[1:], derivation["frontier"], strict=False
                ):
                    cells = [c.replace("*", "").strip() for c in row]
                    if len(cells) < 8:
                        continue
                    chk(
                        f"the frontier row for depth {record['depth']} matches "
                        "the artefact",
                        abs(float(cells[4]) - record["auc_raw"]) < 5e-5,
                        cells[4],
                    )
                    chk(
                        f"the frontier row for depth {record['depth']} matches "
                        "the artefact's reference-corrected AUC",
                        abs(float(cells[6]) - record["auc_reference_corrected"])
                        < 5e-5,
                        cells[6],
                    )

    # --- the plasma assay specification must agree with the artefacts ---
    spec_doc = Path("docs/PLASMA-ASSAY-SPECIFICATION.md")
    chk("the plasma assay specification exists", spec_doc.exists())
    if spec_doc.exists() and leuk_artefact.exists():
        spec_text = spec_doc.read_text()
        leuk = json.loads(leuk_artefact.read_text())
        operating = next(
            r
            for r in leuk["sweep"]
            if r["dataset"] == "NSCLC"
            and r["channel"] == "KCNN4"
            and r["tumour_share_multiplier"] == 1
            and r["leukocyte_fraction"] == 0.99
            and r["n_leukocyte_reference_loci"] == 0
        )
        chk(
            "the specification quotes the relapsing arm's tumour cfDNA share",
            f"{operating['median_tumour_cfDNA_share_relapsers']:.2e}" in spec_text,
            f"{operating['median_tumour_cfDNA_share_relapsers']:.2e}",
        )
        chk(
            "the specification quotes the non-relapsing arm's tumour cfDNA share",
            f"{operating['median_tumour_cfDNA_share_non_relapsers']:.2e}" in spec_text,
            f"{operating['median_tumour_cfDNA_share_non_relapsers']:.2e}",
        )
        chk(
            "the specification quotes the relapsing arm's enrichment noise",
            f"{operating['enrichment_noise_relapsers']:.1f}" in spec_text,
            f"{operating['enrichment_noise_relapsers']:.1f}",
        )
        chk(
            "the specification quotes the non-relapsing arm's enrichment noise",
            f"{operating['enrichment_noise_non_relapsers']:.0f}" in spec_text,
            f"{operating['enrichment_noise_non_relapsers']:.0f}",
        )
        # The design elements the audit forced.
        for phrase in (
            "cfRNA",
            "per molecule",
            "heterozygous germline SNP",
            "control and a normalisation check",
            "0.65",
            "0.98",
        ):
            chk(
                f"the assay specification states {phrase!r}",
                phrase in spec_text,
            )
        # The panel it specifies adds up.
        chk(
            "the specification's panel adds up to the published one",
            "150" in spec_text and "38" in spec_text and "12" in spec_text,
        )
        # The stop rules, and the thresholds that are the programme's own.
        for rule in ("S1", "S2", "S3", "S4", "S5", "S6"):
            chk(
                f"the assay specification carries the stop rule {rule}",
                f"**{rule}**" in spec_text,
            )
        # The scoping inquiry has to ask the three questions the
        # specification makes decisive, and stay inside the form's limit.
        inquiry_path = Path(
            "docs/plco-cdas-submission-package/07-scoping-inquiry.md"
        )
        if inquiry_path.exists():
            inquiry = inquiry_path.read_text()
            for phrase in (
                "How many participants were diagnosed with lung cancer",
                "How many have primary tumour tissue archived",
                "whole-exome sequencing",
                "whole-genome sequencing",
                "germline DNA sample",
                "more than one screening visit",
            ):
                chk(
                    f"the scoping inquiry asks {phrase!r}",
                    phrase in inquiry,
                )
            for tag in ("A", "B", "C"):
                begin = f"<!-- BEGIN MESSAGE {tag} -->"
                end = f"<!-- END MESSAGE {tag} -->"
                if begin not in inquiry or end not in inquiry:
                    chk(False, f"the scoping inquiry does not delimit message {tag}")
                    continue
                body = inquiry.split(begin)[1].split(end)[0].strip()
                chk(
                    f"scoping inquiry message {tag} is inside the form's "
                    "10,000-character limit",
                    len(body) <= 10_000,
                    str(len(body)),
                )
                chk(
                    f"scoping inquiry message {tag} is plain text",
                    "**" not in body,
                )
                chk(
                    f"scoping inquiry message {tag} has no unfilled field",
                    "[TO FILL:" not in body,
                )

            # The sending record has to bind the counts it quotes to the
            # text that was actually submitted, so that the record cannot
            # drift away from the messages.
            topics = {
                "A": "Data Access/Availability",
                "B": "Biospecimen Availability",
                "C": "Data Access/Availability",
            }
            for tag, topic in topics.items():
                begin = f"<!-- BEGIN MESSAGE {tag} -->"
                end = f"<!-- END MESSAGE {tag} -->"
                if begin not in inquiry or end not in inquiry:
                    chk(False, f"the scoping inquiry does not delimit message {tag}")
                    continue
                body = inquiry.split(begin)[1].split(end)[0].strip()
                rows = [
                    line.strip()
                    for line in inquiry.splitlines()
                    if line.strip().startswith(f"| {tag} |")
                ]
                if not rows:
                    chk(
                        False,
                        f"the scoping inquiry records the sending of message {tag}",
                    )
                    continue
                cells = [c.strip() for c in rows[0].strip("|").split("|")]
                chk(
                    f"the sending record for message {tag} names the subject",
                    len(cells) == 5 and cells[1] == "PLCO",
                    cells[1] if len(cells) > 1 else "",
                )
                chk(
                    f"the sending record for message {tag} names the topic",
                    len(cells) == 5 and cells[2] == topic,
                    cells[2] if len(cells) > 2 else "",
                )
                chk(
                    f"the sending record for message {tag} quotes the length of "
                    "the message that was sent",
                    len(cells) == 5 and cells[3] == str(len(body)),
                    f"recorded {cells[3] if len(cells) > 3 else ''}, "
                    f"actual {len(body)}",
                )
                chk(
                    f"the sending record for message {tag} carries the date it "
                    "was sent",
                    len(cells) == 5 and cells[4].startswith("2026-11-11"),
                    cells[4] if len(cells) > 4 else "",
                )
            chk(
                "the scoping inquiry records that the form issues no inquiry number",
                "no inquiry number" in inquiry,
            )
            chk(
                "the scoping inquiry records the confirmation the form returned",
                "Your message was sent successfully" in inquiry,
            )

        chk(
            "the assay specification is linked from the package",
            "PLASMA-ASSAY-SPECIFICATION.md"
            in (Path("docs/plco-cdas-submission-package/01-project-details.md").read_text()
                if Path("docs/plco-cdas-submission-package/01-project-details.md").exists()
                else ""),
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
