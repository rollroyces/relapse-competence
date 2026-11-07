# Research plan — eliminating the relapse-competent state in lung cancer

**Version:** 0.1 (2026-11-06)
**Companion documents:** [`GAP-AUDIT-BIOELECTRIC.md`](GAP-AUDIT-BIOELECTRIC.md) (why the gap exists),
[`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md) (what the assay would cost),
[`ROADMAP.md`](ROADMAP.md) (sequencing and critical path)
**Status:** research and education only. Not a clinical protocol, not a
treatment recommendation, not a regulatory strategy.

---

## 0. The goal, stated so it can be killed

> **Primary objective.** In resected NSCLC and SCLC patients on adjuvant
> therapy, identify a relapse-competent tumour state that is (a) measurable from
> serial plasma DNA, (b) mechanistically distinct from bulk tumour burden, and
> (c) pharmacologically reversible — and show that removing it reduces relapse.

**Falsification.** The programme is dead if any of these is true:

| # | Killing condition | How it is detected |
|---|---|---|
| K1 | The state-specific readout carries no information beyond tumour burden | D2: burden-normalised enrichment AUC ≤ 0.6 |
| K2 | The state is not present, or not relapse-associated, in lung | D2: no state-associated methylation delta between primary and relapsed tissue |
| K3 | The state cannot be inferred from plasma at any affordable read budget | D3: enrichment AUC ≤ 0.65 at 200,000× / 200 loci |
| K4 | Every candidate target has an unacceptable therapeutic window | D0 gate: GTEx specificity verdict fails |
| K5 | Suppressing the state does not reduce relapse competence in patient-derived models | D5: no differential killing of the state-bearing clone |

**Note on the original framing.** The request was "cure lung cancer CSC". That
specific goal is not executable, for reasons that are documented rather than
asserted: the mithramycin trial (the one Phase II that attacked a
cancer-stem-cell signalling axis directly) enrolled 16 patients, produced 0 CR /
0 PR / 0 SD, had 3 deaths on study and closed for low accrual
([NCT01624090](https://clinicaltrials.gov/study/NCT01624090)); and the
mechanism has moved on since 2009 — the relapse-emergent population in lung
cancer is now described as a **YAP1-positive plastic persister state**
([PMID 42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/)), not as a
CD133-positive stem cell. The plan below therefore targets *the state that
actually relapses*, and treats "is that state a cancer stem cell?" as a
falsifiable sub-question rather than an assumption.

---

## 1. The mechanistic spine, with evidence

This is the chain the whole programme rests on. Every link is a retrieved
record; the weak links are marked.

```
   niche stiffness / mechanical stress
            │
            ▼
      PIEZO1  ────────────────► Ca²⁺ influx
   (mechanosensitive)                    │
            │                             ├──► KCa3.1 (KCNN4) ──► membrane potential,
            │                             │      [K⁺ efflux, hyperpolarisation]   electrical
            │                             │                                   signature
            ▼                             │
       YAP / TEAD ◄───────────────────────┘
            │
            ▼
   YAP1+ plastic persister population
   (drug-tolerant, senescent, stem-like;
    abandons SCLC lineage for LCNEC-like)
            │
            ▼
   RELAPSE   ──────────  and the state is
                           detectable in plasma DNA
```

| Link | Evidence | Strength |
|---|---|---|
| Mechanical niche drives lung cancer progression | [PMID 42978946](https://pubmed.ncbi.nlm.nih.gov/42978946/) (Front Cell Dev Biol 2026, 337 refs) | Review |
| Piezo1 axis is a therapeutic target in fibrosis-associated lung cancer | [PMID 42630570](https://pubmed.ncbi.nlm.nih.gov/42630570/) (Front Pharmacol 2026) | Review |
| **Piezo1 → YAP/TEAD in lung fibroblasts** | [PMID 42727476](https://pubmed.ncbi.nlm.nih.gov/42727476/) (BBRC 2026) | **Primary — but fibroblast, not tumour cell** |
| Piezo1 regulates antitumour T-cell cytotoxicity | [PMID 38514773](https://pubmed.ncbi.nlm.nih.gov/38514773/) (Nat Biomed Eng 2024) | Primary — immune arm |
| Piezo1 activation sensitises cells to TRAIL apoptosis | [PMID 31685811](https://pubmed.ncbi.nlm.nih.gov/31685811/) (Cell Death Dis 2019) | Primary |
| Piezo1 promotes PDAC chemoresistance in a stiff matrix | [PMID 39556518](https://pubmed.ncbi.nlm.nih.gov/39556518/) (ACS Biomater Sci Eng 2024) | Primary — other tumour |
| **YAP1+ plastic population emerges at SCLC relapse** | [PMID 42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/) (J Thorac Oncol 2026); preprint [PMID 41279637](https://pubmed.ncbi.nlm.nih.gov/41279637/) | **Primary — the anchor** |
| Lung cancer tumour-initiating cells respond to electric fields via stretch-activated cation channels | [PMID 30015269](https://pubmed.ncbi.nlm.nih.gov/30015269/) (Bioelectrochemistry 2018) | Primary |
| VGCC (CACNA1E / Cav2.3) links lung cancer, methylation and relapse | [PMID 42327581](https://pubmed.ncbi.nlm.nih.gov/42327581/) (J Cancer 2026) | **Review only — the single target-intersection record** |
| Electrical↔methylation coupling exists in recurrent GBM, oesophageal, gastric, thyroid tumours | [PMID 39191501](https://pubmed.ncbi.nlm.nih.gov/39191501/), [36038893](https://pubmed.ncbi.nlm.nih.gov/36038893/), [32777557](https://pubmed.ncbi.nlm.nih.gov/32777557/), [29723302](https://pubmed.ncbi.nlm.nih.gov/29723302/) | Primary, **tissue-based, other tumours** |

### 1.1 The one weak link, named

**Piezo1 → YAP/TEAD is demonstrated in lung *fibroblasts*, not in lung
*tumour cells*** ([PMID 42727476](https://pubmed.ncbi.nlm.nih.gov/42727476/)).
The YAP1+ relapse population is demonstrated in *tumour cells*
([PMID 42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/)). **Nobody has
connected the two inside a lung tumour.** D2 exists precisely to close that
link, and it can fail.

---

## 2. Target table

Targets are ranked by *state-linkage × druggability × window*, not by
literature volume. Window risk is scored with the GTEx-specificity gate that
already exists in `protein-flow-explorer` (54 tissues, specificity verdict).

### Tier 1 — the electrical amplifier

| Target | State link | Existing pharmacology | Window risk | Verdict |
|---|---|---|---|---|
| **KCa3.1 / KCNN4** | Ca²⁺-activated K⁺ efflux; sets the membrane potential that the state reads out | **Senicapoc** (Phase II in IPF, [PMID 42279523](https://pubmed.ncbi.nlm.nih.gov/42279523/); Phase 1 in newly diagnosed GBM with perampanel, [NCT07284069](https://clinicaltrials.gov/study/NCT07284069), recruiting). **Elexacaftor (VX-445)**, an approved CF drug, directly blocks KCa3.1 ([PMID 40688096](https://pubmed.ncbi.nlm.nih.gov/40688096/)) | **High.** KCa3.1 is widely expressed in immune cells and epithelium — the exact reason CF trials dose it systemically | **Highest priority.** Named a novel NSCLC therapeutic target in [PMID 41741906](https://pubmed.ncbi.nlm.nih.gov/41741906/). A **senicapoc-BODIPY fluorescent probe for tumour cells** already exists ([PMID 40969888](https://pubmed.ncbi.nlm.nih.gov/40969888/)) — an imaging read-out for the same channel, which is a gift |
| **Piezo1** | The mechanical→Ca²⁺→YAP/TEAD entry point | **Levistilide A** blocks Piezo1-centred signalling ([PMID 42843051](https://pubmed.ncbi.nlm.nih.gov/42843051/)); GSK2798745 is a clinical-stage Piezo1 inhibitor | **High and ambiguous.** Piezo1 acts as a **tumour suppressor** in one lung context ([PMID 38494915](https://pubmed.ncbi.nlm.nih.gov/38494915/)) — direction is not established | **Second priority, and the most original.** Only 13 PubMed records combine a Piezo1 inhibitor with cancer at all, and almost none are oncology |
| **Cav2.3 / CACNA1E** | VGCC α1E; the single record in the target intersection | SNX-482, peptide blocker | Medium-high | **Third.** Conceptually central, least developed |

**Post-D0 verdicts (2026-11-06).** The ranking above was written before the
window audit was run. The audit's verdicts supersede it, and the authoritative
table is [`D0-TARGET-WINDOW-AUDIT.md`](D0-TARGET-WINDOW-AUDIT.md) §4:

- **KCa3.1 / KCNN4 — closed for the lung indication.** No systemic window:
  lung expression is 12× below minor salivary gland, the gene is
  loss-of-function intolerant (LOEUF 0.515), and on-target neurological and
  cardiac liabilities are recorded. The state-resolved measurement closed it
  further: the relapse-competent state in lung does **not** express KCNN4
  more than the surrounding tumour (detection ratios 0.92, 0.00 and 0.37
  across the lung libraries of GSE299684). A delivery argument is moot when
  the target is not there. KCa3.1 survives as an imaging probe
  (senicapoc-BODIPY) or in non-lung indications.
- **Piezo1 — still the most original, and now the strongest readout
  candidate.** The state expresses PIEZO1 in 39% of cells against 6% of
  neighbouring tumour cells, at every site tested including lung, robust to
  leaving out any library and to how the state is called. As a *drug* it is
  unchanged: no separation from PIEZO2 in bulk tissue (window fold 1.043;
  PIEZO2's germline burden is centred on distal arthrogryposis), no
  clinical-stage asset in Open Targets, and its direction of effect is not
  established.
- **Cav2.3 / CACNA1E — ruled out as a lung target.** 0.126 TPM in lung,
  LOEUF 0.120, and ClinVar asserts developmental and epileptic
  encephalopathy 69.
- **Kv1.3 / KCNA3** moves to the state-modulating immune arm rather than the
  tumour-selective drug table.

### Tier 2 — the immune arm and the readout

| Target | Role | Note |
|---|---|---|
| **Piezo1 on T cells** | Piezo1 mechanically regulates antitumour T-cell cytotoxicity ([PMID 38514773](https://pubmed.ncbi.nlm.nih.gov/38514773/)) | Doubles as an immunotherapy angle and as a **window argument**: blocking tumour-cell Piezo1 and T-cell Piezo1 are opposite therapeutic directions. Any Piezo1 drug must be tumour-directed |
| **Kv1.3 / KCNA3** | Effector-memory T-cell and tumour signalling | 67 records with lung. Antibody, not small molecule, is the leading modality |
| **Sodium-channel blockade** | Precedent exists: **Phase 3 lignocaine blockade of voltage-gated sodium channels in operable breast cancer** ([NCT01916317](https://clinicaltrials.gov/study/NCT01916317), active not recruiting) | A **clinical proof that ion-channel blockade can be an adjuvant in a resected solid tumour** — the exact setting this programme needs |

### Tier 3 — the electrical therapy precedent

| Asset | Status |
|---|---|
| **TTFields in NSCLC** | **LUNAR-2**, Phase 3, TTFields + pembrolizumab + platinum chemo, metastatic NSCLC, n = 734, **recruiting** ([NCT06216301](https://clinicaltrials.gov/study/NCT06216301)). Its predecessor EF-36 terminated for *insufficient enrolment*, not safety ([NCT04892472](https://clinicaltrials.gov/study/NCT04892472)) |
| PEF ablation | PEF for lung tumours **recruiting** ([NCT06739031](https://clinicaltrials.gov/study/NCT06739031)); Aliya PEF + chemo in resectable NSCLC terminated, reason "Strategic", n = 5 ([NCT05583188](https://clinicaltrials.gov/study/NCT05583188)) |

**Read across:** a bioelectric *device* in lung cancer is being tested at
Phase 3 with no companion biomarker. **That is the opening this programme
fills** — not another device trial, but the biomarker that would let such a
trial succeed, and the state that would tell you who to treat.

---

## 3. Experiment ladder

Each stage has an entry gate, an exit criterion, and a kill condition. Stages
are ordered by cost, and **no stage may begin before the previous one exits**.

### Stage D0 — target window audit *(weeks; computational; no samples)* — **executed**

> **Status: executed 2026-11-06.** Full report: [`D0-TARGET-WINDOW-AUDIT.md`](D0-TARGET-WINDOW-AUDIT.md).
> Artefact: `results/d0_window_audit/d0_window_audit.json`. Two targets were
> ruled out, the systemic-window hypothesis was dropped for KCa3.1, and the K4
> kill condition was re-specified as **D0b** and deferred to state-resolved
> data — see the report §6 for why bulk tissue cannot decide it.
>
> **D0b was then executed on public data, 2026-11-07:** see
> [`GSE299684-STATE-EXPRESSION.md`](GSE299684-STATE-EXPRESSION.md). The
> relapse-competent state *is* electrically marked — PIEZO1 in 39% of state
> cells against 6% of neighbouring tumour cells, robust to leaving out any
> library and to how the state is called — but KCNN4 does not mark the state in
> lung, which closes the KCa3.1 arm for the lung indication.

**Question.** Which targets have a therapeutic window in lung tissue?
**Method.** For each Tier-1/2 target: pull GTEx lung and immune expression
for the channel gene and its known regulators; compute the specificity verdict
with the existing `protein-flow-explorer` machinery; pull ClinVar and
AlphaGenome Atlas regulatory-variant scores for the same loci with
`mrnavax variant-regulatory`.
**Exit.** Every candidate target has a written window verdict: *selective*,
*conditionally selective* (e.g. only in the inflamed niche), or *not viable*.
**Kill (K4).** No target is conditionally selective → the pharmacological arm
is dropped and the programme becomes purely a biomarker programme. **This is
the cheapest possible place to learn that.**

### Stage D2 — does the state exist in lung, and is it relapse-linked? *(months; tissue)*

**Question.** Is there a relapse-associated, electrically-marked state in lung
tumour tissue, and does the Piezo1→YAP/TEAD link hold in tumour cells?
**Design.**
- Paired **primary and relapsed/resistant** lung tumour tissue (archived
  material; target n = 30 pairs, powered to detect a methylation delta at
  |Δβ| ≈ 0.15 with 80% power).
- Four arms per sample: bulk tumour; sorted state-bearing fraction
  (YAP1-low/TEAD-luciferase or CD44-high gate); sorted non-state fraction;
  matched adjacent normal.
- Readouts: methylation array (deepcatch's existing pipeline); RNA-seq;
  ion-channel panel expression; Piezo1 activity (Ca²⁺ imaging or
  Yoda1/GSK2833505A agonist challenge); YAP/TEAD reporter.
- **Primary endpoint: the burden-normalised enrichment ratio** — the same
  quantity D1 specified. Raw ion-channel abundance is explicitly *not* the
  primary endpoint, because it tracks burden and would re-confirm the growth
  signal.
- **Electrical endpoint (added by the D0 audit).** Channel expression *per cell
  type* within the same tumour — state-bearing fraction vs non-state fraction
  vs tumour-infiltrating immune cells — and the **state-to-immune ratio** for
  each candidate channel. This is the measurement that decides whether the
  drug arm survives, because D0 could not decide conditional selectivity on
  bulk normal tissue: the state-to-immune ratio is what "conditionally
  selective" means when the condition is a state.
  See [`D0-TARGET-WINDOW-AUDIT.md`](D0-TARGET-WINDOW-AUDIT.md) §6–§7.
**Exit.** (i) A reproducible methylation delta at ion-channel loci between
state-bearing and non-state fractions in the *same* tumour (this is the
burden-free comparison D2 is built for); (ii) that delta is larger in
relapsed than in primary tumours.
**Kill (K1, K2).** No delta, or no relapse association → the electrical state
is not a lung relapse mechanism. **Publish the negative result.**

### Stage D3 — is it readable from plasma? *(months; serial plasma)*

**Question.** Can the state be inferred from serial plasma cfDNA and does it
add information beyond mutation trajectory?
**Design.**
- Serial plasma (pre-op, on-adjuvant, every 3 months to 36 months) from the
  same patients; ctDNA mutation channel as the comparator.
- Assay: methylation → expression deconvolution → ion-channel signature →
  enrichment ratio, at 200,000× / 200 loci with 50 mutation loci
  (D1's affordable operating point).
- **Primary endpoint: ΔAUC over the mutation channel alone, within the
  MRD-positive stratum**, plus the **within-MRD+ PPV** — the quantity D1
  showed is the actual clinical failure mode. At 200,000× depth on a 200-locus
  panel, MRD specificity against MRD-positive non-relapsers is **0.662**, and
  those persistent non-relapsers are **26% of all MRD-positive patients**.
**Exit.** ΔAUC ≥ 0.10 and a calibrated refinement rule that lifts within-MRD+
PPV by ≥ 0.10 at ≥ 90% retained sensitivity.
**Kill (K3).** Otherwise the biomarker arm stops here.

### Stage D4 — does the state predict relapse, prospectively? *(years; prospective cohort)*

**Question.** Does the state predict relapse better than MRD alone?
**Design.** Prospective, blinded, pre-registered. Primary: time to relapse
discrimination vs MRD-alone. Secondary: the 104-day lead-time bar (the
published tumour-informed MRD benchmark).
**Exit.** Hazard ratio for relapse, MRD+ / state− vs MRD+ / state+, with the
state term significant after adjustment for MRD burden.

### Stage D5 — is the state pharmacologically reversible? *(months; patient-derived models)*

**Question.** Does blocking the channel remove the state and its competence?
**Design.** Patient-derived organoids / ex vivo PDX from relapsed tissue,
with confirmed state-bearing fractions. Arms: KCa3.1 block (senicapoc or
elexacaftor), Piezo1 block (GSK2798745 or Levistilide A), YAP/TEAD block,
combination with the standard-of-care agent.
**Primary endpoint.** Differential killing of the **state-bearing** fraction
relative to the non-state fraction, at matched bulk viability.
**Kill (K5).** No differential killing → the target is a marker, not a
mechanism, and the therapeutic arm converts to a biomarker-only programme.

---

## 4. Clinical path

### 4.1 Biomarker validation ladder

| Level | Requirement | Status |
|---|---|---|
| **Analytical validity** | LoD, reproducibility, cross-study harmonisation for the enrichment ratio | Not started; D3 |
| **Clinical validity** | State predicts relapse independent of MRD burden | Not started; D4 |
| **Clinical utility** | Acting on the state changes outcomes | Not started; D5 → trial |

### 4.2 The trial this should feed

**Design sketch — MRD- and state-guided adjuvant escalation, resected NSCLC.**

- **Population:** stage II–IIIA NSCLC, post-resection, on adjuvant osimertinib
  (or the applicable standard). Two biomarker strata:
  - **MRD− / state−** → standard adjuvant therapy
  - **MRD+ / state+** → intensified therapy + the channel-directed agent
    (e.g. KCa3.1 or Piezo1 inhibitor) as an add-on
- **Primary endpoint:** relapse-free survival in the MRD+ stratum.
- **Critical design requirement, from D1:** the state readout must be
  **burden-normalised**. An unnormalised marker will stratify by tumour
  burden and will look like it works while doing nothing.
- **Honest sizing note:** the enrichment rate in MRD+ is the unknown that
  sizes the trial. D1 estimates it at 26% under its assumptions; the trial
  must be sized on the D2/D3 measured rate, not the modelled one.

### 4.3 Why this is complementary to, not competitive with, LUNAR-2

LUNAR-2 tests whether adding an electrical *field* helps. This programme
tests whether adding a *channel-directed drug* helps **and** provides the
biomarker that would let either trial be enriched for likely responders.
A biomarker programme is the cheaper, faster, and more reusable half of the
question, and it is the half nobody is running.

---

## 5. Timeline and critical path

| Phase | Duration | Depends on |
|---|---|---|
| D0 window audit | 2–3 weeks | nothing — start now | **done 2026-11-06**; the gate it was meant to fire was re-specified as D0b and deferred to state-resolved data |
| D2 tissue | 4–6 months | archived tissue access; D0 exit |
| D3 plasma | 6–9 months | serial plasma cohort; **data applications** |
| D4 prospective | 3–5 years | D3 exit; trial funding |
| D5 preclinical | 4–6 months | D2 tissue |

**The critical path is data access, not computation.** PLCO (CDAS) and
Taizhou (EGA DAC) applications have month-scale lead times and gate D3 and
D4. **They should be submitted in parallel with D0, not after it.**

---

## 6. Risk register

| Risk | Likelihood | Impact | Mitigation | Pivot |
|---|---|---|---|---|
| The state is not present in NSCLC (only SCLC) | Medium | High | Run D2 with NSCLC and SCLC arms separately | Restrict to SCLC, where the YAP1 population is already anchored |
| The state is real but not plasma-readable | Medium | High | D3 with a lower detection threshold; accept a longer lead time | Use tissue-anchored selection to enrich the plasma cohort |
| Piezo1 direction is context-dependent | **High** (it is a tumour suppressor in one lung context) | High | D0 + D5 test both directions before any trial | Abandon Piezo1 as a drug target; keep it as a mechanism readout |
| KCa3.1 window too narrow | **High** — D0 measured it: lung expression is 12× below minor salivary gland | High | Conditional selectivity (inflamed niche) may rescue it; senicapoc-BODIPY gives a way to test selectivity; D0 concluded that a *systemic* blocker is not supportable and the modality must be tumour-directed or local | Drop the drug arm; keep the biomarker |
| MRD+ stratum too small for a trial | Medium | High | Use a biomarker-stratified platform trial | Enrich at D2, then re-stratify |
| Modelling assumptions fail (the state fractions were assumed, not fitted) | **Certain to be partly wrong** | Medium | D1's numbers are explicitly conditional | Recompute with D2-measured effect sizes |
| The error floor varies across loci, not only in level | **Unknown, and consequential** — the fidelity audit shows a threshold calibrated on a flat floor collapses to 1.8% specificity under a per-locus-varying floor | **High** | Measure the per-locus background spread of the actual panel; prefer a per-locus-aware statistic (support at *k* independent loci) over an aggregate count | Re-derive the threshold on the measured floor; if the panel cannot support per-locus counts, the mutation channel has to be re-specified |

---

## 7. What this plan uses from the existing tooling

| Asset | Use in this plan |
|---|---|
| `relapse-competence` (`relapse-competence`) | D1 read-budget decisions; MRD design; the enrichment-ratio definition |
| `deepcatch` methylation channel (`src/methylation/`) | D2 and D3 methylation feature extraction; GSE185307 / GSE122126 for method development only |
| `mrnavax variant-regulatory` (AlphaGenome Atlas AVI) | D0: regulatory-variant scores at ion-channel loci |
| `mrnavax neoantigen` (mhcflurry + ESM2) | D5: whether the state creates a neoantigen handle |
| `mrnavax scrna` (scGPT) | D2: state-bearing cluster identification |
| `protein-flow-explorer` | D0: GTEx specificity verdict; pocket detection; the flow-matching design package for a channel-directed binder |
| `py-idp` | D0/D2: literature and document extraction at scale |
| `scrapex` | D0: dataset and registry harvesting |

---

## 8. The three sentences to remember

1. **Target the state that relapses, not the marker that was fashionable in
   2009.** The lung relapse-emergent population is YAP1-positive and plastic
   ([PMID 42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/)); CD133 was
   never the operative thing.
2. **Normalise away burden, or you will measure regrowth and call it a
   mechanism.** D1 showed the raw marker discriminates better than the
   state-specific one *precisely because* it is a growth proxy.
3. **The cheapest possible kill is D0.** Before any sample, check whether the
   channels have a therapeutic window, and before any patient, check whether
   the state is drug-tolerant persister biology or merely a marker of it.

---

## Appendix — records cited in this plan

| PMID | Year | Journal | Role here |
|---|---|---|---|
| [42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/) | 2026 | J Thorac Oncol | The anchor: YAP1+ plastic population at SCLC relapse |
| [41279637](https://pubmed.ncbi.nlm.nih.gov/41279637/) | 2025 | bioRxiv (preprint) | Preprint of the above |
| [42727476](https://pubmed.ncbi.nlm.nih.gov/42727476/) | 2026 | BBRC | Piezo1 → YAP/TEAD in lung fibroblasts |
| [42630570](https://pubmed.ncbi.nlm.nih.gov/42630570/) | 2026 | Front Pharmacol | Piezo1 axis in fibrosis-associated lung cancer |
| [42978946](https://pubmed.ncbi.nlm.nih.gov/42978946/) | 2026 | Front Cell Dev Biol | Mechanochemical coupling in lung cancer |
| [42836163](https://pubmed.ncbi.nlm.nih.gov/42836163/) | 2026 | Drug Des Devel Ther | Dual role of Piezo1 in cancer |
| [41741906](https://pubmed.ncbi.nlm.nih.gov/41741906/) | 2026 | Discov Oncol | KCNN4 as a novel NSCLC therapeutic target |
| [40969888](https://pubmed.ncbi.nlm.nih.gov/40969888/) | 2025 | ACS Pharmacol Transl Sci | Senicapoc-BODIPY probe for KCa3.1 in tumour cells |
| [40688096](https://pubmed.ncbi.nlm.nih.gov/40688096/) | 2025 | PNAS Nexus | Elexacaftor blocks KCa3.1 in bronchial epithelium |
| [42279523](https://pubmed.ncbi.nlm.nih.gov/42279523/) | 2026 | Diagnostics | Senicapoc Phase II protocol in IPF |
| [42341914](https://pubmed.ncbi.nlm.nih.gov/42341914/) | 2026 | Transl Res | Kv1.3 → STAT3 → M2 macrophage polarisation |
| [38514773](https://pubmed.ncbi.nlm.nih.gov/38514773/) | 2024 | Nat Biomed Eng | Piezo1 regulates antitumour T-cell cytotoxicity |
| [40567012](https://pubmed.ncbi.nlm.nih.gov/40567012/) | 2025 | Adv Healthc Mater | Piezo1 mechanotransduction impedes metastasis via CXCR4 clustering |
| [39556518](https://pubmed.ncbi.nlm.nih.gov/39556518/) | 2024 | ACS Biomater Sci Eng | Piezo1 mediates PDAC chemoresistance in stiff matrix |
| [42843051](https://pubmed.ncbi.nlm.nih.gov/42843051/) | 2026 | Phytomedicine | Levistilide A blocks Piezo1-centred signalling |
| [38494915](https://pubmed.ncbi.nlm.nih.gov/38494915/) | 2024 | Thorac Cancer | Piezo1 as tumour suppressor — the contraindication |
| [31685811](https://pubmed.ncbi.nlm.nih.gov/31685811/) | 2019 | Cell Death Dis | Piezo1 activation sensitises to TRAIL apoptosis |
| [30015269](https://pubmed.ncbi.nlm.nih.gov/30015269/) | 2018 | Bioelectrochemistry | Electrotaxis of lung adenocarcinoma tumour-initiating cells |
| [42327581](https://pubmed.ncbi.nlm.nih.gov/42327581/) | 2026 | J Cancer | The single target-intersection record (CACNA1E review) |
| [39191501](https://pubmed.ncbi.nlm.nih.gov/39191501/) | 2024 | Cancer Genomics Proteomics | Ion-channel gene methylation at GBM recurrence |
| [36038893](https://pubmed.ncbi.nlm.nih.gov/36038893/) | 2022 | J Transl Med | MMP depolarisation → DNA methylation → chemoresistance (ESCC) |
| [32777557](https://pubmed.ncbi.nlm.nih.gov/32777557/) | 2020 | J Surg Res | CDO1 methylation ↔ mitochondrial membrane potential (gastric) |
| [29723302](https://pubmed.ncbi.nlm.nih.gov/29723302/) | 2018 | PLoS One | SCN4B voltage-gated channel + methylation + recurrence (thyroid) |
| [42722615](https://pubmed.ncbi.nlm.nih.gov/42722615/) | 2026 | Brain Pathol | PTEN predicts TTFields benefit, and not in untreated controls |
| [41279637](https://pubmed.ncbi.nlm.nih.gov/41279637/) | 2025 | bioRxiv | Preprint of the YAP1 paper |

**Registered interventions:** NCT06216301 (LUNAR-2, Phase 3, recruiting) ·
NCT04892472 (EF-36, terminated, low accrual) · NCT05583188 (Aliya PEF, terminated,
strategic) · NCT06739031 (PEF lung, recruiting) · NCT07284069 (senicapoc +
perampanel, GBM, Phase 1, recruiting) · NCT01916317 (lignocaine sodium-channel
blockade, breast, Phase 3) · NCT01624090 (mithramycin, CSC signalling, Phase 2,
terminated)

**Literature census behind this plan:** Piezo1 × lung = 95 records ·
Piezo1 inhibitor × cancer = 13 records · KCa3.1/KCNN4/Kv1.3/senicapoc × lung
= 67 records · electrical × DNA × relapse × lung = **1** record (PubMed), 0
(Europe PMC).
