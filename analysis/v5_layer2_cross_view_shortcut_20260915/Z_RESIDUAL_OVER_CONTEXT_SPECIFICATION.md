# PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE — mathematical specification only

Status: **SPECIFICATION ONLY. NOT IMPLEMENTED. NOT AUTHORIZED FOR THE REAL TRAINER.**
Blocked on `CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED` and
`PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`. `TRAINING_OFF` remains in force.

## 1. Objects

For cell *i* with disjoint molecular views `V0_i`, `V1_i`:

- `T_i` — the complete teacher target. **Not yet defined**: V5 teacher states do not exist
  and target authority is not frozen. Every expression below is written against `T_i` as a
  placeholder and must not be instantiated with historical V4 semantics.
- `C_i` — the permissible context covariate vector: source indicator, operator indicator,
  and the measured QC family (`Q_DEPTH`, `Q_DETECT`) with whatever lawful transforms are
  declared. Context is **observed metadata**, never derived from the target.
- `g_φ(C_i)` — the context baseline model.
- `f_θ(V0_i)` — the molecular pathway.

## 2. Construction

    baseline_i        = g_φ(C_i)
    increment_i       = f_θ(V0_i)
    prediction_i      = stop_gradient(baseline_i) + increment_i
    loss              = L( prediction_i , T_i )

with `L` the complete objective loss against the **full, unmodified** target.

Three properties are load-bearing and must all hold:

1. **The baseline is frozen.** `stop_gradient` on `baseline_i` means no gradient reaches
   `φ` through the joint loss. `g_φ` is fitted separately, on training folds only, and held
   fixed thereafter. If gradient leaks into the baseline, the construction degenerates into
   an ordinary joint model and provides no anti-shortcut guarantee.
2. **Nothing is subtracted from the input or the target.** `V0_i`, `V1_i` and `T_i` enter
   unmodified. Operator and source means are never removed from the molecular data. This is
   the whole point of preferring this construction over residualization: the representation
   is left intact, and only the *credit assignment* changes.
3. **The loss is against the complete target**, not against a residual target. Writing
   `L(increment_i, T_i − baseline_i)` is algebraically similar under squared error but is a
   different object under any other loss and under normalization, and it invites the target
   to be quietly redefined. Use the form above.

## 3. What it is claimed to do

Because the context baseline is supplied for free, the molecular pathway receives gradient
only for structure the context cannot already produce. Information that is collinear with
source, operator and measured QC yields no loss reduction attributable to `f_θ`, so the
molecular pathway is not rewarded for rediscovering batch identity.

## 4. What it does NOT do

- It does **not** remove batch structure from the representation.
- It does **not** establish that the remaining increment is biological. The correct label is
  `PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`. Unmeasured technical state that
  is not captured by `C_i` remains a live alternative explanation, and
  `BATCH_TECHNICAL_VS_BIOLOGICAL_DECOMPOSITION_NOT_IDENTIFIABLE_IN_FULL104` still stands.
- It does **not** address donor-level generalization. A model may fit within-donor structure
  that fails to transfer to unseen donors; the LODO evidence shows this is a real failure
  mode in HVS and NPH52.

## 5. The quantity already measured

The *statistical* content of this construction — the increment of molecular information over
the strongest lawful context baseline — has already been estimated on the frozen
reconnaissance substrate at a linear model class, and is reported in the Layer-2 closeout:

| view | molecular increment over context |
|---|---|
| unweighted reconnaissance | +0.0311 |
| empirical / FULL104 structure | +0.1207 |
| source-uniform | +0.0287 |
| donor-primary | +0.0323 |

What implementation would additionally answer — and what cannot be answered with training
off — is whether presenting the baseline as a frozen additive term **changes what the
molecular pathway learns**. That is the only reason to build it, and it requires training.

## 6. Preconditions before any implementation

1. V5 teacher target semantics frozen and the authority established.
2. Primary representation authority frozen.
3. The context family `C_i` declared prospectively, including whether operator identity is
   admissible as a training-time input at all.
4. A prospective statement of what increment magnitude would count as evidence — derived
   from design, not chosen after seeing the number.
5. Anti-cheat gates for the construction itself, since a frozen baseline introduces its own
   failure mode: if `g_φ` is overfit on the training folds, the increment is understated.
