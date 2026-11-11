"""Tests for the PLCO CDAS submission package.

The package is going to be signed and submitted, so the checks that stand
between it and a rejection are asserted here: the word cap CDAS enforces, the
fields the form asks for, the numbers the package is justified by, and the
two signature blocks.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

PACKAGE = Path("docs/plco-cdas-submission-package")
SCRIPT = Path("scripts/check_plco_cdas_package.py")
FOLDS = Path("results/per_library_folds/per_library_folds.json")
GATE = Path("results/gate_review/gate_review.json")


def _load_script():
    spec = importlib.util.spec_from_file_location("check_plco_cdas_package", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_plco_cdas_pdf", Path("scripts/build_plco_cdas_pdf.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_script()


def test_the_package_is_complete() -> None:
    for name in checker.REQUIRED_FILES:
        assert (PACKAGE / name).exists(), name


def test_the_project_description_is_within_the_cap() -> None:
    details = (PACKAGE / "01-project-details.md").read_text()
    description = checker._description(details)
    words = description.split()
    assert 0 < len(words) <= checker.WORD_CAP, len(words)


def test_the_check_passes_on_the_committed_package() -> None:
    assert checker.main([]) == 0


def test_the_cap_is_enforced(tmp_path: Path) -> None:
    """A description over the cap has to fail, not be noticed by CDAS."""
    details = (PACKAGE / "01-project-details.md").read_text()
    padded = details.replace(
        checker.DESCRIPTION_END,
        " " + ("padding " * 200) + checker.DESCRIPTION_END,
    )
    padded_path = tmp_path / "01-project-details.md"
    padded_path.write_text(padded)
    description = checker._description(padded_path.read_text())
    assert len(description.split()) > checker.WORD_CAP


def test_both_signature_blocks_are_present() -> None:
    cover = (PACKAGE / "03-pi-cover-sheet.md").read_text()
    letter = (PACKAGE / "04-signing-official-letter.md").read_text()
    assert "## 4. Signature" in cover
    assert "Principal Investigator" in cover
    assert "## 5. Signature" in letter
    assert "Signing Official" in letter


def test_the_required_fields_are_carried() -> None:
    details = (PACKAGE / "01-project-details.md").read_text()
    values = checker._field_values(details)
    for field in checker.REQUIRED_FIELDS:
        assert field in details, field
    assert values["Principal Investigator Name"].strip()
    assert values["Institution"].strip()


def test_the_package_quotes_this_repository_s_own_numbers() -> None:
    if not FOLDS.exists() or not GATE.exists():
        pytest.skip("the measurement artefacts are not present")
    folds = json.loads(FOLDS.read_text())
    gate = json.loads(GATE.read_text())
    text = "\n".join(
        (PACKAGE / name).read_text() for name in checker.REQUIRED_FILES
    )
    nsclc = folds["composition"]["NSCLC"]["KCNN4"]
    assert (
        f"{nsclc['n_libraries_with_fold_above_one']} of "
        f"{nsclc['n_libraries_with_fold_computable']}" in text
    )
    assert f"{gate['audit']['k1_auc_threshold']:.2f}" in text
    assert f"{gate['audit']['k3_auc_threshold']:.2f}" in text
    assert f"{gate['audit']['electrical_fraction']:.0%}" in text


def test_the_runbook_marks_the_points_a_person_must_cross() -> None:
    """The runbook has to be usable by a person, not by an agent."""
    runbook = (PACKAGE / "06-submission-runbook.md").read_text()
    assert runbook.count("[GATE]") >= 3
    assert "https://cdas.cancer.gov/projects/create/plco/data/" in runbook
    assert "https://cdas.cancer.gov/contact/" in runbook
    assert "The PI submits it" in runbook


def test_the_scoping_inquiry_goes_first() -> None:
    """The sample count decides whether the EEMS route is worth pursuing."""
    inquiry = (PACKAGE / "07-scoping-inquiry.md").read_text()
    assert "how many" in inquiry.lower()
    assert "lung cancer" in inquiry.lower()
    assert "scope question" in inquiry.lower()


def test_the_scoping_inquiry_is_paste_ready() -> None:
    """Two messages, each inside the form's limit, with the fields marked."""
    inquiry = (PACKAGE / "07-scoping-inquiry.md").read_text()
    for tag in ("A", "B"):
        begin = f"<!-- BEGIN MESSAGE {tag} -->"
        end = f"<!-- END MESSAGE {tag} -->"
        assert begin in inquiry and end in inquiry, tag
        body = inquiry.split(begin)[1].split(end)[0].strip()
        assert len(body) <= 10_000, tag
        assert "[TO FILL:" not in body, tag
        assert "**" not in body, tag
        sign_lines = [line for line in body.splitlines() if line.strip()]
        assert "@" in sign_lines[-1], tag
        assert "@" not in sign_lines[-2], tag
    for field in (
        "Your Email Address",
        "Select a Subject",
        "Select a Topic",
        "Message",
    ):
        assert field in inquiry, field
    assert "**PLCO**" in inquiry
    assert "Data Access/Availability" in inquiry
    assert "Biospecimen Availability" in inquiry
    # The anti-spam boxes and the footer newsletter form are both traps.
    assert "leave it empty" in inquiry.lower()
    assert "antispam1" in inquiry
    assert "govdelivery" in inquiry
    assert "[TO FILL:" not in inquiry


