# relapse-competence

> **Status: research software. Not a clinical assay, not a medical device, not for
> patient use.** Every number in this repository was produced by code that executed
> in the run that produced it — or, for the public-data audits, by a measurement
> of a public deposit, recorded with its provenance.

Longitudinal cfDNA modelling for the **relapse-competent state** — the condition
in which a tumour cell population has acquired the capacity to re-found a tumour
after treatment — with an evidence chain you can audit end to end.

The package has two halves, and the second half is where the programme now
stands:

- a **simulator** that answers *"how much lead time does a longitudinal ctDNA
  assay actually buy you, and what does that assay have to cost to get it?"*
  before any sample is drawn;
- **five executed audits on public data** that answer the question the simulator
  cannot: *is the relapse-competent state actually electrically marked, and
  does that survive into a plasma assay?*

---

## Where the programme stands

| Step | Question | Answer |
|---|---|---|
| [Gap audit](docs/GAP-AUDIT-BIOELECTRIC.md) | Is "bioelectric state × lung-cancer relapse competence" genuinely unoccupied? | 2,427 records screened; the target intersection holds **one** record, and it is a review |
| [D0 window audit](docs/D0-TARGET-WINDOW-AUDIT.md) | Which candidate channels have a therapeutic window in lung? | **CACNA1E and STOML3 ruled out**; no channel has a systemic window; the kill condition had to be re-specified, because bulk tissue cannot decide a state-dependent question |
| [D1 channel allocation](docs/D1-CHANNEL-ALLOCATION.md) | Would a bulk ion-channel channel earn the read budget it takes from the mutation panel? | Yes for state — **AUC 0.85–0.95** on the burden-normalised enrichment ratio — but only at ≥200 loci, ≥200,000× depth and ≤25% allocation |
| [State-resolved, SCLC](docs/GSE299684-STATE-EXPRESSION.md) | Is the state electrically marked, in tissue? | **Yes.** PIEZO1 in 39% of state cells against 6% of the surrounding tumour |
| [State-resolved, NSCLC](docs/GSE353299-STATE-EXPRESSION.md) | Does it cross to EGFR-mutant lung adenocarcinoma? | **Yes, through a different channel** — KCa3.1 at 2.97×, in 25 of 25 patients |
| [Plasma readability](docs/PLASMA-READABILITY.md) | What does the measured per-cell enrichment mean in blood? | The assay-design result is **disease-specific**: enrichment AUC 0.99 in NSCLC-MRD, 0.70 in SCLC, against 0.93 assumed |
| [Transferability](docs/CHANNEL-TRANSFERABILITY.md) | Does the readout carry to a third dataset? | **Not universally.** A third relapsed-SCLC tumour expresses neither channel at all |
| [Model fidelity](docs/MODEL-FIDELITY.md) | How much do the published numbers depend on the simulator's assumptions? | The biological assumptions barely matter; the *noise structure* assumption breaks the detector |
| [Lineage design](docs/LINEAGE-RESOLVED-ASSAY-DESIGN.md) | How would one tell a persister lineage from a drug-tolerant state from a fixed-driver clone? | Specified, with the controls and the falsification conditions |

---

## The results

### 1. The assay-design result (simulated)

Post-treatment MRD, simulated with a Poisson read-counting model, read
thresholds calibrated on a **held-out split**, evaluated against the published
bar of a 104-day median lead time before radiographic relapse (tumour-informed
MRD):

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

**And the uncomfortable second finding**: MRD specificity is not one number.
The same panel gives 0.983 against patients with no residual disease and
**0.662** against MRD-positive patients who do not relapse — and **26% of all
MRD-positive patients are persistent non-relapsers**. The literature's "≈98.5%
specificity" is measured against the easy population.

### 2. The state-resolved results (observed, not simulated)

Three public deposits, three independently defined states, one measurement
each. The state is called on an axis that is **orthogonal to the ion
channels**, and the call is validated against a signature the source paper
reports independently.

