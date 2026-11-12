# Roadmap

## Where this stands

v0.1.0 answers one question with an executed model:

> At what sequencing depth and panel size does a longitudinal ctDNA MRD assay
> reach a 104-day median lead time before radiographic relapse?

Answer: roughly **200,000× depth on a 200-locus panel** (40M reads/draw). At the
conventional 50,000× / 50-locus configuration the modelled lead time is 41
days.

That number is a *design requirement*, not a result about any assay.

## The scientific gap this points at

The package deliberately does not claim to have solved the cancer-stem-cell
question. It models a **relapse-competent state** — a population with the
capacity to re-found a tumour after treatment — without asserting what that
state *is*.

Three candidate explanations, with different consequences:

| Hypothesis | If true | What would change |
|---|---|---|
| **Stemness** — a persistent CSC-like subpopulation | CSC-targeted therapy becomes rational | Therapy would need to hit the stem-like fraction, not the bulk |
| **Persistence** — a drug-tolerant state that is not stem-like | Bulk-directed combination therapy suffices | No need to define "stemness" at all |
| **Genomic** — a resistant clone with a fixed driver mutation | Genotype-directed therapy suffices | Biomarker work should be on the clone, not the phenotype |

The current literature does not discriminate between these. A 2026 review of
EGFR-mutant NSCLC states the gap directly: what is missing is *"direct evidence
that a prospectively identified persister lineage later acquires serially
propagating CSC function"*, and that *"minimal residual disease may therefore
represent a period in which relapse-competent states are present but not yet
irreversibly established"*.

**Lineage resolution is the discriminating measurement.** That is the single
highest-value addition to this package.

## Planned work

### Near term — model fidelity

1. **Multi-clone resistance.** Currently one residual clone with one doubling
   time. Real resistant disease is heterogeneous: several clones with
   different fitness and different shedding rates. This directly affects lead
   time and would likely shorten it.
2. **Site-dependent shedding.** Lung, bone, liver and brain metastases shed
   ctDNA very differently. A recurrence in a low-shedding site is detectable
   later than one in a high-shedding site — which changes the lead-time
   distribution substantially and is currently not represented.
3. **Gompertzian growth.** Exponential growth with a constant doubling time
   overstates late-stage doubling speed.
4. **Per-locus background variation.** Real error floors vary by locus, batch
   and germline status.
5. **Sampling-interval sweep.** Lead time is currently reported for a single
   90-day interval. How lead time and cost trade off against interval
   frequency is an obvious next question.

### The plan — done: `RESEARCH-PLAN.md`

[`RESEARCH-PLAN.md`](RESEARCH-PLAN.md) is the executable plan for eliminating
the relapse-competent state: five named killing conditions (K1-K5), a ranked
target table (KCa3.1, Piezo1, Cav2.3), the D0-D5 experiment ladder with entry,
exit and kill gates, and the MRD-guided clinical path. D0 (computational
therapeutic-window audit) is the cheapest kill and should start before any
sample is spent.

### D1 — done: channel allocation

Executed. See [`D1-CHANNEL-ALLOCATION.md`](D1-CHANNEL-ALLOCATION.md). Headline:
the bulk electrical channel *does* carry state information beyond burden
(AUC 0.85-0.95 on the burden-normalised enrichment ratio), but it is only
affordable at >=200 loci with >=200,000x depth and <=25% allocation. The same
work also exposed that MRD specificity is 0.983 against responders and 0.662
against MRD-positive non-relapsers, and that 26% of MRD-positive patients are
persistent non-relapsers.

**What D1 changed:** the first question is no longer "is the electrical state
real?" but "can it be measured in plasma at a useful operating point?" -- and
the realistic use is *refinement* of the MRD-positive population, not
detection.

### D0 — done: target window audit

