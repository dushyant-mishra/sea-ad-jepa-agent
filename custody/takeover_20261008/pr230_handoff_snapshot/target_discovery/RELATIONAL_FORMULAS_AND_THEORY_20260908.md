# Relational Target Discovery — formulas, theory, and current scientific interpretation

Date: 2026-09-08
Status: `HANDOFF_REFERENCE__NO_TRAINING_AUTHORITY`

## Core conceptual reframe

The project no longer assumes that Foundation JEPA must discover a fixed biological target tensor before training.

The surviving object class is relational:
- representation coordinates may be emergent;
- the auditable authority can be the protocol that determines which geometry is preserved;
- protocol qualification and checkpoint qualification remain separate.

TD56/TD57B support this reframe. TD57C limits how aggressively the geometry may be localized on the 50k pilot.

## Observation semantics

Never collapse:
- measured scalar zero;
- structurally unmeasured;
- collision/unresolved measurement.

Physical measurement availability and biological-evidence uncertainty remain distinct.

## Tie-aware pair-order coordinate

For cell i and Molecular Ledger addresses g,h:

`s_i(g,h) = sign(x_ig - x_ih) in {-1,0,+1}`.

The zero state is unresolved/tied for that pair at the current measurement, not automatically a biological equality claim.

## Concordance distance

For cells a,b and a fixed pair-coordinate set P:

`I_p(a,b) = 1` iff at least one of `s_a(p), s_b(p)` is nonzero.

Require a prospectively frozen minimum number of informative coordinates.

Then:

`d(a,b) = [sum_p I_p(a,b) * |s_a(p)-s_b(p)|] / [2 * sum_p I_p(a,b)]`.

Therefore `d in [0,1]`.

This is the TD56/TD57B/TD57C relational ruler.

## Scale-free anchored relation

For anchor i and comparison cells j,k:

`q(i;j,k) = sign(d(i,j)-d(i,k))`.

If either distance is not measurable or the distances tie exactly, q is unresolved.

q is invariant to any strictly monotone transform of the distance scale. This is why TD57B demonstrates that absolute numerical distance-scale equivalence across HVS/NPH52/SEA_AD is not required for the recurrent relational object.

## Donor statistic

For a donor, pool eligible relations across lawful operator strata and require the frozen minimum number of resolved relations.

`A_d = mean[ q_X(i;j,k) == q_Y(i;j,k) ]`.

The donor, not the cell/triplet, is the primary inference unit.

Source/block statistics use medians across donor statistics.

## Matched wrong-cell null

X identities remain fixed.

Y identities are reassigned only inside donor×operator depth/detection-matched blocks using deterministic nonzero cyclic shifts.

Critically:
- the base relation set is earned by X only;
- observed Y and every permuted Y null independently earn Y measurability/non-tie;
- conditioning a null on observed-Y measurability is forbidden.

For 64 nulls:
`null_p95 = sorted(null_values)[60]`.

## TD56 theory

Two disjoint 512-gene views, each represented by 2,048 deterministic pair-order coordinates, recover strongly concordant within-donor cell-cell geometry in HVS, NPH52, and SEA_AD.

This establishes redundant molecular encoding of relational biological state without:
- labels;
- universal latent-axis matching;
- hidden-gene scalar reconstruction;
- clustering;
- CCA/PCA axis transfer.

## TD57B theory

TD57B tests ordering of TD56-style distances rather than raw distance correlation.

Two additional independent disjoint gene panels survive:
- 2 panels;
- 3 sources;
- 2 donor splits;
- 2 halves/split;
- 24/24 cases.

Thus the relational object is donor-recurrent and scale-free on the 50k falsification archive.

## TD57C theory and limitation

TD57C used a third disjoint view Z to select exactly the nearest one-third of measurable neighbors, then required independent X and Y views to reproduce distance ordering inside that Z-selected local region.

This is deliberately non-self-referential:
- Z selects locality;
- X/Y are tested;
- Z never defines the tested relation.

HVS Panel 0 failed 2/4 donor halves.

Post-failure diagnostic using the exact same X/Y genes/pairs but no Z localization passed 4/4.

Therefore:
- the molecular panel is not the problem;
- unrestricted/mesoscale relational order remains;
- aggressive nearest-third localization is not broadly recurrent enough in HVS under the pilot design.

Do not rescue TD57C by changing one-third to one-half on the same opened outcome.

## Implication for relational JEPA

A learned EMA-teacher relational objective remains plausible, but the following are distinct gates:

1. **fixed molecular geometry exists** — TD56 PASS;
2. **distance ordering is donor-recurrent and scale-free** — TD57B PASS;
3. **deep nearest-third local geometry is recurrent** — TD57C FAIL;
4. **learned teacher latent geometry inherits disjoint-view continuity** — not yet tested;
5. **partial-evidence student reproduces teacher geometry beyond matched nulls** — not yet tested;
6. **checkpoint retains fine biology rather than only coarse structure** — not yet tested.

## Candidate learned relational loss family

The teacher/student V3 prospective extension currently defines a non-active global within-group loss using direct 160-D `cell_state`:

1. center teacher and student states within donor×operator group;
2. compute teacher Euclidean pair distances;
3. scale both teacher/student distances by the same teacher median positive distance;
4. compute centered-state cosine similarity;
5. Smooth-L1 each relation;
6. total:
   `L_rel = 0.5 L_distance + 0.5 L_angle`.

This is mechanics prior art only, not Target Discovery authority.

## Anti-collapse vs fine-structure

Variance/spread/effective-rank controls prevent degenerate collapse, but they do not prove fine biological structure.

A coarse cell-class representation can remain:
- high variance;
- full rank;
- decorrelated;
while suppressing fine donor-local information.

Therefore:
- collapse prevention is necessary;
- fine-structure qualification is separate;
- TD57C shows that forcing the gradient entirely into the nearest-third region is not currently justified.

## Hard-negative caution

Do not automatically push teacher-neighbor cells apart as generic negatives.

Biological neighboring states may be genuinely continuous.

If a future local/mesoscale term is used, it should reproduce teacher relations among nearby cells rather than assume every nearby cell is a negative.

## Learned-geometry continuity gate

Before learned EMA-teacher geometry may inherit TD56 authority:

1. freeze a checkpoint/state;
2. encode the same cells under disjoint X-only and Y-only lawful gene views;
3. compute latent cell-cell geometry separately;
4. perform donor-primary recurrence and matched Y-cell nulls;
5. require source replication.

If learned latent geometry fails, successful optimization is not enough.

## Protocol vs checkpoint authority

Protocol authority freezes:
- inputs/evidence law;
- batch/block law;
- EMA;
- relational equations;
- nulls;
- anti-collapse rules;
- acceptance criteria.

Checkpoint authority separately requires the resulting learned artifact to clear:
- disjoint-view latent continuity;
- donor recurrence;
- evidence response;
- matched wrong-cell attacks;
- spread/collapse diagnostics;
- source replication.

## Current scientific frontier

Supported:
- global/mesoscale relational concordance geometry;
- scale-free donor-recurrent ordering.

Not supported:
- a universal per-cell fixed coordinate target;
- nearest-third local mining as primary objective;
- arbitrary learned teacher geometry without continuity testing.

Next work should prospectively characterize a locality/mesoscale frontier or qualify a global+mesoscale relational objective without choosing the winning scale post hoc.
