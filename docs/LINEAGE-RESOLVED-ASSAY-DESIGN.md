# Lineage-resolved assay design

**Status:** design document, written by the programme's authors and not
externally reviewed; no measurement is reported here.
**Question:** how to resolve the *lineage* of the relapse-competent state —
which of three explanations of post-treatment relapse the state supports.
**Artefacts:** [`../results/channel_allocation.json`](../results/channel_allocation.json),
[`../results/channel_allocation_200k.json`](../results/channel_allocation_200k.json),
[`../results/mrd_sweep.json`](../results/mrd_sweep.json).

---

## 1. The question

After treatment a patient has residual disease; some relapse; what the state
*is* remains open. The table is the roadmap's:

| Hypothesis | If true | What would change |
|---|---|---|
| **Stemness** — a persistent CSC-like subpopulation | CSC-targeted therapy becomes rational | Therapy would need to hit the stem-like fraction, not the bulk |
| **Persistence** — a drug-tolerant state that is not stem-like | Bulk-directed combination therapy suffices | No need to define "stemness" at all |
| **Genomic** — a resistant clone with a fixed driver mutation | Genotype-directed therapy suffices | Biomarker work should be on the clone, not the phenotype |

**The discriminating measurement** ([`ROADMAP.md`](ROADMAP.md)), in one
sentence: *"Lineage resolution is the discriminating measurement. That is the
single highest-value addition to this package."* The explanations differ in
**time ordering and clonal continuity**, not in any cross-sectional
measurement.

The field has not closed this: the roadmap quotes a 2026 review of EGFR-mutant
NSCLC stating that what is missing is *"direct evidence that a prospectively
identified persister lineage later acquires serially propagating CSC
function"*. **Cell-free DNA cannot measure membrane potential**, so the
electrical phenotype is inferred, never measured
([`GAP-AUDIT-BIOELECTRIC.md`](GAP-AUDIT-BIOELECTRIC.md) §A). What follows is a
**lineage-tracing measurement**: the state resolved per cell inside a clonal
lineage.

---

## 2. What the package already constrains

### 2.1 Depth and panel size are a requirement, not a preference

The read budget, not the depth label, sets the operating point. From
[`../results/mrd_sweep.json`](../results/mrd_sweep.json), read threshold
selected on a held-out calibration split:

| Depth × loci | Reads/draw | Sensitivity | Specificity | Median lead |
|---|---:|---:|---:|---:|
| 50,000× / 50 loci | 2,500,000 | 0.521 | 0.985 | 39 d |
| 50,000× / 200 loci | 10,000,000 | 0.828 | 0.990 | 72 d |
| 200,000× / 50 loci | 10,000,000 | 0.828 | 0.990 | 72 d |
| 200,000× / 200 loci | 40,000,000 | 0.948 | 0.983 | 107 d |

Rows 2 and 3 are identical — depth alone does not rescue a too-small panel.
The 104-day bar is met only at 200,000× / 200 loci, **sixteen times** the
conventional read budget ([`../README.md`](../README.md)). D1's rule binds
this design: the electrical channel is affordable **only at ≥200 loci with
≥200,000× depth, and ≤25% allocation**
([`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md) §E).

### 2.2 The endpoint is the burden-normalised enrichment ratio, never raw abundance

The state-specific score is the **pooled per-locus VAF ratio, electrical ÷
mutation**, pooled across post-baseline draws
(`src/relapse_competence/detectors.py`).

| Score | AUC within MRD+ | What it is |
|---|---:|---|
| `electrical_raw` | 0.993 – 1.000 | burden proxy — "the tumour is regrowing" |
| `electrical_enrichment` | 0.845 – 0.945 | state-specific — the hypothesis under test |

The *worse* discriminator is the one that tests the hypothesis
([`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md) §C.3). Kill condition
K1 is written against the normalised number — enrichment AUC ≤ 0.6 ends the
state-specific readout ([`RESEARCH-PLAN.md`](RESEARCH-PLAN.md) §0).

### 2.3 MRD specificity is two numbers, not one

