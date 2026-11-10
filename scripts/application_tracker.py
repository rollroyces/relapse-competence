#!/usr/bin/env python3
"""Turn the data-access tracker in the report into a machine-readable artefact.

``docs/DATA-ACCESS-APPLICATIONS.md`` is the source of truth for the state of
the two data-access applications. This script parses its tracker tables and
writes ``results/application_tracker/application_tracker.json``, so the state
can be read by a machine and checked in CI.

    python scripts/application_tracker.py            # regenerate the artefact
    python scripts/application_tracker.py --check    # fail if it has drifted

The check compares the parsed content, not the provenance fields, so
regenerating the artefact does not make the check fail on its own timestamp.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "docs" / "DATA-ACCESS-APPLICATIONS.md"
ARTEFACT = REPO / "results" / "application_tracker" / "application_tracker.json"

#: The anchors of the three tables, and the columns each one is expected to
#: have. A change to a table's shape has to be deliberate: the check fails
#: rather than reading a table with the wrong columns.
STEP_TABLE_ANCHOR = "| Application | Step | Owner | Status | Depends on |"
APPLICATION_TABLE_ANCHOR = (
    "| Application | Dataset | Access route | Route verified | Expected turnaround | Status |"
)
PREREQUISITE_TABLE_ANCHOR = "| # | Prerequisite | Owner | Status | Applies to |"
FACT_TABLE_ANCHOR = "| Fact | Value | Source | Verified on |"

STEP_COLUMNS = ["Application", "Step", "Owner", "Status", "Depends on"]
APPLICATION_COLUMNS = [
    "Application",
    "Dataset",
    "Access route",
    "Route verified",
    "Expected turnaround",
    "Status",
]
PREREQUISITE_COLUMNS = [
    "#",
    "Prerequisite",
    "Owner",
    "Status",
    "Applies to",
]
FACT_COLUMNS = ["Fact", "Value", "Source", "Verified on"]


def _clean(cell: str) -> str:
    """Strip the markdown emphasis and code ticks from a table cell."""
    return cell.replace("**", "").replace("`", "").strip()


def _table(text: str, anchor: str) -> list[list[str]]:
    """The rows of the table whose header line is ``anchor``."""
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
        cells = stripped.strip("|").split("|")
        if all(set(cell) <= set("-: ") and cell for cell in cells):
            continue
        rows.append([_clean(cell) for cell in cells])
    return rows


def _rows_after_header(table: list[list[str]], header: list[str]) -> list[dict[str, str]]:
    """The data rows of a table, keyed by the expected column names."""
    if not table:
        return []
    actual = [cell for cell in table[0]]
    if actual != header:
        raise SystemExit(
            "the tracker table's columns have changed:\n"
            f"  expected {header}\n"
            f"  found    {actual}"
        )
    out: list[dict[str, str]] = []
    for row in table[1:]:
        if len(row) != len(header):
            raise SystemExit(f"tracker row has {len(row)} cells, expected {len(header)}: {row}")
        out.append(dict(zip(header, row, strict=True)))
    return out


def parse(text: str) -> dict:
    """The tracker content, as it appears in the report."""
    steps = _rows_after_header(
        _table(text, STEP_TABLE_ANCHOR), STEP_COLUMNS
    )
    applications = _rows_after_header(
        _table(text, APPLICATION_TABLE_ANCHOR), APPLICATION_COLUMNS
    )
    prerequisites = _rows_after_header(
        _table(text, PREREQUISITE_TABLE_ANCHOR), PREREQUISITE_COLUMNS
    )
    facts = _rows_after_header(_table(text, FACT_TABLE_ANCHOR), FACT_COLUMNS)
    if not steps or not applications or not prerequisites or not facts:
        raise SystemExit(
            "the report's tracker tables were not found; the anchors or the "
            "table shapes must have changed"
        )
    return {
        "steps": steps,
        "applications": applications,
        "prerequisites": prerequisites,
        "external_facts": facts,
    }


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip() or None


def build(content: dict) -> dict:
    """The artefact, with its provenance."""
    return {
        "audit": {
            "id": "data-access-applications-2026-11",
            "generated_by": "scripts/application_tracker.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "git_commit": _git_commit(),
            "source_document": "docs/DATA-ACCESS-APPLICATIONS.md",
            "note": (
                "Generated from the tracker tables in the source document. "
                "The document is the source of truth; this file is its "
                "machine-readable projection and is checked against it in CI."
            ),
        },
        **content,
    }


def _comparable(document: dict) -> dict:
    """The part of the artefact that the check compares."""
    return {
        "steps": document.get("steps"),
        "applications": document.get("applications"),
        "prerequisites": document.get("prerequisites"),
        "external_facts": document.get("external_facts"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed artefact does not match the report",
    )
    parser.add_argument("--report", default=str(REPORT))
    parser.add_argument("--artefact", default=str(ARTEFACT))
    args = parser.parse_args(argv)

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"report not found: {report_path}", file=sys.stderr)
        return 1
    content = parse(report_path.read_text())
    document = build(content)

    artefact_path = Path(args.artefact)
    if args.check:
        if not artefact_path.exists():
            print(
                f"{artefact_path} does not exist; run "
                f"python scripts/application_tracker.py to create it",
                file=sys.stderr,
            )
            return 1
        committed = json.loads(artefact_path.read_text())
        if _comparable(committed) != _comparable(document):
            print(
                "the application tracker artefact does not match the report; "
                "run python scripts/application_tracker.py to regenerate it",
                file=sys.stderr,
            )
            return 1
        print(
            f"application tracker matches the report "
            f"({len(content['steps'])} steps, "
            f"{len(content['applications'])} applications, "
            f"{len(content['prerequisites'])} prerequisites, "
            f"{len(content['external_facts'])} external facts)"
        )
        return 0

    artefact_path.parent.mkdir(parents=True, exist_ok=True)
    artefact_path.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {artefact_path}")
    print(
        f"  {len(content['steps'])} steps, "
        f"{len(content['applications'])} applications, "
        f"{len(content['prerequisites'])} prerequisites, "
        f"{len(content['external_facts'])} external facts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
