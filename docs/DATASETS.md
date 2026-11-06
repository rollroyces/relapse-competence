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

## Candidate sources

### Application-gated, serial, large

| Source | Access | Serial? | Scale | Notes |
|---|---|:--:|---:|---|
| **PLCO** (Prostate, Lung, Colorectal, Ovarian Screening Trial) | CDAS application | Yes | n=154,900 | Serial plasma, pre-diagnosis available. Named as the most valuable route in the predecessor benchmark's own dataset survey. |
| **Taizhou Longitudinal Study** (PanSeer, EGA) | EGA Data Access Committee | Yes | n=123,115 enrolled, 575 cancers | The only published dataset that directly validates a longitudinal pre-diagnosis paradigm. 4-year lead time at 2–3 year sampling. Methylation, 595 regions. |
| **DELFI** (dbGaP phs0034536) | dbGaP application | No | n=481 | Fragmentomics parameter extraction only. Not serial. |

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
are behind access applications with lead times measured in months.

This is why the roadmap starts the applications first and does the modelling
work in parallel.

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
