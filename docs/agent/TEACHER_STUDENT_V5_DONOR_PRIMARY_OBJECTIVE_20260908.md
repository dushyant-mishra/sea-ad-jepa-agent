# Teacher/Student V5 donor-primary scientific objective — repaired V2

Status: **scientific target frozen by `TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2`; proposal schedule execution and training remain unfrozen/unauthorized**.

## Base JEPA target — reaffirmed

The full reader-fit population contains 4,553,407 cells but only 104 donors. Raw cell counts differ by orders of magnitude across donors and sources, while the qualified target-discovery result is donor-recurrent. Base JEPA therefore retains:

`L_base = mean_donor(mean_cell_within_donor(mean_view(block_JEPA_loss)))`.

Policy: `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`.

This gives each donor equal scientific mass while retaining the empirical cell distribution inside that donor. Source does not receive equal mass by fiat. Operator/matrix does not set base scientific mass.

## Why relational V1 weighting was superseded

The data-first audit showed that `operator` is not a common cross-source scientific axis:
- HVS reader-fit operators are native-class-pure matrices;
- NPH52 reader-fit operators are native-class-pure Astro/Endo/ExN/InN/MG/OPC/Oligo matrices;
- SEA_AD operators are multi-class matrices containing 17–26 native classes each.

Therefore `mean_operator_group(...)` would mean equal cell-class mass in HVS/NPH52 but equal matrix/region mass in SEA_AD. That source-dependent interpretation was not established by TD57B/TD59. On the full reader-fit data, equal operator-group weighting can upweight a tiny eligible group by as much as ~141.07x relative to its eligible-cell prevalence inside the donor.

V1 is retained as superseded planning history; it is not current authority.

## Relational target — repaired V2

Operator remains valuable as a **same-support/comparison admissibility boundary**, but not as automatically equal scientific mass.

The production-candidate relational target is now:

`L_rel = mean_donor(mean_eligible_anchor_cell_within_donor(mean_unordered_comparator_pair_within_anchor_operator(scale_free_order_loss)))`.

Policy: `DONOR_UNIFORM__ELIGIBLE_ANCHOR_CELL_UNIFORM__SAME_OPERATOR_COMPARATOR_PAIR_UNIFORM_V2`.

Equivalent group statement: within a donor, an eligible operator group receives mass proportional to its number of eligible anchor cells, `n_group / sum_eligible n_group`; inside the group, anchored triplets are uniform. Thus:
- donor cell count does not set donor mass;
- operator identity constrains which cells may be compared but does not receive equal mass;
- O(n^3) triplet capacity never sets scientific mass;
- group mass grows only linearly with eligible anchor-cell prevalence;
- groups with <3 cells are relationally not estimable, while 99.998704% of all reader-fit cells and at least 99.8436% of every donor's cells remain in estimable groups.

## Qualification boundary

TD57B/TD59/TD60 are unchanged. TD57B and TD59 sampled at most 64 triplets per donor×operator stratum and pooled resolved triplets inside donor for their prospective falsification statistics. That historical cap is preserved exactly for qualification and is **not promoted into a production scientific group weight**.

TD60 continues to use its exact frozen TD57B/TD59 triplets. V2 changes no target-discovery outcome.

## Proposal boundary

Proposal `q` remains separate from target `p`.
- Base proposal remains numerically unfrozen; exact `p/q` correction is mandatory whenever `q != p`.
- Operator/group balancing may be used as a *coverage proposal* without redefining the target.
- Relational V2 can sample `q=p` directly via donor-uniform -> group proportional to eligible cells -> uniform anchored triplet within selected group.

No finite triplet budget, visible-gene dose, block size, token budget, presentation horizon, EMA half-life, GPU kernel, training, successor-u0 materialization, or TD60 execution is authorized here.
