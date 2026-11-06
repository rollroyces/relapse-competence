# Gap audit — bioelectric state × lung-cancer relapse competence

**Audit ID:** `bioelectric-lung-relapse-2026-11`
**Date of run:** 2026-11-06T07:59:02Z
**Protocol:** pre-registered query grid + mechanical screening rules
**Reproduce:** `python scripts/gap_audit_bioelectric.py --outdir results/gap_audit_bioelectric`
**Machine-readable artefacts:** `results/gap_audit_bioelectric/audit_log.json`, `results/gap_audit_bioelectric/screening_table.tsv`

---

## Revision history and provenance

This report was first published at commit `c1c5c2a` and has been corrected
several times since. The table records what changed and when.

| Commit | Change | Where the retracted wording now lives |
|---|---|---|
| `c1c5c2a` | First publication — **this is the version that contained the defects below** | — |
| `ba05fce` | Parser reconciliation; attribution corrected; G.3 rewritten; set-based comparison recommended | git history at `c1c5c2a` |
| `615f331` | The four silently dropped book records identified and recovered | git history at `c1c5c2a` |
| `4a4adbc` | Documentation synchronised with the executed D1 | — |
| `b32221e` | Machine-generated findings disposition added | `results/audit_findings_disposition.json` |
| `841dc22` | Licence migrated to AGPL-3.0-or-later + commercial; retracted wording removed from this document's body | git history at `c1c5c2a` |
| `6bffa57` | Executable research plan added | — |

**Editorial rule now in force.** This document states the current truth. It
does **not** restate retracted claims inline, because a superseded sentence
sitting in an authoritative document can be mistaken for a live one — by a
reader, and by an automated check. The retraction record lives in two places:
git history at `c1c5c2a`, and the machine-generated
`results/audit_findings_disposition.json`.

`scripts/audit_findings_disposition.py` verifies **both directions** on every
run: the retracted wording must still be findable in `c1c5c2a` (so the
finding is demonstrably real) and must be absent from this file (so it is
demonstrably fixed).

---

## A. Topic Framing

### The question put to the audit

> Is *"bioelectric state × lung-cancer relapse competence"* a genuine literature gap, and can DNA and bioelectricity be combined into one instrument?

### Scope, stated before searching

| Axis | Definition used | Inclusion terms |
|---|---|---|
| **Electrical** | Membrane potential (resting, polarisation state), ion-channel abundance or activity, electroceuticals, tumour-treating fields, electrotaxis, bioelectric codes | `membrane potential`, `depolariz*`, `hyperpolariz*`, `ion channel(s)`, `voltage-gated`, `mechanosensitive`, `stretch-activated`, `electroceutical*`, `tumor treating fields`, `electric field`, `electrotaxis`, `bioelectric*`, `voltage`, `Piezo1`, `Kv1.3`, `KCa3.1`, `TRPV1`, `ENaC` |
| **DNA** | Cell-free / circulating tumour DNA and its derived readouts | `cell-free DNA`, `cfDNA`, `ctDNA`, `liquid biopsy`, `DNA methylation`, `methylome`, `methylation-based`, `fragmentomics`, `copy number` |
| **Outcome** | Residual disease, relapse, recurrence, drug-tolerant persistence | `relapse*`, `recurren*`, `residual disease`, `minimal residual disease`, `molecular residual`, `MRD`, `persister*`, `drug-tolerant`, `measurable residual` |
| **Stemness** | Cancer-stem / tumour-initiating phenotype and plasticity | `cancer stem`, `stemness`, `tumou?r-initiating`, `stem-like`, `plasticity`, `quiescen*` |
| **Disease** | Lung primary or metastasis | `lung neoplasms[MeSH]`, `lung`, `NSCLC`, `SCLC`, `pulmonary`, `bronchogenic` |
| **Context** | Any malignancy | `cancer`, `tumou?r`, `carcinoma`, `neoplas*`, `glioblastoma`, `melanoma`, `leukemia`, `lymphoma`, `sarcoma`, `metasta*` |

**Evidence layer targeted:** translational — a relapse-competent state that is *detectable from plasma DNA*, not one that is only visible under a microscope.

### Explicit non-goals

- Not a therapeutic trial design, and not a claim that bioelectricity cures cancer.
- Not a review of electroceuticals for their own sake.
- Not a claim of novelty based on "nobody has published on X" alone — see Section D.

### One assumption stated up front, because it shapes everything

**Cell-free DNA cannot measure membrane potential.** There is no plasma assay for the electrical state of a tumour cell. Any "bioelectric + DNA" instrument must therefore be *indirect*: DNA carries the measurement, and the electrical phenotype is inferred from what DNA reports. The audit therefore treats the question as *"is there evidence that an electrical phenotype is (a) real, (b) tied to relapse, and (c) reflected in DNA?"* — three separable sub-claims, each of which can fail independently.

---

## B. Retrieval and Evidence Audit

### B.1 Sources searched

| Source | API | Queries | Errors |
|---|---|---:|---:|
| PubMed (NCBI E-utilities) | esearch + efetch XML | 14 | 0 |
| Europe PMC | REST `search` | 5 | 0 |
| ClinicalTrials.gov | API v2 `studies` | 4 | 0 |
| GEO DataSets (NCBI E-utilities) | esearch `gds` | 2 | 0 |

### B.2 Sources **not** searched — and what that costs