Executed 2026-11-06. See [`D0-TARGET-WINDOW-AUDIT.md`](D0-TARGET-WINDOW-AUDIT.md).
Headline: **no candidate channel has a systemic therapeutic window on bulk
normal tissue, and the verdict does not change between a 2× and a 20× margin.**
Cav2.3 and STOML3 are ruled out outright; KCa3.1 is viable only if delivery is
tumour-directed or local; Piezo1 cannot be separated from PIEZO2.

**What D0 changed:** the kill condition it was built to fire cannot be
evaluated on bulk tissue, because "conditionally selective" is a property of a
state and bulk tissue has no state. The gate is therefore re-specified as
**D0b** and deferred to state-resolved expression, and D2 gains an electrical
endpoint (channel expression per cell type within one tumour).

**What D0 also found:** the anchor dataset of the whole programme is public.
**GSE299684** is the GEO deposit of the YAP1 relapsed-SCLC paper (PMID
42019833) — 15 single-cell libraries of relapsed SCLC from seven metastatic
sites, in standard 10x format, released 2026-05-15. The experiment that
decides D0b therefore no longer waits for an access application.

### Near term — model fidelity — **done**

Executed 2026-11-06. See [`MODEL-FIDELITY.md`](MODEL-FIDELITY.md). The
simulator now models multi-clone resistance, Gompertzian growth,
site-dependent shedding and per-locus background variation — all **default-off**,
with a captured reference fixture proving the published numbers do not move.

Headline: the biological extensions move the 200,000× / 200-locus sensitivity
by at most 5.7 percentage points and the median lead time by at most 5.7 days,
and their read thresholds are *the same number* as the published one. The
extension that does break the design is the per-locus background floor: a
threshold calibrated on a flat floor collapses to 1.8% specificity when the
floor varies by locus. **The aggregate mutant-read count is conditional on the
shape of the error floor, not only its level** — a panel-design constraint,
not a biological one, and a cheap thing to measure.

### The gate review — done: the programme's own kill conditions, applied

Executed 2026-11-09. See [`GATE-REVIEW.md`](GATE-REVIEW.md). The plan's five
killing conditions were applied to the measured evidence rather than to the
simulator's assumptions.

- **K4 has fired.** No candidate channel has a systemic therapeutic window:
  two are not lung targets at all, and the rest fail the specificity verdict.
  The pharmacological arm survives only as a *state-directed* modality, which
  does not exist.
- **K3 has fired as well.** In the projection the plasma pool carried no
  leukocyte compartment, so the channel's signal was the tumour's alone and
  KCa3.1 scored 0.9929 for EGFR-mutant NSCLC. With a leukocyte
  compartment, which is what bulk plasma is, the same statistic does not
  degrade — it **inverts** to 0.0053, and no configuration in the searched
  space clears K3 (the best is 0.5815 against 0.65). The readout that
  survives is therefore a **tissue-level** one: KCa3.1 in EGFR-mutant
  NSCLC, where it is carried in 20 of 23 libraries and all 7 residual-disease
  libraries. PIEZO1 as the NSCLC readout is dead: the state does not
  over-express it there, so it carries no information and both K1 and K3
  fire.
- **K2 and K5 are untested**, and are recorded as untested rather than
  passed. The evidence so far points against K2 (the state is more frequent
  after treatment in NSCLC), but the methylation comparison the condition
  names does not exist here.

### The per-patient audit — done: the readout, tumour by tumour

