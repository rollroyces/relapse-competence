#!/usr/bin/env python3
"""Regenerate the gap audit report's revision-history table.

The table lists every commit that **modified the report**, oldest first.
Commit *subjects* survive a history rewrite, commit *hashes* do not -- so the
table is regenerated from the log rather than maintained by hand, and the
report names commits by subject wherever a commit is cited in prose.

Run it after any change to the report:

    python scripts/regenerate_revision_history.py

and check that the committed table still matches the log:

    python scripts/regenerate_revision_history.py --check

Scope
-----
Both commands use the same scope: the commits that modified the report, as
recorded by ``git log -- <report>``. A commit that leaves the report alone
does not appear in the table and does not make the table stale, so the check
does not have to be re-run for unrelated work.

Self-reference
--------------
The commit that carries the table cannot contain its own id, so the last row
is a placeholder standing for "the commit that last modified this report".
That produces two legitimate shapes:

* *pending* -- rows for every scoped commit so far, plus the placeholder.
  This is what the generator writes, and what a working tree holds between
  regenerating and committing.
* *committed* -- the same rows, minus the newest one, plus the placeholder.
  This is what the repository holds once the regenerated table is committed,
  because the new commit is then the newest scoped commit and is represented
  by the placeholder.

The check accepts either shape; anything else is drift.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPORT_PATH = "docs/GAP-AUDIT-BIOELECTRIC.md"

TABLE_HEADER = "| Commit | Change | Where the retracted wording now lives |\n|---|---|---|\n"

#: The row that stands for the commit carrying the table.
PLACEHOLDER_ROW = "| *(this commit)* | Revision history regenerated from the log | — |"

#: Subject -> what that commit changed. Subjects survive a history rewrite;
#: hashes do not, which is why this file is keyed on subjects. Every key must
#: match exactly one commit that modified the report; a key that matches
#: nothing means a commit was rewritten or removed, and the script says so
#: instead of silently dropping the description.
DESCRIPTIONS: dict[str, str] = {
    "Formal gap audit: bioelectric state x lung-cancer relapse competence":
        "**First publication of the gap audit. Its commit message was amended on "
        "2026-11-06** (see the note below).",
    "Audit corrections: parser reconciliation, false-positive attribution, G.3 accuracy":
        "Parser reconciliation; attribution corrected; G.3 rewritten; set-based "
        "comparison recommended. **Its commit message was amended on 2026-11-06.**",
    "Evidence the parser fix: identify and recover the four dropped book records":
        "The four dropped book records identified and recovered",
    "Close documentation drift after D1; extend the verifier to guard prose":
        "Documentation synchronised with the executed D1; verifier extended to "
        "guard prose. **Its commit message was amended on 2026-11-06.**",
    "Machine-checked disposition for the audit review findings":
        "Machine-generated findings disposition added",
    "Dual licence AGPL-3.0-or-later + commercial; stop restating retracted claims":
        "Licence migrated to AGPL-3.0-or-later plus commercial; retracted wording "
        "removed from the report body",
    "Two-sided proof of the audit findings, plus a revision history in the report":
        "Two-sided historical proof of each finding; revision history added to the report",
    "Amend two commit messages; make the commit reference resolve by content":
        "Two commit messages amended; the commit reference made to resolve by content",
    "Restore one commit subject; add a revision-history generator":
        "One commit subject restored; the revision-history generator added",
    "Remove the last two mentions of the withdrawn wording from the report":
        "The last two mentions of the withdrawn wording removed from the report",
}


def _git(*args: str) -> str:
    out = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    )
    return out.stdout


def _scoped_commits() -> list[tuple[str, str]]:
    """Every commit that modified the report, oldest first, as (sha, subject)."""
    out = _git("log", "--reverse", "--format=%H%x1f%s", "--", REPORT_PATH).strip()
    if not out:
        return []
    return [tuple(line.split("\x1f", 1)) for line in out.splitlines()]  # type: ignore[misc]


def _first_published_commit() -> str:
    """The commit that first added the report, resolved by content.

    Resolved rather than hardcoded: the history was rewritten, so a hardcoded
    id would rot the moment a commit is amended.
    """
    out = _git("log", "--diff-filter=A", "--format=%H", "--", REPORT_PATH).strip()
    lines = out.splitlines()
    return lines[-1] if lines else ""


def build_rows(commits: list[tuple[str, str]]) -> str:
    """Table body for the given commits, one row each."""
    rows: list[str] = []
    for sha, subject in commits:
        desc = DESCRIPTIONS.get(subject, subject)
        where = (
            "git history at the first-published commit"
            if subject.startswith("Formal gap audit")
            else "—"
        )
        rows.append(f"| `{sha[:7]}` | {desc} | {where} |")
    return "\n".join(rows)


def _extract_table(text: str) -> tuple[str, int, int]:
    """Return (table text, start offset, end offset) for the revision table.

    The table runs from its header to the first line that is not a table row,
    so the section that follows it can be reworded without breaking this.
    """
    marker = "| Commit | Change | Where the retracted wording now lives |"
    if marker not in text:
        raise SystemExit(
            f"could not find the revision history table in {REPORT_PATH}; "
            "the header row is missing"
        )
    start = text.index(marker)
    lines = text[start:].splitlines()
    table: list[str] = []
    for index, line in enumerate(lines):
        if index == 0 or line.startswith("|"):
            table.append(line)
            continue
        break
    body = "\n".join(table)
    return body, start, start + len(body)


def _check_descriptions(commits: list[tuple[str, str]]) -> None:
    """Fail loudly if a described subject no longer matches any commit."""
    subjects = {subject for _, subject in commits}
    dead = sorted(set(DESCRIPTIONS) - subjects)
    if dead:
        raise SystemExit(
            "DESCRIPTIONS contains entries that match no commit subject "
            f"(the history was rewritten or a commit was removed): {dead}\n"
            "If this repository is a shallow clone, fetch the full history "
            "first: the table can only be checked against the commits that "
            "modified the report."
        )


def _rewrite_first_published(text: str, first: str) -> str:
    """Keep the prose reference to the first-published commit in step."""
    pattern = re.compile(
        r"This report was first published at commit `([0-9a-f]{7,40})`"
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise SystemExit(
            "expected exactly one 'first published at commit' reference in the "
            f"report, found {len(matches)}"
        )
    return pattern.sub(
        lambda _m: f"This report was first published at commit `{first[:7]}`",
        text,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report_path = root / REPORT_PATH
    if not report_path.exists():
        print(f"report not found: {report_path}")
        return 1

    commits = _scoped_commits()
    if not commits:
        print(f"no commit in the history modified {REPORT_PATH}")
        return 1
    _check_descriptions(commits)

    text = report_path.read_text(encoding="utf-8")
    current, start, end = _extract_table(text)

    if args.check:
        committed_form = (
            TABLE_HEADER + build_rows(commits[:-1]) + "\n" + PLACEHOLDER_ROW
        )
        pending_form = TABLE_HEADER + build_rows(commits) + "\n" + PLACEHOLDER_ROW
        if current.rstrip() == committed_form.rstrip():
            print(
                f"revision history table is up to date "
                f"({len(commits) - 1} rows plus the carrying commit)"
            )
            return 0
        if current.rstrip() == pending_form.rstrip():
            print(
                "revision history table is up to date "
                f"({len(commits)} rows; regenerated but not yet committed)"
            )
            return 0
        print(
            "DRIFT: the revision history table does not match the commits that "
            "modified the report; run without --check"
        )
        return 1

    body = build_rows(commits)
    new_table = TABLE_HEADER + body + "\n" + PLACEHOLDER_ROW
    updated = text[:start] + new_table + text[end:]

    first = _first_published_commit()
    if first:
        updated = _rewrite_first_published(updated, first)

    report_path.write_text(updated, encoding="utf-8")
    print(
        f"revision history table regenerated ({len(body.splitlines())} rows "
        f"plus the carrying commit)"
    )
    print(f"first published commit: {first[:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