- **Google Scholar** — no API access. Consequence: no citation-network or "cited-by" chasing, so a study that avoids the searched vocabulary and is discoverable only through forward citation would be missed.
- **Web of Science** — no API access. Consequence: no indexed-coverage check, no grey-literature sweep, no conference abstracts.
- **bioRxiv / medRxiv direct API** — not queried directly; Europe PMC preprint coverage was used instead (it indexes preprints, and one preprint was in fact retrieved and screened — see B.5).
- **Full text of paywalled articles** — not accessed. Abstract-level screening only, which is standard for a gap audit and is why Section H records abstract-level screening as a residual risk.
- **Trial registries other than ClinicalTrials.gov** (ISRCTN, EU CTIS, ChiCTR) — not searched. A negative trial finding is therefore *registry-specific*, not global.

**Absence of records here is not proof of absence in the literature.** Section H states which claims survive this limitation and which do not.

### B.3 Query grid and hit counts

All queries are recorded verbatim in `audit_log.json` with timestamps, hit counts and retrieved IDs.

**PubMed**

| ID | Query | Hits | Retrieved | Purpose |
|---|---|---:|---:|---|
| Q01 | bioelectric × lung | 11,315 | 300 | Size of the bioelectric-in-lung cluster |
| Q02 | bioelectric × relapse | 14,284 | 300 | Electrical phenotype ↔ relapse, any tumour |
| Q03 | bioelectric × stemness | 9,566 | 300 | **Saturation reference** — is electrical↔stemness established? |
| Q04 | DNA × relapse × lung | 1,086 | 300 | **Saturation reference** — ctDNA MRD in lung |
| Q05 | stemness × relapse × lung | 2,226 | 300 | **Saturation reference** — CSC and relapse in lung |
| Q06 | bioelectric × DNA | 455 | 300 | Does anyone read an electrical state off DNA? |
| Q07 | bioelectric × DNA × relapse | **42** | 42 | Core intersection, tumour-agnostic |
| **Q08** | **bioelectric × DNA × relapse × lung** | **1** | **1** | **Target query** |
| Q09 | bioelectric × stemness × relapse | 704 | 300 | Is electrical↔stemness extended to relapse? |
| Q10 | bioelectric × relapse × lung | 963 | 300 | Electrical phenotype and lung relapse, DNA axis removed |
| Q11 | bioelectric × DNA × stemness | 29 | 29 | Electrical state inferred from DNA in a stemness context |
| Q12 | CONTROL: bioelectric × relapse, non-lung | 13,321 | 300 | Transferability control |
| Q13 | CONTROL: bioelectric × relapse × lung, oncology only | 752 | 300 | Noise control |
| Q14 | MECHANISM: ion channel expression from cfDNA | 149 | 149 | Does the needed readout channel exist? |

**Europe PMC**

| ID | Query | Hits |
|---|---|---:|
| E08 | TARGET: bioelectric × DNA × relapse × lung | **0** |
| E07 | bioelectric × DNA × relapse (tumour-agnostic) | 1 |
| E09 | bioelectric × stemness × relapse | 66 |
| E12 | CONTROL: non-lung | 1,367 |
| E03 | bioelectric × stemness (saturation reference) | 308 |

**ClinicalTrials.gov** — C01 bioelectric × lung cancer: 135 · C02 ion-channel drug × cancer: 8 · C03 bioelectric × MRD: 6 · C04 bioelectric × cfDNA: 9

**GEO DataSets** — G01 lung-cancer ctDNA serial: 109 · G02 ion-channel expression in cancer: 71

### B.4 The arithmetic that matters

The absolute counts are not the finding. The **contraction ratio** is:

| Intersection | Hits | Contraction from its parent |
|---|---:|---|
| bioelectric × lung (Q01) | 11,315 | — |
| bioelectric × relapse (Q02) | 14,284 | — |
| bioelectric × stemness (Q03) | 9,566 | — |
| DNA × relapse × lung (Q04) | 1,086 | — |
| **bioelectric × DNA (Q06)** | **455** | 455 / (11,315 × 14,284) — a 3-order-of-magnitude collapse |
| **bioelectric × DNA × relapse (Q07)** | **42** | 9× further |
| **bioelectric × DNA × relapse × lung (Q08)** | **1** | 42× further |
| Same target, Europe PMC (E08) | **0** | independent replication |
| Same target, registered trials (C03 ∩ C04) | **0 relevant of 12 retrieved** | independent replication |

Meanwhile the two adjacent clusters are **crowded**: electrical↔stemness has 9,566 PubMed records and 308 in Europe PMC; ctDNA-MRD-in-lung has 1,086. **The white space is a true intersection of two mature fields, not an abandoned margin of one.**

### B.5 Screening

- **2,427** unique PMIDs in the retrieved union across the PubMed grid; **2,427** parsed and screened.
- **Screening coverage: 100.00% of the union** — no sampling, no exclusions before screening.
- Records were fetched as XML and screened mechanically on title + abstract + publication type against the patterns above.
- Screening rule (pre-registered): a **core hit** must match the electrical axis, the DNA axis, the relapse axis and the oncology axis. A **target hit** additionally matches the lung axis.
- **Core hits: 10. Target hits (core + lung): 1.**
- Every core hit was then read in full and adjudicated by hand against the scope. Results in Section B.6.

#### Retrieval reconciliation

Every PMID returned by `esearch` is reconciled against the parsed record set, and the result is written to `audit_log.json` under `retrieval_reconciliation`:

| Quantity | Value |
|---|---:|
| PMIDs in the retrieved union | 2,427 |
| Records parsed | 2,427 |
| PMIDs returned by `esearch` but not parsed | **0** |
| Screening coverage | **100.00%** |

