#!/usr/bin/env python3
"""D0 — target therapeutic-window audit.

Stage D0 of the research plan is the cheapest kill in the programme: before any
sample is spent, decide whether the candidate channels have a therapeutic
window in lung at all. This script produces that verdict from public data, so
that every number in the D0 report can be re-derived by anyone with a network
connection.

It is deliberately self-contained: no sibling repository is imported, and the
decision rule lives in this file rather than in a dependency that could change
underneath it.

Sources
-------
1. **GTEx Portal v2** — median gene expression per tissue (54 tissues,
   ``gtex_v8``). The expression basis of every window verdict.
2. **Open Targets GraphQL** — tractability flags, gnomAD genetic constraint,
   known safety liabilities, and clinical-stage drug candidates for the target.
3. **NCBI ClinVar** — germline pathogenicity per variant and the traits those
   variants are asserted to cause.
4. **AlphaGenome Atlas** — optional. The official ``alphagenome`` package is a
   heavy optional dependency and is not required for the window verdict; when
   it is absent the run records that it was not executed rather than
   substituting a proxy.

The decision rule
-----------------
The rule is fixed in this file, before it is applied, and it is applied to
every target identically:

* ``lung_detected``      lung median TPM >= 1 (the GTEx/HPA "detected" floor)
* ``selective``          lung TPM >= 10x the highest non-lung tissue
* ``conditionally_selective``  lung TPM >= 3x the highest non-lung tissue
* ``no_bulk_window``     lung is expressed but no such margin exists
* ``not_a_lung_target``  lung median TPM < 1

The 10x and 3x margins are conventions, not fitted parameters, and the
threshold is the one place where a reader should demand sensitivity analysis:
the run therefore also sweeps the margin over 2x/3x/5x/10x/20x and records how
many targets change class.

**Disclosure.** The analyst had already seen the aggregate lung and tissue
expression values before the margins were fixed, because the data pull and the
rule design were interleaved. The margins are therefore reported with the
sweep rather than as a single number, and the report states this.

Usage
-----
    python scripts/d0_window_audit.py --outdir results/d0_window_audit
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

AUDIT_ID = "d0-target-window-2026-11"
USER_AGENT = "relapse-competence-d0/0.1 (https://github.com/rollroyces/relapse-competence)"

GTEX_API = "https://gtexportal.org/api/v2"
OT_API = "https://api.platform.opentargets.org/api/v4/graphql"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

#: The target table, verbatim from ``docs/RESEARCH-PLAN.md`` section 2, plus
#: the mechanosensory partners of PIEZO1 that the plan's D0 method calls
#: "known regulators". Each entry states why the gene is in the audit.
TARGETS: list[dict[str, str]] = [
    {
        "symbol": "KCNN4",
        "tier": "1",
        "role": "Ca2+-activated K+ efflux; sets the membrane potential the state reads out",
        "why": "Primary drug target; senicapoc and elexacaftor already block it",
    },
    {
        "symbol": "PIEZO1",
        "tier": "1",
        "role": "Mechanical -> Ca2+ -> YAP/TEAD entry point",
        "why": "Primary drug target; direction of effect is not established",
    },
    {
        "symbol": "CACNA1E",
        "tier": "1",
        "role": "VGCC alpha1E; the single record in the target intersection",
        "why": "Primary drug target; conceptually central, least developed",
    },
    {
        "symbol": "KCNA3",
        "tier": "2",
        "role": "Kv1.3 effector-memory T-cell and tumour signalling",
        "why": "Immune arm; the readout channel of the same state",
    },
    {
        "symbol": "STOML3",
        "tier": "regulator",
        "role": "PIEZO1 complex partner; modulates Piezo1 gating",
        "why": "A regulator of the primary target: a selective partner widens the window",
    },
    {
        "symbol": "TMEM150C",
        "tier": "regulator",
        "role": "PIEZO1 complex partner; modulates Piezo1 gating",
        "why": "A regulator of the primary target: a selective partner widens the window",
    },
    {
        "symbol": "PIEZO2",
        "tier": "offtarget",
        "role": "Piezo1 homologue; the dominant on-target off-target of any Piezo1 drug",
        "why": "Included because selectivity against it decides whether a Piezo1 drug is viable",
    },
]

#: How the 54 GTEx tissues are grouped for the liability axes. The grouping is
#: an explicit judgement, written down here so a reader can argue with it.
TISSUE_GROUPS: dict[str, tuple[str, ...]] = {
    "immune": (
        "Cells_EBV-transformed_lymphocytes",
        "Spleen",
        "Whole_Blood",
    ),
    "epithelial": (
        "Bladder",
        "Breast_Mammary_Tissue",
        "Cervix_Ectocervix",
        "Cervix_Endocervix",
        "Colon_Sigmoid",
        "Colon_Transverse",
        "Esophagus_Gastroesophageal_Junction",
        "Esophagus_Mucosa",
        "Esophagus_Muscularis",
        "Fallopian_Tube",
        "Minor_Salivary_Gland",
        "Prostate",
        "Skin_Not_Sun_Exposed_Suprapubic",
        "Skin_Sun_Exposed_Lower_leg",
        "Small_Intestine_Terminal_Ileum",
        "Stomach",
        "Uterus",
        "Vagina",
    ),
    "neural": (
        "Brain_Amygdala",
        "Brain_Anterior_cingulate_cortex_BA24",
        "Brain_Caudate_basal_ganglia",
        "Brain_Cerebellar_Hemisphere",
        "Brain_Cerebellum",
        "Brain_Cortex",
        "Brain_Frontal_Cortex_BA9",
        "Brain_Hippocampus",
        "Brain_Hypothalamus",
        "Brain_Nucleus_accumbens_basal_ganglia",
        "Brain_Putamen_basal_ganglia",
        "Brain_Spinal_cord_cervical_c-1",
        "Brain_Substantia_nigra",
        "Nerve_Tibial",
    ),
    "cardiac": (
        "Heart_Atrial_Appendage",
        "Heart_Left_Ventricle",
    ),
}

#: The target tissue the programme is aimed at.
TARGET_TISSUE = "Lung"

#: Decision margins for the window verdict, and the sweep reported alongside.
SELECTIVE_MARGIN = 10.0
CONDITIONAL_MARGIN = 3.0
SWEEP_MARGINS = (2.0, 3.0, 5.0, 10.0, 20.0)

#: Expression floor for "detected", matching the GTEx/HPA convention.
DETECTION_FLOOR_TPM = 1.0


# =============================================================================
# HTTP
# =============================================================================
class SourceError(RuntimeError):
    """A data source could not be read."""


def _fetch(url: str, *, timeout: int = 60, retries: int = 3, backoff: float = 1.5) -> bytes:
    """GET a URL, retrying transient failures. Raises SourceError."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(backoff * (attempt + 1))
                continue
            raise SourceError(f"HTTP {exc.code} for {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(backoff * (attempt + 1))
    raise SourceError(f"could not fetch {url}: {last}")


#: NCBI allows three requests per second per IP without an API key. The audit
#: makes two calls per gene, so the calls are spaced rather than bursted, and
#: a 429 is retried with a longer pause.
_NCBI_MIN_INTERVAL = 0.4
_last_ncbi_call = 0.0


def _ncbi_fetch(url: str) -> bytes:
    """Fetch from NCBI E-utilities, respecting the unauthenticated rate limit."""
    global _last_ncbi_call
    wait = _NCBI_MIN_INTERVAL - (time.monotonic() - _last_ncbi_call)
    if wait > 0:
        time.sleep(wait)
    try:
        return _fetch(url, retries=5, backoff=4.0)
    finally:
        _last_ncbi_call = time.monotonic()


def _get_json(url: str, **kwargs: object) -> dict:
    return json.loads(_fetch(url, **kwargs).decode("utf-8"))


def _post_json(url: str, payload: dict, **kwargs: object) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        detail = body[:400]
        try:
            errors = json.loads(body).get("errors") or []
            if errors:
                detail = str(errors[0].get("message"))[:400]
        except (json.JSONDecodeError, AttributeError):
            pass
        raise SourceError(f"HTTP {exc.code} for {url}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceError(f"could not POST {url}: {exc}") from exc


# =============================================================================
# GTEx
# =============================================================================
def gtex_gene(symbol: str) -> dict:
    """The GTEx v8 gene record for a symbol."""
    url = f"{GTEX_API}/reference/gene?geneId={urllib.parse.quote(symbol)}"
    data = _get_json(url)
    rows = data.get("data") or []
    if not rows:
        raise SourceError(f"GTEx has no gene record for {symbol}")
    return rows[0]


def gtex_median_expression(gencode_id: str) -> dict[str, float]:
    """Median TPM per tissue for a GTEx gene."""
    url = (
        f"{GTEX_API}/expression/medianGeneExpression?"
        f"gencodeId={urllib.parse.quote(gencode_id)}&datasetId=gtex_v8&itemsPerPage=100"
    )
    data = _get_json(url)
    rows = data.get("data") or []
    if not rows:
        raise SourceError(f"GTEx returned no expression for {gencode_id}")
    return {
        row["tissueSiteDetailId"]: float(row["median"])
        for row in rows
        if row.get("median") is not None
    }


def expression_metrics(expression: dict[str, float]) -> dict:
    """Window metrics derived from the per-tissue expression."""
    lung = expression.get(TARGET_TISSUE)
    values = list(expression.values())
    mean_all = sum(values) / len(values)
    max_tissue, max_tpm = max(expression.items(), key=lambda kv: kv[1])
    off_target = {t: v for t, v in expression.items() if t != TARGET_TISSUE}
    max_off_tissue, max_off_tpm = max(off_target.items(), key=lambda kv: kv[1])

    groups = {}
    for name, members in TISSUE_GROUPS.items():
        present = {t: expression[t] for t in members if t in expression}
        if not present:
            continue
        tissue, tpm = max(present.items(), key=lambda kv: kv[1])
        groups[name] = {
            "max_tissue": tissue,
            "max_tpm": tpm,
            "fold_vs_lung": (lung / tpm) if (lung is not None and tpm) else None,
        }

    top = sorted(expression.items(), key=lambda kv: -kv[1])[:5]
    return {
        "n_tissues": len(expression),
        "lung_tpm": lung,
        "mean_tpm": mean_all,
        "max_tissue": max_tissue,
        "max_tpm": max_tpm,
        "max_offtarget_tissue": max_off_tissue,
        "max_offtarget_tpm": max_off_tpm,
        "fold_vs_mean": (lung / mean_all) if (lung is not None and mean_all) else None,
        "fold_vs_max_offtarget": (
            (lung / max_off_tpm) if (lung is not None and max_off_tpm) else None
        ),
        "groups": groups,
        "top_tissues": [{"tissue": t, "median_tpm": v} for t, v in top],
    }


def classify(metrics: dict, selective_margin: float, conditional_margin: float) -> str:
    """The window verdict for one target under one pair of margins."""
    lung = metrics.get("lung_tpm")
    if lung is None:
        return "not_determined"
    if lung < DETECTION_FLOOR_TPM:
        return "not_a_lung_target"
    fold = metrics.get("fold_vs_max_offtarget")
    if fold is None:
        return "not_determined"
    if fold >= selective_margin:
        return "selective"
    if fold >= conditional_margin:
        return "conditionally_selective"
    return "no_bulk_window"


# =============================================================================
# Open Targets
# =============================================================================
OT_QUERY = """
query($id:String!){
  target(ensemblId:$id){
    approvedSymbol
    approvedName
    isEssential
    targetClass{id label level}
    tractability{modality value label}
    geneticConstraint{constraintType oeLower oeUpper score obs exp}
    safetyLiabilities{event eventId datasource url}
    drugAndClinicalCandidates{
      count
      rows{maxClinicalStage drug{id name maximumClinicalStage}}
    }
  }
}
"""


def opentargets_target(ensembl_id: str) -> dict:
    """The Open Targets record for an Ensembl gene id."""
    data = _post_json(OT_API, {"query": OT_QUERY, "variables": {"id": ensembl_id}})
    if data.get("errors"):
        raise SourceError(f"Open Targets error: {data['errors'][0].get('message')}")
    target = (data.get("data") or {}).get("target")
    if not target:
        raise SourceError(f"Open Targets has no record for {ensembl_id}")
    return target


# =============================================================================
# ClinVar
# =============================================================================
PATHOGENIC_CLINSIG = "(pathogenic[clinsig] OR likely_pathogenic[clinsig])"


def clinvar_records(gene: str) -> tuple[list[dict], int, bool]:
    """ClinVar records for a gene, the total on file, and a truncation flag.

    The fetch is capped, so a gene with more records than the cap is reported
    as truncated rather than silently summarised over the records that fitted.
    """
    search = urllib.parse.urlencode(
        {
            "db": "clinvar",
            "term": f"{gene}[gene]",
            "retmode": "json",
            "retmax": 2000,
            "tool": "relapse_competence_d0",
        }
    )
    result = json.loads(_ncbi_fetch(f"{EUTILS}/esearch.fcgi?{search}"))["esearchresult"]
    ids = result.get("idlist") or []
    total = int(result.get("count") or 0)
    if not ids:
        return [], total, total > 0
    summaries: dict[str, dict] = {}
    # Batched: a few hundred comma-separated ids make a URL that some proxies
    # reject with HTTP 414.
    for start in range(0, len(ids), 100):
        batch = ids[start : start + 100]
        summary_query = urllib.parse.urlencode(
            {
                "db": "clinvar",
                "id": ",".join(batch),
                "retmode": "json",
                "tool": "relapse_competence_d0",
            }
        )
        summaries.update(
            json.loads(_ncbi_fetch(f"{EUTILS}/esummary.fcgi?{summary_query}"))["result"]
        )
    records = []
    for uid in ids:
        record = summaries.get(uid)
        if record:
            records.append(record)
    return records, total, len(ids) < total


def clinvar_metrics(records: list[dict]) -> dict:
    """Germline liability: aggregate classifications and the traits asserted."""
    counts: dict[str, int] = {}
    traits: dict[str, int] = {}
    expert_reviewed = 0
    for record in records:
        germline = record.get("germline_classification") or {}
        description = (germline.get("description") or "unknown").strip()
        counts[description] = counts.get(description, 0) + 1
        review = (germline.get("review_status") or "").lower()
        if "expert panel" in review or "practice guideline" in review:
            expert_reviewed += 1
        if description.lower().startswith(("pathogenic", "likely pathog")):
            for trait in germline.get("trait_set") or []:
                name = (trait.get("trait_name") or "").strip()
                if name and name.lower() != "not provided":
                    traits[name] = traits.get(name, 0) + 1
    pathogenic = sum(
        count
        for label, count in counts.items()
        if label.lower().startswith(("pathogenic", "likely pathog"))
    )
    return {
        "n_records": len(records),
        "aggregate_germline_class_counts": dict(sorted(counts.items())),
        "germline_pathogenic_or_likely": pathogenic,
        "expert_panel_or_guideline_records": expert_reviewed,
        "traits_asserted_by_pathogenic_variants": dict(
            sorted(traits.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
    }


# =============================================================================
# AlphaGenome (optional)
# =============================================================================
def alphagenome_status() -> dict:
    """Whether the optional regulatory-variant scorer can run here."""
    try:
        import importlib.util

        spec = importlib.util.find_spec("alphagenome")
    except (ImportError, ValueError):
        spec = None
    if spec is None:
        return {
            "status": "not_executed",
            "reason": (
                "the official `alphagenome` package is not installed in this "
                "environment; the window verdict does not depend on it"
            ),
        }
    return {
        "status": "available",
        "reason": "the official `alphagenome` package is importable",
    }


# =============================================================================
# Assembly
# =============================================================================
def _git_commit(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%H"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def audit_target(spec: dict[str, str]) -> dict:
    """Audit one target, recording per-source failures rather than hiding them."""
    symbol = spec["symbol"]
    record: dict = {
        "symbol": symbol,
        "tier": spec["tier"],
        "role": spec["role"],
        "why_in_audit": spec["why"],
    }

    # --- GTEx: the expression basis of the verdict ---
    try:
        gene = gtex_gene(symbol)
        expression = gtex_median_expression(gene["gencodeId"])
        metrics = expression_metrics(expression)
        record["ensembl_id"] = gene.get("gencodeId", "").split(".")[0]
        record["gtex"] = {"status": "ok", **metrics}
    except SourceError as exc:
        record["ensembl_id"] = None
        record["gtex"] = {"status": "unavailable", "error": str(exc)}
        metrics = None

    # --- Open Targets ---
    ensembl = record.get("ensembl_id")
    if ensembl:
        try:
            target = opentargets_target(ensembl)
            record["opentargets"] = {
                "status": "ok",
                "target_class": target.get("targetClass"),
                "is_essential": target.get("isEssential"),
                "tractability": [
                    {
                        "modality": t.get("modality"),
                        "value": t.get("value"),
                        "label": t.get("label"),
                    }
                    for t in (target.get("tractability") or [])
                ],
                "genetic_constraint": target.get("geneticConstraint"),
                "safety_liabilities": [
                    {
                        "event": s.get("event"),
                        "event_id": s.get("eventId"),
                        "datasource": s.get("datasource"),
                        "url": s.get("url"),
                    }
                    for s in (target.get("safetyLiabilities") or [])
                ],
                "drug_candidate_count": (
                    target.get("drugAndClinicalCandidates") or {}
                ).get("count"),
                "drug_candidates": [
                    {
                        "name": (row.get("drug") or {}).get("name"),
                        "max_clinical_stage": (row.get("drug") or {}).get(
                            "maximumClinicalStage"
                        ),
                    }
                    for row in (
                        (target.get("drugAndClinicalCandidates") or {}).get("rows") or []
                    )
                ],
            }
        except SourceError as exc:
            record["opentargets"] = {"status": "unavailable", "error": str(exc)}
    else:
        record["opentargets"] = {
            "status": "skipped",
            "error": "no Ensembl id (GTEx lookup failed)",
        }

    # --- ClinVar ---
    try:
        records, total, truncated = clinvar_records(symbol)
        record["clinvar"] = {
            "status": "ok",
            "n_records_fetched": len(records),
            "n_records_on_file": total,
            "truncated": truncated,
            **clinvar_metrics(records),
        }
    except SourceError as exc:
        record["clinvar"] = {"status": "unavailable", "error": str(exc)}

    # --- Verdict ---
    if metrics is None:
        record["verdict"] = {
            "class": "not_determined",
            "reason": "expression data unavailable",
        }
    else:
        verdict_class = classify(metrics, SELECTIVE_MARGIN, CONDITIONAL_MARGIN)
        record["verdict"] = {
            "class": verdict_class,
            "selective_margin": SELECTIVE_MARGIN,
            "conditional_margin": CONDITIONAL_MARGIN,
            "window_fold_vs_max_offtarget": metrics.get("fold_vs_max_offtarget"),
            "immune_window_fold": (
                metrics.get("groups", {}).get("immune", {}).get("fold_vs_lung")
            ),
            "epithelial_window_fold": (
                metrics.get("groups", {}).get("epithelial", {}).get("fold_vs_lung")
            ),
            "sweep": {
                f"{margin:g}x": classify(metrics, margin, margin)
                for margin in SWEEP_MARGINS
            },
        }
    return record


def write_tsv(path: Path, targets: list[dict]) -> None:
    """One machine-readable row per target."""
    header = [
        "symbol",
        "tier",
        "lung_tpm",
        "max_offtarget_tissue",
        "max_offtarget_tpm",
        "fold_vs_max_offtarget",
        "immune_window_fold",
        "epithelial_window_fold",
        "germline_pathogenic_or_likely",
        "expert_panel_records",
        "verdict",
    ]
    lines = ["\t".join(header)]
    for target in targets:
        gtex = target.get("gtex") or {}
        clinvar = target.get("clinvar") or {}
        verdict = target.get("verdict") or {}
        values = [
            target.get("symbol", ""),
            target.get("tier", ""),
            _fmt(gtex.get("lung_tpm")),
            gtex.get("max_offtarget_tissue", ""),
            _fmt(gtex.get("max_offtarget_tpm")),
            _fmt(verdict.get("window_fold_vs_max_offtarget")),
            _fmt(verdict.get("immune_window_fold")),
            _fmt(verdict.get("epithelial_window_fold")),
            _fmt(clinvar.get("germline_pathogenic_or_likely")),
            _fmt(clinvar.get("expert_panel_or_guideline_records")),
            verdict.get("class", ""),
        ]
        lines.append("\t".join(str(v) for v in values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def markdown_table(targets: list[dict]) -> str:
    """The report table, rendered from the same numbers the artefact stores."""
    header = (
        "| Target | Tier | Lung TPM | Highest non-lung tissue | Window fold "
        "| Immune fold | Epithelial fold | Germline P/LP | Verdict |"
    )
    divider = "|---|---|---|---|---|---|---|---|---|"
    lines = [header, divider]
    for target in targets:
        gtex = target.get("gtex") or {}
        clinvar = target.get("clinvar") or {}
        verdict = target.get("verdict") or {}
        lines.append(
            "| `{symbol}` | {tier} | {lung} | {off} ({off_tpm}) | {fold} | "
            "{immune} | {epi} | {plp} | **{verdict}** |".format(
                symbol=target.get("symbol", ""),
                tier=target.get("tier", ""),
                lung=_fmt(gtex.get("lung_tpm")),
                off=gtex.get("max_offtarget_tissue", "—"),
                off_tpm=_fmt(gtex.get("max_offtarget_tpm")),
                fold=_fmt(verdict.get("window_fold_vs_max_offtarget")),
                immune=_fmt(verdict.get("immune_window_fold")),
                epi=_fmt(verdict.get("epithelial_window_fold")),
                plp=_fmt(clinvar.get("germline_pathogenic_or_likely")),
                verdict=verdict.get("class", ""),
            )
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="D0 target therapeutic-window audit.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--outdir", default="results/d0_window_audit")
    parser.add_argument(
        "--markdown-table",
        action="store_true",
        help="print the report table and exit without writing",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    outdir = root / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    targets = [audit_target(spec) for spec in TARGETS]

    if args.markdown_table:
        print(markdown_table(targets))
        return 0

    gate_reached = [
        t["symbol"]
        for t in targets
        if (t.get("verdict") or {}).get("class")
        in ("selective", "conditionally_selective")
    ]
    sweep: dict[str, dict[str, int]] = {}
    for margin in SWEEP_MARGINS:
        counts: dict[str, int] = {}
        for target in targets:
            verdict = (target.get("verdict") or {}).get("sweep") or {}
            label = verdict.get(f"{margin:g}x", "not_determined")
            counts[label] = counts.get(label, 0) + 1
        sweep[f"{margin:g}x"] = dict(sorted(counts.items()))

    payload = {
        "audit": {
            "id": AUDIT_ID,
            "generated_by": "scripts/d0_window_audit.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "git_commit": _git_commit(root),
            "rule": {
                "detection_floor_tpm": DETECTION_FLOOR_TPM,
                "selective_margin": SELECTIVE_MARGIN,
                "conditional_margin": CONDITIONAL_MARGIN,
                "sweep_margins": list(SWEEP_MARGINS),
                "target_tissue": TARGET_TISSUE,
                "source": (
                    "fixed in scripts/d0_window_audit.py; the 3x and 10x margins "
                    "are conventions, and the sensitivity sweep is reported so "
                    "that no single margin carries the conclusion"
                ),
            },
            "sources": {
                "gtex": "https://gtexportal.org/api/v2 (gtex_v8 median gene expression)",
                "open_targets": OT_API,
                "clinvar": f"{EUTILS}/esearch.fcgi + esummary.fcgi (db=clinvar)",
                "alphagenome": alphagenome_status(),
            },
            "disclosure": (
                "The aggregate lung and tissue expression values were seen before "
                "the margins were fixed, because the data pull and the rule "
                "design were interleaved. The verdict is therefore reported "
                "together with the threshold sweep."
            ),
        },
        "gate": {
            "k4": {
                "definition": (
                    "kill condition K4: no target is conditionally selective -> "
                    "the pharmacological arm is dropped and the programme becomes "
                    "a biomarker programme"
                ),
                "targets_reaching_conditional_or_better": gate_reached,
                "fired": not gate_reached,
                "scope": (
                    "evaluated on bulk normal tissue (GTEx), which cannot see "
                    "state-restricted expression; see the report's limitations"
                ),
            },
            "threshold_sensitivity": sweep,
        },
        "targets": targets,
    }

    (outdir / "d0_window_audit.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_tsv(outdir / "d0_window_audit.tsv", targets)

    print(f"{'symbol':<12} {'tier':<10} {'lung TPM':>10} {'window fold':>12}  verdict")
    print("-" * 68)
    for target in targets:
        gtex = target.get("gtex") or {}
        verdict = target.get("verdict") or {}
        print(
            f"{target['symbol']:<12} {target['tier']:<10} "
            f"{_fmt(gtex.get('lung_tpm')):>10} "
            f"{_fmt(verdict.get('window_fold_vs_max_offtarget')):>12}  "
            f"{verdict.get('class')}"
        )
    print()
    print(
        "K4 fired (no target conditionally selective on bulk tissue): "
        f"{payload['gate']['k4']['fired']}"
    )
    print(f"wrote {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