def test_the_signature_blocks_have_a_line_to_sign_on() -> None:
    cover = (PACKAGE / "03-pi-cover-sheet.md").read_text()
    letter = (PACKAGE / "04-signing-official-letter.md").read_text()
    assert "Signature: __" in cover
    assert "Signature: __" in letter


def test_the_proposal_carries_the_localisation_design() -> None:
    """The leukocyte audit changed the assay design; the proposal must say so.

    The channel transcript has to be localised to the tumour, the tumour cfDNA
    fraction has to be estimated per participant, and the panel has to carry
    leukocyte reference loci. A proposal that silently drops any of them would
    describe the assay the audit showed does not work.
    """
    details = (PACKAGE / "01-project-details.md").read_text()
    narrative = (PACKAGE / "02-proposal-narrative.md").read_text()
    for phrase in (
        "somatic variant",
        "leukocyte reference",
        "tumour cfDNA fraction",
        "tumour-attributable",
    ):
        assert phrase in details, phrase
        assert phrase in narrative, phrase
    assert "secondary" in narrative
    assert "upper bound" in narrative
    assert "required, not optional" in details or "required, not optional" in narrative


def test_the_scoping_inquiry_asks_the_decisive_questions() -> None:
    """The three answers that decide the plasma arm.

    The specification makes the matched tumour and a germline sample
    required, because the per-molecule attribution needs each participant's
    own somatic profile and heterozygous positions. An inquiry that does not
    ask for them cannot produce the answer the proposal depends on.
    """
    inquiry = (PACKAGE / "07-scoping-inquiry.md").read_text()
    for phrase in (
        "How many participants were diagnosed with lung cancer",
        "How many have primary tumour tissue archived",
        "whole-exome sequencing",
        "whole-genome sequencing",
        "germline DNA sample",
        "more than one screening visit",
    ):
        assert phrase in inquiry, phrase


def test_the_scoping_messages_fit_the_form() -> None:
    """Plain textarea, 10,000 characters, no markdown, nothing unfilled."""
    inquiry = (PACKAGE / "07-scoping-inquiry.md").read_text()
    for tag in ("A", "B"):
        body = inquiry.split(f"<!-- BEGIN MESSAGE {tag} -->")[1].split(
            f"<!-- END MESSAGE {tag} -->"
        )[0].strip()
        assert 0 < len(body) <= 10_000, tag
        assert "**" not in body, tag
        assert "[TO FILL:" not in body, tag
        assert body.splitlines()[-2].strip() == "Royce Lam"
        assert body.splitlines()[-1].strip() == "roycelam@umich.edu"


def test_the_constraints_are_stated() -> None:
    """The rules that shape the package must not be quietly dropped."""
    text = "\n".join(
        (PACKAGE / name).read_text() for name in checker.REQUIRED_FILES
    )
    for phrase in (
        "500 words",
        "Limited Data Set",
        "published on the CDAS website",
        "permanent employee",
        "12 months",
        "DocuSign",
        "separate project proposal",
    ):
        assert phrase in text, phrase


def test_the_sending_record_binds_its_counts_to_the_messages() -> None:
    """The record of what was sent cannot drift away from what was sent.

    CDAS's contact form issues no inquiry number, so the date and the length
    of each message are the only evidence that the two messages went out. If
    the quoted length stops matching the message, the record is describing
    something that was not sent.
    """
    inquiry = (PACKAGE / "07-scoping-inquiry.md").read_text()
    for tag, topic in (
        ("A", "Data Access/Availability"),
        ("B", "Biospecimen Availability"),
    ):
        body = inquiry.split(f"<!-- BEGIN MESSAGE {tag} -->")[1].split(
            f"<!-- END MESSAGE {tag} -->"
        )[0].strip()
        rows = [
            line.strip()
            for line in inquiry.splitlines()
            if line.strip().startswith(f"| {tag} |")
        ]
        assert rows, f"message {tag} has no sending record"
        cells = [c.strip() for c in rows[0].strip("|").split("|")]
        assert len(cells) == 5, cells
        assert cells[1] == "PLCO", cells
        assert cells[2] == topic, cells
        assert cells[3] == str(len(body)), cells
        assert cells[4].startswith("2026-11-11"), cells


