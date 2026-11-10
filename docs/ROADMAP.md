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
- **The readout is now named.** KCa3.1 for EGFR-mutant NSCLC (enrichment AUC
  0.9929 at 200,000× / 200 loci); PIEZO1 for relapsed SCLC, but only just
  (0.6945 against a 0.65 threshold). PIEZO1 as the NSCLC readout is dead:
  the state does not over-express it there, so it carries no information and
  both K1 and K3 fire.
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