> **Correction notice (coverage).** An earlier version of this report under-counted the retrieved union and asserted a screening-coverage figure that the audit log did not support: the parser matched only `<PubmedArticle>` and therefore **silently discarded book articles**, and the drop was recorded nowhere. The parser now also matches `<PubmedBookArticle>`, and the audit log carries an explicit reconciliation block so a record can never again be dropped without appearing in `pmids_returned_by_esearch_but_not_parsed`. The four records that were dropped are identified by PMID, and the superseded wording is quoted, in the machine-generated disposition artefact. The union size also drifts between runs for the reason given in Section B.8, so **the coverage figure is the meaningful one, not the union size**; the union quoted above is the size of the run whose log is committed here.

**The four dropped records, identified and recovered.** The defect was not merely
hypothetical. Diffing the pre-fix run's retrieved union against its screened
record set isolates exactly four PMIDs that came back from `esearch` and
produced no record:

| PMID | XML root element | In the current union? | In the current screening table? |
|---|---|:--:|:--:|
| 22787676 | `<PubmedBookArticle>` | yes | **yes** |
| 31424841 | `<PubmedBookArticle>` | yes | **yes** |
| 31971703 | `<PubmedBookArticle>` | yes | **yes** |
| 32119350 | `<PubmedBookArticle>` | yes | **yes** |

An `efetch` batch of those four returns **4 `<PubmedBookArticle>` and 0
`<PubmedArticle>`** — the old parser's `<PubmedArticle>`-only regex could not
match any of them. All four are now retrieved, parsed and screened.

One nuance worth recording, because it is easy to get wrong: PubMed's default
search **excludes the `books` subset**, which is why a separate
`"pubmed books"[filter]` query for the same topic returns 11 *different* book
records that are not in this audit at all. The four records above are different
again — they are book-formatted records that PubMed cross-lists in the main
database, so they do come back from an ordinary query. **Both failure modes
are now covered**: the search does not silently include the books subset, and
the parser does not silently drop any record that the search *did* return.

### B.8 Reproducibility evidence

The audit was run twice, one day apart, with the same code and the same queries. The comparison is set-based rather than textual, because `sort=relevance` is not a stable ordering (see Section H).

| Quantity | Run 1 | Run 2 | Change |
|---|---:|---:|---|
| Queries whose **hit count** changed | — | — | **0 of 25** |
| Core hits | 10 | 10 | **0 added, 0 removed** |
| Core hits + lung axis | 1 | 1 | **0 added, 0 removed** |
| PubMed union (set) | 2,422 | 2,427 | +25 / −20 |

The hit counts are identical across every query, and both the core-hit set and the single target hit are unchanged. The union *set* moved by 45 PMIDs because relevance ranking shifts which records land inside the `retmax=300` window — precisely why a textual diff of the two logs would produce a large volume of ordering noise while the substantive results are unchanged.

Artefact: `results/gap_audit_bioelectric/comparison_to_previous_run.json`.

### B.6 Adjudication of the 10 core hits

| PMID | Year | Study | Adjudication |
|---|---:|---|---|
| **42327581** | 2026 | *The Emerging Role of CACNA1E in Cancer* (J Cancer) — narrative review | **Closest to target.** Voltage-gated Ca²⁺ channel (Cav2.3): somatic mutations in air-pollution-related lung cancer and NSCLC; DNA methylation differences in breast cancer; METTL3-m6A stabilisation driving WNT7B/Ca²⁺ chemoresistance; amplification/overexpression correlating with relapse in Wilms' tumour; downregulation linked to temozolomide resistance in GBM. **No primary data. No cfDNA. No serial sampling.** Review only. |
| **39191501** | 2024 | *DNA Methylation in Recurrent Glioblastomas: Increased TEM8…* | **Near-miss, high value.** Genome-wide methylation arrays, 11 primary vs 13 recurrent GBM: differential methylation of **solute carrier and ion channel genes**; functionally validated hypomethylated-upregulated TEM8/ANTXR1. **Tissue-based, no plasma. GBM, not lung.** |
| **36038893** | 2022 | *Low mtDNA copy number induces chemo resistance via EMT by DNA methylation in ESCC* | **Near-miss, the exact causal chain.** Low mtDNA → **mitochondrial membrane potential depolarisation** → DNMT-mediated DNA methylation → EMT and chemoresistance. 88 patient specimens + cell lines. **Tissue-based. Oesophageal, not lung.** |
| **32777557** | 2020 | *Prediction of Efficacy of Postoperative Chemotherapy by DNA Methylation of CDO1 in Gastric Cancer* | **Near-miss.** CDO1 promoter methylation ↔ **mitochondrial membrane potential**; predicts differential recurrence-free survival in 321 stage II/III gastric cases. **Tissue-based. Gastric, not lung.** |
| **29723302** | 2018 | *Preserved SCN4B expression … recurrence-free survival in papillary thyroid cancer* | **Near-miss.** Voltage-gated Na⁺ channel β-subunit (SCN4B); RNA/protein down in tumour, one CpG hypermethylation site anti-correlated with expression (r = −0.48); preserved expression predicts favourable RFS. GEO + TCGA. **Tissue-based. Thyroid, not lung.** |
| **42722615** | 2026 | *PTEN homozygous deletion is a negative prognostic factor in TTFields-treated glioblastoma* | **Near-miss, the bioelectric-therapy biomarker angle.** DNA methylation profiling + TSO500 on 80 TTFields-treated gliomas; homozygous PTEN deletion predicts worse survival **under TTFields but not in TTFields-naïve controls** (HR 3.86, p = 0.0049). A predictive biomarker for an electrical therapy, found via DNA methylation. **Tissue-based, treatment-response not residual disease. GBM, not lung.** |
| 40628732 | 2025 | *Glioblastoma at the crossroads* (review) | Excluded: narrative review; electrical axis only as a passing mention of "electric field therapy". |
| 41465586 | 2025 | *Glioblastoma — A Contemporary Overview* (review) | Excluded: narrative review; no electrical-relapse mechanism. |
| 23818572 | 2013 | *Common gene pathways altered by DNA methylation in breast and prostate cancers* (review) | Excluded: review; "potassium voltage-gated family members" is a passing mention; no relapse mechanism. |
| 41648746 | 2024 | *VOLTAGE-2: nivolumab monotherapy in dMMR resected colon cancer* | **Excluded — artefact.** Matched the literal substring "voltage" in the trial name VOLTAGE-2. No electrical content whatsoever. |

