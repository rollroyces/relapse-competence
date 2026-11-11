#!/usr/bin/env python3
"""Render the PLCO CDAS submission package as a printable PDF.

The package's source of truth is the markdown under
``docs/plco-cdas-submission-package/``. This renders it to HTML with print
styling and prints it to PDF, so that what gets signed is what is in the
repository -- there is no second copy to keep in step.

    python scripts/build_plco_cdas_pdf.py            # build the PDF
    python scripts/build_plco_cdas_pdf.py --check    # check the inputs only

The PDF is a build product and is not committed: a committed PDF would drift
from the markdown the moment either side was edited. Each document ends with
the SHA-256 of the package sources it was built from, so a printed copy
carries the state it was printed from.

The PI's and the Signing Official's own details -- telephone, ORCID, degrees,
position title -- are deliberately left as markers in the committed package,
because the repository is public and a telephone number committed here cannot
be taken back. They are filled in a local copy instead:

    python scripts/build_plco_cdas_pdf.py --init-local
    $EDITOR build/package-private/03-pi-cover-sheet.md
    python scripts/build_plco_cdas_pdf.py --package-dir build/package-private

``build/`` is gitignored, so the filled copy never reaches the repository.

Chrome is used to print, because it is present on the machines this is
likely to be built on and produces better print typography than the other
options; ``--check`` does not need it, so CI can verify the inputs on
runners that have no browser.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "docs" / "plco-cdas-submission-package"
BUILD = REPO / "build"

#: The documents, in the order they are printed. The two signature documents
#: come last, so that they are the last pages of the file.
DOCUMENTS = (
    "README.md",
    "01-project-details.md",
    "02-proposal-narrative.md",
    "06-submission-runbook.md",
    "07-scoping-inquiry.md",
    "05-documents-checklist.md",
    "03-pi-cover-sheet.md",
    "04-signing-official-letter.md",
)

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)

#: The heading each document starts with, so a check can tell the documents
#: apart and detect a renamed or missing one.
EXPECTED_HEADINGS = {
    "README.md": "PLCO CDAS submission package",
    "01-project-details.md": "CDAS project details, pre-filled",
    "02-proposal-narrative.md": "Proposal narrative",
    "03-pi-cover-sheet.md": "Principal Investigator cover sheet",
    "04-signing-official-letter.md": "Letter of institutional authorisation",
    "05-documents-checklist.md": "Documents checklist",
    "06-submission-runbook.md": "Submission runbook",
    "07-scoping-inquiry.md": "Scoping inquiry to CDAS",
}

STYLE = """
@page { size: A4; margin: 20mm 18mm; }
body {
  font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.5; color: #111; max-width: 170mm;
  margin: 0 auto;
}
h1 { font-size: 19pt; margin: 0 0 4pt; }
h2 { font-size: 14pt; margin: 20pt 0 6pt; border-bottom: 1px solid #bbb;
     padding-bottom: 3pt; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; }
p, li { orphans: 2; widows: 2; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 12pt;
        font-size: 9.2pt; }
th, td { border: 1px solid #bbb; padding: 4pt 6pt; text-align: left;
         vertical-align: top; }
