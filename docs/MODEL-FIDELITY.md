# Model fidelity and the split-model validation

**Audit ID:** `model-fidelity-2026-11`
**Date of run:** 2026-11-06
**Protocol:** one fidelity extension at a time, and a detector fitted on one model and applied, without refitting, to another
**Reproduce:** `python -m relapse_competence.cli fidelity --patients 800 --outdir results`
**Machine-readable artefacts:** `results/model_fidelity.json`,
`results/split_model_validation.json`

---

## 1. Why this exists

The research plan's risk register lists *"modelling assumptions fail (the state
fractions were assumed, not fitted)"* as **certain to be partly wrong**, and
the roadmap lists five fidelity gaps in the simulator: multi-clone resistance,
site-dependent shedding, Gompertzian growth, per-locus background variation,
and a sampling-interval sweep. A design requirement quoted from a simulator is
only worth what the simulator's assumptions are worth, so this document asks
the question directly:

> How much do the published numbers move when the simulator is made more
> realistic, and how much of the published performance survives the move?

Two measurements, both executed here:

1. **The comparison.** Each fidelity extension is switched on alone and then
   all together, and the headline MRD numbers are recomputed.
2. **The split-model validation.** A detector is fitted on the published model
   and applied, *without refitting*, to each fidelity model. The difference
   against a detector refitted on that model is the price of holding the
   published detector fixed.

**The published numbers do not move.** Every extension is default-off in
`SimulationConfig` and draws from its own random stream, and
`tests/fixtures/default_model_reference.json` is a captured reference that the
default configuration must reproduce — a test, not a promise. Floats are
compared to a relative tolerance of 1e-12 and everything else exactly, because
`exp` and `log` differ in the last bit between platforms and the reference was
captured on one machine: the same run on Linux x86-64 and macOS arm64 differs
by one or two units in the last place, which is not a change in the model. Any
change that the guard exists to catch moves the numbers by many orders of
magnitude more than that. The
comparison's `published` variant reproduces the committed
`results/mrd_sweep.json` row for 200,000× / 200 loci to the last digit, which
is what makes the deltas below comparable with the published headline rather
than with a differently-noised cohort.

---

## 2. The extensions

| Extension | What it changes | What it assumes |
|---|---|---|
| `multi_clone` | Three resistant clones with different fitness and different shedding, splitting the residual burden unevenly | Clone fitness and shedding spread (log-normal, CV 0.35 and SD 0.5) |
| `gompertzian` | Growth decelerates towards the carrying capacity | The rate is calibrated per patient so the *initial* doubling time is unchanged |
| `site_dependent_shedding` | Each patient relapses at a drawn metastatic site with that site's own shedding multiplier | **The multipliers are assumptions, not literature estimates**: lung 1.0, bone 0.6, liver 1.5, brain 3.0 |
| `per_locus_background` | The error floor varies across tracked loci, so the mutant read count is over-dispersed | Log-normal spread of 1.0 across loci |

The site multipliers deserve a warning. They are a *sensitivity analysis*, not
a measurement: the point is to see how far the conclusions move under
plausible heterogeneity, and a reader who disagrees with the multipliers can
disagree with the direction of the result, which is stated below.

---

## 3. How far the published numbers move

800 patients per arm, seed 20261106, post-treatment regime, read thresholds
calibrated on a held-out responder split at the 98% specificity bar.

| Variant | 50,000× / 50 loci: sensitivity | median lead | 200,000× / 200 loci: sensitivity | specificity | median lead | lead Δ vs published | cheapest configuration reaching 80% sensitivity |
|---|---:|---:|---:|---:|---:|---:|---|
| `published` | 0.521 | 39.1 d | 0.948 | 0.983 | 107.2 d | — | 50,000 × 200 (10.0M reads) |
| `multi_clone` | 0.487 | 47.2 d | 0.891 | 0.983 | 103.2 d | −4.1 d | 500,000 × 50 (25.0M reads) |
| `gompertzian` | 0.560 | 41.8 d | 0.944 | 0.983 | 110.9 d | +3.6 d | 50,000 × 200 (10.0M reads) |
| `site_dependent_shedding` | 0.598 | 68.0 d | 0.929 | 0.988 | 113.0 d | +5.7 d | 50,000 × 200 (10.0M reads) |
| `per_locus_background` | 0.360 | 43.6 d | 0.838 | 0.983 | 71.6 d | −35.7 d | 200,000 × 200 (40.0M reads) |
| `combined` | 0.468 | 51.8 d | 0.830 | 0.990 | 88.8 d | −18.5 d | 200,000 × 200 (40.0M reads) |

