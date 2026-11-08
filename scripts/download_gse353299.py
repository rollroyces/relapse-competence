#!/usr/bin/env python3
"""Download the GSE353299 supplementary matrices.

GSE353299 is the GEO deposit of the KRT17+ drug-tolerant-persister study in
EGFR-mutant NSCLC: 25 single-cell libraries of lung adenocarcinoma collected
at treatment-naive, osimertinib-treated minimal-residual-disease and
progression timepoints.

The sample table is discovered from GEO rather than hardcoded: the archive
listing gives the deposited file names, and each sample's own record gives
the title, the tissue and the treatment timepoint. The deposited file names
are read from each sample's own directory, because a previous deposit in this
repository (GSE299684) carried file names belonging to a different accession.

    python scripts/download_gse353299.py --outdir data/gse353299
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

GEO = "https://ftp.ncbi.nlm.nih.gov/geo"
SERIES = "GSE353299"
BUCKET = "GSE353nnn"
FILELIST = f"{GEO}/series/{BUCKET}/{SERIES}/suppl/filelist.txt"
ACC = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={gsm}&targ=self&form=text&view=brief"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
SUFFIXES = ("barcodes.tsv.gz", "features.tsv.gz", "matrix.mtx.gz")


def _get(url: str, ua: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8", "replace")


def _bucket(gsm: str) -> str:
    return gsm[:-3] + "nnn"


def _sample_record(gsm: str) -> dict[str, object]:
    """The GEO record of one sample: title, tissue, timepoint."""
    text = _get(ACC.format(gsm=gsm), BROWSER_UA)

    def field(name: str) -> str:
        match = re.search(rf"^{re.escape(name)} = (.*)$", text, flags=re.M)
        return match.group(1).strip() if match else ""

    characteristics = re.findall(
        r"^!Sample_characteristics_ch1 = (.*)$", text, flags=re.M
    )
    parsed: dict[str, str] = {}
    for entry in characteristics:
        key, _, value = entry.partition(":")
        parsed[key.strip().lower()] = value.strip()
    return {
        "title": field("!Sample_title"),
        "source": field("!Sample_source_name_ch1"),
        "tissue": parsed.get("tissue", ""),
        "treatment": parsed.get("treatment", ""),
        "genotype": parsed.get("genotype", ""),
        "cell_type": parsed.get("cell type", ""),
    }


def _deposited_files(gsm: str) -> list[str]:
    listing = _get(f"{GEO}/samples/{_bucket(gsm)}/{gsm}/suppl/", BROWSER_UA)
    return [n for n in re.findall(r'href="([^"]+)"', listing) if n.endswith(SUFFIXES)]


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    with urllib.request.urlopen(request, timeout=900) as response:
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                handle.write(chunk)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default="data/gse353299")
    args = parser.parse_args(argv)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 1. which samples, and what are their deposited file names?
    listing = _get(FILELIST, BROWSER_UA)
    candidates: list[tuple[str, str]] = []
    for line in listing.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) < 5 or not parts[1].endswith(".barcodes.tsv.gz"):
            continue
        name = parts[1]
        gsm = name.split("_")[0]
        stem = name[: -len(".barcodes.tsv.gz")]
        candidates.append((gsm, stem[len(gsm) + 1 :] if stem.startswith(gsm + "_") else stem))
    print(f"{len(candidates)} samples in the archive listing", flush=True)

    manifest: list[dict[str, object]] = []
    failures: list[str] = []
    for gsm, stem in candidates:
        try:
            deposited = sorted(_deposited_files(gsm))
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            failures.append(f"{gsm}: {exc}")
            print(f"  FAILED to list {gsm}: {exc}", flush=True)
            continue

        prefix = None
        for name in deposited:
            destination = outdir / name
            if not (destination.exists() and destination.stat().st_size > 0):
                try:
                    _download(
                        f"{GEO}/samples/{_bucket(gsm)}/{gsm}/suppl/{name}", destination
                    )
                    print(f"  {name} ({destination.stat().st_size:,} bytes)", flush=True)
                except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                    failures.append(f"{name}: {exc}")
                    print(f"  FAILED {name}: {exc}", flush=True)
            if name.endswith(".barcodes.tsv.gz"):
                prefix = name[: -len(".barcodes.tsv.gz")]
        if prefix is None:
            failures.append(f"{gsm}: no supplementary files listed")
            continue

        record = _sample_record(gsm)
        actual_stem = (
            prefix[len(gsm) + 1 :] if prefix.startswith(gsm + "_") else prefix
        )
        record["accession"] = gsm
        record["file_prefix"] = actual_stem
        record["filename_mismatch"] = actual_stem != stem
        manifest.append(record)
        print(
            f"  {gsm}: {record['tissue']} | {record['treatment']} | {record['title']}",
            flush=True,
        )
        time.sleep(0.4)

    manifest_path = outdir / "manifest.tsv"
    with manifest_path.open("w", encoding="utf-8") as handle:
        handle.write(
            "accession\tfile_prefix\tgeo_title\ttissue\ttreatment\tgenotype\t"
            "cell_type\tfilename_mismatch\n"
        )
        for record in manifest:
            handle.write(
                "\t".join(
                    [
                        str(record["accession"]),
                        str(record["file_prefix"]),
                        str(record["title"]),
                        str(record["tissue"]),
                        str(record["treatment"]),
                        str(record["genotype"]),
                        str(record["cell_type"]),
                        "yes" if record["filename_mismatch"] else "no",
                    ]
                )
                + "\n"
            )
    print(f"wrote {manifest_path}")
    print(
        "timepoints: "
        + json.dumps(
            {
                treatment: sum(
                    1 for r in manifest if r["treatment"] == treatment
                )
                for treatment in sorted({str(r["treatment"]) for r in manifest})
            }
        )
    )
    if failures:
        print(f"{len(failures)} problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
