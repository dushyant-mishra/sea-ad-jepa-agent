# TD57 pre-freeze design correction — learned relational geometry continuity and fine-structure gradient

Status: `PRE_FREEZE_DESIGN_CORRECTION__NO_TRAINING_AUTHORITY`
Date: 2026-09-08

## Why this amendment exists

TD56 qualified one specific label-free biological object on the 50k falsification archive:
**tie-aware pairwise concordance-derived within-donor cell geometry from disjoint gene views**.

The post-TD56 relational-JEPA reframe correctly moved the project away from requiring a named per-cell biological target tensor. However, it would be an unjustified substitution to assume that arbitrary Euclidean/cosine geometry of a learned EMA-teacher embedding automatically inherits TD56's reproducibility.

TD57 must therefore separate:

1. **concordance geometry already shown by TD56**, from
2. **learned embedding geometry proposed as a training target**.

The second must earn continuity with the first prospectively.

## Literature check informing this design

Current literature strengthens, but does not settle, the proposed direction.

- **RKD (Park et al., CVPR 2019)** transfers pairwise distances and triplet angles rather than pointwise teacher outputs.
- **GeneJEPA (2025)** predicts latent representations of masked gene sets from visible context using an EMA teacher and variance/covariance regularization.
- **Cell-JEPA (2026)** predicts an EMA teacher cell embedding from a masked student cell using pointwise cosine distance and also retains masked-gene reconstruction.
- **scJEPA (ICLR 2026 workshop)** uses cross-view cell-embedding prediction plus SIGReg and denoising reconstruction.
- **LeJEPA (2025)** introduces SIGReg as a distributional anti-collapse regularizer.
- **UniSurg / SurgMotion (2026)**, built on V-JEPA, adds **affinity self-distillation**: teacher/student pairwise affinity distributions are matched with KL divergence, providing direct JEPA-family prior art for relational consistency.
- Feature-suppression work (Robinson et al. 2021; Zhang et al. 2024 MCL) shows that SSL can settle on dominant/easy features while suppressing finer information; feature-aware negative sampling inside already-learned clusters is one demonstrated mitigation.

These references justify pursuing relational latent objectives, but none pre-qualifies the exact biology-specific objective required here.

## Mandatory TD57 continuity gate

Before learned teacher geometry may become scientific supervision, it must pass a **TD56-on-latents** continuity test.

For a frozen checkpoint/teacher state and each source independently:

1. Construct the exact TD56 disjoint X/Y gene views or a prospectively frozen successor preserving:
   - disjoint common-scalar gene sets;
   - no labels;
   - donor×operator blocking;
   - matched depth/detection wrong-cell nulls.
2. Encode the same cell under X-only and Y-only lawful views using the learned teacher.
3. Compute cell-cell geometry from the learned embeddings separately for X and Y.
4. Use donor-primary correlation/recurrence and the matched Y-cell null exactly analogously to TD56.
5. Require survival in HVS -> NPH52 -> SEA_AD under a prospectively frozen terminal.

If learned embedding geometry fails this test, it is **not** a lawful successor to TD56 even if its training loss, variance, covariance, or downstream clustering look strong.

This gate prevents silently replacing the qualified concordance object with an unrelated learned manifold.

## VICReg/SIGReg are anti-collapse, not fine-structure guarantees

Variance/covariance or distributional regularization can prevent constant or low-rank collapse. They do **not** establish that the representation preserves fine within-neighborhood biological variation.

A coarse cell-class/type geometry can:
- have large variance;
- have high effective rank;
- satisfy covariance/distributional regularization;
- make teacher/student relational loss small;
while still discarding the cell-specific structure required by this project.

Therefore anti-collapse and fine-structure preservation are separate requirements.

## Fine-neighborhood requirement must contribute gradient

The previous note placed the fine-neighborhood wrong-cell construction primarily as an acceptance gate. That is insufficient.

TD57 training must preferentially obtain relational gradient from regions where coarse geometry is least informative.