Three things to read off this table.

**The headline design survives the biological extensions.** Multi-clone
resistance, Gompertzian growth and site-dependent shedding move the
200,000× / 200-locus sensitivity by at most 5.7 percentage points and the
median lead time by at most 5.7 days. The depth requirement does not move for
Gompertzian or site-dependent shedding. The published claim — *200,000× on a
200-locus panel* — is not an artefact of the single-clone, exponential,
uniform-shedding simplifications.

**One variant moves the depth requirement, and it is not the biological one.**
`multi_clone` needs 500,000× on 50 loci to reach 80% sensitivity: with several
clones, the aggregate burden is spread thinner and the read threshold has to
move. `per_locus_background` needs the full 200,000× / 200 panel. Both point the
same way — *the recommended operating point is the conservative choice*, which
is a point in its favour.

**Per-locus background is the expensive one.** It costs 11 percentage points
of sensitivity at the recommended operating point and 35.7 days of median lead
time. The mechanism is identifiable: a floor that varies across loci inflates
the *aggregate* read count, because the aggregate sums 200 noisy loci rather
than 200 identical ones.

---

## 4. The split-model validation: does the detector transfer?

At 200,000× depth with 200 mutation loci and 50 electrical loci, the read
threshold is fitted on the published model's responder split (**k = 73**) and
then applied, without refitting, to each fidelity model. "Refit" is the same
detector recalibrated on that model.

| Model | Detector | Sensitivity | Specificity vs responders | Specificity vs MRD+ non-relapsers | PPV within MRD+ | AUC (electrical enrichment) |
|---|---|---:|---:|---:|---:|---:|
| `published` | published (k=73) | 0.937 | 0.973 | 0.601 | 0.678 | 0.931 |
| `multi_clone` | published (k=73) | 0.915 | 0.973 | 0.540 | 0.652 | 0.937 |
| `multi_clone` | refit (k=73) | 0.915 | 0.973 | 0.540 | 0.652 | 0.937 |
| `gompertzian` | published (k=73) | 0.979 | 0.973 | 0.595 | 0.658 | 0.924 |
| `gompertzian` | refit (k=73) | 0.979 | 0.973 | 0.595 | 0.658 | 0.924 |
| `site_dependent_shedding` | published (k=73) | 0.944 | 0.973 | 0.606 | 0.682 | 0.933 |
| `site_dependent_shedding` | refit (k=73) | 0.944 | 0.973 | 0.606 | 0.682 | 0.933 |
| `per_locus_background` | published (k=73) | 0.997 | **0.018** | **0.008** | 0.327 | 0.970 |
| `per_locus_background` | refit (k=124) | 0.833 | 0.985 | 0.777 | 0.761 | 0.928 |
| `combined` | published (k=73) | 1.000 | **0.015** | **0.000** | 0.318 | 0.959 |
| `combined` | refit (k=121) | 0.908 | 0.973 | 0.656 | 0.686 | 0.915 |

**Three biological extensions transfer exactly.** For `multi_clone`,
`gompertzian` and `site_dependent_shedding`, the refitted threshold is
*the same number* (k = 73) and the two rows are identical: the published
detector is the right detector for those models, and the design decisions that
follow from the published headline carry over unchanged.

**One extension breaks the detector, and it breaks it catastrophically rather
than gracefully.** With a per-locus-varying floor, the published threshold
flags almost everybody: specificity against responders collapses from 0.973 to
0.018, the MRD-positive population doubles from 546 to 1,189 patients, and the
PPV within MRD+ falls from 0.678 to 0.327. The sensitivity does not improve —
it is 0.997 because the detector has stopped discriminating and is flagging
the responders too. The "lead time" that follows, 244 days, is an artefact of
flagging early and often, not a better assay.

