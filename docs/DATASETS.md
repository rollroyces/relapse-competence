# Datasets

What this project would need to move from simulation to evidence, and where the
data actually is.

## The requirement

To validate the relapse-competent state model, a dataset needs:

1. **Serial plasma**, drawn on a fixed schedule after treatment, long enough to
   capture the median 104-day lead time plus its tail — realistically 24–36
   months of follow-up per patient.
2. **A known outcome**: which patients relapsed, and when, radiographically.
3. **A matched primary tumour** for tumour-informed panel design (the tumour
   mutation set is what the assay tracks).
4. Ideally, **pre-treatment baseline plasma** to establish each patient's own
   background.

**None of the application-gated cohorts below meets requirement 1.** PLCO and
the Taizhou Longitudinal Study are both screening cohorts: PLCO enrolled
participants between 1993 and 2001 and reports diagnoses through 2009, and
TZL enrolled healthy adults who were then followed for cancer occurrence.
Neither collects serial plasma *after treatment*. What they do provide is the
discrimination contrast the model assumes — participants who progress to
cancer against matched participants who do not — one window earlier, and the
per-participant state fraction that the per-patient audit showed is the
decisive uncertainty. A genuinely post-treatment cohort with matched tumour
remains the programme's largest gap, and it is a clinical collaboration rather
than a registry application.

## Candidate sources

### Application-gated, serial, large

| Source | Access | Serial? | Scale | Notes |
|---|---|:--:|---:|---|
| **PLCO** (Prostate, Lung, Colorectal, Ovarian Screening Trial) | CDAS: a data-only project for the phenotype data, **plus a separate EEMS preliminary application for the plasma aliquots** | Yes, at screening visits | n=154,900 | Serial plasma, pre-diagnosis available. Named as the most valuable route in the predecessor benchmark's own dataset survey. The two CDAS routes have different lead times: 1–4 weeks for data, 4–6 months for biospecimens. |
| **Taizhou Longitudinal Study** (PanSeer) | **Direct request to the study investigators** — see the note below | Yes, 2–3 year sampling | n=123,115 enrolled, 575 cancers | The only published dataset that directly validates a longitudinal pre-diagnosis paradigm. 4-year lead time. Methylation, 595 regions. |
| **DELFI** (dbGaP phs0034536) | dbGaP application | No | n=481 | Fragmentomics parameter extraction only. Not serial. |

**The Taizhou access route was corrected on 2026-11-10.** This table used to
record an EGA Data Access Committee as the route. The EGA's own public
metadata API was queried in full — 10,814 studies and 21,922 datasets — and no
record matches Taizhou, PanSeer or Chen Xingdong, so there is no DAC to apply
to. The route is a collaboration request to the Fudan Taizhou Institute of
Health Sciences and the authors of Chen X et al., *Nature Communications*
2020, doi:10.1038/s41467-020-17316-z. The prepared request, the disclosure it
has to carry, and the tracker for both applications are in
[`DATA-ACCESS-APPLICATIONS.md`](DATA-ACCESS-APPLICATIONS.md).

**Two constraints on that cohort were recorded on 2026-11-12.** The published
informed consent did not include full genetic sequencing, so only methylation
status per genomic position was released. The programme's per-molecule
attribution reads a heterozygous germline SNP that the participant's own
tumour shifts, so that germline information was never collected for these
participants. Whether it can be consented for going forward is one of the two
questions the request has to ask, because the answer decides whether the
collaboration can deliver the attribution the readout rests on.

The second constraint is the one the published record cannot answer. The
measurement reads cell-free RNA; PanSeer read cell-free DNA methylation, and
neither "cfRNA" nor "cell-free RNA" occurs anywhere in the paper, so the
consent's coverage of molecular analysis of RNA is unknown. It gates the
germline question, because if the consent does not permit RNA analysis the
archived aliquots cannot be used for this programme at all. The archive is a
second unknown: the samples were collected before modern plasma preservation,
the blood was held at 4 °C until the end of the business day, only 1 mL of
plasma was available per sample, and the aliquots are twelve to nineteen
years old. How much usable RNA they contain is unmeasured, so the first
material ask is a pilot rather than the stratum.


### Open, small, immediately usable

| Accession | Contents | Use |
|---|---|---|
| **GSE185307** | 13 plasma cfDNA samples, Oxford Nanopore 5mC methylation bedgraphs, ~4.9M CpG each, 6 lung adenocarcinoma + 7 healthy. Berman BP et al., PMID [35841107](https://pubmed.ncbi.nlm.nih.gov/35841107/), preprint doi 10.1101/2021.10.18.464684. RAW.tar 2.1 GB. | Methylation-channel feature extraction and the epigenetic readout of the relapse-competent state. **Not** a MRD cohort — no serial sampling, no treatment timeline. The predecessor repo used it as a feasibility check at n=13, and said so. |
| **GSE122126** | Moss 2018, cfDNA Illumina 450K/EPIC, 11 cancer + 59 cfDNA with a cell-type reference atlas; colorectal 4, lung 4, breast 3, CUP 4. | Methylation array baseline. No serial sampling. |
| **GSE71378** (Snyder 2016) | Healthy cfDNA nucleosome maps | cfDNA biology parameters |
| **TCGA / GDC** | Open tumour tissue | Tumour-informed panel design, mutation priors, LUAD mutation panels |

## The gap

**None of the open datasets is a serial post-treatment NSCLC MRD cohort.** The
open accessions are cross-sectional detection datasets. The serial datasets
are behind access applications with lead times measured in months, and the two
serial cohorts this programme can apply for are screening cohorts rather than
post-treatment ones.

This is why the roadmap starts the applications first and does the modelling
work in parallel. The applications, their drafted content and the tracker of
what is outstanding are in [`DATA-ACCESS-APPLICATIONS.md`](DATA-ACCESS-APPLICATIONS.md).


## Practical notes

- The predecessor repository (`deepcatch`) holds working loaders for
  `GSE185307` and `GSE122126`, including genome-wide methylation feature
  extraction with autosomal-only filtering to avoid sex-chromosome confounds.
  Those loaders carry hard-coded absolute paths and will need the usual
  portability treatment before reuse.
- The methylation channel here is the **epigenetic readout** of the
  relapse-competent state: it is what would distinguish a pre-existing
  relapse-competent state from a therapy-induced one. The mutation channel
  alone cannot, because it reports persistence rather than mechanism.
- Nothing in this project requires sending any patient-identifiable data
  anywhere. All analysis is local.

## Ethics

Any use of patient-level data requires institutional review approval and a
data use agreement covering the relevant registry. This package handles no
patient data itself.