### B.7 A screening error that was found and corrected

The first audit run produced **11** core hits, including PMID 42019833 (Stewart et al., *YAP1 Defines an Emergent, Plastic Population of Relapsed SCLC*, J Thorac Oncol 2026) — a paper that is unmistakably on the lung-relapse-stemness axis. It was a **false positive**: the regex term `enac` (the epithelial sodium channel acronym, case-insensitive) matched inside the ordinary English word **"tenac|ious"** — from the phrase *"a tenacious subpopulation"*. The word `treatment-naive` also occurs in the abstract and is an equally plausible-looking candidate, but it does **not** contain the substring; `tenacious` is the only word in the abstract that does.

> **Correction notice.** An earlier version of this report attributed the false positive to the wrong word. The true source is `"tenac|ious"` — the only word in that abstract containing the pattern. The retracted wording is quoted in the machine-generated disposition artefact and also appears in the commit message of `c1c5c2a`, the commit that first published this audit; that history is left in place rather than rewritten, and this notice is the correction of record.

Two things were done, and both are recorded here rather than quietly fixed:

1. The short acronyms (`ENaC`, `Piezo1`, `Kv1.3`, `KCa3.1`, `TRPV1`) are now word-anchored with lookbehind/lookahead assertions.
2. The screening output now records **which term matched which axis** for every record, so a reviewer can see the reason for any inclusion without re-running anything.

This is exactly the class of silent error the `relapse-competence` package exists to prevent, and it is disclosed here because a gap audit that hides its own errors cannot be audited.

**Consequence for the findings:** the YAP1/SCLC paper drops out of the *electrical* core — correctly, because YAP1 is a **mechanotransduction** transcriptional coactivator, not an ion channel or a membrane-potential phenotype. It is instead handled in Section C as the single most important *adjacent* paper.

---

## C. Structured Gap Map

| # | Gap | Type | Confidence | Audit basis |
|---|---|---|---|---|
| **G1** | **No study joins an electrical phenotype to a relapse-competent state in any tumour type, let alone lung.** | Mechanism-to-translation gap | **High** | Q07 = 42 PubMed / E07 = 1 Europe PMC; after adjudication, **zero** of the 10 core hits links a measured electrical phenotype to relapse in the same tumour. The 4 mechanistic near-misses (39191501, 36038893, 32777557, 29723302) each establish *one* edge of the chain in a *different* tumour. |
| **G2** | **The lung-specific relapse-competent state was only defined in 2026, and its defining readout was mechanical/transcriptional (YAP1), not electrical.** | Population gap + mechanism gap | **High** | 42019833 / 41279637 (preprint 2025-10-22, peer-reviewed 2026-04-20) is the only lung paper that defines a relapse-emergent plastic population, and it used ctDNA, CTCs and biopsies — the DNA channel is already open in lung. |
| **G3** | **The electrical↔DNA coupling has only ever been demonstrated on tissue.** | Method-resolution gap | **High** | All four mechanistic near-misses used tissue: methylation arrays on paired primary/recurrent GBM (39191501), 88 ESCC surgical specimens (36038893), 321 gastric cases (32777557), GEO+TCGA tissue (29723302). GEO shows the data exist separately (G01: 109 lung ctDNA datasets; G02: 71 ion-channel-expression datasets) but not joined. |
| **G4** | **The electrical phenotype has never been used as a plasma-derived predictor of lung relapse.** | Mechanism-to-translation gap | **Medium-High** | C03 (bioelectric × MRD) = 6 registered trials and C04 (bioelectric × cfDNA) = 9 — **all 12 retrieved records were manually inspected and none is relevant** (CLL, pancreatic cancer, hydrogen inhalation, PSMA radioligand therapy, tirzepatide, etc.). Zero registered trials combine an electrical intervention or electrical biomarker with plasma MRD monitoring. |
| **G5** | **No validated biomarker predicts who benefits from a bioelectric therapy.** | Evidence gap | **Medium** | 42722615 shows the method works (PTEN deletion predicts TTFields benefit, and *not* in TTFields-naïve controls). It is tissue-based, GBM-specific, and n = 80. No lung equivalent; no cfDNA equivalent. |
| **G6** | **Electroceuticals are largely untested in lung cancer, and the ones that exist target non-lung tumours.** | Population gap | **Medium** | C02 (ion-channel drug × cancer) = 8 registered trials; the verified ones are GBM (senicapoc/KCa3.1 + perampanel, EARLY_PHASE1, recruiting; potassium-channel reprogramming of the GBM microenvironment, status unknown). TTFields in lung: LUNAR-2 Phase 3 recruiting (NCT06216301, n = 734) after EF-36 terminated for **insufficient enrolment** (n = 15, *not* safety). Aliya PEF + chemotherapy in resectable NSCLC terminated, reason "Strategic", n = 5 (NCT05583188). |

**What the field has NOT been short of:** electrical↔stemness (9,566 PubMed records), ctDNA MRD in lung (1,086), CSC and relapse in lung (2,226). Any framing that implies these sub-fields are unexplored would be a pseudo-gap.

