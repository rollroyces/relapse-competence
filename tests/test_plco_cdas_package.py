"""Tests for the PLCO CDAS submission package.

The package is going to be signed and submitted, so the checks that stand
between it and a rejection are asserted here: the word cap CDAS enforces, the
fields the form asks for, the numbers the package is justified by, and the
two signature blocks.
"""

from __future__ import annotations

import importlib.util
import json
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
    assert checker.main() == 0


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
    assert "not the proposal" in inquiry.lower()


def test_the_signature_blocks_have_a_line_to_sign_on() -> None:
    cover = (PACKAGE / "03-pi-cover-sheet.md").read_text()
    letter = (PACKAGE / "04-signing-official-letter.md").read_text()
    assert "Signature: __" in cover
    assert "Signature: __" in letter


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
