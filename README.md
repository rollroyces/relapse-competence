# relapse-competence

> **Status: research software. Not a clinical assay, not a medical device, not for
> patient use. Every number in this repository is produced by code that executed in
> the run that produced it.**

Longitudinal cfDNA modelling for the **relapse-competent state** — the condition
in which a tumour cell population has acquired the capacity to re-found a tumour
after treatment — with an evidence chain you can audit end to end.

The question this package exists to answer is not "which marker identifies a
cancer stem cell". It is:

> **How much lead time does a longitudinal ctDNA assay actually buy you, and
> what does that assay have to cost to get it?**

---

## The headline result

Post-treatment MRD, simulated with a Poisson read-counting model, read thresholds
calibrated on a **held-out split**, evaluated against the published bar of a
104-day median lead time before radiographic relapse (tumour-informed MRD):

| Depth | Loci | Reads/draw | k | Sensitivity | Sens @360d | Specificity | Median lead | Min detectable burden | Meets bar |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| 5,000 | 50 | 250K | 3 | 0.116 | 0.077 | 0.978 | **46 d** | 26.7 cm³ | no |
| 5,000 | 200 | 1.0M | 6 | 0.279 | 0.175 | 0.985 | **38 d** | 13.3 cm³ | no |
| 50,000 | 50 | 2.5M | 10 | 0.521 | 0.345 | 0.985 | **39 d** | 8.9 cm³ | no |
| 50,000 | 200 | 10.0M | 24 | 0.828 | 0.632 | 0.990 | **72 d** | 5.3 cm³ | no |
| 200,000 | 50 | 10.0M | 24 | 0.828 | 0.632 | 0.990 | **72 d** | 5.3 cm³ | no |
| 200,000 | 200 | 40.0M | 74 | 0.948 | 0.729 | 0.983 | **107 d** | 4.1 cm³ | yes |
| 500,000 | 50 | 25.0M | 48 | 0.924 | 0.728 | 0.970 | **102 d** | 4.3 cm³ | no |
| 500,000 | 200 | 100.0M | 170 | 0.968 | 0.789 | 0.980 | **118 d** | 3.8 cm³ | yes |

**Two findings worth acting on.**

1. **At a conventional tumour-informed MRD configuration — 50,000× depth, a
   50-locus panel — the modelled median lead time is 39 days and sensitivity
   52.1%.** That is well short of the 104-day bar that published MRD assays
   report. Reaching the bar requires roughly **200,000× depth on a 200-locus
   panel — 40 million reads per draw**, sixteen times the read budget of the
   conventional configuration.

2. **The binding constraint is the assay, not the statistics.** Adding read
   depth moves the lead time; adding a smarter detector does not. The
   "minimum detectable burden" column shows why: at 50,000× the assay cannot
   see a tumour smaller than ~8.9 cm³, and by the time it can, the patient has
   usually already relapsed.

### The D1 result, and why it changes the programme's shape

[`docs/D1-CHANNEL-ALLOCATION.md`](docs/D1-CHANNEL-ALLOCATION.md) asks the first
question the gap audit left open: **if a bulk ion-channel channel existed, would
it earn the sequencing budget it takes from the mutation panel?**

Two results, one of them uncomfortable:

- **MRD specificity is not one number.** The same panel gives 0.983 against
  patients with no residual disease and **0.662** against MRD-positive patients
  who do not relapse — and **26% of all MRD-positive patients are persistent
  non-relapsers**. The literature's "≈98.5% specificity" is measured against the
  easy population.
- **The state signal does survive bulk dilution**, but only once burden is
  divided out: the burden-normalised enrichment score separates relapsers from
  non-relapsers within the MRD-positive population at **AUC 0.85–0.95**. The
  *raw* marker scores higher (0.99–1.00) but is a burden proxy — "the tumour is
  regrowing" — which is **not** evidence for the bioelectric hypothesis.

The cost is quantified: a 25% electrical allocation costs ~3 points of MRD
sensitivity at 200 loci and ~12 points at 50 loci. **The channel is affordable
only at ≥200 loci with ≥200,000× depth**, and a 100% electrical allocation is
degenerate (no mutation panel means no MRD assay to refine).

### The secondary result, and why it matters

In the screening regime, a sequential (CUSUM) detector and a single-timepoint
threshold were **both** calibrated on the same held-out healthy split at the
same specificity target, then evaluated on the complementary split:

| Detector | Sensitivity | Specificity | Median volume at detection |
|---|---:|---:|---:|
| Sequential (CUSUM over read counts) | 0.994 | 0.990 | 7,474 mm³ |
| Single timepoint, final draw | 0.988 | 0.995 (FPR 0.005) | — |

The longitudinal advantage in this regime is about **0.6 percentage points of
sensitivity**, not the order-of-magnitude advantage that marketing-adjacent
claims about "5.3×" tend to assert. At 50,000× depth, by the final draw the
tumour signal is already far above threshold for both detectors, so a
trajectory buys very little. The trajectory matters when the signal is *near*
threshold — which is exactly the MRD regime, and the reason this package puts
its weight there.