Executed 2026-11-09. See [`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md). The
gate review's projection used a pooled per-cell fold and a pooled state
fraction, both cell-count weighted, and in the relapsed-SCLC deposit three
libraries hold 86.4% of the state cells while the channel's baseline
expression differs by metastatic site by up to 65-fold. Both inputs are now
recomputed per library and the projection is re-run for each tumour over the
full depth x panel-size grid.

- **The pooled fold is a contrast between metastatic sites, not within one
  tumour.** SCLC/KCa3.1's within-tumour fold exceeds 1 in 3 of 12 libraries;
  SCLC/Piezo1's in 11 of 14; NSCLC/KCa3.1's in 20 of 23, against a pooled
  3.698 that is representative of its own libraries.
- **The SCLC readout does not survive per tumour.** The projection clears the
  programme's own threshold in 1 of 12 SCLC libraries for KCa3.1 and 4 of 14
  for Piezo1. Piezo1 remains a consistent state *marker* in SCLC; what fails is
  the readability, because most relapsed-SCLC tumours carry too little state.
- **The NSCLC readout does.** All 7 residual-disease libraries clear the
  threshold, with per-patient AUCs from 0.949 to 0.999.
- **The programme has one readout, not three.** Every downstream design
  question — panel size, read depth, the gate, the cohort — is now a question
  about EGFR-mutant NSCLC.

The gate review's published numbers stand as the pooled projection they are;
the per-patient audit narrows how they may be read, and the two documents say
so in terms.

### The leukocyte audit — done: the bulk-plasma readout does not survive

Executed 2026-11-10. See [`LEUKOCYTE-AUDIT.md`](LEUKOCYTE-AUDIT.md). The
plasma model had no leukocyte compartment: the cfDNA pool was all
tumour-derived, so the electrical channel's signal was the tumour's alone. In
bulk plasma most cfDNA is leukocyte cfDNA, and KCa3.1 is expressed in immune
cells.

The compartment was added default-off — with it off the golden fixture is
byte-identical on the machine that captured it, so the published model is
untouched — and the audit sweeps it against the tumour's cfDNA share.
The published statistic does not degrade under a leukocyte background, it
**inverts**: 0.9929 becomes 0.0053 for the surviving NSCLC readout, because
the leukocyte term divided by the tumour's cfDNA share is inversely related to
tumour burden. Subtracting the leukocyte reads first — which is what a readout
that localises the channel transcript to the tumour would measure — leaves
0.5111, which is chance.

The consequence is a design requirement rather than a refutation: the assay has
to localise the channel transcript to the tumour, by co-occurrence with a
tumour-specific variant on the same molecule, or read it after a leukocyte
correction. Neither is in the proposal yet, and the proposal is what the
data-access applications are for.

### The localisation audit — done: the specification's own correction works

Executed 2026-11-12. See [`LOCALISATION-AUDIT.md`](LOCALISATION-AUDIT.md).
The leukocyte audit searched the space of background-*subtraction* statistics.
The assay specification's answer is different and had never been simulated:
per-molecule attribution, counting the channel-transcript reads that carry an
informative tumour signature. A leukocyte-derived channel molecule carries the
germline allele, not the tumour's shift of it, so it is never counted, and the
compartment is removed by construction rather than by subtraction.

For the one readout the programme has — KCa3.1 in EGFR-mutant NSCLC — the
attributed statistic clears K1 and K3 at the published operating point
(0.9091 against a 0.65 bar) where the bulk one inverts to 0.0053, and it is
insensitive to the leukocyte compartment by construction. A matched-state
control establishes that it measures the state and not the burden: with the two
arms carrying the same state fraction it falls back to chance (0.5170). The
raw-VAF form of the same statistic does not, which is why the denominator has
to be the participant's estimated tumour cfDNA fraction — which is what the
specification asks for anyway.

So **the plasma arm is not dead**, and the gate review's K3 verdict stands for
the bulk statistic rather than for the readout. What remains unmeasured is the
attribution rate and the fraction of participants with an informative
position; the audit says the statistic survives across the plausible range of
both, which is a statement about the arithmetic and not about the biology. The
SCLC candidates are not rescued, which agrees with the per-patient audit.

### The assay specification — done: what is measured, and what would stop us

Executed 2026-11-11. See [`PLASMA-ASSAY-SPECIFICATION.md`](PLASMA-ASSAY-SPECIFICATION.md).
Every plasma number this programme has published is a projection, and the
leukocyte audit showed what the projection was assuming: a tumour-purified
measurement. The assay itself had never been written down, which is why the
model could carry a compartment-free pool without anyone noticing the
assumption.

The specification fixes the analyte (cfRNA for the channel, cfDNA for the
mutation panel, because only a transcript assay reports a transcript), the
attribution (per molecule, by a germline heterozygous SNP that the
participant's own tumour shifts — the matched primary tumour is what makes it
available, which is why the data request makes it required rather than
optional), the statistic, the panel, the controls and six numeric stop rules.
The attribution has to be per molecule because the alternative — subtracting
the background — is amplified by the inverse of the patient's own tumour cfDNA
share, and the two arms of the MRD-positive cohort sit two orders of
magnitude apart in that share.

### Medium term — empirical validation

6. **A real cohort.** See `DATASETS.md`. Nothing here becomes evidence until
   it runs on real serial plasma. **The two applications are prepared and
   tracked**: [`DATA-ACCESS-APPLICATIONS.md`](DATA-ACCESS-APPLICATIONS.md)
   holds the drafted CDAS fields, the drafted Taizhou collaboration request,
   the prerequisite list and the approval tracker, and
   `results/application_tracker/application_tracker.json` is its machine-
   readable state, checked in CI. Neither application has been submitted --
   both need the PI's account, the PI's submission and a signature.
   The review also corrected the route: the Taizhou study has **no EGA
   deposit** (the catalogue holds 10,814 studies and 21,922 datasets, none of
   them a match), so the route is a direct request to the investigators, and
   neither PLCO nor TZL is post-treatment -- both are screening cohorts, so
   what they can settle is the per-participant state fraction rather than the
   post-treatment MRD claim.

   The Taizhou request is now written
   ([`TAIZHOU-COLLABORATION-REQUEST.md`](TAIZHOU-COLLABORATION-REQUEST.md)),
   drafted and not sent. It asks two consent questions before it asks for
   samples. The informed consent did not include full genetic sequencing, so
   the per-molecule attribution the readout depends on has no source in that
   cohort; and because PanSeer read cell-free DNA methylation while this
   programme reads cell-free RNA, the published record cannot say whether the
   consent covers molecular analysis of RNA at all. The archive is a third
   unknown — collected before modern plasma preservation, 1 mL of plasma per
   sample, twelve to nineteen years old — so the ask is a pilot rather than
   the stratum.

   The PLCO side now has a **package ready to sign**:
   [`plco-cdas-submission-package/`](plco-cdas-submission-package/README.md)
   holds the pre-filled CDAS fields, the proposal narrative, the PI cover
   sheet with its attestations, the Signing Official's letter and the
   documents checklist, a submission runbook and the scoping inquiry.
   `scripts/check_plco_cdas_package.py` checks it in CI, including CDAS's
   500-word cap on the project description, and
   `scripts/build_plco_cdas_pdf.py` prints it from the same markdown so that
   what is signed is what is in the repository.
   **The scoping inquiry has been sent** — two messages through the CDAS
   contact form on 2026-11-11, one per topic, the clinical data and the
   archived material. CDAS's form issues no inquiry number, so the reply is
   the only reference there will be; the sending record and the length of
   each message are in
   [`plco-cdas-submission-package/07-scoping-inquiry.md`](plco-cdas-submission-package/07-scoping-inquiry.md)
   §0, and the verifier checks those lengths against the message blocks
   themselves. The answers decide whether the EEMS route is worth starting
   and how large the pilot has to be, so nothing else moves until they
   arrive.
7. **Split the model.** *Done:* use the simulator to generate data with known
   ground truth, then apply a detector fitted on the published model to the
   fidelity model and report how much performance is lost to the modelling gap.
   See [`MODEL-FIDELITY.md`](MODEL-FIDELITY.md). The answer was asymmetric:
   the biological extensions transfer exactly, and the per-locus background
   floor does not.
8. **D2 with the D1 design requirement.** The tissue-level check must read out
   the **burden-normalised enrichment ratio**, not raw ion-channel abundance. A
   tissue study measuring raw abundance would confirm the growth signal and say
   nothing about the relapse-competent state.

### Longer term — the biological question

9. **Relapse-competent state classifier** on methylation and mutation channels
   jointly, with lineage-resolved validation. *The design is written*:
   [`LINEAGE-RESOLVED-ASSAY-DESIGN.md`](LINEAGE-RESOLVED-ASSAY-DESIGN.md).
10. **Tumour-informed vs tumour-naive panels.** The current model assumes a
    tumour-informed panel. A tumour-naive design changes the depth/lead-time
    trade-off completely and deserves its own sweep.

## Dependencies, ordered by lead time

| Dependency | Why | Lead time | Start |
|---|---|---|---|
| **State-resolved single-cell data** (GSE299684, public) | Decides D0b: does the relapse-competent state express the channels more than the surrounding lung? | Days — public, no application | **done 2026-11-07** |
| **Serial NSCLC cohort access** (PLCO via CDAS, or Taizhou via EGA) | Every empirical claim | Months | In parallel |
| **GitHub Actions billing** | Continuous machine-checking of every push | Hours, once the account is unlocked | Now |
| Multi-clone model | Realism of lead time | Days | Alongside |
| Split-model validation | Bounds the simulation gap | Days | After multi-clone |
| Lineage-resolved assay design | The actual scientific question | Months | After cohort access |

The dataset applications dominate the critical path because they are
application-gated and measured in months, while the modelling work is measured
in days. **One dependency has come off it:** the anchor single-cell dataset is
public, so the first state-resolved measurement can be run without an
application, in parallel with the applications rather than after them.

**That measurement has now been run** (2026-11-07): see
[`GSE299684-STATE-EXPRESSION.md`](GSE299684-STATE-EXPRESSION.md). The state
*is* electrically marked — PIEZO1 in 39% of state cells against 6% of
neighbouring tumour cells, at every site tested — but KCa3.1 does not mark
the state in lung — and the NSCLC replication
([`GSE353299-STATE-EXPRESSION.md`](GSE353299-STATE-EXPRESSION.md)) finds the
opposite in EGFR-mutant lung, so the KCa3.1 arm is blocked on its window
rather than on a missing target. The third-dataset test
([`CHANNEL-TRANSFERABILITY.md`](CHANNEL-TRANSFERABILITY.md)) then finds that
the readout is **not universal across tumours either**: a third relapsed-SCLC
tumour expresses neither channel, which means a plasma assay keyed on one
channel needs a tumour-expression gate.

**The Actions billing lock is diagnosed, not guessed.** Every job in every
repository on this account fails within a few seconds with no runner and no
log; GitHub's own annotation reads *"The job was not started because your
account is locked due to a billing issue."* The repository's own workflow
configuration is not the cause — Actions permissions are enabled and allow all
actions. Until the account is unlocked, `scripts/ci_local.sh` runs the same
checks locally, so no verification is lost, only the automatic trigger.

## Pivot conditions

| If this turns out to be true | Then |
|---|---|
| Real assays behave worse than the model predicts (extraction loss, index hopping) | Add an efficiency parameter before any further design work; the depth requirement will rise |
| Multi-clone resistance shortens lead time substantially | Re-derive the depth requirement; the current figure is optimistic |
| No serial cohort is accessible | Pivot the contribution to "what an auditable longitudinal biomarker benchmark looks like when audited" — the methods paper is worth publishing on its own |
| The relapse-competent state turns out not to be lineage-stable | Drop the stemness framing entirely and publish the state-detection work without it |

## Explicitly not planned

- Clinical trial design or regulatory strategy.
- Any patient-facing tool.
- A claim that any of this constitutes a cancer treatment.
