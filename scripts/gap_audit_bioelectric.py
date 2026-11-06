#!/usr/bin/env python3
"""Formal gap audit: bioelectric state x lung-cancer relapse competence.

This script is the auditable spine of the audit. Every query it runs is
recorded verbatim in the audit log together with the database, the UTC
timestamp, the hit count and the retrieved PMIDs, so the audit can be re-run
and diffed rather than taken on trust.

Sources searched
----------------
1. PubMed (NCBI E-utilities)          -- primary biomedical anchor
2. Europe PMC (REST API)             -- broader recall, includes preprints
3. ClinicalTrials.gov (API v2)       -- registered interventions
4. GEO DataSets (NCBI E-utilities)    -- datasets

Coverage limitation, stated up front
-------------------------------------
Google Scholar and Web of Science have no API access from this environment, so
this audit has no citation-network or indexing-coverage check. Absence of
records here is not proof of absence in the literature; see the risk review in
the report for what that limits.

Usage
-----
    python scripts/gap_audit_bioelectric.py --outdir results/gap_audit_bioelectric
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"
USER_AGENT = "relapse-competence-gap-audit/0.1 (research use)"


# =============================================================================
# Query vocabulary
# =============================================================================
# Each block is one concept. Block composition is deliberately generous:
# over-recall is cheap, under-recall is not.

LUNG = (
    '("lung neoplasms"[MeSH Terms] OR lung[tiab] OR "lung cancer"[tiab] '
    'OR NSCLC[tiab] OR SCLC[tiab] OR "lung adenocarcinoma"[tiab] '
    'OR "lung carcinoma"[tiab] OR "lung metastasis"[tiab] OR "lung metastases"[tiab] '
    'OR "pulmonary"[tiab] OR "bronchogenic"[tiab])'
)

BIOELECTRIC = (
    '("membrane potential"[tiab] OR "resting membrane potential"[tiab] '
    'OR depolariz*[tiab] OR depolaris*[tiab] OR hyperpolariz*[tiab] '
    'OR hyperpolaris*[tiab] OR "ion channel"[tiab] OR "ion channels"[tiab] '
    'OR "voltage-gated"[tiab] OR "ligand-gated"[tiab] OR "mechanosensitive"[tiab] '
    'OR "stretch-activated"[tiab] OR electroceutical*[tiab] '
    'OR "tumor treating fields"[tiab] OR "tumour treating fields"[tiab] '
    'OR "electric field"[tiab] OR "electrical field"[tiab] '
    'OR electrotaxis[tiab] OR electrotaxis[tiab] OR bioelectric*[tiab] '
    'OR "voltage"[tiab] OR "ion channel expression"[tiab] '
    'OR Piezo1[tiab] OR PIEZO1[tiab] OR Kv1.3[tiab] OR KCNA3[tiab] '
    'OR KCa3.1[tiab] OR KCNN4[tiab] OR TRPV1[tiab] OR ENaC[tiab] '
    'OR SCNN1A[tiab] OR "ENaC"[tiab])'
)

DNA = (
    '("cell-free DNA"[tiab] OR "cell free DNA"[tiab] OR cfDNA[tiab] '
    'OR ctDNA[tiab] OR "circulating tumor DNA"[tiab] '
    'OR "circulating tumour DNA"[tiab] OR "liquid biopsy"[tiab] '
    'OR "plasma DNA"[tiab] OR "DNA methylation"[tiab] '
    'OR "methylation-based"[tiab] OR "methylome"[tiab] '
    'OR fragmentomic*[tiab] OR "fragmentation profile"[tiab] '
    'OR "methylation deconvolution"[tiab] OR "expression deconvolution"[tiab] '
    'OR "transcriptional inference"[tiab] OR "transcriptome inference"[tiab])'
)

RELAPSE = (
    '(relapse*[tiab] OR recurren*[tiab] OR "residual disease"[tiab] '
    'OR "minimal residual disease"[tiab] OR "molecular residual"[tiab] '
    'OR MRD[tiab] OR persist*[tiab] OR persister*[tiab] '
    'OR "drug-tolerant"[tiab] OR "drug tolerant"[tiab] '
    'OR "measurable residual"[tiab])'
)

STEMNESS = (
    '("cancer stem"[tiab] OR "cancer stem cell"[tiab] OR "cancer stem cells"[tiab] '
    'OR stemness[tiab] OR "tumor-initiating"[tiab] OR "tumour-initiating"[tiab] '
    'OR "tumor initiating"[tiab] OR "tumour initiating"[tiab] '
    'OR "stem cell"[tiab] OR "stem-like"[tiab] OR plasticity[tiab] '
    'OR "lineage plasticity"[tiab])'
)

#: A block that must NOT appear: pure electrophysiology without a cancer context.
NOT_ONCOLOGY = (
    'NOT ("cardiac"[tiab] OR "neuronal"[tiab] OR "epilepsy"[tiab] '
    'OR "skeletal muscle"[tiab] OR "plant"[tiab] OR "bacterial"[tiab] '
    'OR "viral"[tiab] OR "fungal"[tiab] OR "Arabidopsis"[tiab] '
    'OR "mouse"[tiab] OR "rat"[tiab] OR "zebrafish"[tiab])'
)

QUERIES: list[tuple[str, str, str, str]] = [
    # id, label, pubmed query, purpose
    (
        "Q01",
        "bioelectric x lung",
        f"{BIOELECTRIC} AND {LUNG}",
        "Establish how large the bioelectric-in-lung-cancer cluster already is.",
    ),
    (
        "Q02",
        "bioelectric x relapse/residual",
        f"{BIOELECTRIC} AND {RELAPSE}",
        "Does anyone connect an electrical phenotype to relapse or residual disease, in any tumour type?",
    ),
    (
        "Q03",
        "bioelectric x stemness",
        f"{BIOELECTRIC} AND {STEMNESS}",
        "The mature cluster: is the electrical-stemness coupling established?",
    ),
    (
        "Q04",
        "DNA x relapse x lung",
        f"{DNA} AND {RELAPSE} AND {LUNG}",
        "The mature cluster: ctDNA MRD in lung cancer. Saturation reference.",
    ),
    (
        "Q05",
        "stemness x relapse x lung",
        f"{STEMNESS} AND {RELAPSE} AND {LUNG}",
        "The mature cluster: CSC and relapse in lung cancer. Saturation reference.",
    ),
    (
        "Q06",
        "bioelectric x DNA",
        f"{BIOELECTRIC} AND {DNA}",
        "The core combination question: does anyone read an electrical state off DNA?",
    ),
    (
        "Q07",
        "bioelectric x DNA x relapse",
        f"{BIOELECTRIC} AND {DNA} AND {RELAPSE}",
        "Core intersection, tumour-type agnostic.",
    ),
    (
        "Q08",
        "TARGET: bioelectric x DNA x relapse x lung",
        f"{BIOELECTRIC} AND {DNA} AND {RELAPSE} AND {LUNG}",
        "The headline target query.",
    ),
    (
        "Q09",
        "bioelectric x stemness x relapse",
        f"{BIOELECTRIC} AND {STEMNESS} AND {RELAPSE}",
        "Is the electrical-stemness link extended to relapse?",
    ),
    (
        "Q10",
        "bioelectric x relapse x lung",
        f"{BIOELECTRIC} AND {RELAPSE} AND {LUNG}",
        "Electrical phenotype and lung relapse, without the DNA axis.",
    ),
    (
        "Q11",
        "bioelectric x DNA x stemness",
        f"{BIOELECTRIC} AND {DNA} AND {STEMNESS}",
        "Does anyone infer an electrical state from DNA in a stemness context?",
    ),
    (
        "Q12",
        "CONTROL: bioelectric x relapse, non-lung",
        f"{BIOELECTRIC} AND {RELAPSE} NOT {LUNG}",
        "Transferability control. If the intersection exists in another tumour type, the gap is an extension gap, not a knowledge gap.",
    ),
    (
        "Q13",
        "CONTROL: bioelectric x relapse x lung, cancer only",
        f"{BIOELECTRIC} AND {RELAPSE} AND {LUNG} {NOT_ONCOLOGY}",
        "Noise control: how many hits survive removing non-oncology electrophysiology.",
    ),
    (
        "Q14",
        "MECHANISM: ion channel expression from cfDNA",
        f'{DNA} AND ("ion channel"[tiab] OR "ion channels"[tiab] OR "channel expression"[tiab] '
        f'OR "transporter expression"[tiab])',
        "Does the readout channel needed for the combination already exist?",
    ),
]

#: Europe PMC queries. Europe PMC uses its own query syntax, so these are
#: written out rather than translated.
EPMC_QUERIES: list[tuple[str, str, str]] = [
    (
        "E08",
        "TARGET: bioelectric x DNA x relapse x lung",
        '(TITLE_ABS:"membrane potential" OR TITLE_ABS:"ion channel" OR TITLE_ABS:electrotaxis '
        'OR TITLE_ABS:"tumor treating fields" OR TITLE_ABS:bioelectric OR TITLE_ABS:depolariz* '
        'OR TITLE_ABS:"electric field") '
        'AND (TITLE_ABS:"cell-free DNA" OR TITLE_ABS:cfDNA OR TITLE_ABS:ctDNA '
        'OR TITLE_ABS:"liquid biopsy" OR TITLE_ABS:fragmentomic* OR TITLE_ABS:"DNA methylation") '
        'AND (TITLE_ABS:relapse* OR TITLE_ABS:recurren* OR TITLE_ABS:"residual disease" '
        'OR TITLE_ABS:MRD OR TITLE_ABS:persister*) '
        'AND (TITLE_ABS:lung OR TITLE_ABS:NSCLC OR TITLE_ABS:SCLC OR TITLE_ABS:pulmonary)',
    ),
    (
        "E07",
        "bioelectric x DNA x relapse (tumour-agnostic)",
        '(TITLE_ABS:"membrane potential" OR TITLE_ABS:"ion channel" OR TITLE_ABS:electrotaxis '
        'OR TITLE_ABS:"tumor treating fields" OR TITLE_ABS:bioelectric) '
        'AND (TITLE_ABS:"cell-free DNA" OR TITLE_ABS:cfDNA OR TITLE_ABS:ctDNA '
        'OR TITLE_ABS:"liquid biopsy") '
        'AND (TITLE_ABS:relapse* OR TITLE_ABS:recurren* OR TITLE_ABS:"residual disease")',
    ),
    (
        "E09",
        "bioelectric x stemness x relapse (tumour-agnostic)",
        '(TITLE_ABS:"membrane potential" OR TITLE_ABS:"ion channel" OR TITLE_ABS:electrotaxis '
        'OR TITLE_ABS:"tumor treating fields" OR TITLE_ABS:bioelectric) '
        'AND (TITLE_ABS:"cancer stem" OR TITLE_ABS:stemness OR TITLE_ABS:"tumor-initiating" '
        'OR TITLE_ABS:"tumour-initiating") '
        'AND (TITLE_ABS:relapse* OR TITLE_ABS:recurren* OR TITLE_ABS:"residual disease" '
        'OR TITLE_ABS:persister*)',
    ),
    (
        "E12",
        "CONTROL: bioelectric x relapse, non-lung",
        '(TITLE_ABS:"membrane potential" OR TITLE_ABS:"ion channel" OR TITLE_ABS:electrotaxis '
        'OR TITLE_ABS:"tumor treating fields" OR TITLE_ABS:bioelectric) '
        'AND (TITLE_ABS:relapse* OR TITLE_ABS:recurren* OR TITLE_ABS:"residual disease" '
        'OR TITLE_ABS:persister*) NOT (TITLE_ABS:lung OR TITLE_ABS:NSCLC OR TITLE_ABS:SCLC)',
    ),
    (
        "E03",
        "bioelectric x stemness (saturation reference)",
        '(TITLE_ABS:"membrane potential" OR TITLE_ABS:"ion channel" OR TITLE_ABS:electrotaxis '
        'OR TITLE_ABS:"tumor treating fields" OR TITLE_ABS:bioelectric) '
        'AND (TITLE_ABS:"cancer stem" OR TITLE_ABS:stemness OR TITLE_ABS:"tumor-initiating" '
        'OR TITLE_ABS:"tumour-initiating")',
    ),
]


# =============================================================================
# Infrastructure
# =============================================================================
def http_get(url: str, params: dict[str, str] | None = None, timeout: int = 45) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - retried below
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed after 3 attempts: {url} ({last_error})")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class QueryResult:
    query_id: str
    label: str
    source: str
    query: str
    purpose: str
    total_hits: int
    retrieved: list[str]
    timestamp: str
    note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "label": self.label,
            "source": self.source,
            "query": self.query,
            "purpose": self.purpose,
            "total_hits": self.total_hits,
            "n_retrieved": len(self.retrieved),
            "retrieved_ids": self.retrieved,
            "timestamp_utc": self.timestamp,
            "note": self.note,
        }


# =============================================================================
# PubMed
# =============================================================================
def pubmed_search(query_id: str, label: str, query: str, purpose: str, limit: int = 300) -> QueryResult:
    payload = json.loads(
        http_get(
            f"{EUTILS}/esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": str(limit),
                "sort": "relevance",
            },
        )
    )
    result = payload.get("esearchresult", {})
    ids = result.get("idlist", [])
    total = int(result.get("count", 0))
    note = "" if total <= limit else f"truncated at retmax={limit}"
    return QueryResult(
        query_id=query_id,
        label=label,
        source="PubMed",
        query=query,
        purpose=purpose,
        total_hits=total,
        retrieved=ids,
        timestamp=utc_now(),
        note=note,
    )


def pubmed_fetch_records(pmids: list[str]) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Return ({pmid: record}, [pmids that could not be parsed]).

    The second element exists so that a record can never be dropped silently.
    An earlier version of this function matched only ``<PubmedArticle>`` and
    silently discarded book articles; the reconciliation now records every
    PMID that came back from esearch but produced no record.
    """
    records: dict[str, dict[str, str]] = {}
    for start in range(0, len(pmids), 100):
        chunk = pmids[start : start + 100]
        if not chunk:
            continue
        xml = http_get(
            f"{EUTILS}/efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(chunk),
                "rettype": "abstract",
                "retmode": "xml",
            },
        ).decode("utf-8", errors="replace")
        articles = re.findall(
            r"<(PubmedArticle|PubmedBookArticle)>(.*?)</\1>", xml, re.S
        )
        for _kind, article in articles:
            pmid = _first(article, r"<PMID[^>]*>(.*?)</PMID>")
            if not pmid:
                continue
            title = _first(article, r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>")
            if not title:
                title = _first(article, r"<BookTitle[^>]*>(.*?)</BookTitle>")
            records[pmid] = {
                "pmid": pmid,
                "title": _clean(title),
                "journal": _clean(_first(article, r"<Title>(.*?)</Title>")),
                "year": _clean(_first(article, r"<PubDate>.*?<Year>(\d{4})</Year>")),
                "doi": _clean(_first(article, r'<ArticleId IdType="doi">(.*?)</ArticleId>')),
                "pubtype": "; ".join(re.findall(r"<PublicationType[^>]*>(.*?)</PublicationType>", article)),
                "authors": _first(article, r"<Author ValidYN.*?</Author>", group=True),
                "abstract": _clean(
                    " ".join(re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", article, re.S))
                ),
            }
        time.sleep(0.4)
    unparsed = [pmid for pmid in pmids if pmid not in records]
    return records, unparsed


def _first(text: str, pattern: str, group: bool = False) -> str:
    match = re.search(pattern, text, re.S)
    if not match:
        return ""
    value = match.group(1) if match.groups() else match.group(0)
    if group:
        names = re.findall(r"<LastName>(.*?)</LastName>", value)
        return ", ".join(names[:6]) + (" et al." if len(names) > 6 else "")
    return value


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


# =============================================================================
# Europe PMC
# =============================================================================
def epmc_search(query_id: str, label: str, query: str, purpose: str, limit: int = 100) -> QueryResult:
    payload = json.loads(
        http_get(
            EPMC,
            {
                "query": query,
                "format": "json",
                "pageSize": str(limit),
                "resultType": "core",
            },
        )
    )
    hits = payload.get("resultList", {}).get("result", [])
    total = int(payload.get("hitCount", 0))
    ids = [str(h.get("pmid") or h.get("id", "")) for h in hits]
    return QueryResult(
        query_id=query_id,
        label=label,
        source="EuropePMC",
        query=query,
        purpose=purpose,
        total_hits=total,
        retrieved=[i for i in ids if i],
        timestamp=utc_now(),
        note="" if total <= limit else f"truncated at pageSize={limit}",
    )


# =============================================================================
# ClinicalTrials.gov
# =============================================================================
def ctgov_search(query_id: str, label: str, query: str, purpose: str, limit: int = 100) -> QueryResult:
    payload = json.loads(
        http_get(
            CTGOV,
            {
                "query.term": query,
                "pageSize": str(limit),
                "countTotal": "true",
                "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,InterventionName",
            },
        )
    )
    studies = payload.get("studies", [])
    ids = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        nct = protocol.get("identificationModule", {}).get("nctId")
        if nct:
            ids.append(nct)
    return QueryResult(
        query_id=query_id,
        label=label,
        source="ClinicalTrials.gov",
        query=query,
        purpose=purpose,
        total_hits=int(payload.get("totalCount", len(studies))),
        retrieved=ids,
        timestamp=utc_now(),
    )


# =============================================================================
# GEO
# =============================================================================
def geo_search(query_id: str, label: str, query: str, purpose: str, limit: int = 100) -> QueryResult:
    payload = json.loads(
        http_get(
            f"{EUTILS}/esearch.fcgi",
            {"db": "gds", "term": query, "retmode": "json", "retmax": str(limit)},
        )
    )
    result = payload.get("esearchresult", {})
    ids = result.get("idlist", [])
    return QueryResult(
        query_id=query_id,
        label=label,
        source="GEO DataSets",
        query=query,
        purpose=purpose,
        total_hits=int(result.get("count", 0)),
        retrieved=[str(i) for i in ids],
        timestamp=utc_now(),
    )


# =============================================================================
# Screening rules
# =============================================================================
#: Inclusion requires the record to address BOTH the electrical axis and the
#: DNA/MRD axis, in an oncological context. Stated in advance, applied
#: mechanically, and every exclusion is recorded with its reason.
SCREEN_PATTERNS = {
    "electrical": re.compile(
        r"membrane potential|depolariz|depolaris|hyperpolariz|hyperpolaris|"
        r"\bion channels?\b|voltage[- ]gated|ligand[- ]gated|mechanosensitive|stretch[- ]activated|"
        r"electroceutical|tumou?r treating fields|electric field|electrical field|"
        r"electrotaxis|electrotaxism|bioelectric|\bvoltage\b|"
        # Short acronyms MUST be word-anchored. The ENaC pattern, unanchored,
        # matched inside an ordinary English word in one abstract and produced
        # a false core hit on the first audit run. The word it actually
        # matched inside is recorded in the report's correction notice; it is
        # not reproduced here, so that no copy of the retracted attribution
        # survives in this repository. The lookbehind/lookahead assertions
        # below are what prevent the recurrence.
        r"(?<![A-Za-z])Piezo1(?![A-Za-z0-9])|(?<![A-Za-z0-9])Kv1\.3(?![0-9])"
        r"|(?<![A-Za-z0-9])KCa3\.1(?![0-9])|(?<![A-Za-z0-9])TRPV1(?![0-9])"
        r"|(?<![A-Za-z])ENaC(?![A-Za-z0-9])",
        re.I,
    ),
    "dna": re.compile(
        r"cell[- ]free dna|cfdna|ctdna|circulating tumou?r dna|liquid biopsy|"
        r"dna methylation|methylome|methylation|fragmentomic|fragmentation profile|"
        r"copy number|\bcnv\b",
        re.I,
    ),
    "relapse": re.compile(
        r"relapse|recurren|residual disease|minimal residual|molecular residual|"
        r"\bmrd\b|persister|drug[- ]tolerant|measurable residual|"
        r"re[- ]?challenge|second[- ]?line",
        re.I,
    ),
    "stemness": re.compile(
        r"cancer stem|stemness|tumou?r[- ]initiating|stem[- ]like|stem cell|"
        r"plasticity|persister|quiescen",
        re.I,
    ),
    "lung": re.compile(
        r"\blung\b|\bnsclc\b|\bsclc\b|pulmonary|bronchogenic|lung adenocarcinoma|"
        r"lung squamous|\badenocarcinoma\b",
        re.I,
    ),
    "oncology": re.compile(
        r"cancer|tumou?r|carcinoma|neoplas|glioblastoma|melanoma|leukemia|"
        r"leukaemia|lymphoma|sarcoma|adenoma|metasta",
        re.I,
    ),
}


def screen_record(text: str) -> tuple[bool, list[str], dict[str, list[str]]]:
    """Apply the pre-registered screen.

    Returns ``(is_core_hit, matched_axes, matched_terms_per_axis)``.
    """
    axes: list[str] = []
    terms: dict[str, list[str]] = {}
    for name, pattern in SCREEN_PATTERNS.items():
        found = sorted({m.group(0).lower() for m in pattern.finditer(text)})
        if found:
            axes.append(name)
            terms[name] = found
    is_core = (
        "electrical" in axes
        and "dna" in axes
        and "relapse" in axes
        and "oncology" in axes
    )
    return is_core, axes, terms


# =============================================================================
# Run comparison
# =============================================================================
def compare_runs(current: dict, previous: dict) -> dict[str, object]:
    """Set-based comparison of two audit runs.

    Deliberately *not* a textual diff. The PubMed retrieval uses
    ``sort=relevance``, whose ranking is not stable between runs, so the
    ordered ``retrieved_ids`` lists can differ in order and in membership at
    the retmax boundary. Comparing the *sets* of PMIDs and the per-query hit
    counts is the reproducible comparison.
    """

    def _by_id(run: dict) -> dict[str, dict]:
        return {q["query_id"]: q for q in run.get("queries", [])}

    cur_q = _by_id(current)
    prev_q = _by_id(previous)

    hit_deltas = {}
    for qid, q in cur_q.items():
        if qid in prev_q:
            delta = q["total_hits"] - prev_q[qid]["total_hits"]
            if delta:
                hit_deltas[qid] = {
                    "previous": prev_q[qid]["total_hits"],
                    "current": q["total_hits"],
                    "delta": delta,
                }

    def _union(run: dict) -> set[str]:
        ids: set[str] = set()
        for q in run.get("queries", []):
            if q["source"] == "PubMed":
                ids.update(q.get("retrieved_ids", []))
        return ids

    cur_union = _union(current)
    prev_union = _union(previous)

    cur_screen = current.get("screening", {})
    prev_screen = previous.get("screening", {})
    cur_core = set(cur_screen.get("core_hit_pmids", []))
    prev_core = set(prev_screen.get("core_hit_pmids", []))
    cur_lung = set(cur_screen.get("core_hit_and_lung_pmids", []))
    prev_lung = set(prev_screen.get("core_hit_and_lung_pmids", []))

    return {
        "comparison": "set-based; ordered id lists are not comparable because "
        "PubMed sort=relevance ranking is not stable across runs",
        "hit_count_deltas": hit_deltas,
        "pubmed_union": {
            "previous_size": len(prev_union),
            "current_size": len(cur_union),
            "added": sorted(cur_union - prev_union),
            "removed": sorted(prev_union - cur_union),
            "n_added": len(cur_union - prev_union),
            "n_removed": len(prev_union - cur_union),
        },
        "core_hits": {
            "added": sorted(cur_core - prev_core),
            "removed": sorted(prev_core - cur_core),
        },
        "core_hits_and_lung": {
            "added": sorted(cur_lung - prev_lung),
            "removed": sorted(prev_lung - cur_lung),
        },
    }


# =============================================================================
# Main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Formal gap audit: bioelectric x lung relapse.")
    parser.add_argument(
        "--outdir",
        default="results/gap_audit_bioelectric",
        help="directory for the audit log and screening table",
    )
    parser.add_argument(
        "--skip-ctgov",
        action="store_true",
        help="skip ClinicalTrials.gov (slowest source)",
    )
    parser.add_argument(
        "--compare-with",
        default=None,
        help="path to a previous audit_log.json to compare against (set-based)",
    )
    args = parser.parse_args(argv)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    results: list[QueryResult] = []
    errors: list[dict[str, str]] = []

    print("== PubMed ==")
    for query_id, label, query, purpose in QUERIES:
        try:
            result = pubmed_search(query_id, label, query, purpose)
        except Exception as exc:  # noqa: BLE001 - logged, not fatal
            errors.append({"query_id": query_id, "source": "PubMed", "error": str(exc)})
            print(f"  {query_id} FAILED: {exc}")
            continue
        results.append(result)
        print(f"  {query_id} {label:<45} hits={result.total_hits:<6} retrieved={len(result.retrieved)}")

    print("== Europe PMC ==")
    for query_id, label, query in EPMC_QUERIES:
        purpose = f"Europe PMC replication of the PubMed-side question: {label}"
        try:
            result = epmc_search(query_id, label, query, purpose)
        except Exception as exc:  # noqa: BLE001
            errors.append({"query_id": query_id, "source": "EuropePMC", "error": str(exc)})
            print(f"  {query_id} FAILED: {exc}")
            continue
        results.append(result)
        print(f"  {query_id} {label:<45} hits={result.total_hits:<6} retrieved={len(result.retrieved)}")

    if not args.skip_ctgov:
        print("== ClinicalTrials.gov ==")
        ct_queries = [
            ("C01", "bioelectric x lung cancer", '"tumor treating fields" OR "pulsed electric field" OR "electric field" AND (lung cancer OR NSCLC OR SCLC)'),
            ("C02", "ion channel drug x cancer", '"ion channel" AND (cancer OR tumor) AND (inhibitor OR antibody OR drug)'),
            ("C03", "bioelectric x MRD", '(membrane potential OR "ion channel" OR bioelectric) AND ("minimal residual disease" OR MRD OR "cell-free DNA")'),
            ("C04", "bioelectric x cfDNA", '(membrane potential OR "ion channel" OR bioelectric OR electrotaxis) AND ("cell-free DNA" OR ctDNA OR cfDNA OR "liquid biopsy")'),
        ]
        for query_id, label, query in ct_queries:
            try:
                result = ctgov_search(query_id, label, query, label)
            except Exception as exc:  # noqa: BLE001
                errors.append({"query_id": query_id, "source": "ClinicalTrials.gov", "error": str(exc)})
                print(f"  {query_id} FAILED: {exc}")
                continue
            results.append(result)
            print(f"  {query_id} {label:<45} hits={result.total_hits:<6} retrieved={len(result.retrieved)}")

    print("== GEO ==")
    geo_queries = [
        ("G01", "lung cancer ctDNA serial", 'lung cancer AND ("cell-free DNA" OR ctDNA OR "liquid biopsy")'),
        ("G02", "ion channel expression cancer", '"ion channel" AND (cancer OR tumor) AND ("expression" OR "RNA-seq")'),
    ]
    for query_id, label, query in geo_queries:
        try:
            result = geo_search(query_id, label, query, label)
        except Exception as exc:  # noqa: BLE001
            errors.append({"query_id": query_id, "source": "GEO", "error": str(exc)})
            print(f"  {query_id} FAILED: {exc}")
            continue
        results.append(result)
        print(f"  {query_id} {label:<45} hits={result.total_hits:<6} retrieved={len(result.retrieved)}")

    # ---- fetch records for the union of PubMed hits ----
    print("== Fetching PubMed records for screening ==")
    union_pmids: list[str] = []
    for result in results:
        if result.source == "PubMed":
            for pmid in result.retrieved:
                if pmid not in union_pmids:
                    union_pmids.append(pmid)
    print(f"  union of PubMed PMIDs: {len(union_pmids)}")
    records, unparsed_pmids = pubmed_fetch_records(union_pmids)
    print(f"  records parsed:  {len(records)}")
    print(f"  NOT parsed:      {len(unparsed_pmids)}")
    if unparsed_pmids:
        print(f"    unparsed PMIDs (recorded in audit log): {unparsed_pmids}")

    # ---- screening ----
    print("== Screening ==")
    screening_rows = []
    core_hits: list[str] = []
    core_lung_hits: list[str] = []
    for pmid, record in records.items():
        text = " ".join(
            [
                record.get("title", ""),
                record.get("abstract", ""),
                record.get("pubtype", ""),
            ]
        )
        is_core, axes, terms = screen_record(text)
        row = {
            "pmid": pmid,
            "title": record.get("title", ""),
            "journal": record.get("journal", ""),
            "year": record.get("year", ""),
            "doi": record.get("doi", ""),
            "pubtype": record.get("pubtype", ""),
            "authors": record.get("authors", ""),
            "matched_axes": axes,
            "matched_terms": terms,
            "core_hit": is_core,
            "core_hit_and_lung": is_core and "lung" in axes,
            "abstract": record.get("abstract", ""),
        }
        screening_rows.append(row)
        if is_core:
            core_hits.append(pmid)
            if "lung" in axes:
                core_lung_hits.append(pmid)

    screening_rows.sort(key=lambda r: (not r["core_hit"], r["year"], r["pmid"]), reverse=False)

    # ---- write outputs ----
    audit = {
        "audit": {
            "name": "bioelectric state x lung-cancer relapse competence",
            "started_utc": utc_now(),
            "protocol": "pre-registered query grid + mechanical screening rules",
            "sources": sorted({r.source for r in results}),
            "sources_not_searched": [
                "Google Scholar (no API access)",
                "Web of Science (no API access)",
                "preprint servers without an index (bioRxiv/medRxiv direct API not used; "
                "Europe PMC preprint coverage used instead)",
            ],
        },
        "queries": [r.as_dict() for r in results],
        "errors": errors,
        "retrieval_reconciliation": {
            "pmids_in_union": len(union_pmids),
            "records_parsed": len(records),
            "pmids_returned_by_esearch_but_not_parsed": unparsed_pmids,
            "n_not_parsed": len(unparsed_pmids),
            "note": (
                "Every PMID returned by esearch is reconciled against the parsed "
                "record set. A non-empty 'pmids_returned_by_esearch_but_not_parsed' "
                "means those records were screened on title/abstract only if they "
                "parsed; if this list is non-empty the screening coverage is not "
                "100% and must be stated."
            ),
        },
        "screening": {
            "union_pmids_screened": len(screening_rows),
            "screening_coverage_pct": (
                round(100.0 * len(screening_rows) / len(union_pmids), 4) if union_pmids else None
            ),
            "core_hit_pmids": core_hits,
            "n_core_hits": len(core_hits),
            "core_hit_and_lung_pmids": core_lung_hits,
            "n_core_hits_and_lung": len(core_lung_hits),
            "rules": {
                "core_hit_requires": [
                    "electrical axis matched in title/abstract/publication type",
                    "dna axis matched",
                    "relapse axis matched",
                    "oncology axis matched",
                ],
                "axes_patterns": {k: v.pattern for k, v in SCREEN_PATTERNS.items()},
            },
        },
    }

    (outdir / "audit_log.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with (outdir / "screening_table.tsv").open("w", encoding="utf-8") as handle:
        handle.write("pmid\tyear\tjournal\tcore_hit\tcore_and_lung\taxes\tmatched_terms\tdoi\ttitle\n")
        for row in screening_rows:
            axes = ",".join(row["matched_axes"])
            terms = ";".join(f"{k}={'|'.join(v)}" for k, v in row["matched_terms"].items())
            title = row["title"].replace("\t", " ")
            handle.write(
                f"{row['pmid']}\t{row['year']}\t{row['journal']}\t{row['core_hit']}\t"
                f"{row['core_hit_and_lung']}\t{axes}\t{terms}\t{row['doi']}\t{title}\n"
            )

    print()
    print("=== SUMMARY ===")
    for result in results:
        print(f"  {result.query_id:<4} {result.source:<18} {result.label:<45} hits={result.total_hits}")
    print()
    print(f"  union size:      {len(union_pmids)}")
    print(f"  union screened:  {len(screening_rows)}")
    print(f"  coverage:        {100.0 * len(screening_rows) / len(union_pmids):.2f}% of union")
    print(f"  CORE HITS (electrical + dna + relapse + oncology): {len(core_hits)}")
    for pmid in core_hits:
        row = next(r for r in screening_rows if r["pmid"] == pmid)
        print(f"    {pmid} ({row['year']}, {row['journal']}) {row['title'][:110]}")
    print(f"  CORE HITS + LUNG AXIS: {len(core_lung_hits)}")
    for pmid in core_lung_hits:
        row = next(r for r in screening_rows if r["pmid"] == pmid)
        terms = ";".join(f"{k}={'|'.join(v)}" for k, v in row["matched_terms"].items())
        print(f"    {pmid} ({row['year']}, {row['journal']})")
        print(f"        matched: {terms}")
        print(f"        {row['title'][:120]}")
    print()
    print(f"  wrote {outdir / 'audit_log.json'}")
    print(f"  wrote {outdir / 'screening_table.tsv'}")

    if args.compare_with:
        previous = json.loads(Path(args.compare_with).read_text())
        comparison = compare_runs(audit, previous)
        comparison_path = outdir / "comparison_to_previous_run.json"
        comparison_path.write_text(
            json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print()
        print("=== COMPARISON TO PREVIOUS RUN (set-based) ===")
        print(f"  hit-count deltas: {comparison['hit_count_deltas'] or 'none'}")
        u = comparison["pubmed_union"]
        print(
            f"  PubMed union: {u['previous_size']} -> {u['current_size']} "
            f"(+{u['n_added']} / -{u['n_removed']})"
        )
        print(f"  core hits added:   {comparison['core_hits']['added'] or 'none'}")
        print(f"  core hits removed: {comparison['core_hits']['removed'] or 'none'}")
        print(
            f"  core+lung added:   {comparison['core_hits_and_lung']['added'] or 'none'}"
        )
        print(
            f"  core+lung removed: {comparison['core_hits_and_lung']['removed'] or 'none'}"
        )
        print(f"  wrote {comparison_path}")
    if errors:
        print(f"  {len(errors)} source(s) reported errors; see audit_log.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
