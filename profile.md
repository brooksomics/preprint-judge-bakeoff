# Reading profile

I close-read one preprint every two weeks and write it up. I am a data
scientist who works on genomic data infrastructure, with a past in microbial
ecology.

What I pick:

- **Single-cell**: foundation models and whether they beat simple baselines;
  reference-based cell-type annotation and label harmonization; atlas-scale
  (10M+ cells) integration; ambient RNA, doublets, and empty droplets treated
  as controls rather than nuisances.
- **Spatial transcriptomics**: imaging-based (MERFISH, Xenium) and
  sequencing-based atlases, especially where resolution outruns the QC.
- **Microbiome and metagenomics**: low-biomass contamination, negative
  controls, taxonomic classification, assembly of novel taxa or phages.
- **Protein language models and variant effect prediction**: sequence-only
  versus structure- or alignment-augmented predictors, ClinVar and ProteinGym
  benchmarks, distillation and ensembling.
- **Population-scale sequencing**: biobank WGS (UK Biobank, All of Us), rare
  and structural variation, and what a new resource buys over what existed.
- **Evaluation methodology**: benchmark leakage, label circularity (the ground
  truth is itself model output), self-consistency dressed up as accuracy,
  baselines run at defaults.

I favor papers with one clear, checkable claim on a large public dataset, and
papers that argue against the field's default (a smaller model wins, curation
beats scale). Data-infrastructure consequences (storage, re-analysis, query at
scale) are a plus.

Not for me: neuroscience without a genomics angle, plant and ecology field
studies, structural biophysics, clinical trials, and wet-lab mechanism papers
with no computational method or dataset.
