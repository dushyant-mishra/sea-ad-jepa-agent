# DEV2048 v2 role allocation — feasible prospective candidate, not a new dataset

This is an incremental source-only feasibility result on top of PR #599. The frozen PR #547 DEV2048 v1 code/data, PR328 biology, real RNA authority and controller files remain unchanged.

**Design correction to Macha's v2 proposal** (PR547 comment 6649566055): Instead of 4 gene addresses in each of three views plus 3 tail, place **3 per view**. For rare regime 0—the same 15 genes that are perturbed by PR328—reserve **3 positive q** (one rare and two perturb) and **3 shared non-query programme panel members**. This uses exactly 9+3+3 = 15. Other rare regimes get 9 view genes, 1 positive q, 3 panel members and 2 reserve genes, totalling 15 each. Two null q have zero rare/perturb membership but other8 panels containing programme genes.

The old v1 rule reserved globally disjoint panels; this v2 candidate **intentionally changes only the cross-query panel overlap policy**, not the requirement for eight distinct OTHER genes within each query or the prohibition on using ANY q in ANY panel. Original PR526 measured-panel producer validates eight distinct other per query and q exclusion, not cross-query global disjointness; original TD gate and evaluator assumptions still require independent review before this is approved.

Each query has eight source-common structurally supported other genes. Three rare0 q-specific panels reuse exactly three nonquery rare0 programme genes; five fillers per panel are distinct. Query genes are excluded everywhere in the student's RNA counts and must be excluded from q-locus ATAC in any eventual q-blind student. No physical student array, latent rare cell, source×split activity or observed count is generated here.

The new code is **deterministic metadata** using a single preregistered seed and salt commitment; it performs no outcome comparison, real-data extraction, training or adaptive seed search. The 4×15 programmed gene locations are a new versioned layout; they do **not** claim that literal PR328 genes remain at indices 0–59, nor that PR328 unchanged original world is being overwritten. Physical perturbation overlaps rare programme 0 exactly as before.

Even when all metadata tests pass, approval for new synthetic world creation depends on independent C3 panel sharing review, controller-only active donor/source/split estimability, source-technical shortcut tests, query normalization noninterference, and the complete frozen TRAIN-only realism contract. The latter reuses V74/77/S174 real summaries, V78/V79 negative data, #239 E0–E4 class propagation and Task3/#598 physical observation binding gaps. No 'qualified' statement, C1–C6 gate decision, producer execution, optimizer, Stage4 or authorization results from these checks.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