---

## D. Pseudo-Gaps Rejected

| Candidate | Why rejected |
|---|---|
| *"Add single-cell to the CSC field"* | Generic upgrade. 2,226 PubMed records already link stemness to lung relapse; the sub-field is crowded, and single-cell adds a method without a question. |
| *"Do multi-omics integration of cfDNA"* | 1,086 records already do ctDNA-MRD in lung. Integration is the current baseline, not a gap. |
| *"Study dynamic changes during treatment"* | Already the standard design of ctDNA-MRD studies; the open question is *which* state, not *when*. |
| *"Bioelectricity is a promising new anticancer therapy"* | Not a gap statement. It is a field-status claim, and it is partly falsified by the trial record in G6. |
| *"Nobody has studied ion channels in lung cancer"* | **Factually false.** CACNA1E somatic mutations in air-pollution-related lung cancer and NSCLC (42327581); SCNN1A/ENaC and Piezo1 have lung literature; Li et al. 2018 (PMID 30015269) demonstrated electrotaxis of lung adenocarcinoma tumour-initiating cells via stretch-activated cation channels. |
| *"The literature is completely empty here"* | **False.** One target hit (42327581), four mechanistic near-misses with the exact causal chain, one lung paper defining the state, and one bioelectric-therapy biomarker paper. The gap is *narrow, specific and real* — not empty. |
| *"TTFields works, so electrotherapy will cure lung cancer"* | Overclaim. EF-36 (first-line NSCLC) terminated for insufficient enrolment with 15 patients; the Aliya PEF neoadjuvant trial terminated after 5. LUNAR-2 (Phase 3) is running; no readout exists. |

---

## E. Top Priority Opportunities

Only medium/high-confidence gaps qualify.

**Opportunity 1 (from G1 + G2 + G3): The electrical phenotype of the relapse-competent state, inferred from plasma DNA.**
The only lung-specific definition of a relapse-emergent plastic population (42019833) used ctDNA. The electrical↔DNA coupling is established in four other tumours (G3). Nobody has asked whether the same coupling exists in lung, and nobody has asked whether it is readable from plasma.

**Opportunity 2 (from G5 + G6): A plasma DNA biomarker for who benefits from electrotherapy.**
42722615 proves the concept end-to-end in tissue: a DNA alteration (PTEN loss) predicts TTFields benefit *and does not predict outcome in untreated controls* — the signature of a genuine predictive biomarker. In lung, electrotherapy is being tested in Phase 3 with **no** companion biomarker, so the LUNAR-2 readout will have to be interpreted without one.

**Opportunity 3 (from G4): Close the loop for the first time — electrical state → DNA → relapse, measured longitudinally.**
This is Opportunity 1 plus the explicit, falsifiable comparison against the existing mutation channel: does an electrical signature add lead time over mutation trajectory alone?

---

## F. Primary Recommended Direction

**Opportunity 3**, on the grounds of novelty × feasibility × impact balance:

> **Measure the electrical phenotype of the lung-cancer relapse-competent state from serial plasma DNA, and test whether it adds lead time over the mutation channel alone.**

Why it wins:

- **Credibility.** It is the only candidate that directly attacks the named open question in the lung field (a relapse-competent population defined in 2026, with a DNA readout already working) while using a mechanism that is *already demonstrated in four other tumours*, so it is not a speculative bolt-on.
- **Novelty.** It is the first to make the electrical phenotype a *plasma-derived*, *plasma-serialised* quantity rather than a tissue or microscopy observation. The audit's core-hit table shows that no other study occupies this cell.
- **Feasibility.** The pieces exist and are already owned: `deepcatch`'s methylation channel, `mrnavax`'s `variant-regulatory` (AlphaGenome Atlas AVI, covering the 98% of the genome where AlphaMissense is silent), and the `relapse-competence` benchmark engine, which can compute whether an added channel is worth the read budget **before any cohort exists**.

