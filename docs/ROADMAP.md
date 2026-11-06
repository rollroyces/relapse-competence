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

### Medium term — empirical validation

6. **A real cohort.** See `DATASETS.md`. Nothing here becomes evidence until
   it runs on real serial plasma.
7. **Split the model.** Use the simulator to generate data with known ground
   truth, then fit a detector to that data and report how much performance is
   lost to the modelling gap. This is the standard way to bound the value of a
   simulation-based design.
8. **D2 with the D1 design requirement.** The tissue-level check must read out
   the **burden-normalised enrichment ratio**, not raw ion-channel abundance. A
   tissue study measuring raw abundance would confirm the growth signal and say
   nothing about the relapse-competent state.

### Longer term — the biological question

8. **Relapse-competent state classifier** on methylation and mutation channels
   jointly, with lineage-resolved validation.
9. **Tumour-informed vs tumour-naive panels.** The current model assumes a
   tumour-informed panel. A tumour-naive design changes the depth/lead-time
   trade-off completely and deserves its own sweep.

## Dependencies, ordered by lead time

| Dependency | Why | Lead time | Start |
|---|---|---|---|
| **Serial NSCLC cohort access** (PLCO via CDAS, or Taizhou via EGA) | Every empirical claim | Months | **First. Start now.** |
| Multi-clone model | Realism of lead time | Days | Alongside |
| Split-model validation | Bounds the simulation gap | Days | After multi-clone |
| Lineage-resolved assay design | The actual scientific question | Months | After cohort access |

The dataset applications dominate the critical path because they are
application-gated and measured in months, while the modelling work is measured
in days.

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
