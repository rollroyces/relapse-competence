#!/usr/bin/env python3
"""Is the relapse-competent state already present before therapy?

GSE138474 (Stewart et al., *Single-cell analyses reveal increasing
intatumoral heterogeneity as an essential component of treatment resistance in
small cell lung cancer*, Cancer Res 2021) is the treatment-naive comparator
this programme was missing. Its GEO record labels every library with the
treatment that model received — ``untreated``, ``vehicle-treated``,
``cisplatin, relapsed``, ``talazoparib, relapsed``, ``prexasertib,
relapsed`` — and several models appear in more than one arm, so the contrast
is within-model as well as between-arm.

The gate review records that "for relapsed SCLC there is no treatment-naive
comparator at all", and that K2 is *not evaluable* for want of one. This
script supplies the comparator and asks the question the gate names: **does
the YAP1(+) state that marks the relapsed population in GSE299684 exist in
untreated SCLC?**

Design notes
------------

**The ruler is imported, not re-implemented.** The state call, the cell-type
modules, the state-validation signature, the channel statistics and the
multiple-testing correction are loaded from
``scripts/gse299684_state_expression.py``. The relapsed cohort and this
cohort are therefore measured on one definition, and a difference between
them cannot be a difference in the definition.

**The matrices are streamed, not stored.** Each library is a 62 MB tar.gz
containing an uncompressed 10x triplet whose matrix is about 250 MB and
20 million non-zeros. The machine this ran on had 1.1 GB of free disk, so the
deposit is read over the network and reduced in memory: only the genes the
analysis needs are kept, together with the per-cell library sizes, detected
gene counts and mitochondrial counts that the quality filter needs. Nothing
is written to disk except one small per-library summary, which makes the run
resumable.

**The decision rule is fixed before the measurement.** The gate names a
treatment-naive SCLC cohort showing the state is already present before
therapy as the thing that would change the K2 verdict. "Present" is given a
number here, anchored to a number the programme already uses: the pooled
relapsed-SCLC state fraction measured on GSE299684. The state counts as
present before therapy if the median per-library state fraction in the
untreated arm reaches **half of that pooled relapsed value**. The
untreated-versus-relapsed contrast is reported whatever the rule returns, so
the reader sees the effect size and not only the verdict.

**A null result must be distinguishable from a broken pipeline.** The state
call is validated against an axis the state paper reports independently —
YAP1(+) cells co-express CD276 (B7-H3), TACSTD2 (TROP2) and ERBB2, and lose
DLL3, SEZ6 and CEACAM5 — and none of those six genes is an ion channel. The
housekeeping genes are carried as a negative control: if they move with the
state, the pipeline is at fault rather than the biology.

Run
---
    python scripts/gse138474_state_expression.py
    python scripts/gse138474_state_expression.py --samples 3      # a subset
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import itertools
import json
import re
import statistics
import sys
import tarfile
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.stats import mannwhitneyu

REPO = Path(__file__).resolve().parents[1]


def _load_core():
    spec = importlib.util.spec_from_file_location(
        "gse299684_state_expression", REPO / "scripts" / "gse299684_state_expression.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = _load_core()

CHANNELS = core.CHANNELS
STATE_GENE = core.YAP1_GENE
STATE_VALIDATION_UP = core.STATE_VALIDATION_UP
STATE_VALIDATION_DOWN = core.STATE_VALIDATION_DOWN
CONTROL_GENES = core.CONTROL_GENES
STATE_DEFINITIONS = core.STATE_DEFINITIONS
PRIMARY_DEFINITION = core.PRIMARY_DEFINITION

#: The quality thresholds are the ones the relapsed cohort used, so the two
#: cohorts are filtered the same way.
QC_MIN_GENES = 200
QC_MIN_COUNTS = 500
QC_MAX_MITO = 0.20

#: The pooled relapsed-SCLC state fraction measured on GSE299684, which is
#: the anchor for the pre-registered "already present before therapy"
#: threshold. The threshold is half of it, and it is read from that cohort's
#: own artefact rather than written down here, so the two cannot drift apart.
RELAPSED_SCLC_STATE_FRACTION = 0.104
RELAPSED_ARTIFACT = Path("results/gse299684/state_expression.json")


def _relapsed_pooled_state_fraction() -> float | None:
    """The relapsed cohort's pooled state fraction, read from its artefact."""
    if not RELAPSED_ARTIFACT.exists():
        return None
    data = json.loads(RELAPSED_ARTIFACT.read_text())
    sweep = data["state_definition_sweep"]
    primary = next(
        entry for entry in sweep if entry["definition"] == "detected"
    )
    positive = primary["n_yap1_positive"]
    negative = primary["n_yap1_negative"]
    return positive / (positive + negative)