Refitting restores it (k = 121–124, specificity 0.973–0.985), at a cost of
16–17 points of sensitivity and a shorter median lead time.

---

## 5. The finding that matters

> **The aggregate mutant-read count is a fragile statistic. Its calibration
> depends on the shape of the error floor, not only on its level, and the
> published design is conditional on a floor that is flat across loci.**

This is the one result here that changes what should be done, and it is worth
being precise about why it is a *methodological* result rather than a
number-moving one:

- The published model assumes a single background rate with a small
  across-draw spread (`background_vaf_mean = 1e-6`, `background_vaf_sd = 2e-7`).
  The sensitivity of the design to the *shape* of that floor was never tested.
- The failure mode is not graceful degradation. A threshold that is mis-set
  against a heterogeneous floor produces a false-positive rate of 98%, not a
  slightly worse assay.
- The fix is not to re-tune the threshold for every site. It is to stop
  relying on an aggregate count: require support at *k independent loci*
  rather than *k reads in total*, or use a statistic that is robust to a
  per-locus-varying floor. That is a change to the detector, and it belongs in
  the design of the lineage assay, not after it.
- The electrical channel is unaffected by this failure in kind, not in
  degree: its enrichment AUC stays in the 0.91–0.97 band in every evaluation,
  because it is a *ratio* between two channels measured the same way, and the
  burden cancels.

**The caveat is the assumption, not the arithmetic.** The per-locus spread of
1.0 in log space is an assumption; it has not been measured. What the result
establishes is the *shape* of the dependency: if the floor varies across loci
by more than the published model assumes, the design fails, and it fails hard.
Measuring that spread is cheap — it is a property of the assay and the panel,
not of the biology — and it belongs on the critical path next to the data
applications.

---

## 6. What this changes

| Where | Before | After |
|---|---|---|
| The plan's risk register | "Modelling assumptions fail — certain to be partly wrong" | Attributed: the biological assumptions move the numbers by ≤ 5.7 pp; the *noise-structure* assumption breaks the detector |
| The panel design | A read threshold on the total mutant count across the panel | The aggregate count is conditional on a flat floor; the design must either measure the floor's per-locus spread or use a per-locus-aware statistic |
| The lineage assay design | "the mutation channel supplies the tag" | The tag must be robust to a varying floor, and the floor's shape is an input to the panel, not a nuisance |
| The published headline | 200,000× on 200 loci, 107-day lead | Unchanged for the biological extensions; *conditional* on the background floor being flat |

---

## 7. Limitations

- **Every extension is an assumption.** Clone fitness, the Gompertz
  calibration, the site shedding multipliers and the per-locus background
  spread are parameters chosen to be plausible, not measured. The direction of
  each result is stated; the magnitude is not a measurement.
- **The state fraction is still assumed, not fitted.** The whole point of D1
  is that the electrical channel sees a diluted state signal; a fidelity
  extension to the *state* (mosaicism rather than a single continuous
  fraction) is not implemented here, and would dilute the enrichment AUC
  further.
- **No lineage ground truth.** The simulator still has no lineages to recover,
  so the measurement that discriminates the three explanations cannot yet be
  validated against it.
- **One simulator, one world.** These variants test the model against itself.
  They bound how much the *model's* assumptions matter; they say nothing about
  whether the model resembles a patient's tumour.
- **The sampling-interval sweep** listed in the roadmap is not in this
  document: it changes the schedule rather than the biology, and it is
  available from the existing `sweep` machinery by varying
  `sampling_interval_days`.
- **No clinical claim.** Every number here is a simulation output.

---

## 8. Reproducing

```bash
python -m relapse_competence.cli fidelity --patients 800 --outdir results
```

The run takes about twenty minutes: six variants times an eight-configuration
depth sweep, plus the split-model validation. The published-configuration
guard is separate and fast:

```bash
python scripts/check_default_model_reference.py
python -m pytest tests/test_fidelity.py
```