th { background: #f0f0f0; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 9pt; }
hr { border: 0; border-top: 1px solid #ccc; margin: 18pt 0; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 10pt;
             color: #333; }
.document { page-break-after: always; }
.document:last-child { page-break-after: auto; }
.signature { margin-top: 26pt; }
.source-hash { font-size: 7.5pt; color: #777; margin-top: 22pt;
               border-top: 1px solid #ddd; padding-top: 4pt; }
a { color: #111; text-decoration: none; }
"""


def _source_hash(package: Path) -> str:
    """A hash of every document that goes into the PDF."""
    digest = hashlib.sha256()
    for name in DOCUMENTS:
        digest.update(name.encode())
        digest.update((package / name).read_bytes())
    return digest.hexdigest()[:16]


def _chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    found = shutil.which("google-chrome") or shutil.which("chromium")
    return found


def _check(package: Path) -> list[str]:
    problems: list[str] = []
    for name in DOCUMENTS:
        path = package / name
        if not path.exists():
            problems.append(f"missing package document: {name}")
            continue
        heading = EXPECTED_HEADINGS.get(name)
        if heading and heading not in path.read_text():
            problems.append(f"{name} no longer starts with {heading!r}")
    return problems


def _html(source_hash: str, package: Path) -> str:
    """The package as one HTML document, with print styling."""
    parts: list[str] = []
    from_repo = package.resolve() == PACKAGE.resolve()
    regenerate = "python scripts/build_plco_cdas_pdf.py"
    origin = "the repository markdown"
    if not from_repo:
        regenerate = f"python scripts/build_plco_cdas_pdf.py --package-dir {package}"
        origin = "a local copy of the package"
    for name in DOCUMENTS:
        body = subprocess.run(
            [
                "pandoc",
                str(package / name),
                "--from=markdown",
                "--to=html5",
                "--standalone",
                # An empty title suppresses pandoc's own title block; the
                # document's own H1 is the heading we want.
                "--metadata=title=",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # Keep the body of each document, drop pandoc's own header.
        start = body.find("<body>")
        if start >= 0:
            body = body[start + len("<body>") :]
            end = body.rfind("</body>")
            if end >= 0:
                body = body[:end]
        parts.append(
            f'<section class="document">{body}'
            f'<p class="source-hash">PLCO CDAS submission package — '
            f'source hash {source_hash}. Generated from {origin}; '
            f"regenerate with <code>{regenerate}</code>.</p>"
            f"</section>"
        )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{STYLE}</style></head><body>" + "\n".join(parts) + "</body></html>"
    )


def _init_local(package: Path) -> int:
    """Copy the package into a local, gitignored directory to fill in.

    The committed package keeps the PI's and the Signing Official's details
    as markers, because the repository is public and a telephone number
    committed here cannot be taken back. This makes the copy they fill in.
    An existing copy is never overwritten, so a filled one cannot be lost
    by a second run.
    """
    target = BUILD / "package-private"
    if target.exists() and any(target.iterdir()):
        print(
            f"{target} already exists and is not empty; it may hold "
            "filled-in details, so it is left alone. Remove it yourself if "
            "you want a fresh copy.",
            file=sys.stderr,
        )
        return 1
    target.mkdir(parents=True, exist_ok=True)
    for name in DOCUMENTS:
        shutil.copy2(package / name, target / name)
    print(f"wrote a local copy of the package to {target}")
    print("fill in the [PI] and [SO] markers there, then print it with:")
    print(f"  python scripts/build_plco_cdas_pdf.py --package-dir {target}")
    print("(build/ is gitignored, so nothing in it reaches the repository)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the inputs and the toolchain, without building the PDF",
    )
    parser.add_argument(
        "--package-dir",
        default=str(PACKAGE),
        help=(
            "the directory holding the package markdown; point it at a local "
            "copy to print the PI's own details"
        ),
    )
    parser.add_argument(
        "--init-local",
        action="store_true",
        help=(
            "copy the package into build/package-private for the PI to fill in, "
            "and stop"
        ),
    )
    parser.add_argument(
        "--out",
        default=str(BUILD / "plco-cdas-submission-package.pdf"),
    )
    args = parser.parse_args(argv)

    package = Path(args.package_dir).expanduser()
    package = package if package.is_absolute() else (REPO / package)
    package = package.resolve()

    if args.init_local:
        return _init_local(package)

    problems = _check(package)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1

    if args.check:
        chrome = _chrome()
        pandoc = shutil.which("pandoc")
        print(
            "the package inputs are complete; "
            + (f"pandoc at {pandoc}" if pandoc else "pandoc is NOT installed")
            + "; "
            + (
                f"a browser for printing is available at {chrome}"
                if chrome
                else "no browser found for printing, the PDF cannot be built here"
            )
        )
        return 0

    chrome = _chrome()
    if chrome is None:
        print(
            "no Chrome or Chromium found, so the PDF cannot be printed here; "
            "run this on a machine that has one",
            file=sys.stderr,
        )
        return 1

    source_hash = _source_hash(package)
    html = _html(source_hash, package)
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "package.html"
        html_path.write_text(html)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={out_path}",
                html_path.as_uri(),
            ],
            capture_output=True,
            text=True,
        )
    if not out_path.exists() or out_path.stat().st_size == 0:
        print(f"the PDF was not produced: {result.stderr[-500:]}", file=sys.stderr)
        return 1
    print(f"wrote {out_path} ({out_path.stat().st_size // 1024} KiB)")
    print(f"source hash {source_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
