# G4 — pathology-blind signal-preservation gate: design

Date: 2026-09-20
Status: **design only. No functional selected, no tolerance frozen, no rung
opened.** No terminal masking outcome, D_shared, pathology, DEV or SEALED data
was consulted.

G5 is blocked on this item, so this is the critical path. What follows specifies
what a G4 functional has to satisfy and what can lawfully be built now — it does
not pick one.

---

## 1. The question G4 must answer

Masking deliberately destroys predictability. A gate that asks "did biological
signal survive?" therefore has to separate two things that live in the same
expression matrix:

* **signal masking is supposed to destroy** — local expression interpolation,
  the shortcut: recovering a held-out address from its co-expressed neighbours;
* **signal masking must preserve** — the cellular state the representation
  exists to carry.

If those cannot be told apart, then a masking policy that passes the shortcut
test is indistinguishable from one that has lobotomised the representation. That
is the actual failure G4 exists to prevent, and it is why "the shortcut score
went down" is not by itself good news.

## 2. Hard constraints

**C1 — pathology-blind.** No AT8, no donor-level outcome, no protected variable.
Authorisation to read one outcome variable never extends to another, and a
functional calibrated on pathology would disqualify the confirmation set for
every later use.

**C2 — intervention, not association.** The gate must ask whether changing only
the measurement process for the *same cell* changes the biological conclusion —
not whether the representation is statistically independent of technical
covariates. The independence formulation is biologically wrong: genuinely
activated or injured states really do alter transcript complexity and detected
gene count, so demanding independence rejects true signal.

**C3 — unconditional.** Every attempted unit in the denominator. Cells whose
score is undefined, donors with non-estimable composition, failed fits: none may
vanish into "conditional on successful evaluation."

**C4 — correct sample size.** Cells sharpen the *measurement* of the donor
representation. They are not replicates of any donor-level quantity. Any
donor-level limb of the gate has n = 104, regardless of the 4,553,407 cells.

**C5 — bounded.** A relative tolerance is only meaningful on a metric bounded in
the rewarded direction. An unbounded score invites passing by inflation.

**C6 — paired.** Masked and reference arms evaluated on the same cells, the same
folds, and common random numbers, so the contrast is a difference and not a
comparison of two noisy absolutes.

**C7 — geometry-derived.** Any scale-sensitive parameter derives from the real
dataset geometry (104 donors, 17,186 strict common-core addresses, the observed
per-donor row distribution), not from a hard-coded constant.

**C8 — frozen prospectively, with a justification or an explicit label.**
Declaring a number in advance does not make it authoritative. Each constant
needs an external rationale, or it carries a label saying it has none.

## 3. Why one limb is not enough

A single-limb gate fails in one direction or the other.

*Content alone* ("the representation still predicts annotated cell state") can
be satisfied by a representation that has simply retained the shortcut — cell
type is partly recoverable from exactly the local co-expression masking is meant
to suppress.

*Stability alone* ("the representation is unchanged under measurement
intervention") is satisfied perfectly by a **constant** representation. Maximal
invariance, zero information. The existing same-cell thinning machinery measures
this limb and cannot, alone, carry the gate.

So G4 must be **conjunctive**: the representation must still carry biological
state information, **and** that information must be stable under same-cell
measurement intervention. Neither limb substitutes for the other.

## 4. Candidate content functionals (none selected)

All are pathology-blind; all use annotation or structure already present in the
Level-4 package or from an external source.

| candidate | what S measures | bounded? | main risk |
|---|---|---|---|
| **A. Annotated cell-state recovery** | donor-held-out balanced accuracy recovering annotated subclass from the representation | yes, [0,1] | cell-type identity is the *easiest* biological signal and is partly co-expression-recoverable; passing is weak evidence |
| **B. External program coherence** | coherence of a frozen, externally defined gene program, scored on addresses outside the masked set | needs explicit normalisation | depends on a genuinely independent external program list |
| **C. Donor state-composition recovery** | agreement between representation-derived and annotation-derived per-donor state composition, n = 104 | yes, if a bounded divergence is used | closest to what the JEPA exists to produce; lowest cell-level resolution |
| **D. Within-donor heterogeneity structure** | preservation of the rank structure of cell-cell relationships within a donor | yes, rank-based | most sensitive to the shortcut; hardest to argue is not circular |

**C is the most defensible target** because it is the quantity the pipeline
actually exists to produce — cells improving the measurement of a 104-donor
representation — and because its sample size is honest by construction. **A is
the most tractable** and is the natural first null-fixture subject. Neither is
selected here.

## 5. The discrimination requirement — the part that makes G4 real

A candidate S is useless unless it can tell the two signals apart. So before any
S is frozen, it must be run on controlled fixtures and shown to behave
correctly in **all three** of these conditions:

| fixture | construction | required behaviour of S |
|---|---|---|
| **F-null** | biological state structure removed, shortcut structure retained | S **must fall** — otherwise S is reading the shortcut, not biology |
| **F-shortcut-only** | shortcut structure removed, biological state retained | S **must not fall materially** — otherwise S punishes exactly what masking is for, and no policy can ever pass |
| **F-both** | both retained (as-built) | S at its reference level |

A functional that fails F-null is measuring the shortcut. One that fails
F-shortcut-only makes the whole masking programme unpassable. Only a functional
that separates them can carry the gate — and this is checkable **now**, on
synthetic fixtures, with no terminal outcome opened.

The fixtures must match the real geometry — the real n, dimensionality, marginal
shapes, dependence structure and missingness — or the discrimination result will
not transfer. A fixture that is easier than the data proves nothing about the
data.

## 6. What G5 needs back from G4

G5's biological-consequence basis requires

```
δ = max { r : |S(model | residual = r) − S(model | residual = 0)| < ε_bio }
```

so G4 must deliver three things, not one:

1. a frozen S satisfying §2 and §5;
2. a **characterised relation** between residual shortcut magnitude and S —
   monotone, or with its non-monotonicity described;
3. **ε_bio in S's own units**, with its own justification.

Point 3 is where the arbitrariness can quietly reappear one level up. If ε_bio
is picked to make a preferred outcome pass, nothing has been gained over picking
δ directly — the unjustified constant has only been moved. ε_bio needs an
argument in S's units that would survive being stated on its own.

## 7. Lawful work available now

In dependency order, none of it requiring a terminal outcome:

1. Build F-null, F-shortcut-only and F-both at real FULL104 geometry.
2. Evaluate candidates A–D on those fixtures; report the discrimination table in
   §5 for each, unconditionally.
3. Discard every candidate that fails either direction. **Report the discards** —
   a functional that cannot separate the two signals is itself a finding.
4. For survivors, characterise S against a swept planted-residual magnitude to
   get the relation G5 needs.
5. Only then argue ε_bio, in S's units, in writing, before seeing any policy.

Step 3 is the one most likely to be skipped under time pressure, and it is the
one that makes the gate mean anything.

## 8. Status

```
G4_SIGNAL_PRESERVATION_FUNCTIONAL = NOT_SELECTED
G4_DISCRIMINATION_EVIDENCE        = NOT_YET_GATHERED
G5                                = BLOCKED_ON_G4
```

The requirements are now specific enough to be executed against, and the first
step is fixture construction, which is lawful preterminal work. Nothing is
frozen, no tolerance is chosen, and no candidate is endorsed.
