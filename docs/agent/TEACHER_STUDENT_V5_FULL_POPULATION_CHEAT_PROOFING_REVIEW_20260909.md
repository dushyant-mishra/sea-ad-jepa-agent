# Teacher/Student V5 full-population cheat-proofing review — 2026-09-09

Status: `PROSPECTIVE_CANDIDATE__NO_TRAINING_AUTHORITY`

This review integrates the T0 V20 failure lessons, the historical T1 mechanics failure, the real 50k shortcut audit, and the reader-fit 4,553,407-cell geometry into two pre-training corrections.

## External-review finding 1: population-equivalent is not full population coverage

The current frozen V5 horizon names exactly 4,553,407 base-cell presentations, equal to the number of reader-fit cells. Under the current with-replacement proposal that does **not** prove that every reader-fit cell is seen. A low-probability cell can receive zero presentations while another cell repeats.

That is inconsistent with the project requirement to build the framework around the full dataset rather than around a sampled surrogate.

Candidate repair: `full_population_coverage_schedule_v1.py`.

- every frozen stable cell key has multiplicity >= 1;
- small donor x operator groups are topped up only to a separately frozen coverage floor;
- repeats are spread deterministically over group members;
- a separately frozen per-cell repeat cap is enforced;
- realized proposal is q_i = multiplicity_i / total schedule presentations;
- target remains p_i = 1/(D * donor_cells);
- exact p/q makes repeats incapable of redefining donor-uniform scientific mass;
- hardware packing may reorder the frozen multiset but may not change identity, multiplicity or weight.

This candidate does **not** yet supersede `TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V3` or `PRESENTATION_HORIZON_AUTHORITY_V1`.

### Full 4,553,407-cell audit completed

Executable audit:

- `scripts/v5_anticheat/audit_full_population_coverage_conditioning_v1.py`
- `docs/agent/v5_anticheat/results/FULL_POPULATION_COVERAGE_CONDITIONING_AUDIT_V1.json`
- input metadata SHA-256 `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

The exact reader-fit geometry is 4,553,407 unique stable cell keys, 104 donors, 42 operators and 1,400 donor×operator groups.

A naive full pass plus only the minimum group top-up is **rejected** as a production schedule. It needs just 1,811 extra presentations and keeps max cell multiplicity at 16, but its importance ESS fraction is only `0.0968911` and its max/min importance-weight ratio is `2149.52x`.

More importantly, the full dataset proves a feasibility constraint. The smallest reader-fit donor has 81 cells and the largest has 174,111, so donor-uniform target per-cell probability varies by `2149.5185x`. Guaranteed full coverage gives every cell multiplicity at least 1. Under the currently frozen max multiplicity 32, **any** schedule has max/min p/q importance-weight ratio at least:

`2149.5185 / 32 = 67.1724537x`.

Therefore the existing `<=64x` ratio limit, max repeat cap 32, and guaranteed full-cell coverage are mathematically incompatible. No sampler, optimizer or GPU implementation can satisfy all three simultaneously. To make a 64x ratio ceiling even theoretically feasible while preserving full coverage requires cell cap at least 34.

A deterministic donor-balanced dataset-only calibration under group floor 16, cap 32 and ESS floor 0.50 found a candidate with:

- total presentations `5,271,158` = `1.15762944` reader-fit population equivalents;
- 717,751 extra presentations;
- ESS fraction `0.50092751`;
- max cell multiplicity 32;
- minimum donor×operator presentations 16;
- importance-weight ratio `67.1724537x`, exactly the dataset/cap lower bound;
- no pathology or outcome input.

This greedy candidate is not claimed globally optimal and is not training authority. Its value is that it proves a well-conditioned full-coverage schedule exists close to one population pass **if** the internally inconsistent 64x constraint is prospectively superseded.

Reviewer recommendation: preserve full unique-cell coverage, donor-uniform target mass, ESS >=0.50, group floor 16 and repeat cap 32; prospectively replace the old 64x ceiling with a dataset-feasibility rule whose floor is derived from donor-size geometry and the frozen repeat cap. Do not set the new ceiling from checkpoint behavior or from post-training outcomes.

## External-review finding 2: a single cell state can still learn acquisition identity

The encoder does not receive source, matrix or donor IDs directly. That is necessary but insufficient. Its cell state is computed from the measurement mask and expression. The real anti-cheat audit found support-only/mask-only source prediction at balanced accuracy 1.0 and depth/QC-only source prediction around 0.592 on the 50k real sample.

Therefore acquisition identity is available to the current single representation by construction.

Candidate repair: `representation_firewall_v1.py`.

- `z_bio` is the only representation allowed into base biological cell-state loss, future relational geometry, biological checkpoint selection and downstream biology readouts;
- `z_obs` is the lawful route for measurement mask/support/depth/uncertainty/operator descriptors;
- donor/source/matrix/operator/support fingerprint/pathology/protected labels are forbidden direct `z_bio` inputs;
- biological state requires a same-cell common-core anchor;
- operator-native evidence may help biology only by predicting that common-core-anchored `z_bio`, not by redefining the target from native support identity;
- same-cell support-family, mask, evidence-fraction and measurement-depth interventions are mandatory qualification views;
- gene/ledger reconstruction may use both `z_bio` and `z_obs`;
- blind source-adversarial erasure is not a default because source can be confounded with legitimate biology.

No invariance coefficient or anti-cheat numerical threshold is chosen here. Those remain prospective calibration authorities.

## Failure-mode integration

| Historical failure | Production invariant |
|---|---|
| loss decreased while 48 protected attention-routing tensors were dead | fp16 forward -> backward autocast disabled -> unscale -> exact 48-gradient gate -> proved optimizer step -> both Adam moments -> EMA |
| exact-zero gradients passed an old gate | exact-zero is a STOP; frozen 48-name registry defines completeness |
| torch-dependent tests skipped green | critical test skip count must be zero |
| support fingerprint identifies source | z_obs/z_bio routing plus same-cell support interventions; source probes remain mandatory |
| depth/QC predicts source | measurement-depth intervention/response curve is mandatory |
| mask identity can identify acquisition geometry | mask-only attack and keyed scientific view identity independent of update/device/microbatch |
| proposal can change scientific mass | exact p/q audit; target p remains donor-uniform |
| one population-equivalent can omit cells | coverage-first multiplicity audit over all 4,553,407 stable keys |
| stale support-geometry digest | all dataset-derived overlays must rederive and root-bind exact geometry before adoption |
| hardcoded role label caused Stage 3 STOP after access | typed/explicit role APIs; donor-set role digest before conclusion |
| raw-byte evidence broke under CRLF conversion | `-text` evidence paths plus committed-blob-versus-disk tests |
| frozen decision omitted sensitivity evidence fields | future checkpoint/qualification record must atomically include every gate **and its evidence**, not only a terminal |
| technology field absent | do not relabel source/matrix as technology; require separate observation-operator mapping authority |
| rare-tail measurement QC veto | measurement adequacy must gate rare-tail biology before disease interpretation |
| historical fixed-coordinate target search failed | initial V5 remains base JEPA; relational extension stays downstream of lawful teacher + TD60 + partial-evidence relation predictability |

## T0 result and V5

T0's `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL` is a downstream scientific fact, not a V5 optimization target. It must not be used to tune the foundation architecture, masking schedule, thresholds, checkpoint selection or hyperparameters after the fact. A future frozen evaluation may ask whether a qualified `z_bio` represents the broad immune-expression relationship.

The rare tail remains measurement-underdetermined and must not be promoted into a training target.

## Next required executable audits

1. **Completed:** full 4,553,407-cell coverage/conditioning audit. Next: external review and prospective supersession decision for the mathematically incompatible 64x conditioning ceiling versus repeat cap/full-coverage requirements.
2. Bind the common-core/native support candidate to the corrected operator-family geometry digest; do not use the stale V3 overlay digest.
3. Build the actual `z_bio`/`z_obs` model adapter and prove routing with source/mask/depth negative controls before optimizer authority.
4. Execute the real-data anti-cheat probes on held-out donor/matrix/source splits; technology remains not estimable until a lawful mapping exists.
5. Run the protected-gradient torch tests with zero skips and CUDA Gate-2/hardware-invariance qualification.
6. Only then freeze update geometry, EMA half-life, target-query budget and final trainer authority.

Local candidate self-check: initial coverage/firewall surface 10/10 PASS; full-population feasibility audit tests 6/6 PASS; py_compile PASS. No optimizer or pathology access.