**Status: the simulation half of this recommendation (D1) has since been executed** — see [`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md). It confirmed that the state signal survives bulk dilution (enrichment AUC 0.85–0.95 within the MRD-positive population), quantified the cost (a 25% electrical allocation costs ~3 points of MRD sensitivity at 200 loci, ~12 at 50 loci), and reframed the claim from *detection* to *refinement* of the MRD-positive population. The empirical half (D2, D3) remains open and is now the critical path, because it needs a serial cohort that no open dataset provides.
- **Project value.** It publishes even if the biology disappoints: a rigorous negative ("the electrical signature carries no information beyond the mutation channel in lung") is a result, and it would be the first such measurement.

Opportunity 2 is deliberately *not* the lead: it depends on Opportunity 1 defining the phenotype, and on LUNAR-2's readout landing.

---

## G. Gap-to-Study Conversion

### G.1 The combined instrument — how DNA and bioelectricity join

```
          PLASMA cfDNA (the only channel that can be sampled serially)
                        │
        ┌───────────────┼────────────────┐
        │               │                │
  Channel 1        Channel 2         Channel 3
  mutation         methylation        fragmentomics
  trajectory    → deconvolution    → size / motif profile
        │               │                │
  "persistence"   "expression       "tumour-vs-normal
                   profile"          fraction"
        │               │
        │        ┌──────┴──────────┐
        │        │ ELECTRICAL      │
        │        │ PHENOTYPE       │  ← inferred, never directly measured
        │        │ ion-channel      │
        │        │ signature        │
        │        │ (KCa3.1, CACNA1E,│
        │        │  SCN4B, ENaC,    │
        │        │  Piezo1, TRPV1)  │
        │        └──────┬──────────┘
        │               │
        └───────┬───────┘
                │
        relapse-competent state?
                │
        ├─ MRD+ / electrical+ → escalate with electroceutical
        └─ MRD+ / electrical− → different biology, different drug
```

**The honest constraint, restated:** the electrical phenotype is *inferred* through the chain methylation → expression → ion-channel abundance → electrical state. **Cell-free DNA cannot measure a membrane potential.** Every step of that chain is an assumption that has to earn its place, and the study must be designed to break each link separately.

### G.2 Study designs, ranked

| Design | Answers | Sample / data | Key endpoint | Falsifiable if |
|---|---|---|---|---|
| **D1. Simulation feasibility — EXECUTED, see [`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md)** | Does a bulk ion-channel channel earn the read budget it takes from the mutation panel? | `relapse-competence` simulator, extended with a bulk electrical channel whose signal is boosted by a modelled relapse-competent fraction `f_state` | MRD sensitivity cost vs within-MRD+ PPV gain and state-specific AUC, across depth × allocation grids | The channel adds no information once tumour burden is divided out |
| **D2. Retrospective cohort, tissue-anchored** | Does the electrical↔methylation coupling exist in lung, as it does in GBM/ESCC/gastric/thyroid? | Paired primary + recurrent lung tumour tissue, methylation arrays, RNA-seq, ion-channel panel | Concordance between methylation-derived and measured ion-channel expression; methylation delta at relapse | Coupling absent in lung while present in the four published tumours |
| **D3. Retrospective cohort, plasma** | Is the electrical signature readable from plasma, and does it predict relapse? | Serial plasma cfDNA (methylation + mutation) from treated lung cancer patients with known relapse timing | Δlead time over mutation channel alone; sensitivity at 98.5% specificity | Electrical signature adds nothing beyond mutation trajectory |
| **D4. Prospective, MRD-guided** | Does using the electrical signature change decisions? | MRD- and electrical-stratified randomisation of electroceutical escalation | Relapse-free survival | No benefit from electrical-stratified escalation |
| **D5. Preclinical, therapeutic** | Does blocking the inferred electrical phenotype kill the relapse-competent clone? | Patient-derived organoids with confirmed relapse-competent state; ion-channel inhibitors ± TKI | Clonal kill rate at the relapse-competent state | Inhibitors spare the relapse-competent clone |

**Recommended sequence: D1 → D2 → D3 → D4.** D1 costs days and can kill the whole programme on its own; D2 is the cheapest way to learn whether the coupling transfers to lung at all; D3 is the first claim anyone would cite.

### G.3 Minimum executable plan for D1