---

## Why this package exists

An audit of an earlier longitudinal biomarker benchmark in this account found
that its simulator imported a module (`agent3_longitudinal`) that existed in
**no repository**, and that the two classes it needed (`CETDetector`,
`LongitudinalSimulator`) were defined **nowhere in the codebase**. The import
therefore always failed, the benchmark always fell back to a hard-coded
projection, and the resulting report was published with `Status: COMPLETE` and
a headline comparison of a hand-tuned projection against published clinical
trial numbers.

The failure was not arithmetic. It was that **nothing in the pipeline could
distinguish a measured number from an assumed one.**

This package is built so that mistake is structurally impossible:

- **Every result file carries `metadata.mode`.** `simulated` means code ran.
  `projected` means the numbers are assumptions — and the writer *refuses* to
  emit a projected file unless `RELAPSE_COMPETENCE_ALLOW_PROJECTION=1` is set
  explicitly.
- **Missing dependencies fail loudly.** `LayerDependencyError` for a missing
  dependency or mode; `LayerContractError` for a violated output contract.
  The second is never overridable, because it is always a bug.
- **Thresholds are calibrated on a held-out split and evaluated on another.**
  The MRD read threshold and the screening CUSUM threshold are both selected on
  even-indexed controls and evaluated on odd-indexed controls plus all cases.
- **Late detections count as failures.** A flag at or after radiographic
  relapse is not a detection; it is counted as a false negative for the
  sensitivity figure and reported separately.
- **Lead time is continuous**, computed from the growth model rather than
  quantised to the 90-day sampling interval.

---

## Running it

```bash
pip install -e ".[dev]"

pytest                                    # 33 tests
relapse-competence sweep --patients 800   # depth x panel-size grid
relapse-competence all --patients 800     # everything -> results/benchmark_results.json
```

Every invocation writes a JSON record containing the full configuration, the
calibration provenance (each constant with its literature source), the
reference benchmarks being compared against, the git commit, and the mode
stamp.

Committed evidence lives in `results/`.

### Continuous integration

`.github/workflows/ci.yml` runs lint, tests, and the benchmark on Python
3.11–3.14 across Linux and macOS.

If Actions cannot be scheduled — for example when the account is in a
billing-locked state and jobs are refused before they start — the identical
checks run locally in a few seconds:

```bash
bash scripts/ci_local.sh
```

---

## How it works

```
src/relapse_competence/
├── config.py       Typed configuration. Every knob that moves a number lives here.
├── contracts.py    Fail-fast contracts and the projection guard.
├── calibration.py  Literature anchors with sources.
├── simulator.py    Ground truth: tumour growth + Poisson read sampling.
├── detectors.py    MRD read-count threshold; screening CUSUM.
├── benchmark.py    Held-out calibration, evaluation, lead time, sweeps.
├── report.py       Results assembly with the mode stamp.
└── cli.py          Command line entry point.
```

### The simulator

Mutant reads are drawn from a Poisson distribution, so the **Poisson floor of
ctDNA detection is reproduced rather than assumed away**. Two modelling
choices matter:

- **Multi-locus read counting.** Real tumour-informed panels track 50–500
  somatic loci and flag on the total read count. Modelling one locus
  understates sensitivity by roughly an order of magnitude.
- **The background floor is an assay constant** (per-locus error rate under
  duplex suppression), not a quantity estimated from the patient. Estimating
  it from a handful of ultra-low-count draws is itself a false-positive
  source — an earlier log-scale SPRT formulation of the screening detector
  produced a 17% false-positive rate on healthy patients for exactly this
  reason, and was replaced with a count-domain CUSUM.

### The detectors

`MrdThresholdDetector` flags when total mutant reads reach `k`. The aggregate
VAF threshold is a *consequence* (`k / (depth × loci)`), not an input.

`SequentialRiseDetector` is a CUSUM over excess reads with a streak bonus for
consecutive signal-consistent elevations and a trend bonus for a rising slope.

---

## What this package does not do

- It does **not** measure anything. Every figure is simulated.
- It does **not** model a specific assay. Depth, panel size, background floor
  and shedding are parameters, not claims about a commercial kit.
- It does **not** establish that a real assay achieves these numbers. The
  model reproduces the physics of Poisson sampling and exponential tumour
  growth; it does not reproduce assay-specific biases, cfDNA extraction
  efficiency, or the biology of a real resistant clone.
- It does **not** address the cancer-stem-cell hypothesis specifically. The
  "relapse-competent state" is the deliverable; CSC is one explanatory
  hypothesis among several. See `docs/ROADMAP.md`.

---

## Documentation

