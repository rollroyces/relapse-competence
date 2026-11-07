#!/usr/bin/env python3
"""Download the GSE299684 supplementary matrices.

Each GEO sample contributes three 10x files: barcodes, features and matrix.
The file names are read from the sample's own ``suppl/`` directory rather
than assumed from the sample title, because two accessions in this deposit
carry file names that belong to the *other* accession — a submission-side
mislabelling. The accession-to-sample identity is taken from the GEO record,
which is authoritative, and the discrepancy is recorded in the manifest rather
than silently resolved.

    python scripts/download_gse299684.py --outdir data/gse299684
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

GEO = "https://ftp.ncbi.nlm.nih.gov/geo"
USER_AGENT = "relapse-competence-gse299684/0.1"

#: The 15 libraries of GSE299684. The accession, the GEO sample title and the
#: tissue are from the GEO record (``!Sample_title`` and
#: ``!Sample_source_name_ch1`` in the series matrix).
SAMPLES: list[tuple[str, str, str]] = [
    ("GSM9043712", "SC123_135A", "liver core needle biopsy"),
    ("GSM9043713", "SC123_140A", "liver core needle biopsy"),
    ("GSM9043714", "SC134_142A", "lymph node core needle biopsy"),
    ("GSM9043715", "SC134_145A", "head and neck core needle biopsy"),
    ("GSM9043716", "SC181_151B", "adrenal gland core needle biopsy"),
    ("GSM9043717", "SC229_233A", "liver core needle biopsy"),
    ("GSM9043718", "SC267_162B", "lung core needle biopsy"),
    ("GSM9043719", "SC267_262A", "lung surgical resection"),
    ("GSM9043720", "SC324_SC279A", "brain surgical resection"),
    ("GSM9043721", "SC409_SC363A", "brain surgical resection"),
    ("GSM9043722", "SC354_SC396-A", "lung core needle biopsy"),
    ("GSM9043723", "SC419_SC416A", "lung/mediastinal core needle biopsy"),
    ("GSM9043724", "SC419_SC439A", "head and neck core needle biopsy"),
    ("GSM9043725", "SC429_SC437A", "retroperitoneal core needle biopsy"),
    ("GSM9043726", "SC437_SC370A", "adrenal gland core needle biopsy"),
]

SUFFIXES = ("barcodes.tsv.gz", "features.tsv.gz", "matrix.mtx.gz")


def _bucket(gsm: str) -> str:
    """The GEO FTP bucket directory for a sample accession."""
    return gsm[:-3] + "nnn"


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8", "replace")


def _list_supplementary(gsm: str) -> list[str]:
    """The file names actually deposited for a sample."""
    listing = _fetch_text(f"{GEO}/samples/{_bucket(gsm)}/{gsm}/suppl/")
    return [
        name
        for name in re.findall(r'href="([^"]+)"', listing)
        if name.endswith(SUFFIXES)
    ]


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=600) as response:
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                handle.write(chunk)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default="data/gse299684")
    args = parser.parse_args(argv)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    manifest_rows: list[str] = []
    for gsm, title, tissue in SAMPLES:
        try:
            deposited = sorted(_list_supplementary(gsm))
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            failures.append(f"{gsm}: {exc}")
            print(f"  FAILED to list {gsm}: {exc}", flush=True)
            continue

        prefix = None
        for name in deposited:
            destination = outdir / name
            if not (destination.exists() and destination.stat().st_size > 0):
                try:
                    _download(f"{GEO}/samples/{_bucket(gsm)}/{gsm}/suppl/{name}", destination)
                    print(f"  {name} ({destination.stat().st_size:,} bytes)", flush=True)
                except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                    failures.append(f"{name}: {exc}")
                    print(f"  FAILED {name}: {exc}", flush=True)
            if name.endswith(".barcodes.tsv.gz"):
                prefix = name[: -len(".barcodes.tsv.gz")]

        if prefix is None:
            failures.append(f"{gsm}: no supplementary files listed")
            continue
        stem = prefix[len(gsm) + 1 :] if prefix.startswith(gsm + "_") else prefix
        mismatch = stem != title
        if mismatch:
            print(
                f"  NOTE {gsm}: deposited file names say '{stem}', the GEO record "
                f"says '{title}'; the accession identity is used and the "
                "discrepancy is recorded in the manifest",
                flush=True,
            )
        manifest_rows.append(
            f"{gsm}\t{stem}\t{title}\t{tissue}\t{'yes' if mismatch else 'no'}"
        )

    manifest = outdir / "manifest.tsv"
    manifest.write_text(
        "accession\tfile_prefix\tgeo_title\ttissue\tfilename_mismatch\n"
        + "".join(row + "\n" for row in manifest_rows),
        encoding="utf-8",
    )
    print(f"wrote {manifest}")
    if failures:
        print(f"{len(failures)} problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