| Dataset | Disease | State | State fraction | Channel | Detection ratio, state vs tumour | Abundance fold |
|---|---|---|---:|---|---:|---:|
| GSE299684 | relapsed SCLC, 15 libraries | YAP1+ | 0.104 | **PIEZO1** | **6.91** | 3.36 |
| GSE353299 | EGFR-mutant NSCLC, 25 libraries | KRT17+ | 0.392 at MRD (0.125 at baseline) | **KCNN4** | **2.97** | 3.70 |
| GSE324849 | relapsed SCLC, 1 library, tarlatamab | — | absent from the sample | none | — | — |

Three things follow.

- **The state is electrically marked, and the paper that defines this population
  never mentions an ion channel.** Zero occurrences of KCNN4, PIEZO, CACNA1E,
  KCNA3 or "ion channel" in the full text of PMID 42019833. The electrical
  reading of this state was not in the literature because it had not been done.
- **The channel that carries it is disease-specific.** PIEZO1 in SCLC, KCa3.1
  in NSCLC — and the leave-one-patient-out range is 2.69–3.64 for KCa3.1 in
  NSCLC, with the ratio above 1 in 25 of 25 patients.
- **The state is drug-emergent, on the authors' own data.** In EGFR-mutant
  NSCLC every minimal-residual-disease library has a KRT17+ fraction between
  0.28 and 0.65, against a treatment-naive median of 0.125.

**How universal is the readout?** Across the 39 tumours with a measurable
malignant compartment, PIEZO1 is detected in **38 (97.4%)** and KCa3.1 in
**36 (92.3%)**; the exception expresses neither. So a channel-keyed plasma
assay has a high yield — but the failure mode is real, and it is a *tumour*
failure rather than a patient failure.

### 3. What it means in plasma

The simulator carried an assumed electrical fold (3.0) and an assumed state
fraction (0.25). Both are now measured, per disease and per channel, and the
channel allocation sweep is re-run with them. The control row reproduces the
published D1 result exactly (0.9312), which is what makes the rest
attributable to the measurements:

| Configuration | Bulk plasma elevation | Enrichment AUC within MRD+ |
|---|---:|---:|
| the simulator's assumption | 1.750 | 0.9312 |
| NSCLC, KCa3.1 measured | 2.057 | **0.9929** |
| SCLC, PIEZO1 measured | 1.246 | 0.6945 |
| SCLC, KCa3.1 measured | 1.162 | 0.7065 |
| NSCLC, PIEZO1 measured | 1.000 | 0.4658 |

So the headline "AUC 0.85–0.95" was never one number: it is disease- and
channel-specific, it fits the NSCLC case, and it sits well above the SCLC one.
The same measurement also separates two metrics that look interchangeable and
are not — the **detection rate** governs a tissue readout, the **abundance
fold** governs the bulk plasma signal, and in NSCLC PIEZO1 they disagree
(1.24× on detection, 0.84× on abundance, hence an AUC of 0.466, which is
chance).

### 4. The window audit, and what it closed

[D0-TARGET-WINDOW-AUDIT.md](docs/D0-TARGET-WINDOW-AUDIT.md) pulled GTEx lung
and immune expression, Open Targets tractability and constraint, and ClinVar
germline pathogenicity for seven candidate genes.

- **CACNA1E and STOML3 are ruled out** as lung targets: 0.126 TPM in lung,
  loss-of-function intolerance, and a germline epileptic encephalopathy.
- **KCa3.1 has no systemic window**: lung expression is 12× below minor
  salivary gland, the gene is loss-of-function intolerant (LOEUF 0.515), and
  on-target neurological and cardiac liabilities are recorded. The arm is
  blocked on its *window*, not on a missing target — the state-resolved
  measurements found the target in EGFR-mutant lung.
- **Piezo1 remains the most original target and has no clinical asset**; its
  germline and isoform problems are quantified in the audit.