- [`docs/RESEARCH-PLAN.md`](docs/RESEARCH-PLAN.md) — **the executable plan**: targets (KCa3.1, Piezo1, Cav2.3), the D0–D5 experiment ladder with entry/exit/kill criteria, and the MRD-guided clinical path
- [`docs/D0-TARGET-WINDOW-AUDIT.md`](docs/D0-TARGET-WINDOW-AUDIT.md) — **D0, executed**: the therapeutic-window audit. Two targets ruled out, the systemic-window hypothesis dropped for KCa3.1, and the kill condition re-specified — because bulk tissue cannot decide a state-dependent question
- [`docs/GSE299684-STATE-EXPRESSION.md`](docs/GSE299684-STATE-EXPRESSION.md) — **the state-resolved measurement, executed on public data**: is the relapse-competent state electrically readable? Yes — PIEZO1 marks it at every site including lung; KCa3.1 does not mark it in lung — and the NSCLC replication finds the opposite there, which moves the KCa3.1 arm from "no target" to "no window"
- [`docs/GSE353299-STATE-EXPRESSION.md`](docs/GSE353299-STATE-EXPRESSION.md) — **the NSCLC replication, executed on public data**: does the electrical reading cross to EGFR-mutant lung adenocarcinoma? Yes, through KCa3.1 (2.97×, in 25 of 25 patients) — and it corrects the SCLC-only conclusion that the KCa3.1 arm was closed for lung
- [`docs/PLASMA-READABILITY.md`](docs/PLASMA-READABILITY.md) — **what the measured state enrichment means in blood**: the per-cell fold and the state fraction, measured, replace the simulator's assumptions — and D1's enrichment AUC turns out to be disease-specific (0.99 in NSCLC-MRD, 0.70 in SCLC, against 0.93 assumed)
- [`docs/MODEL-FIDELITY.md`](docs/MODEL-FIDELITY.md) — **model fidelity, executed**: how far the published numbers move when the simulator is made more realistic, and whether a detector fitted on one model transfers to another. It does — except when the error floor varies by locus, which collapses it
- [`docs/LINEAGE-RESOLVED-ASSAY-DESIGN.md`](docs/LINEAGE-RESOLVED-ASSAY-DESIGN.md) — **the lineage measurement**: how to distinguish a persister lineage that acquires stem-cell function from a drug-tolerant state and from a fixed-driver clone
- [`docs/D1-CHANNEL-ALLOCATION.md`](docs/D1-CHANNEL-ALLOCATION.md) — **D1, executed**: does a bulk ion-channel channel earn its read budget? Yes for state (AUC 0.85–0.95 after burden normalisation), but only at ≥200 loci and ≤25% allocation
- [`docs/GAP-AUDIT-BIOELECTRIC.md`](docs/GAP-AUDIT-BIOELECTRIC.md) — **formal gap audit**: is *"bioelectric state × lung-cancer relapse competence"* genuinely unoccupied? Pre-registered query grid over PubMed, Europe PMC, ClinicalTrials.gov and GEO; 2,427 records screened; the target intersection holds **one** record, and it is a review
- [`MODEL_CARD.md`](MODEL_CARD.md) — intended use, training data, performance, limitations
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — what comes next, and the open dependencies
- [`docs/DATASETS.md`](docs/DATASETS.md) — dataset requirements and access routes

### The research plan

[`docs/RESEARCH-PLAN.md`](docs/RESEARCH-PLAN.md) is the executable plan:
targets, experiment ladder, clinical path and kill conditions, for the goal of
**eliminating the relapse-competent state** in lung cancer rather than chasing
a marker that was fashionable in 2009.

Its spine is mechanotransduction → electrical state → relapse competence:

```
niche stiffness → PIEZO1 → Ca²⁺ → KCa3.1 (KCNN4) → membrane potential
                  ↘ YAP/TEAD ↘
                     YAP1+ plastic persister population (2026, SCLC)
```

The plan opens with five named killing conditions (K1–K5) and starts at the
cheapest possible kill: a computational therapeutic-window audit of the
candidate channels before any sample is spent.

### The research programme in one paragraph

The gap audit's conclusion was not "nobody has looked". It was that the field has
three mature, separate pieces and has never joined them: an **electrical**
phenotype (membrane potential, ion channels) that has been tied to relapse
separately in glioblastoma, oesophageal, gastric and thyroid cancer; a
**lung-cancer relapse-competent state** that was only defined in 2026, using
ctDNA; and a **DNA** channel that reads everything from plasma. The proposed
work is to close the loop for the first time — and the first step costs days,
because `relapse-competence` can compute whether an added electrical channel is
worth the read budget *before* any cohort exists.

## Licence

**AGPL-3.0-or-later**, with a commercial licence available — the same
dual-licence arrangement used by this account's other bio tooling
(`mrnavax`, `mrnavax-rare`, `employee-voice-analytics`, `py-idp`).

- Open source: see [`LICENSE`](LICENSE) for the full GNU Affero General Public
  License v3.0 text.
- Commercial: see [`COMMERCIAL_LICENSE.md`](COMMERCIAL_LICENSE.md) for how to
  obtain a licence that does not carry the AGPL obligations.

Cite with [`CITATION.cff`](CITATION.cff).