### Preferred primary mechanism: local relational matching

Do **not** automatically treat nearby teacher cells as arbitrary negatives or force them apart.

Instead, for each anchor cell i:

1. define a prospectively frozen teacher-local candidate neighborhood within lawful donor/block constraints;
2. sample pairs/triples preferentially from that neighborhood using a deterministic rule;
3. match the teacher's **fine local distance/affinity/angle structure** within that neighborhood.

This means near states remain near if the teacher says they are near; the student is required to reproduce the distinctions *among* nearby states rather than win using easy cross-type separation.

Candidate relational forms to compare prospectively before outcome:
- normalized local pair distances;
- teacher/student local affinity distributions with KL divergence (UniSurg-style);
- local triplet angles;
- local rank/neighborhood ordering.

The exact form, temperature/normalization, neighborhood construction, and weights must be frozen before any conclusion-bearing run.

### Secondary candidate: coarse-component residual geometry

An alternative is to remove prospectively specified dominant teacher relational components and match residual geometry.

This is more fragile because:
- component count becomes a target hyperparameter;
- eigenspaces can rotate or become unstable;
- source-specific coarse modes may differ.

It should therefore be a secondary falsification candidate unless the local-relational mechanism fails for a clearly diagnosed reason.

## Training loss and acceptance null must test the same scientific object

The optimizer must be pushed toward the property used for acceptance.

A TD57 success cannot be:

- low global relational loss;
- healthy variance/effective rank;
- followed by failure against a fine-neighborhood wrong-cell null.

The training objective must contain a local/fine relational term whose semantics match the acceptance attack.

The acceptance attack remains distinct and held out:
- replace the correct student's partial-evidence cell with a depth/detection/operator-matched cell drawn from the frozen teacher-local neighborhood;
- keep the target teacher geometry fixed;
- require the correct-cell student geometry to beat this fine-matched alternative donor-wise.

Training-time local sampling and evaluation-time wrong-cell substitution must use separately frozen deterministic seeds/partitions to avoid circularity.

## Protocol qualification vs checkpoint qualification

Two authorities must remain distinct.

### Protocol qualification
Authorizes a deterministic procedure:
- architecture/mechanics identity;
- evidence/masking schedule;
- EMA update rule;
- relational loss;
- local-mining/sampling rule;
- anti-collapse regularizer;
- donor/block batch construction;
- nulls and acceptance thresholds.

### Checkpoint qualification
Authorizes one resulting learned artifact only after it prospectively clears:
- learned X/Y disjoint-view continuity;
- donor-block recurrence;
- fine-neighborhood correct-cell superiority;
- collapse/spread/effective-rank diagnostics;
- evidence-ladder behavior;
- source replication.

A protocol-qualified training recipe does not make every checkpoint scientifically qualified.

## Relationship to teacher/student V3 mechanics branch

Do not modify the frozen V3 teacher/student mechanics package while TD57 is still being designed.

V3 remains the mechanical baseline. The final relational objective, if qualified, should later be integrated as a narrow successor layer while preserving:
- IPB encoder;
- weight-EMA teacher;
- optimizer/AMP repairs;
- gradient and Adam-moment gates;
- EMA chronology;
- checkpoint/RNG/source authority;
- population firewalls.

No u1 training is authorized by this note.

## TD57 design terminal

Before execution, TD57 must freeze at minimum:

1. learned representation used for geometry;
2. global vs local relational terms;
3. exact teacher-local neighborhood rule;
4. deterministic pair/triple/affinity sampling;
5. anti-collapse regularizer and diagnostics;
6. evidence-level schedule;
7. donor×operator/block batch geometry;
8. TD56-on-latents continuity test;
9. ordinary matched wrong-cell null;
10. fine-neighborhood wrong-cell null;
11. protocol-vs-checkpoint acceptance distinction.

Only after those are prospectively specified may a bounded 50k falsification run be considered.
