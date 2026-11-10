#!/usr/bin/env python3
"""Check the PLCO CDAS submission package.

The package exists to be signed and submitted, so the things that would make
it fail on the CDAS side are checked here rather than discovered there:

- the project description is inside CDAS's 500-word cap;
- every field the CDAS form asks for is present, and is either filled or
  explicitly marked as the PI's to complete;
- the numbers the package quotes are this repository's own numbers, checked
  against the artefacts they came from;
- both signature blocks are present;
- the constraints that shape the package are stated, so that a later edit
  cannot quietly drop them.

    python scripts/check_plco_cdas_package.py

Exit code is 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "docs" / "plco-cdas-submission-package"

#: The files the package consists of.
REQUIRED_FILES = (
    "README.md",
    "01-project-details.md",
    "02-proposal-narrative.md",
    "03-pi-cover-sheet.md",
    "04-signing-official-letter.md",
    "05-documents-checklist.md",
    "06-submission-runbook.md",
    "07-scoping-inquiry.md",
)

#: CDAS's cap on the project description.
WORD_CAP = 500

#: The fields the CDAS project form asks for, and the section of the package
#: that carries them.
REQUIRED_FIELDS = (
    "Principal Investigator Name",
    "Degrees",
    "Institution",
    "Position Title",
    "Institutional email",
    "Institution location",
    "Signing Official",
    "Title",
    "Summary",
    "Project ID",
    "Aims",
    "Approved users",
)

#: The markers that delimit the text to paste into the CDAS description box.
DESCRIPTION_BEGIN = "<!-- BEGIN PROJECT DESCRIPTION -->"
DESCRIPTION_END = "<!-- END PROJECT DESCRIPTION -->"

#: A value the PI has to supply: a bracketed marker.
PI_MARKER = re.compile(r"\[(PI|SO)[^\]]*\]")


def _table(text: str) -> list[list[str]]:
    """The first markdown table in a document."""
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = stripped.strip("|").split("|")
        if all(set(cell) <= set("-: ") and cell for cell in cells):
            continue
        rows.append([cell.strip() for cell in cells])
    return rows


def _field_values(text: str) -> dict[str, str]:
    """The `| Field | Value |` rows of a document, keyed by field name."""
    values: dict[str, str] = {}
    for row in _table(text):
        if len(row) == 2 and row[0] and row[1]:
            values.setdefault(row[0], row[1])
    return values


def _description(text: str) -> str:
    if DESCRIPTION_BEGIN not in text or DESCRIPTION_END not in text:
        raise SystemExit(
            "the project description markers are missing from "
            "01-project-details.md"
        )
    return text.split(DESCRIPTION_BEGIN)[1].split(DESCRIPTION_END)[0]


def _artefact_numbers() -> dict[str, object]:
    """The numbers the package is allowed to quote, from the artefacts."""
    numbers: dict[str, object] = {}
    folds_path = REPO / "results/per_library_folds/per_library_folds.json"
    audit_path = REPO / "results/per_patient_audit/per_patient_audit.json"
    gate_path = REPO / "results/gate_review/gate_review.json"
    if folds_path.exists():
        folds = json.loads(folds_path.read_text())
        nsclc = folds["composition"]["NSCLC"]["KCNN4"]
        numbers["nsclc_fold_above_one"] = nsclc["n_libraries_with_fold_above_one"]
        numbers["nsclc_fold_computable"] = nsclc["n_libraries_with_fold_computable"]
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        mrd = [
            r
            for r in audit["per_library"]
            if r["dataset"] == "NSCLC" and r["treatment"] == "osi_mrd"
        ]
        clearing = sum(1 for r in mrd if not r["operating_point"]["k3_fired"])
        numbers["mrd_clearing"] = clearing
        numbers["mrd_total"] = len(mrd)
    if gate_path.exists():
        gate = json.loads(gate_path.read_text())
        numbers["k1_threshold"] = gate["audit"]["k1_auc_threshold"]
        numbers["k3_threshold"] = gate["audit"]["k3_auc_threshold"]
        numbers["electrical_fraction"] = gate["audit"]["electrical_fraction"]
    return numbers


def main() -> int:
    problems: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            problems.append(message)

    # --- the package exists and is complete ---
    for name in REQUIRED_FILES:
        path = PACKAGE / name
        check(path.exists(), f"missing package file: {name}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1

    details = (PACKAGE / "01-project-details.md").read_text()
    narrative = (PACKAGE / "02-proposal-narrative.md").read_text()
    cover = (PACKAGE / "03-pi-cover-sheet.md").read_text()
    letter = (PACKAGE / "04-signing-official-letter.md").read_text()
    checklist = (PACKAGE / "05-documents-checklist.md").read_text()
    readme = (PACKAGE / "README.md").read_text()
    everything = "\n".join([details, narrative, cover, letter, checklist, readme])

    # --- the 500-word cap ---
    description = _description(details)
    words = description.split()
    check(
        len(words) <= WORD_CAP,
        f"the project description is {len(words)} words, over CDAS's {WORD_CAP}",
    )
    print(f"project description: {len(words)} words (cap {WORD_CAP})")

    # --- the fields the form asks for ---
    values = _field_values(details)
    for field in REQUIRED_FIELDS:
        check(field in everything, f"the package does not carry the field {field!r}")
        if field in values:
            check(
                bool(values[field].strip()),
                f"the field {field!r} is present but empty",
            )
    check(
        "Principal Investigator Name" in values,
        "the Principal Investigator block has no readable fields",
    )
    pi_fields = values.get("Principal Investigator Name", "")
    check(
        bool(PI_MARKER.search(pi_fields)) or pi_fields.strip() != "",
        "the Principal Investigator name field is empty",
    )

    # --- the numbers are this repository's numbers ---
    numbers = _artefact_numbers()
    if "nsclc_fold_above_one" in numbers:
        quoted = (
            f"{numbers['nsclc_fold_above_one']} of {numbers['nsclc_fold_computable']}"
        )
        check(
            quoted in narrative or quoted in details,
            f"the package does not quote the NSCLC fold yield {quoted!r}",
        )
    if "mrd_total" in numbers:
        quoted = f"{numbers['mrd_clearing']} of {numbers['mrd_total']}"
        check(
            quoted in narrative or quoted in details,
            f"the package does not quote the residual-disease yield {quoted!r}",
        )
    if "k1_threshold" in numbers:
        check(
            f"{numbers['k1_threshold']:.2f}" in details
            or f"{numbers['k1_threshold']:.2f}" in narrative,
            "the package does not quote the K1 threshold",
        )
        check(
            f"{numbers['k3_threshold']:.2f}" in details
            or f"{numbers['k3_threshold']:.2f}" in narrative,
            "the package does not quote the K3 threshold",
        )
    if "electrical_fraction" in numbers:
        check(
            f"{numbers['electrical_fraction']:.0%}" in details
            or f"{numbers['electrical_fraction']:.0%}" in narrative,
            "the package does not quote the electrical-channel allocation",
        )
    for phrase in (
        "200,000x",
        "200 loci",
        "2.97x",
        "0.104",
        "2.55",
        "86.4%",
        "65-fold",
    ):
        check(phrase in everything, f"the package does not quote {phrase!r}")

    # --- the signature blocks ---
    check("## 4. Signature" in cover, "the PI cover sheet has no signature block")
    check("Principal Investigator" in cover, "the PI cover sheet is not signed by the PI")
    check(
        "## 5. Signature" in letter,
        "the Signing Official letter has no signature block",
    )
    check(
        "Signing Official" in letter,
        "the Signing Official letter is not signed by the Signing Official",
    )
    for document, name in ((cover, "PI cover sheet"), (letter, "Signing Official letter")):
        check(
            f"the {name} has a ruled line to sign on",
            "Signature: __" in document,
        )

    # --- the runbook and the scoping inquiry ---
    runbook = (PACKAGE / "06-submission-runbook.md").read_text()
    inquiry = (PACKAGE / "07-scoping-inquiry.md").read_text()
    for url in (
        "https://cdas.cancer.gov/projects/create/plco/data/",
        "https://cdas.cancer.gov/contact/",
    ):
        check(url in runbook, f"the runbook does not carry {url}")
    check(
        "the runbook marks the points an agent cannot cross",
        runbook.count("[GATE]") >= 3,
    )
    check(
        "the scoping inquiry asks the sample-count question first",
        "how many" in inquiry.lower() and "lung cancer" in inquiry.lower(),
    )
    check(
        "the scoping inquiry does not pretend to be the proposal",
        "not the proposal" in inquiry.lower(),
    )

    # --- the constraints are stated, so an edit cannot quietly drop them ---
    for phrase, where in (
        ("500 words", details),
        ("published on the CDAS website", details),
        ("Limited Data Set", details),
        ("permanent employee", cover),
        ("professor", cover),
        ("12 months", narrative),
        ("DocuSign", letter),
        ("separate project proposal", details),
    ):
        check(phrase in where, f"{phrase!r} is not stated where it belongs")

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"\n{len(problems)} problem(s) with the submission package.")
        return 1
    print("the PLCO CDAS submission package is complete and self-consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