### 5. The secondary result, and why it matters

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
  explicitly. The public-data audits carry their own provenance: the accession,
  the deposited file names, the retrieval time.
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
- **Every claim in every report is checked against the artefact that produced
  it**, and the check is in CI. 502 report-consistency checks and 73 tests
  currently run; several of them exist only because a reviewer caught a number
  that did not match.

---

## Running it

```bash
pip install -e ".[dev]"

pytest                                    # 73 tests
relapse-competence sweep --patients 800   # depth x panel-size grid
relapse-competence all --patients 800     # everything -> results/benchmark_results.json
relapse-competence fidelity --patients 800  # model variants + plasma readability
```

The public-data audits are separate scripts, because each needs its own
download:

```bash
python scripts/download_gse299684.py && python scripts/gse299684_state_expression.py
python scripts/download_gse353299.py && python scripts/gse353299_state_expression.py
python scripts/gse324849_state_expression.py        # three small files, no downloader
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
├── detectors.py    MRD read-count threshold; screening CUSUM; electrical channel.
├── benchmark.py    Held-out calibration, evaluation, lead time, sweeps.
├── fidelity.py     Model variants, and the split-model validation.
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

The fidelity extensions (multi-clone resistance, Gompertzian growth,
site-dependent shedding, per-locus background variation) are all **default-off**
and draw from their own random streams, so the published numbers cannot move
because of them. A captured reference fixture enforces that.

### The detectors

`MrdThresholdDetector` flags when total mutant reads reach `k`. The aggregate
VAF threshold is a *consequence* (`k / (depth × loci)`), not an input.

`SequentialRiseDetector` is a CUSUM over excess reads with a streak bonus for
consecutive signal-consistent elevations and a trend bonus for a rising slope.

`ElectricalChannelDetector` scores the burden-normalised enrichment ratio —
the electrical channel divided by the mutation channel — because the raw
marker is a burden proxy and would only re-confirm that the tumour is growing.

### The audits

The state-expression audits share one discipline, and it is the point of the
exercise:

- **the state is defined on an axis independent of the feature under test**
  (YAP1 in SCLC, KRT17 in NSCLC, NEUROD1 after tarlatamab);
- **the call is validated against a signature the source paper reports
  independently** (surface targets, the basaloid programme, DLL3
  downregulation);
- **the measurement then asks about channels that played no part in either**;
- **and every number in the report is checked against the generated artefact**,
  by a script in CI.

---

## What this package does not do

- It does **not** measure anything in a patient. The simulator's figures are
  simulated; the audits are measurements of **public deposits**; no clinical
  sample was processed.
- It does **not** model a specific assay. Depth, panel size, background floor
  and shedding are parameters, not claims about a commercial kit.
- It does **not** establish that a real assay achieves these numbers. The
  model reproduces the physics of Poisson sampling and exponential tumour
  growth; it does not reproduce assay-specific biases, cfDNA extraction
  efficiency, or the biology of a real resistant clone.
- It does **not** establish that the state is electrically *driven*. The
  measurements are expression measurements: the state over-expresses these
  channels, which is a correlation with the state, not a mechanism.
- It does **not** resolve the lineage question. No dataset in this repository
  has a mutation-defined lineage tag in serial plasma, so "persister lineage"
  versus "drug-tolerant state" versus "fixed-driver clone" is still open; see
  [`docs/LINEAGE-RESOLVED-ASSAY-DESIGN.md`](docs/LINEAGE-RESOLVED-ASSAY-DESIGN.md).
- It does **not** address the cancer-stem-cell hypothesis specifically. The
  "relapse-competent state" is the deliverable; CSC is one explanatory
  hypothesis among several. See [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Documentation

- [`docs/GAP-AUDIT-BIOELECTRIC.md`](docs/GAP-AUDIT-BIOELECTRIC.md) — **formal gap audit**: is *"bioelectric state × lung-cancer relapse competence"* genuinely unoccupied? Pre-registered query grid over PubMed, Europe PMC, ClinicalTrials.gov and GEO; 2,427 records screened; the target intersection holds **one** record, and it is a review
- [`docs/D0-TARGET-WINDOW-AUDIT.md`](docs/D0-TARGET-WINDOW-AUDIT.md) — **D0, executed**: the therapeutic-window audit. Two targets ruled out, the systemic-window hypothesis dropped for KCa3.1, and the kill condition re-specified — because bulk tissue cannot decide a state-dependent question
- [`docs/D1-CHANNEL-ALLOCATION.md`](docs/D1-CHANNEL-ALLOCATION.md) — **D1, executed**: does a bulk ion-channel channel earn its read budget? Yes for state (AUC 0.85–0.95 after burden normalisation), but only at ≥200 loci and ≤25% allocation
- [`docs/GSE299684-STATE-EXPRESSION.md`](docs/GSE299684-STATE-EXPRESSION.md) — **the state-resolved measurement, executed on public data**: is the relapse-competent state electrically readable? Yes — PIEZO1 marks it at every site including lung; KCa3.1 does not mark it in lung — and the NSCLC replication finds the opposite there, which moves the KCa3.1 arm from "no target" to "no window"
- [`docs/GSE353299-STATE-EXPRESSION.md`](docs/GSE353299-STATE-EXPRESSION.md) — **the NSCLC replication, executed on public data**: does the electrical reading cross to EGFR-mutant lung adenocarcinoma? Yes, through KCa3.1 (2.97×, in 25 of 25 patients) — and it corrects the SCLC-only conclusion that the KCa3.1 arm was closed for lung
- [`docs/CHANNEL-TRANSFERABILITY.md`](docs/CHANNEL-TRANSFERABILITY.md) — **the third-dataset test**: the ion-channel readout does **not** transfer — a third relapsed-SCLC tumour expresses neither channel at all, so a plasma assay keyed on one channel needs a tumour-expression gate
- [`docs/PLASMA-READABILITY.md`](docs/PLASMA-READABILITY.md) — **what the measured state enrichment means in blood**: the per-cell fold and the state fraction, measured, replace the simulator's assumptions — and D1's enrichment AUC turns out to be disease-specific (0.99 in NSCLC-MRD, 0.70 in SCLC, against 0.93 assumed)
- [`docs/MODEL-FIDELITY.md`](docs/MODEL-FIDELITY.md) — **model fidelity, executed**: how far the published numbers move when the simulator is made more realistic, and whether a detector fitted on one model transfers to another. It does — except when the error floor varies by locus, which collapses it
- [`docs/LINEAGE-RESOLVED-ASSAY-DESIGN.md`](docs/LINEAGE-RESOLVED-ASSAY-DESIGN.md) — **the lineage measurement**: how to distinguish a persister lineage that acquires stem-cell function from a drug-tolerant state and from a fixed-driver clone
- [`docs/RESEARCH-PLAN.md`](docs/RESEARCH-PLAN.md) — **the executable plan**: targets (KCa3.1, Piezo1, Cav2.3), the D0–D5 experiment ladder with entry/exit/kill criteria, the risk register, and the MRD-guided clinical path
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — what comes next, and the open dependencies
- [`docs/DATASETS.md`](docs/DATASETS.md) — dataset requirements and access routes
- [`MODEL_CARD.md`](MODEL_CARD.md) — intended use, calibration sources, performance and limitations of the simulator

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

---

## Licence

**AGPL-3.0-or-later**, with a commercial licence available — the same
dual-licence arrangement used by this account's other bio tooling
(`mrnavax`, `mrnavax-rare`, `employee-voice-analytics`, `py-idp`).

- Open source: see [`LICENSE`](LICENSE) for the full GNU Affero General Public
  License v3.0 text.
- Commercial: see [`COMMERCIAL_LICENSE.md`](COMMERCIAL_LICENSE.md) for how to
  obtain a licence that does not carry the AGPL obligations.

Cite with [`CITATION.cff`](CITATION.cff).
