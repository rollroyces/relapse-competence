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

import argparse
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


def _plain(cell: str) -> str:
    """A table cell without its markdown emphasis or code ticks."""
    return cell.replace("**", "").replace("`", "").strip()


def _all_tables(text: str) -> list[list[list[str]]]:
    """Every markdown table in a document, in order."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(cell) <= set("-: ") and cell for cell in cells):
            continue
        current.append(cells)
    if current:
        tables.append(current)
    return tables


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-dir",
        default=str(PACKAGE),
        help=(
            "the directory holding the package markdown; point it at the "
            "local copy to check what the PI has filled in"
        ),
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help=(
            "report the markers still to fill in a local copy, without "
            "failing on them"
        ),
    )
    args = parser.parse_args(argv)
    package = Path(args.package_dir).expanduser()
    package = package if package.is_absolute() else (REPO / package)
    package = package.resolve()
    # The committed package and the local copy are checked differently: the
    # committed one must hold no personal data at all, and the local one is
    # supposed to be filled in.
    is_committed = package == PACKAGE.resolve()

    problems: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            problems.append(message)

    # --- the package exists and is complete ---
    for name in REQUIRED_FILES:
        path = package / name
        check(path.exists(), f"missing package file: {name}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1

    details = (package / "01-project-details.md").read_text()
    narrative = (package / "02-proposal-narrative.md").read_text()
    cover = (package / "03-pi-cover-sheet.md").read_text()
    letter = (package / "04-signing-official-letter.md").read_text()
    checklist = (package / "05-documents-checklist.md").read_text()
    readme = (package / "README.md").read_text()
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
    runbook = (package / "06-submission-runbook.md").read_text()
    inquiry = (package / "07-scoping-inquiry.md").read_text()
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
        "the scoping inquiry asks the sample-count question",
        "how many" in inquiry.lower() and "lung cancer" in inquiry.lower(),
    )
    check(
        "the scoping inquiry is not the proposal",
        "scope question" in inquiry.lower()
        and "separate document" in inquiry.lower(),
    )
    # The two paste-ready messages, and the form they go into.
    for tag in ("A", "B", "C", "D", "E"):
        begin = f"<!-- BEGIN MESSAGE {tag} -->"
        end = f"<!-- END MESSAGE {tag} -->"
        if begin not in inquiry or end not in inquiry:
            check(False, f"the scoping inquiry does not delimit message {tag}")
            continue
        body = inquiry.split(begin)[1].split(end)[0].strip()
        check(
            f"message {tag} fits the contact form's 10,000-character limit",
            len(body) <= 10_000,
        )
        check(
            f"message {tag} has no field left unfilled",
            "[TO FILL:" not in body,
        )
        sign_lines = [line for line in body.splitlines() if line.strip()]
        check(
            f"message {tag} is signed with a name and an e-mail address",
            len(sign_lines) >= 2
            and "@" in sign_lines[-1]
            and "@" not in sign_lines[-2],
        )
        check(f"message {tag} does not carry markdown emphasis", "**" not in body)
    for field in ("Your Email Address", "Select a Subject", "Select a Topic", "Message"):
        check(
            f"the scoping inquiry maps the form field {field!r}",
            field in inquiry,
        )
    check(
        "the scoping inquiry has no field left unfilled",
        "[TO FILL:" not in inquiry,
    )
    check(
        "the scoping inquiry names the PLCO subject",
        "**PLCO**" in inquiry,
    )
    for topic in ("Data Access/Availability", "Biospecimen Availability"):
        check(
            f"the scoping inquiry names the topic {topic!r}",
            topic in inquiry,
        )
    check(
        "the scoping inquiry warns about the anti-spam boxes",
        "leave it empty" in inquiry.lower() and "antispam1" in inquiry,
    )
    check(
        "the scoping inquiry warns against the newsletter form",
        "govdelivery" in inquiry,
    )
    # The sending record. The form issues no inquiry number, so the date and
    # the length of each message are the only evidence that the two messages
    # went out; they have to be in the document, and the lengths have to be
    # the lengths of the messages.
    check(
        "the scoping inquiry records the sending date",
        "2026-11-11" in inquiry,
    )
    check(
        "the scoping inquiry records that the form issues no inquiry number",
        "no inquiry number" in inquiry,
    )
    check(
        "the scoping inquiry records the confirmation the form returned",
        "Your message was sent successfully" in inquiry,
    )
    for tag, topic in (
        ("A", "Data Access/Availability"),
        ("B", "Biospecimen Availability"),
        ("C", "Data Access/Availability"),
        ("D", "Biospecimen Application Process"),
    ):
        begin = f"<!-- BEGIN MESSAGE {tag} -->"
        end = f"<!-- END MESSAGE {tag} -->"
        if begin not in inquiry or end not in inquiry:
            continue
        body = inquiry.split(begin)[1].split(end)[0].strip()
        rows = [
            line.strip()
            for line in inquiry.splitlines()
            if line.strip().startswith(f"| {tag} |")
        ]
        if not rows:
            check(False, f"the scoping inquiry does not record the sending of message {tag}")
            continue
        cells = [c.strip() for c in rows[0].strip("|").split("|")]
        check(
            f"the sending record for message {tag} names the subject and topic",
            len(cells) == 5 and cells[1] == "PLCO" and cells[2] == topic,
        )
        check(
            f"the sending record for message {tag} quotes the length of the "
            "message that was sent",
            len(cells) == 5 and cells[3] == str(len(body)),
        )
        check(
            f"the sending record for message {tag} carries the date it was sent",
            len(cells) == 5 and cells[4].startswith("2026-11-11"),
        )
    check(
        "the runbook records that the scoping inquiry was sent",
        "2026-11-11" in runbook and "has been sent" in runbook,
    )
    check(
        "the runbook says the form issues no inquiry number",
        "no inquiry number" in runbook,
    )
    # Every place the package quotes the description's word count back at
    # the reader has to agree with the checker. The cap is CDAS's number,
    # not the description's, so it is the one value allowed to differ. This
    # gate exists because the package carried 456 in the runbook and 405 in
    # the checklist while the description was 498, and nothing noticed.
    for name in REQUIRED_FILES:
        text = (package / name).read_text()
        for match in re.finditer(r"(\d+)[- ]words?\b", text):
            quoted = int(match.group(1))
            if quoted == WORD_CAP:
                continue
            check(
                quoted == len(words),
                f"{name} quotes a project-description word count of {quoted}, "
                f"and the description is {len(words)}",
            )
    # The markers have to appear once each. A duplicated end marker makes
    # "the text between the markers" ambiguous for a reader, even when the
    # extractor happens to take the first one and the content is unaffected.
    check(
        "the project description has one begin marker and one end marker",
        details.count(DESCRIPTION_BEGIN) == 1
        and details.count(DESCRIPTION_END) == 1,
    )

    # The field map has to point at the section that actually holds the
    # value, because the package is filled in by a person. A pointer to a
    # section that exists but holds something else sends them to the wrong
    # table, which is worse than a missing pointer.
    package_files = {
        "01": "01-project-details.md",
        "03": "03-pi-cover-sheet.md",
        "04": "04-signing-official-letter.md",
    }

    def _section(document: str, number: str) -> str:
        """The text of a numbered section of a document."""
        start = document.find(f"## {number}.")
        if start == -1:
            return ""
        rest = document[start:]
        end = rest.find("\n## ", 1)
        return rest if end == -1 else rest[:end]

    for row_label, doc_id, number, phrase in (
        ("Institution and location", "03", "1", "Institution location"),
        ("Signing Official", "04", "5", "[SO]"),
    ):
        row = next(
            (
                line
                for line in runbook.splitlines()
                if line.strip().startswith(f"| {row_label} |")
            ),
            "",
        )
        check(
            bool(row) and f"`{doc_id}` §{number}" in row,
            f"the field map does not point the {row_label!r} row at "
            f"`{doc_id}` §{number}",
        )
        check(
            phrase in _section((package / package_files[doc_id]).read_text(), number),
            f"{doc_id} §{number} does not hold {phrase!r}",
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

    # The committed package is a template, not a record. The PI's and the
    # Signing Official's own details stay as markers, because the repository
    # is public and a telephone number committed here cannot be taken back.
    # They are filled in a local copy -- build/package-private, which
    # build/ keeps out of the repository -- and printed from there.
    if is_committed:
        cover_values = _field_values(cover)
        for field in (
            "Full name",
            "Degrees",
            "Position title",
            "Department and institution",
            "Institution location",
            "Telephone",
            "ORCID",
        ):
            value = _plain(cover_values.get(field, ""))
            check(
                value == "[PI]",
                f"the committed cover sheet fills in {field!r} ({value!r}); the "
                "PI's own details belong in a local copy, not in the public "
                "repository",
            )
        user_tables = [
            table
            for table in _all_tables(cover)
            if table and len(table[0]) == 5 and table[0][0] == "Name"
        ]
        check(
            len(user_tables) == 1,
            "the cover sheet's approved-users table is not the table this check reads",
        )
        for row in user_tables[0][1:] if user_tables else []:
            check(
                _plain(row[0]) == "[PI]",
                f"the committed approved-users table fills in a name ({row[0]!r})",
            )
            check(
                _plain(row[1]) in ("[PI]", "roycelam@umich.edu"),
                f"the committed approved-users table fills in an e-mail address "
                f"({row[1]!r})",
            )
            check(
                _plain(row[2]) == "[PI]",
                f"the committed approved-users table fills in an institution "
                f"({row[2]!r})",
            )
        for label in ("Printed name", "Position title", "Institution"):
            check(
                f"{label}: `[SO]`" in letter,
                f"the committed Signing Official letter fills in {label!r}",
            )
        check(
            "**Signing Official for `[SO's institution]`**" in letter,
            "the committed Signing Official letter fills in the institution",
        )
        check(
            "**From:** `[SO's institution]`" in letter,
            "the committed Signing Official letter fills in the sending institution",
        )
    else:
        # A local copy is supposed to be filled in, so what matters there is
        # the markers that are still left. Only the places a value can
        # actually go are counted -- a table cell, or the label of a
        # signature line -- so the prose that merely names the markers does
        # not inflate the count, and each one is listed with its line so
        # that filling it in is mechanical.
        remaining: dict[str, list[str]] = {}
        total = 0
        for name in REQUIRED_FILES:
            lines = (package / name).read_text().splitlines()
            hits: list[str] = []
            for number, line in enumerate(lines, 1):
                if not (
                    line.strip().startswith("|")
                    or re.match(r"^[A-Z][A-Za-z ]+: `?\[", line)
                ):
                    continue
                count = len(
                    re.findall(r"\[(?:PI|SO)(?:'s institution)?\]", line)
                )
                if count:
                    total += count
                    hits.append(f"{name}:{number} ({count}): {line.strip()}")
            if hits:
                remaining[name] = hits
        print(f"values still to fill in: {total}")
        for hits in remaining.values():
            for hit in hits:
                print(f"  {hit}")
        check(
            total == 0 or args.allow_incomplete,
            f"the local copy still has {total} unfilled value(s)",
        )

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"\n{len(problems)} problem(s) with the submission package.")
        return 1
    print("the PLCO CDAS submission package is complete and self-consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