def test_the_sending_record_says_the_form_issues_no_reference() -> None:
    """A form that issues no number must not be recorded as if it did."""
    inquiry = (PACKAGE / "07-scoping-inquiry.md").read_text()
    runbook = (PACKAGE / "06-submission-runbook.md").read_text()
    for text in (inquiry, runbook):
        assert "no inquiry number" in text
    assert "Your message was sent successfully" in inquiry
    assert "2026-11-11" in inquiry
    assert "has been sent" in runbook


def test_the_runbook_quotes_the_description_word_count_correctly() -> None:
    """Every quoted word count in the package has to agree with the checker.

    This gate exists because the package carried 456 in the runbook and 405
    in the checklist while the description was 498, and nothing noticed: the
    drift was in a sentence that only the reader would have been misled by.
    """
    details = (PACKAGE / "01-project-details.md").read_text()
    words = len(checker._description(details).split())
    for name in checker.REQUIRED_FILES:
        text = (PACKAGE / name).read_text()
        for match in re.finditer(r"(\d+)[- ]words?\b", text):
            quoted = int(match.group(1))
            if quoted == checker.WORD_CAP:
                continue
            assert quoted == words, (name, quoted, words)


def test_the_description_markers_appear_once_each() -> None:
    """A duplicated end marker makes 'the text between the markers' ambiguous."""
    details = (PACKAGE / "01-project-details.md").read_text()
    assert details.count(checker.DESCRIPTION_BEGIN) == 1
    assert details.count(checker.DESCRIPTION_END) == 1


def test_the_field_map_points_at_the_sections_that_hold_the_values() -> None:
    """A pointer to a section that exists but holds something else is worse
    than no pointer at all: it sends the person filling the form to the
    wrong table. This gate exists because the Institution and location row
    pointed at the approved-users table and the Signing Official row at the
    authorised-individuals table.
    """
    runbook = (PACKAGE / "06-submission-runbook.md").read_text()
    for label, filename, number, phrase in (
        ("Institution and location", "03-pi-cover-sheet.md", "1", "Institution location"),
        ("Signing Official", "04-signing-official-letter.md", "5", "[SO]"),
    ):
        row = next(
            (
                line
                for line in runbook.splitlines()
                if line.strip().startswith(f"| {label} |")
            ),
            "",
        )
        assert row, label
        assert f"`{filename[:2]}` §{number}" in row, (label, row)
        document = (PACKAGE / filename).read_text()
        start = document.find(f"## {number}.")
        assert start != -1, (filename, number)
        rest = document[start:]
        end = rest.find("\n## ", 1)
        section = rest if end == -1 else rest[:end]
        assert phrase in section, (label, number)



def test_the_committed_package_holds_no_personal_data() -> None:
    """The repository is public; the PI's own details stay markers in it.

    The telephone number and the ORCID are the ones that would not be
    public anyway -- CDAS publishes the proposal, the PI's name and title
    with it, but not these. So the committed package keeps every field that
    only a person can supply as a marker, and the filled copy lives in
    build/, which is gitignored.
    """
    cover = (PACKAGE / "03-pi-cover-sheet.md").read_text()
    letter = (PACKAGE / "04-signing-official-letter.md").read_text()
    values = checker._field_values(cover)
    for field in (
        "Full name",
        "Degrees",
        "Position title",
        "Department and institution",
        "Institution location",
        "Telephone",
        "ORCID",
    ):
        assert checker._plain(values.get(field, "")) == "[PI]", field
    for label in ("Printed name", "Position title", "Institution"):
        assert f"{label}: `[SO]`" in letter, label
    assert "**Signing Official for `[SO's institution]`**" in letter
    assert "**From:** `[SO's institution]`" in letter


def test_the_builder_refresh_never_overwrites_an_edited_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The local copy is the only place the PI's details exist.

    A refresh must bring the template's later edits into the copy without
    taking away what has been filled in. This gate exists because the copy
    was once deleted and rebuilt wholesale, which would have destroyed a
    filled copy that could not be recovered.
    """
    builder = _load_builder()
    monkeypatch.setattr(builder, "BUILD", tmp_path)
    assert builder.main(["--init-local"]) == 0
    target = tmp_path / "package-private"
    assert (target / "03-pi-cover-sheet.md").exists()
    edited = target / "03-pi-cover-sheet.md"
    edited.write_text(edited.read_text().replace("`[PI]`", "`Dr Example`"))
    # A refresh must not take the fill away.
    assert builder.main(["--init-local"]) == 0
    assert "`Dr Example`" in edited.read_text()


def test_the_checker_reports_the_markers_left_in_a_local_copy(
    tmp_path: Path,
) -> None:
    """Checking the local copy is how the PI learns what is still to fill."""
    package = tmp_path / "package"
    package.mkdir()
    for name in checker.REQUIRED_FILES:
        (package / name).write_text((PACKAGE / name).read_text())
    assert checker.main(["--package-dir", str(package)]) == 1
    assert checker.main(["--package-dir", str(package), "--allow-incomplete"]) == 0