The same panel has two specificities, and the literature's headline figure
measures the easy one. At 0% electrical allocation:

| Configuration | Spec. vs responders | Spec. vs MRD+ non-relapsers | Persistent share of MRD+ | PPV within MRD+ |
|---|---:|---:|---:|---:|
| 50,000× / 50 loci | 0.985 | 0.881 | 18.8% | 0.805 |
| 50,000× / 200 loci | 0.990 | 0.726 | 24.8% | 0.734 |
| 200,000× / 200 loci | 0.983 | 0.662 | 26.3% | 0.708 |

Rows 1 and 3 are from the allocation artefacts; the model card quotes 0.726
and 26% ([`../MODEL_CARD.md`](../MODEL_CARD.md)). **The stratum the channel
operates in is a quarter of the MRD-positive population, defined by people who
did not relapse** — so a lineage endpoint must be scored inside that stratum,
against the mutation channel alone.

### 2.4 The electrical channel refines; it does not detect

The realistic use is *refinement* of the MRD-positive population, not
detection: the mutation channel detects, the electrical channel would stratify
MRD-positive patients into "will relapse" and "will not"
([`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md) §E). A 100% electrical
allocation is degenerate — no mutation loci, no MRD assay to refine. State
fractions are assumed, not fitted (0.25 ± 0.12 relapsers, 0.10 ± 0.12
persistent patients): every AUC above is conditional.

---

## 3. The lineage measurement

### 3.1 What is observed

One observation, repeated on the same patient: **the state-bearing fraction
of a clonal lineage, tracked across time.** Per draw — the lineage composition
of the plasma pool, the mutation channel supplying the tag; the state marker
within each lineage (the fraction of cells carrying it *inside that lineage*,
not inside the sample); and the ordering: baseline, post-treatment draws,
relapse specimen. The claim to support is the roadmap's: a *prospectively
identified persister lineage* that *later acquires serially propagating CSC
function*.

### 3.2 The resolution it requires

**Cell-level**, because the state is a fraction of cells and bulk tissue
averages it away. **Clonal**, because only a mutation tag assigns an
observation to a lineage. **Temporal and within patient**, because the
explanations differ in time ordering. **Longitudinal plasma**, because the
mutation channel alone reports persistence, not mechanism.

### 3.3 Controls

- **Clonal-fraction normalisation.** *f_state(L) = cells in lineage L carrying
  the state marker ÷ cells in lineage L*, with the lineage's own share of the
  sample normalised out — otherwise a growing lineage produces a state signal
  that is really a clone-size signal.
- **Time ordering.** Post-treatment draws are ordered before relapse: a marker
  present at relapse but absent at the MRD draw is acquisition, present at both
  it is inheritance. The pre-treatment baseline is the patient's own background
  and is never evaluated as a detection.
- **Held-out features, patient-level splits, site control.** The state
  definition and the classifier testing it must not be the same data; splits
  are by patient, not by cell; and where more than one site is sampled, site
  is recorded, because a site effect can masquerade as a lineage effect.

### 3.4 What each explanation predicts

| Observation | Stemness | Persistence | Genomic |
|---|---|---|---|
| MRD-positive lineage at the post-treatment draw | is the lineage that seeds relapse | is not the lineage that seeds relapse | is irrelevant to the seeding clone |
| State marker inside the lineage, MRD → relapse | present, stably inherited, in the expanding sub-lineage | present post-treatment, then uncoupled or lost | tracks clone size, not a sub-lineage |
| Within-lineage state fraction over time | conserved within the lineage | transient; resolves | no lineage structure to conserve |
| Relapse attributable to | the state-bearing lineage | a different, non-state lineage | a fixed-driver clone |

---

## 4. Assay design

### 4.1 Channel composition

Three channels, one job each: the mutation channel is the lineage tag *and*
burden reference; methylation is the expression proxy standing in for a
measurement cfDNA cannot make; the electrical channel is the state marker.

| Channel | What it carries | Where resolved | Budget at the operating point | Quantified here? |
|---|---|---|---|---|
| Mutation | lineage tag, burden, clonal frequency | per ctDNA molecule | 150 of 200 loci; 40,000,000 reads/draw | Yes — 0.956 → 0.926 sensitivity at 200,000× / 200 loci |
| Methylation | expression profile → deconvolution → ion-channel signature | bulk plasma | **not quantified** — the simulator has no methylation channel | No |
| Electrical (bulk) | the state marker as a burden-normalised ratio | bulk plasma, per locus | 50 of 200 loci | Yes — enrichment AUC 0.845–0.945 within MRD+ |
| Cell-level state | state marker per cell, inside a lineage | single cell | the public single-cell libraries | No — state fractions are assumed |

The budget follows D1 exactly: 200,000× depth, 200 loci split 150 mutation / 50
electrical. The cost is stated, not absorbed: 25% electrical costs 3.0 pp of
MRD sensitivity here (0.956 → 0.926) and 12.2 pp at 50,000× / 50 loci
(0.556 → 0.434).

**One constraint the budget does not cover.** The mutation channel is the
lineage tag, and the tag is currently a threshold on the *aggregate* mutant
read count across the panel. The fidelity audit shows that this statistic is
conditional on the shape of the error floor, not only its level: a threshold
calibrated on a flat per-locus floor collapses to 1.8% specificity when the
floor varies across loci ([`MODEL-FIDELITY.md`](MODEL-FIDELITY.md) §5). A
lineage tag that fragile cannot carry the lineage measurement, so the panel
must either measure its own per-locus floor or use a statistic that counts
support at *k* independent loci rather than *k* reads in total. This is a
property of the assay, not of the biology, and it is cheap to settle.

**Operating point.** 200,000× / 200 loci — lower fails the affordability rule
and the K3 gate (enrichment AUC ≤ 0.65 at 200,000× / 200 loci ends the plasma
arm). 25% electrical — 50% costs a further 5.8 pp of MRD sensitivity for
0.006 of extra enrichment AUC, so 25% is at the knee. Endpoint: the
burden-normalised enrichment ratio of §2.2, pooled across post-baseline draws
and — new here — computed **within lineage** wherever a lineage tag exists.

### 4.2 Sampling schedule

Serial plasma: pre-operative, on-adjuvant, then every 3 months to 36 months
([`RESEARCH-PLAN.md`](RESEARCH-PLAN.md) §3, stage D3). Follow-up must run
24–36 months per patient to catch the 104-day median lead time plus its tail
([`DATASETS.md`](DATASETS.md)). A relapse specimen is required: without it
there is no lineage endpoint.

### 4.3 Endpoint hierarchy

| Tier | Endpoint, and the denominator it is scored against |
|---|---|
| **Primary** | Burden-normalised enrichment ratio of the state marker **within the MRD-positive stratum** — about a quarter of whom did not relapse |
| Secondary | ΔAUC over the mutation channel alone, within the same stratum, against a mutation-only comparator |
| Secondary | Within-MRD+ PPV of the refined call, at ≥90% retained sensitivity, over MRD-positive patients |
| Secondary | Clonal continuity between the MRD-positive draw and the relapse specimen, in relapse patients with an informative lineage |
| Exploratory | Within-lineage state-acquisition rate between ordered draws, in patients with ≥2 informative draws |

The D3 exit criteria are reused unchanged: ΔAUC ≥ 0.10 and a calibrated
refinement rule lifting within-MRD+ PPV by ≥ 0.10 at ≥ 90% retained
sensitivity.

---

## 5. Decision rules

The gates are fixed before any lineage data is seen, and each is falsifiable on
its own.

| Gate | Supports | Falsified by |
|---|---|---|
| **Continuity** — is the MRD lineage the one that seeds relapse? | Continuity **plus** a stably inherited state-bearing sub-lineage → **stemness** | The relapse clone is not the MRD lineage → the state did not seed relapse |
| **Acquisition** — is the state acquired, lost or uncoupled by relapse? | State present at MRD, uncoupled from the seeding clone → **persistence** | State inherited and expanded within the seeding lineage → contradicts **persistence** |
| **Genomic attribution** — is relapse explained by a fixed-driver clone? | Relapse attributable to a fixed-driver clone with no state-bearing sub-lineage → **genomic** | Relapse not attributable to any fixed driver → contradicts **genomic** |
| **Burden-independence (K1)** — does the readout add to burden? | Burden-normalised enrichment AUC > 0.6 | AUC ≤ 0.6 → the channel is a burden proxy and the mechanistic claim dies |
| **Plasma readability (K3)** — is it readable at an affordable budget? | Enrichment AUC > 0.65 at 200,000× / 200 loci | AUC ≤ 0.65 → the biomarker arm stops here |
| **D0b (deferred K4)** — do the state cells express the channels above surrounding lung? | State-bearing cells express the channels above non-state malignant cells and tumour-infiltrating immune cells | No such excess → the drug arm is dropped; the programme becomes a biomarker programme |
| **Lineage stability (pivot)** — is the state stable within a lineage? | State-bearing sub-lineage stable across draws | Not lineage-stable → drop the stemness framing and publish the state-detection work without it |

**Why the drug arm cannot be decided on bulk tissue.** The D0 audit's verdict
is that K4 "does not fire as written": "conditionally selective" is a statement
about a state, and bulk GTEx tissue is state-free by construction, so a screen
that cannot separate "conditionally selective" from "no window" has failed to
be a decision, not to fail the target. K4 was re-labelled **D0b** and deferred
to state-resolved expression
([`D0-TARGET-WINDOW-AUDIT.md`](D0-TARGET-WINDOW-AUDIT.md) §6).

**The honest negative** is not "we found no effect". It is one of two: the
state is there but it is a burden proxy (K1 fires — the programme publishes
the state-detection work and drops the mechanistic claim); or the state is
there but it does not seed relapse (a *persistence* result, retiring the
stemness framing the roadmap names as a pivot rather than a failure).

---

## 6. What is already public and can be run now

**GSE299684** is the GEO deposit of PMID 42019833 (Stewart et al., *YAP1
Defines an Emergent, Plastic Population of Relapsed SCLC*, J Thorac Oncol 2026).
It holds **15 relapsed-SCLC single-cell libraries** from seven metastatic
sites, as standard 10x `barcodes/features/matrix` triplets (~700 MB), public
since 2026-05-15
([`D0-TARGET-WINDOW-AUDIT.md`](D0-TARGET-WINDOW-AUDIT.md) §9,
[`ROADMAP.md`](ROADMAP.md)). **The first state-resolved measurement does not
wait for a data-access application** — the roadmap's dependency table puts it
first: "Days — public, no application. **First. Start now.**"

**What it can answer.** D0b directly: identify the state-bearing population in
relapsed SCLC single cells and read out channel expression per cell — the
targets the D0 audit tabled (KCNN4, PIEZO1, CACNA1E, KCNA3, TMEM150C, PIEZO2)
— comparing state-bearing cells against surrounding malignant cells and
tumour-infiltrating immune cells, giving the state-to-immune ratio that
decides whether the drug arm survives. It also gives a burden-free
within-tumour contrast of the kind D2 is built for.

**What it cannot answer.**

- **No lineage** — no post-treatment MRD time point in the same patient, so no
  clonal continuity and no time ordering; every library is relapsed tissue.
- **No plasma** — no ctDNA and no mutation-defined lineage, hence no
  clonal-fraction normalisation against a lineage tag.
- **No treatment timeline** — "drug-tolerant" cannot be established.
- **Not the target population** — relapsed SCLC tissue, whereas the plan's
  objective is resected NSCLC on adjuvant therapy: a Medium-likelihood,
  High-impact risk.

---

## 7. What still requires an application

The lineage endpoint needs serial plasma, a known outcome, and follow-up long
enough to capture the lead time. Two cohorts qualify, and they are not
interchangeable.

| Source | Access | Scale | What it uniquely provides |
|---|---|---|---|
| **PLCO** (Prostate, Lung, Colorectal, Ovarian Screening Trial) | CDAS application | n = 154,900 | Serial plasma at screening-cohort scale, pre-diagnosis plasma available |
| **Taizhou Longitudinal Study** (PanSeer) | EGA Data Access Committee | n = 123,115 enrolled, 575 cancers | The only published dataset that directly validates a longitudinal pre-diagnosis paradigm, with a methylation readout over 595 regions — the channel the simulator does not model |

Taizhou's 2–3 year sampling interval is far coarser than the 3-month D3
schedule, so it cannot resolve the 104-day lead-time bar. Both are
application-gated with month-scale lead times, and the roadmap's conclusion is
that they **should be submitted in parallel with the modelling work, not after
it**. The open datasets do not substitute — `DATASETS.md` states the gap in
one line: none is a serial post-treatment NSCLC MRD cohort.

---

## 8. Falsification and risks

1. **State-resolved versus bulk expression is a different estimand.** Median
   TPM hides the cell-type mixture: a lung median of 9.5 TPM for KCNN4
   averages alveolar, bronchial, endothelial, immune and stromal cells. A bulk
   null does not predict a cell-level null; a large per-cell difference in a
   minority population can be invisible in bulk yet dominate the lineage
   analysis. That minority's size is assumed (§2.4).
2. **The state fraction is assumed uniform; real tumours are mosaics.** Each
   simulated patient carries one continuous state fraction, while real disease
   mixes subclones and sites. If state composition varies within a patient,
   the bulk electrical channel averages over exactly the heterogeneity that
   carries the biology. The model has no noise on the state itself, so no
   simulated AUC includes that dilution.
3. **Lineage versus clonal-frequency confounding.** A mutation channel yields
   both a lineage tag and a clonal frequency, so a state signal that rises with
   its own lineage's clonal frequency is indistinguishable from one that is a
   function of clone size: burden normalisation removes total burden, not
   clonal structure. The control is to compute the state fraction within
   lineage and test whether it changes while the clonal frequency is stable.
   The simulator cannot exercise that control: multi-clone resistance is now
   modelled ([`MODEL-FIDELITY.md`](MODEL-FIDELITY.md)), but a clone is not a
   lineage — it carries no tag that survives therapy, which is what the
   control needs.
4. **Fitting a classifier to a state defined by the same data.** Calling the
   state-bearing population by an expression signature and then classifying
   with a signature derived from the same cells makes the AUC circular. The
   package's threshold mitigations apply here too: define the state
   independently of the feature tested, hold out the feature set, and split by
   patient rather than by cell.
5. **A state that is common but not relapse-linked.** The MRD-positive stratum
   already contains a substantial persistent non-relapser fraction, and
   separating them is the electrical channel's proposed job. A state common
   across that stratum and unrelated to relapse will not discriminate; and if
   it appears to, note that the D1 refinement PPV of exactly 1.000 is a model
   artefact of the 900-day versus 60-day doubling times.

---

## 9. What this document does not claim

- **Research and education only.** A design document: not a clinical protocol,
  treatment recommendation, regulatory strategy or trial design.
- **No patient-specific advice, and no clinical claim.** Nothing here is
  actionable for any individual; this repository handles no patient data, and
  the lineage endpoint has not been measured anywhere.
- **No modelled number here is an empirical result.** Every figure in §2 is a
  simulation output or a literature-derived value from a committed artefact,
  not a measurement of any assay.
- **The three explanations remain open.** This document does not assert that
  the state is a stem cell, nor that it is not; it specifies the measurement
  that would decide it.
- **No claim that the operating point is sufficient.** 200,000× / 200 loci is
  D1's requirement for the mutation and electrical channels. The methylation
  channel's read cost, and the cell-resolution arm's, are not quantified
  anywhere in this repository and must be measured before the design is
  costed.
- **No claim about GSE299684 beyond its contents.** Relapsed SCLC
  single-cell libraries, and no lineage, no post-treatment time point, no
  plasma and no treatment timeline.