**D1 has since been executed.** The full write-up, with the measured numbers
and the honest limits, is in [`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md).
What was actually built differs from the sketch below in one important way, and
the difference is worth recording.

**What was planned.** A multi-channel refactor followed by an electrical channel
whose information content about the relapse-competent state was to be swept as
an abstract "amount of information" parameter.

**What was built.** The same multi-channel refactor, but the electrical channel
is parameterised **biologically** rather than information-theoretically: a
latent `f_state` — the fraction of the tumour that is relapse-competent — with
overlapping distributions for relapsers (0.25 ± 0.12) and persistent
non-relapsers (0.10 ± 0.12). The channel's per-locus signal is
`c · V · shedding · (1 + κ · f_state)`. Two scores are reported, because the
distinction is the whole point: a **raw** score that is a burden proxy, and a
**burden-normalised enrichment ratio** that isolates the state.

The biological parameterisation replaced the information-theoretic one for a
reason that only became visible during implementation: an abstract "information
content" parameter cannot distinguish *state* information from *burden*
information, and those two are exactly what the hypothesis is about. Sweeping
one would have hidden the key distinction instead of exposing it.

**What D1 found.** The state signal does survive bulk dilution — enrichment
AUC 0.85–0.95 within the MRD-positive population — but the *raw* score
discriminates better (0.99–1.00) precisely because it is a growth proxy. And
the cost is real: a 25% electrical allocation costs ~3 points of MRD
sensitivity at 200 loci and ~12 points at 50 loci.

**What this changes for D2.** The tissue-level readout must be the
**burden-normalised enrichment ratio**, not raw ion-channel abundance. A tissue
study measuring raw abundance would re-confirm the growth signal and say
nothing about the relapse-competent state.

This is the "combine DNA and bioelectricity" done honestly: it is a decision, not a demonstration.

### G.4 Datasets and access routes

- **Serial lung plasma**: PLCO via CDAS, or Taizhou via EGA DAC (both application-gated; see `DATASETS.md`).
- **Open accessions**: GSE185307 (13 plasma cfDNA, ONT 5mC methylation, 6 LUAD + 7 healthy — feasibility only, no serial sampling), GSE122126 (Moss 2018 cfDNA 450K, 11 cancer + 59 cfDNA incl. 4 lung).
- **Tissue for D2**: GEO returns 109 lung-cancer ctDNA datasets and 71 ion-channel-expression datasets as *separate* pools; no joined dataset exists.

---

## H. Risk Review

**Strongest part of this analysis.** The contraction arithmetic is machine-generated and re-runnable: 455 → 42 → 1 across the PubMed grid, independently 0 in Europe PMC, and 0 relevant of 12 manually inspected registered trials. The claim "this specific intersection is unoccupied" rests on counts and an adjudication table, not on impression.

**Weakest evidence-supported claim.** G5 and G6 are Medium rather than High. They rest on ClinicalTrials.gov keyword searches that are vulnerable to vocabulary drift (a trial on an ion channel with no electrical framing would not surface), on a registry set that excludes ISRCTN / EU CTIS / ChiCTR, and on a single example (42722615) of a bioelectric-therapy biomarker. Absence of a registered predictive biomarker for LUNAR-2 is an inference from search coverage, not a documented fact.

**Most assumption-dependent claim.** That the methylation → expression → ion-channel → electrical-state chain survives the move from tissue to plasma. Plasma cfDNA is a dilute, heavily size-selected, cell-of-origin-skewed sample. A signal that is reproducible in bulk tissue methylation may not survive that dilution. D2 exists precisely to test this before D3 spends cohort access.

**Most likely pseudo-gap risk.** That "electrical phenotype of the relapse-competent state" is a *retrospective rationalisation* of four papers that each studied something else (ion-channel methylation in recurrent GBM; mtDNA/methylation in ESCC; CDO1 in gastric cancer; SCN4B in thyroid), whose convergence is real but whose unification is mine, not the field's. The defence is that the audit does **not** claim the field wants this — it claims the cell is unoccupied and that the components exist. If the field's own framing is "mechanotransduction, not bioelectricity" (as YAP1/SCLC suggests), then this is a competing hypothesis to be tested, not a gap to be filled. **That distinction should be tested with the field, not asserted by me.**

**Easiest thing to over-interpret.** The single target hit (42327581). It is a narrative review of one gene. Its presence does not mean the field is converging; it means one review happened to mention several of the searched terms. It should not be cited as evidence that anyone is working on this.

**Coverage limitation that could invalidate a negative.** No Google Scholar, no Web of Science, no citation chasing, no non-English registries, no conference abstracts, abstract-level screening only, and paywalled full texts unread. **The defensible claim is narrow:** *no indexed, searchable record in PubMed, Europe PMC, ClinicalTrials.gov or GEO combines an electrical phenotype with a plasma-DNA readout of relapse in lung cancer.* That is not the same as *nobody has done it*, and the report does not say so.

**Fallback if the top gap collapses.** If D2 shows the coupling does not transfer to lung, the programme does not die — it becomes a cross-tumour comparison ("the electrical↔DNA coupling is present in GBM, ESCC, gastric and thyroid but absent in lung"), which is still a result. And the D1 simulation and the audited evidence chain publish independently of the biology.

**What would change the conclusion.** A Google Scholar / Web of Science sweep that surfaces work using vocabulary outside the defined term sets (for example "voltage", "electrophysiology", "transcriptomic electrical phenotype"); a registered trial not indexed in ClinicalTrials.gov; or a 2026-2027 preprint on lung relapse competence that already includes ion-channel profiling. Given the pace of the field, the last of these is the most likely and would be checked before any wet work begins.

---

## I. Retrieved and Verified References

All metadata below was retrieved directly from NCBI E-utilities or the publisher DOI record during this audit. Peer-reviewed and preprint status is stated explicitly.

### Target and near-miss studies

1. **Hou W.** The Emerging Role of CACNA1E in Cancer: Molecular Mechanisms and Therapeutic Implications. *J Cancer.* 2026 Jun 4;17(6):1155–1164. doi:10.7150/jca.133409. PMID [42327581](https://pubmed.ncbi.nlm.nih.gov/42327581/). PMCID PMC13280633. *Peer-reviewed review. The only record matching the full target intersection.*

2. **Stewart CA, Ramkumar K, Wang R, et al.** YAP1 Defines an Emergent, Plastic Population of Relapsed SCLC. *J Thorac Oncol.* 2026 Aug;21(8):103730. doi:10.1016/j.jtho.2026.103730. PMID [42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/). PMCID PMC13120736. *Peer-reviewed. Preprint version: bioRxiv 2025 Oct 22, doi:10.1101/2025.10.21.683746, PMID [41279637](https://pubmed.ncbi.nlm.nih.gov/41279637/). **Not an electrical study** — YAP1 is a mechanotransduction coactivator. Included as the key adjacent paper (G2).*

3. **Kundu P, Jain R, Kanuri NN, et al.** DNA Methylation in Recurrent Glioblastomas: Increased TEM8 Expression Activates the Src/PI3K/AKT/GSK-3β/B-Catenin Pathway. *Cancer Genomics Proteomics.* 2024 Sep-Oct;21(5):485–501. doi:10.21873/cgp.20466. PMID [39191501](https://pubmed.ncbi.nlm.nih.gov/39191501/). PMCID PMC11363927. *Peer-reviewed. Tissue methylation; ion-channel gene differential methylation at recurrence.*

4. **Kubo Y, Tanaka K, Masuike Y, et al.** Low mitochondrial DNA copy number induces chemotherapy resistance via epithelial-mesenchymal transition by DNA methylation in esophageal squamous cancer cells. *J Transl Med.* 2022 Aug 29;20(1):383. doi:10.1186/s12967-022-03594-2. PMID [36038893](https://pubmed.ncbi.nlm.nih.gov/36038893/). PMCID PMC9422107. *Peer-reviewed. Mitochondrial membrane potential depolarisation → DNA methylation → EMT/chemoresistance.*

5. **Harada H, Soeno T, Yokoi K, et al.** Prediction of Efficacy of Postoperative Chemotherapy by DNA Methylation of CDO1 in Gastric Cancer. *J Surg Res.* 2020 Dec;256:404–412. doi:10.1016/j.jss.2020.07.001. PMID [32777557](https://pubmed.ncbi.nlm.nih.gov/32777557/). *Peer-reviewed. CDO1 promoter methylation ↔ mitochondrial membrane potential; 321 stage II/III cases.*

6. **Gong Y, Yang J, Wu W, et al.** Preserved SCN4B expression is an independent indicator of favorable recurrence-free survival in classical papillary thyroid cancer. *PLoS One.* 2018 May 3;13(5):e0197007. doi:10.1371/journal.pone.0197007. PMID [29723302](https://pubmed.ncbi.nlm.nih.gov/29723302/). PMCID PMC5933725. *Peer-reviewed. Voltage-gated Na⁺ channel β-subunit; methylation–expression anti-correlation r = −0.48.*

7. **Nückles J, Jelgersma C, Siewert C, et al.** PTEN homozygous deletion is a negative prognostic factor in tumor treating fields-treated glioblastoma, IDH wildtype patients. *Brain Pathol.* 2026 Sep 10:e70143. doi:10.1111/bpa.70143. PMID [42722615](https://pubmed.ncbi.nlm.nih.gov/42722615/). PMCID PMC13561735. *Peer-reviewed. DNA-methylation-based predictive biomarker for a bioelectric therapy; HR 3.86, p = 0.0049, and absent in TTFields-naïve controls.*

8. **Li Y, Yu WK, Chen L, et al.** Electrotaxis of tumor-initiating cells of H1975 lung adenocarcinoma cells is associated with both activation of stretch-activated cation channels (SACCs) and internal calcium release. *Bioelectrochemistry.* 2018 Dec;124:80–92. doi:10.1016/j.bioelechem.2018.03.013. PMID [30015269](https://pubmed.ncbi.nlm.nih.gov/30015269/). *Peer-reviewed. Not retrieved by the Q08 query because its abstract lacks a DNA term — identified by the tumour-agnostic control searches.*

### Registered interventions (ClinicalTrials.gov)

9. **NCT06216301** — LUNAR-2: TTFields with pembrolizumab + platinum chemotherapy in metastatic NSCLC. Phase 3, n = 734, **RECRUITING** (2024-07-31 → 2028-10).
10. **NCT04892472** — EF-36/Keynote B36: TTFields + pembrolizumab, first-line advanced/metastatic NSCLC. Phase 2, n = 15, **TERMINATED**: *"Phase 2 study terminated due to insufficient enrollment and was not based on safety concerns."*
11. **NCT05583188** — Neoadjuvant Aliya™ PEF ablation + systemic therapy in resectable stage IIB–IIIA NSCLC. n = 5, **TERMINATED**, reason "Strategic".
12. **NCT06739031** — PEF ablation devices for lung tumours (NSCLC). **RECRUITING** (2024-12-25).
13. **NCT07284069** — Senicapoc (KCa3.1) and Perampanel in newly diagnosed glioblastoma. EARLY_PHASE 1, n = 36, **RECRUITING** (2026-03).
14. **NCT03954691** — Targeting potassium channels to reprogram the glioblastoma microenvironment. n = 50, status **UNKNOWN**.

### Register of rejected core hits

15. Day TK, Bianco-Miotto T. *Endocr Relat Cancer.* 2013;20(5):R215–32. PMID [23818572](https://pubmed.ncbi.nlm.nih.gov/23818572/) — review, passing mention.
16. Singh S, et al. *Signal Transduct Target Ther.* 2025;10(1):213. PMID [40628732](https://pubmed.ncbi.nlm.nih.gov/40628732/) — review.
17. Królikowska K, et al. *Int J Mol Sci.* 2025;26(24):12162. PMID [41465586](https://pubmed.ncbi.nlm.nih.gov/41465586/) — review.
18. VOLTAGE-2 colon cancer trial, *ESMO GI Oncol.* 2024. PMID [41648746](https://pubmed.ncbi.nlm.nih.gov/41648746/) — **artefact**, matched on the trial name.

---

### Disposition of review findings

Four defects were raised against the first published version of this report.
Each is dispositioned in [`results/audit_findings_disposition.json`](../results/audit_findings_disposition.json),
which is **generated by running the checks** rather than written by hand, so it
cannot disagree with the repository it describes:

```bash
python scripts/audit_findings_disposition.py
```

| Finding | Status | Fixed in |
|---|---|---|
| F1 — §B.5 coverage claim vs the log; four book records silently dropped | RESOLVED | `ba05fce`, `615f331` |
| F2 — §B.7 attributed the false positive to the wrong word | RESOLVED | `ba05fce` |
| F3 — §G.3 described a channel the simulator did not implement | RESOLVED | `ba05fce`, `c98d4c5`, `4a4adbc` |
| F4 — the report advised a textual diff that `sort=relevance` makes noisy | RESOLVED | `ba05fce` |

F2 is re-derived from the source record on every run: the script re-fetches
PMID 42019833 and asserts that `tenacious` is the only word in the abstract
containing the substring, and that `treatment-naive` does not.

### Reproducing this audit

```bash
python scripts/gap_audit_bioelectric.py --outdir results/gap_audit_bioelectric
```

The script writes `audit_log.json` (every query, timestamp, hit count, retrieved IDs, source errors, screening rules, per-axis matched terms and the retrieval reconciliation) and `screening_table.tsv` (one row per record with per-axis matched terms).

**Compare runs set-wise, not by textual diff.** PubMed retrieval uses
`sort=relevance`, whose ranking is not stable between runs, so the ordered
`retrieved_ids` lists can differ in order and in membership at the `retmax`
boundary — a textual diff of the two files therefore produces a large volume
of ordering noise. The reproducible comparison is:

```bash
python scripts/gap_audit_bioelectric.py \
    --outdir results/gap_audit_bioelectric_rerun \
    --compare-with results/gap_audit_bioelectric/audit_log.json
```

which writes `comparison_to_previous_run.json` containing per-query hit-count
deltas, the added/removed PMID **sets** for the PubMed union, and the added/
removed core-hit and core+lung sets. Those are the quantities that should not
change if the literature has not moved; the file ordering is not one of them.