def _present_before_therapy_threshold() -> tuple[float, str]:
    """Half the relapsed cohort's pooled state fraction, and where it came from."""
    pooled = _relapsed_pooled_state_fraction()
    if pooled is None:
        return (
            RELAPSED_SCLC_STATE_FRACTION / 2,
            "half the pooled relapsed-SCLC state fraction measured on "
            f"GSE299684 ({RELAPSED_SCLC_STATE_FRACTION}), which the artefact "
            "for that cohort did not supply at run time",
        )
    return (
        pooled / 2,
        "half the pooled relapsed-SCLC state fraction measured on GSE299684 "
        f"({pooled}), read from that cohort's artefact",
    )

USER_AGENT = "relapse-competence-gse138474/0.1"

GEO = "https://ftp.ncbi.nlm.nih.gov/geo/samples"

#: The libraries of GSE138474 that have a deposited matrix, with the
#: treatment label from the GEO record (``!Sample_characteristics_ch1``) and
#: the sample title. The titles carry the model: ``SC4`` is one
#: patient-derived model sampled before and after different treatments.
#: ``SC55`` is a circulating-tumour-cell series and is kept apart from the
#: solid-tissue contrast.
SAMPLES: list[dict] = [
    {"gsm": "GSM4104144", "title": "SC16.LB17028", "model": "SC16", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104145", "title": "SC16.LB17029", "model": "SC16", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104146", "title": "SC39.LB17018", "model": "SC39", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104147", "title": "SC39.LB17019", "model": "SC39", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104148", "title": "SC39.LB17020", "model": "SC39", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104149", "title": "SC49.LB17023", "model": "SC49", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104150", "title": "SC49.LB17024", "model": "SC49", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104151", "title": "SC49.LB17025", "model": "SC49", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104152", "title": "SC4.LB17009", "model": "SC4", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104153", "title": "SC4.LB17013", "model": "SC4", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104154", "title": "SC4.LB17014", "model": "SC4", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104155", "title": "SC55-1.LB17001", "model": "SC55", "tissue": "CTC", "treatment": "untreated", "compartment": "ctc"},
    {"gsm": "GSM4104156", "title": "SC55-2.LB17002", "model": "SC55", "tissue": "CTC", "treatment": "cisplatin", "compartment": "ctc"},
    {"gsm": "GSM4104157", "title": "SC55-3.LB17026", "model": "SC55", "tissue": "CTC", "treatment": "cisplatin, relapsed", "compartment": "ctc"},
    {"gsm": "GSM4104158", "title": "SC4_LY2606368.LB17003", "model": "SC4", "tissue": "CDX flank", "treatment": "prexasertib, relapsed", "compartment": "pdx"},
    {"gsm": "GSM4104159", "title": "SC4_LY2606368.LB17016", "model": "SC4", "tissue": "CDX flank", "treatment": "prexasertib, relapsed", "compartment": "pdx"},
    {"gsm": "GSM4104160", "title": "SC4_Talazoparib.LB17004", "model": "SC4", "tissue": "CDX flank", "treatment": "talazoparib, relapsed", "compartment": "pdx"},
    {"gsm": "GSM4104161", "title": "SC4_Talazoparib.LB17011", "model": "SC4", "tissue": "CDX flank", "treatment": "talazoparib, relapsed", "compartment": "pdx"},
    {"gsm": "GSM4104162", "title": "SC4_Talazoparib.LB17015", "model": "SC4", "tissue": "CDX flank", "treatment": "talazoparib, relapsed", "compartment": "pdx"},
    {"gsm": "GSM4104163", "title": "SC55.LB19001", "model": "SC55", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4104164", "title": "SC68_cr.LB19003", "model": "SC68", "tissue": "CDX flank", "treatment": "cisplatin, relapsed", "compartment": "pdx"},
    {"gsm": "GSM4104165", "title": "SC68. LB19002", "model": "SC68", "tissue": "CDX flank", "treatment": "vehicle-treated", "compartment": "pdx"},
    {"gsm": "GSM4104166", "title": "SC75.LB19004", "model": "SC75", "tissue": "CDX flank", "treatment": "untreated", "compartment": "pdx"},
    {"gsm": "GSM4851437", "title": "SC53cis", "model": "SC53", "tissue": "CDX flank", "treatment": "cisplatin, relapsed", "compartment": "pdx"},
    {"gsm": "GSM4851438", "title": "SC53", "model": "SC53", "tissue": "CDX flank", "treatment": "vehicle-treated", "compartment": "pdx"},
]

#: The arms the contrast is drawn from. "no chemo" pools the untreated
#: libraries with the vehicle-treated ones, because a vehicle is no active
#: drug; the two are also reported separately, because the vehicle arm is
#: the proper control for the relapsed libraries of the same models.
ARMS = ("untreated", "vehicle", "relapsed", "no chemo")


def _arm(treatment: str) -> str:
    if treatment == "untreated":
        return "untreated"
    if treatment == "vehicle-treated":
        return "vehicle"
    if "relapsed" in treatment:
        return "relapsed"
    return "other"


def _bucket(accession: str) -> str:
    """The GEO FTP bucket directory for a sample accession."""
    return accession[:-3] + "nnn"


def _read_manifest(path: Path) -> dict[str, str]:
    """The file names already resolved, if a manifest exists."""
    if not path.exists():
        return {}
    resolved: dict[str, str] = {}
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        accession, name = line.split("\t", 1)
        resolved[accession] = name
    return resolved


def _write_manifest(path: Path, resolved: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["accession\tdeposited_file_name"]
    for accession in sorted(resolved):
        lines.append(f"{accession}\t{resolved[accession]}")
    path.write_text("\n".join(lines) + "\n")


def _list_sample_files(accession: str) -> list[str]:
    """The file names actually deposited for a sample.

    The file names are read from the sample's own directory rather than
    assumed from the sample title: in this deposit the title and the file
    name disagree, and the file name recorded in the GEO metadata disagrees
    with the file name on disk. The deposit has to be read, not assumed.

    GEO refuses directory listings after a burst of requests, so the
    listing is retried with a back-off and the resolved names are kept in a
    manifest, which means a re-run does not ask the server again.
    """
    url = f"{GEO}/{_bucket(accession)}/{accession}/suppl/"
    last: Exception | None = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                listing = response.read().decode("utf-8", "replace")
            names = re.findall(r'href="([^"?/][^"]*)"', listing)
            return [name for name in names if name.endswith(".tar.gz")]
        except Exception as error:  # noqa: BLE001 - retried below
            last = error
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{accession}: the deposited files could not be listed: {last}")


def _sample_url(sample: dict, manifest: dict[str, str]) -> str:
    """The deposit URL of one sample's matrix tarball."""
    accession = sample["gsm"]
    if accession in manifest:
        chosen = manifest[accession]
    else:
        files = _list_sample_files(accession)
        if not files:
            raise RuntimeError(f"{accession}: no deposited tarball was found")
        preferred = [name for name in files if "matrix" in name]
        chosen = sorted(preferred or files)[0]
        manifest[accession] = chosen
    sample["deposited_file_name"] = chosen
    return f"{GEO}/{_bucket(accession)}/{accession}/suppl/{urllib.parse.quote(chosen)}"


def _target_genes() -> tuple[set[str], set[str]]:
    """The genes the analysis needs, and the mitochondrial genes."""
    wanted: set[str] = set(CHANNELS)
    wanted.add(STATE_GENE)
    wanted.update(STATE_VALIDATION_UP)
    wanted.update(STATE_VALIDATION_DOWN)
    wanted.update(CONTROL_GENES)
    for module in core.CELL_TYPE_MARKERS.values():
        wanted.update(module)
    return wanted, set()


class _MemberStream(io.RawIOBase):
    """A readable, non-seekable view of one member of a streamed tarball.

    ``tarfile`` in stream mode returns an object that cannot be wrapped by
    ``io.TextIOWrapper`` directly, because the wrapper asks whether the
    stream is seekable and the tar reader has no such method. This adapter
    answers the question and reads line by line, so a 250 MB matrix never
    has to be held in memory.
    """

    def __init__(self, handle):
        self._handle = handle

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def read(self, size: int = -1) -> bytes:
        return self._handle.read(size)

    def readinto(self, buffer) -> int:
        data = self._handle.read(len(buffer))
        length = len(data)
        buffer[:length] = data
        return length


#: The member names the deposit uses for the 10x triplet. They are not
#: uniform: most libraries deposit ``barcodes.tsv`` / ``genes.tsv`` /
#: ``matrix.mtx`` and some deposit the same three files with a ``.txt``
#: extension, so the names are matched rather than assumed. The names
#: actually found are recorded per library.
MEMBER_NAMES = {
    "barcodes.tsv": "barcodes",
    "barcodes.txt": "barcodes",
    "genes.tsv": "genes",
    "genes.txt": "genes",
    "matrix.mtx": "matrix",
    "matrix.txt": "matrix",
}

#: The triplet members are matched on their suffix rather than on their
#: whole name: some libraries deposit them bare and some prefix them with
#: the sample name (``SC53cis.genes.tsv``).
MEMBER_SUFFIXES = tuple(MEMBER_NAMES.items())


def _stream_members(url: str):
    """Yield the triplet members of the sample tarball, in stream order."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=600) as response:
        with tarfile.open(fileobj=response, mode="r|gz") as archive:
            for member in archive:
                base = member.name.split("/")[-1]
                canonical = None
                for suffix, kind in MEMBER_SUFFIXES:
                    if base.endswith(suffix):
                        canonical = kind
                        break
                if canonical is None:
                    continue
                handle = archive.extractfile(member)
                if handle is not None:
                    yield canonical, base, handle


def _parse_sample(url: str) -> dict:
    """Stream one library and reduce it to what the analysis needs.

    Returns the library's dimensions, the per-cell library size, detected
    gene count and mitochondrial count (so the quality filter can be applied
    exactly as on the relapsed cohort), and a genes-by-cells matrix holding
    only the genes the analysis reads.
    """
    wanted, _ = _target_genes()
    gene_symbols: list[str] = []
    n_cells = 0
    entries: list[tuple[int, int, int]] = []
    totals = np.zeros(0)
    detected = np.zeros(0)
    mito = np.zeros(0)
    n_genes = 0
    nnz = 0
    kept_symbols: list[str] = []
    position: dict[str, int] = {}
    row_of_gene_index: dict[int, int] = {}
    mito_rows: set[int] = set()

    member_names: dict[str, str] = {}
    for name, base, handle in _stream_members(url):
        member_names[name] = base
        if name == "barcodes":
            text = io.TextIOWrapper(_MemberStream(handle), encoding="utf-8", errors="replace")
            n_cells = sum(1 for line in text if line.strip())
            text.close()
        elif name == "genes":
            text = io.TextIOWrapper(_MemberStream(handle), encoding="utf-8", errors="replace")
            gene_symbols = [
                line.rstrip("\n").split("\t")[1] for line in text if line.strip()
            ]
            text.close()
            # The reduced matrix keeps one row per symbol the analysis reads,
            # in the order the deposit lists them.
            seen: set[str] = set()
            for index, symbol in enumerate(gene_symbols):
                if symbol.startswith("MT-"):
                    mito_rows.add(index)
                if symbol not in wanted and not symbol.startswith("MT-"):
                    continue
                if symbol in seen:
                    continue
                seen.add(symbol)
                position[symbol] = len(kept_symbols)
                kept_symbols.append(symbol)
                row_of_gene_index[index] = position[symbol]
        elif name == "matrix":
            if not gene_symbols:
                raise RuntimeError(
                    "the gene list comes after the matrix in this tarball; "
                    "the deposit has to be read in two passes"
                )
            text = io.TextIOWrapper(_MemberStream(handle), encoding="utf-8", errors="replace")
            header = next(text, "")
            rows: list[int] = []
            cols: list[int] = []
            vals: list[int] = []
            if header.startswith("%%MatrixMarket"):
                matrix_format = "matrixmarket"
                n_genes, n_cells_matrix, nnz = 0, 0, 0
                for line in text:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("%"):
                        continue
                    n_genes, n_cells_matrix, nnz = (int(x) for x in stripped.split())
                    break
                if n_cells and n_cells_matrix != n_cells:
                    raise RuntimeError(
                        f"the matrix has {n_cells_matrix} columns but the barcode "
                        f"file has {n_cells} rows"
                    )
                totals = np.zeros(n_cells_matrix, dtype=np.float64)
                detected = np.zeros(n_cells_matrix, dtype=np.int64)
                mito = np.zeros(n_cells_matrix, dtype=np.float64)
                for line in text:
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    gene = int(parts[0]) - 1
                    cell = int(parts[1]) - 1
                    value = int(parts[2])
                    totals[cell] += value
                    detected[cell] += 1
                    if gene in mito_rows:
                        mito[cell] += value
                    row = row_of_gene_index.get(gene)
                    if row is not None:
                        rows.append(row)
                        cols.append(cell)
                        vals.append(value)
            else:
                # The deposit is not uniform: one library ships the matrix as
                # a dense tab-separated table, one row per gene and one
                # column per cell, with no MatrixMarket header. The shape is
                # checked against the gene and barcode lists before it is
                # read, so a transposed table is refused rather than
                # silently misread.
                matrix_format = "dense_tsv"
                n_cells_matrix = n_cells
                totals = np.zeros(n_cells_matrix, dtype=np.float64)
                detected = np.zeros(n_cells_matrix, dtype=np.int64)
                mito = np.zeros(n_cells_matrix, dtype=np.float64)
                gene_index = 0
                # The first line was read to tell the formats apart; in the
                # dense table there is no header, so it is the first gene's
                # row and it has to be processed like every other row.
                for line in itertools.chain([header], text):
                    if not line.strip():
                        continue
                    fields = line.rstrip("\n").split("\t")
                    if len(fields) != n_cells_matrix:
                        raise RuntimeError(
                            f"the dense matrix row {gene_index} has {len(fields)} "
                            f"fields, expected {n_cells_matrix}; the table may "
                            "be transposed"
                        )
                    values = np.fromstring(line, dtype=np.int64, sep="\t")
                    totals += values
                    detected += (values > 0)
                    if gene_index in mito_rows:
                        mito += values
                    row = row_of_gene_index.get(gene_index)
                    if row is not None:
                        nonzero = np.flatnonzero(values)
                        if nonzero.size:
                            rows.extend([row] * nonzero.size)
                            cols.extend(nonzero.tolist())
                            vals.extend(values[nonzero].tolist())
                    gene_index += 1
                if gene_index != len(gene_symbols):
                    raise RuntimeError(
                        f"the dense matrix has {gene_index} rows but the gene "
                        f"list has {len(gene_symbols)}"
                    )
                n_genes = gene_index
                nnz = 0
            text.close()
            entries = list(zip(rows, cols, vals, strict=False))

    if not gene_symbols:
        raise RuntimeError("the gene list was not found in the tarball")
    n_genes = len(gene_symbols)

    row_index = [entry[0] for entry in entries]
    col_index = [entry[1] for entry in entries]
    data = [entry[2] for entry in entries]
    matrix = sparse.csr_matrix(
        (data, (row_index, col_index)),
        shape=(len(kept_symbols), n_cells),
        dtype=np.float32,
    )
    return {
        "member_names": member_names,
        "matrix_format": matrix_format,
        "n_genes": n_genes,
        "n_cells": n_cells,
        "nnz": nnz,
        "gene_symbols": kept_symbols,
        "matrix": matrix,
        "totals": totals,
        "detected": detected,
        "mito": mito,
    }


def _qc_keep(totals: np.ndarray, detected: np.ndarray, mito: np.ndarray) -> np.ndarray:
    """The cells that pass quality control, on the relapsed cohort's rules."""
    with np.errstate(invalid="ignore", divide="ignore"):
        mito_fraction = np.divide(
            mito, totals, out=np.zeros_like(totals), where=totals > 0
        )
    keep = (
        (detected >= QC_MIN_GENES)
        & (totals >= QC_MIN_COUNTS)
        & (mito_fraction <= QC_MAX_MITO)
    )
    return np.flatnonzero(keep)


def _normalise(matrix: sparse.csr_matrix, totals: np.ndarray, target: float = 1e4):
    """Counts per cell to a fixed library size, then log1p.

    The library size is the cell's total over *all* genes, not over the
    reduced set, so the normalisation is the one the relapsed cohort used.
    """
    scale = np.divide(
        target, totals, out=np.zeros_like(totals), where=totals > 0
    )
    scaled = matrix.multiply(scale).tocsr()
    scaled.data = np.log1p(scaled.data)
    return scaled


def _library_summary(sample: dict, parsed: dict) -> dict:
    """Everything this script reports about one library."""
    matrix: sparse.csr_matrix = parsed["matrix"]
    totals = parsed["totals"]
    keep = _qc_keep(totals, parsed["detected"], parsed["mito"])
    if len(keep) == 0:
        raise RuntimeError("no cell passed the quality filter")
    # The quality filter comes first, exactly as on the relapsed cohort: the
    # cell types and the state are called on the cells that passed, not on
    # the raw library.
    matrix = matrix[:, keep]
    totals = totals[keep]
    detected_kept = parsed["detected"][keep]
    gene_index = {symbol: i for i, symbol in enumerate(parsed["gene_symbols"])}
    normalised = _normalise(matrix, totals)
    labels = core.assign_cell_types(normalised, gene_index)
    malignant = labels == "malignant"
    immune = np.isin(
        labels, ["t_nk", "myeloid", "b_plasma", "endothelial", "fibroblast"]
    )
    values = {
        symbol: np.asarray(normalised[gene_index[symbol]].todense()).ravel()
        for symbol in parsed["gene_symbols"]
        if symbol in gene_index
    }
    yap1_counts = core.raw_counts(matrix, gene_index, STATE_GENE)
    yap1_expression = core.gene_values(normalised, gene_index, STATE_GENE)

    definitions = {}
    for definition, description in STATE_DEFINITIONS:
        entry = core._definition_entry(
            definition,
            description,
            labels,
            yap1_counts,
            yap1_expression,
            values,
            immune,
        )
        positive, negative = core.state_masks(
            definition, labels, yap1_counts, yap1_expression
        )
        n_malignant = int(malignant.sum())
        entry["state_fraction"] = (
            float(positive.sum() / n_malignant) if n_malignant else None
        )
        entry["n_malignant"] = n_malignant
        # The top-decile definition degenerates when the state is rare: the
        # 90th percentile of a mostly-zero distribution is zero, so every
        # malignant cell passes the threshold. The flag says so rather than
        # letting a 1.0 be read as a state fraction.
        if definition == "top_decile":
            threshold = (
                float(np.quantile(yap1_expression[malignant], 0.9))
                if malignant.any()
                else 0.0
            )
            entry["threshold"] = threshold
            entry["degenerate_zero_threshold"] = bool(threshold <= 0.0)
        definitions[definition] = entry

    # The complexity control. A state that is simply harder to sequence would
    # show fewer detected genes everywhere, so the state fraction could fall
    # without the state being absent. The relapsed cohort's medians are the
    # reference.
    positive, negative = core.state_masks(
        PRIMARY_DEFINITION, labels, yap1_counts, yap1_expression
    )
    totals_kept = totals
    complexity = {
        "median_genes_detected": (
            float(np.median(detected_kept)) if len(detected_kept) else None
        ),
        "median_genes_detected_yap1_positive": (
            float(np.median(detected_kept[positive])) if positive.any() else None
        ),
        "median_genes_detected_yap1_negative": (
            float(np.median(detected_kept[negative])) if negative.any() else None
        ),
        "median_counts_per_cell": (
            float(np.median(totals_kept)) if len(totals_kept) else None
        ),
        "n_cells_measured": int(len(detected_kept)),
    }

    # The housekeeping control: if it moves with the state, the pipeline is
    # at fault rather than the biology.
    control = {}
    positive, negative = core.state_masks(
        PRIMARY_DEFINITION, labels, yap1_counts, yap1_expression
    )
    for gene in CONTROL_GENES:
        series = values.get(gene)
        if series is None:
            continue
        pos = series[positive]
        neg = series[negative]
        control[gene] = {
            "mean_yap1_positive": float(pos.mean()) if len(pos) else None,
            "mean_yap1_negative": float(neg.mean()) if len(neg) else None,
            "detection_yap1_positive": float((pos > 0).mean()) if len(pos) else None,
            "detection_yap1_negative": float((neg > 0).mean()) if len(neg) else None,
        }

    cell_counts = {
        name: int((labels == name).sum()) for name in core.CELL_TYPE_MARKERS
    }
    cell_counts["unassigned"] = int((labels == "unassigned").sum())

    return {
        "accession": sample["gsm"],
        "title": sample["title"],
        "model": sample["model"],
        "tissue": sample["tissue"],
        "treatment": sample["treatment"],
        "arm": _arm(sample["treatment"]),
        "compartment": sample["compartment"],
        "url": sample.get("url", ""),
        "deposited_file_name": sample.get("deposited_file_name", ""),
        "member_names": parsed["member_names"],
        "matrix_format": parsed["matrix_format"],
        "n_genes": parsed["n_genes"],
        "n_cells": parsed["n_cells"],
        "nnz": parsed["nnz"],
        "n_cells_passing_qc": int(len(keep)),
        "cell_types": cell_counts,
        "state_definitions": definitions,
        "controls": control,
        "complexity": complexity,
    }


def _arm_statistics(libraries: list[dict], definition: str) -> dict:
    """The per-arm state fraction, and the untreated-versus-relapsed contrast.

    The arms are read from the solid-tissue libraries only. The circulating
    tumour-cell series is a different compartment with a different depth
    profile, and it is reported separately rather than pooled in.
    """
    by_arm: dict[str, list[float]] = {}
    by_arm_model: dict[str, list[tuple[str, float]]] = {}
    ctc: list[float] = []
    for library in libraries:
        fraction = library["state_definitions"][definition]["state_fraction"]
        if fraction is None:
            continue
        if library["compartment"] != "pdx":
            ctc.append(fraction)
            continue
        by_arm.setdefault(library["arm"], []).append(fraction)
        if library["arm"] in {"untreated", "vehicle"}:
            by_arm.setdefault("no chemo", []).append(fraction)
        by_arm_model.setdefault(library["model"], []).append(
            (library["arm"], fraction)
        )
    arms = {}
    for arm, values in by_arm.items():
        arms[arm] = {
            "n_libraries": len(values),
            "median_state_fraction": float(statistics.median(values)) if values else None,
            "min_state_fraction": float(min(values)) if values else None,
            "max_state_fraction": float(max(values)) if values else None,
            "state_fraction": [float(v) for v in values],
        }
    if ctc:
        arms["ctc_all"] = {
            "n_libraries": len(ctc),
            "median_state_fraction": float(statistics.median(ctc)),
            "min_state_fraction": float(min(ctc)),
            "max_state_fraction": float(max(ctc)),
            "state_fraction": [float(v) for v in ctc],
        }
    contrast = {}
    untreated = by_arm.get("untreated", []) + by_arm.get("vehicle", [])
    relapsed = by_arm.get("relapsed", [])
    if untreated and relapsed:
        test = mannwhitneyu(untreated, relapsed, alternative="two-sided")
        contrast = {
            "untreated_or_vehicle_vs_relapsed": {
                "n_untreated_or_vehicle": len(untreated),
                "n_relapsed": len(relapsed),
                "median_untreated_or_vehicle": float(statistics.median(untreated)),
                "median_relapsed": float(statistics.median(relapsed)),
                "mannwhitney_p": float(test.pvalue),
            }
        }
    # Within-model pairs: the same patient-derived model, before and after
    # treatment. A model that contributes both arms is the cleanest contrast
    # in the deposit.
    pairs = []
    for model, entries in sorted(by_arm_model.items()):
        arms_present = {arm for arm, _ in entries}
        if "relapsed" in arms_present and (
            "untreated" in arms_present or "vehicle" in arms_present
        ):
            before = [
                value
                for arm, value in entries
                if arm in {"untreated", "vehicle"}
            ]
            after = [value for arm, value in entries if arm == "relapsed"]
            pairs.append(
                {
                    "model": model,
                    "n_before": len(before),
                    "n_after": len(after),
                    "median_before": float(statistics.median(before)),
                    "median_after": float(statistics.median(after)),
                    "after_minus_before": float(
                        statistics.median(after) - statistics.median(before)
                    ),
                    "relapse_raises_state_fraction": bool(
                        statistics.median(after) > statistics.median(before)
                    ),
                }
            )
    if pairs:
        contrast["within_model_pairs"] = pairs
    return {"arms": arms, "contrast": contrast}


def _decision(arms: dict, threshold: float, threshold_basis: str) -> dict:
    """The pre-registered rule, applied to the untreated arm.

    The rule itself is fixed: the state counts as present before therapy if
    the untreated arm's median per-library state fraction reaches half the
    pooled relapsed-SCLC value measured on GSE299684. What the rule cannot
    say on its own is whether the cohort had the power to answer the
    question at all, and that is a measurement rather than a choice: if the
    relapsed arm of the same deposit does not carry the state either, then
    a low untreated value cannot be read as "absent before therapy",
    because it would have been low before therapy whether or not the state
    were relapse-associated. The third branch reports that, and it does not
    change the threshold or the untreated arm's number.
    """
    untreated = arms.get("untreated", {})
    relapsed = arms.get("relapsed", {})
    median = untreated.get("median_state_fraction")
    median_relapsed = relapsed.get("median_state_fraction")
    if median is None:
        return {
            "status": "not evaluable",
            "reason": "no untreated library produced a state fraction",
            "threshold": threshold,
        }
    present = median >= threshold
    relapsed_carries = (
        median_relapsed is not None and median_relapsed >= threshold
    )
    if present:
        status = "state present before therapy"
        evaluable = True
        reason = None
    elif relapsed_carries:
        status = "state absent before therapy"
        evaluable = True
        reason = None
    else:
        status = "not evaluable: the cohort carries the state in neither arm"
        evaluable = False
        reason = (
            "the relapsed arm of the same deposit reaches "
            f"{median_relapsed:.5f}, also far below the threshold, so a low "
            "untreated value cannot be separated from the state being absent "
            "in this model system rather than before therapy"
        )
    return {
        "status": status,
        "threshold": threshold,
        "threshold_basis": threshold_basis,
        "untreated_median_state_fraction": median,
        "untreated_n_libraries": untreated.get("n_libraries"),
        "relapsed_median_state_fraction": median_relapsed,
        "relapsed_n_libraries": relapsed.get("n_libraries"),
        "relapsed_arm_carries_the_state": bool(relapsed_carries),
        "route_evaluable": evaluable,
        "reason": reason,
        "k2_route_taken": bool(present),
    }


def _write_tsv(path: Path, libraries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["accession\ttitle\tmodel\ttissue\ttreatment\tarm\tcompartment\tn_cells_passing_qc\tn_malignant\tn_state_cells\tstate_fraction"]
    for library in libraries:
        entry = library["state_definitions"][PRIMARY_DEFINITION]
        fraction = entry["state_fraction"]
        lines.append(
            "\t".join(
                [
                    library["accession"],
                    library["title"],
                    library["model"],
                    library["tissue"],
                    library["treatment"],
                    library["arm"],
                    library["compartment"],
                    str(library["n_cells_passing_qc"]),
                    str(entry["n_malignant"]),
                    str(entry["n_yap1_positive"]),
                    "" if fraction is None else f"{fraction:.6f}",
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples", type=int, default=0, help="use only the first N libraries"
    )
    parser.add_argument(
        "--cache",
        default="data/gse138474",
        help="directory for the per-library summaries, which make the run resumable",
    )
    parser.add_argument(
        "--outdir", default="results/gse138474", help="where to write the artefacts"
    )
    parser.add_argument(
        "--definition",
        default=PRIMARY_DEFINITION,
        help="the state definition the decision rule uses",
    )
    parser.add_argument("--force", action="store_true", help="ignore the cache")
    args = parser.parse_args(argv)

    samples = SAMPLES if args.samples <= 0 else SAMPLES[: args.samples]
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    manifest_path = cache / "files.tsv"
    manifest = _read_manifest(manifest_path)

    libraries: list[dict] = []
    for sample in samples:
        cached = cache / f"{sample['gsm']}.v4.json"
        if cached.exists() and not args.force:
            libraries.append(json.loads(cached.read_text()))
            print(f"  {sample['gsm']}: from cache", flush=True)
            continue
        print(f"  {sample['gsm']} ({sample['title']}, {sample['treatment']}): downloading", flush=True)
        sample["url"] = _sample_url(sample, manifest)
        parsed = _parse_sample(sample["url"])
        summary = _library_summary(sample, parsed)
        cached.write_text(json.dumps(summary, indent=2) + "\n")
        libraries.append(summary)
        print(
            f"    cells {summary['n_cells']} -> {summary['n_cells_passing_qc']} after QC, "
            f"malignant {summary['state_definitions'][args.definition]['n_malignant']}, "
            f"state fraction {summary['state_definitions'][args.definition]['state_fraction']}",
            flush=True,
        )

    definition = args.definition
    threshold = _present_before_therapy_threshold()
    per_definition = {}
    for name, _ in STATE_DEFINITIONS:
        per_definition[name] = _arm_statistics(libraries, name)

    document = {
        "audit": {
            "id": "gse138474-state-expression-2026-11",
            "generated_by": "scripts/gse138474_state_expression.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "source_document": "docs/GSE138474-TREATMENT-NAIVE-SCLC.md",
            "question": (
                "Is the YAP1(+) relapse-competent state already present in "
                "untreated SCLC, and is it relapsed-associated?"
            ),
            "limits": (
                "The libraries are patient-derived models sampled in a flank, "
                "not lung, and the untreated arm is a xenograft without "
                "systemic chemotherapy rather than a patient at diagnosis. "
                "This is the treatment-naive comparator the gate review named, "
                "and it is the closest public SCLC comparator that carries "
                "the treatment label, but it is not a lung biopsy."
            ),
        },
        "dataset": {
            "accession": "GSE138474",
            "paper": (
                "Stewart et al., Single-cell analyses reveal increasing "
                "intratumoral heterogeneity as an essential component of "
                "treatment resistance in small cell lung cancer, Cancer Res 2021"
            ),
            "organism": "Homo sapiens",
            "platform": "GPL11154",
            "n_libraries_with_matrix": len(libraries),
            "state_gene": STATE_GENE,
            "state_definitions": {name: text for name, text in STATE_DEFINITIONS},
            "primary_definition": definition,
        },
        "qc": {
            "min_genes": QC_MIN_GENES,
            "min_counts": QC_MIN_COUNTS,
            "max_mito_fraction": QC_MAX_MITO,
        },
        "libraries": libraries,
        "arms": per_definition,
        "decision": _decision(
            per_definition[definition]["arms"], *threshold
        ),
    }

    _write_manifest(manifest_path, manifest)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "state_expression.json").write_text(json.dumps(document, indent=2) + "\n")
    _write_tsv(outdir / "state_expression.tsv", libraries)

    decision = document["decision"]
    print()
    print(f"decision: {decision['status']}")
    for name, _ in STATE_DEFINITIONS:
        arms = per_definition[name]["arms"]
        print(f"  {name}:")
        for arm in ARMS:
            if arm in arms:
                print(
                    f"    {arm:<10} n={arms[arm]['n_libraries']:<3} "
                    f"median state fraction {arms[arm]['median_state_fraction']}"
                )
    print(f"wrote {outdir / 'state_expression.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
