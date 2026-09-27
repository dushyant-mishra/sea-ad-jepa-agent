# JEPA R15 — concrete anti-cheat control-sensitivity repair

**Scope:** developmental research successor to Claude's `276a3e6e0282bf472584bc24ebb832ab7c63e73f`. Original GitHub implementation is unchanged. No protected outcomes or FULL104 training are touched. `TRAINING=OFF`.

## Source audit

Claude's `control_sensitivity_ledger_v1.py` did not require its healthy leg to return `QUIET`: healthy `REFUSED_DEGENERATE`, planted `FIRED`, degenerate `REFUSED_DEGENERATE` could be classified `SENSITIVE`. The classifier also did not validate that leg records really belonged to their named roles. `run_leg` used Python truthiness, allowing arbitrary nonempty strings or response objects to masquerade as successful assertions. Graph identity used `repr()`, which is representation-dependent; a distinct digest says nothing about whether an actual structural intervention is large enough to be informative. An interval spanning zero was handled by throwing `DegenerateConfiguration`, conflating insufficient evidence for a direction with failure of the experimental design.

These are software findings from direct inspection of `276a3e6e`; none is a claim that production training previously executed with an invalid record.

## Implemented in `control_sensitivity_ledger_v2.py`

- Exact three-leg truth table, explicit mismatched-leg, healthy-refusal, planted-refusal, false-positive, vacuous and degenerate-scoring verdicts; an empty ledger fails closed.
- Strict Python `bool` from controls: unrelated runtime exceptions propagate rather than counting as detected planted failures.
- Non-authorizing digest-bound ledger with fully reported leg outcomes.
- `effect_direction`: an interval including zero reports `INCONCLUSIVE`, not degenerate; strictly positive and strictly negative intervals remain separately identifiable; nonfinite/inverted intervals refuse.
- Canonical numeric-array digest includes shape, numeric type and dtype width, normalizes memory order and byte order, rejects empty/object/nonfinite arrays.
- Canonical directed weighted graph digest is invariant to edge-row order and sensitive to weights. Duplicate edges, missing identities and empty graphs refuse.
- A *separate* graph intervention strength gate requires meaningful changed-edge fraction and tests weighted-edge correlation over the explicit edge union. A changed hash alone is insufficient; too-small, constant, or otherwise uninformative comparisons refuse.

The graph-gate numerical defaults (`>=0.2` changed edges and `<=0.5` absolute weighted-edge correlation) are **research diagnostics only**; they do not supersede the frozen control-authority contract. The weighted correlation here is over the edge union, not an assertion that it reproduces the historical Stage73R matrix-based estimator.

## Tests

`python -m pytest -q test_control_sensitivity_ledger_v2.py`

**39 passed, zero failures or skips** in the local container. Tests cover truth-table states, leg spoofing, vacuity, unrelated exceptions, inconclusive confidence intervals, array endianness/strides/dtype/shape and generator-based graph iterators, identical graph structures under reordered edges, graph weights and topology, and informative versus trivially different graph interventions.

`python run_r15_mutation_tests.py`

**6/6 hostile mutations detected** by genuinely failing tests: accept healthy refusal; accept wrong leg labels; turn inconclusive intervals into negative findings; ignore graph edge weights; accept a changed hash without sufficient topology change; count arbitrary `RuntimeError` as a planted-control success.

The original version of the new strong-intervention graph fixture **failed** its structural-correlation test despite 100% edge change. That exposed a confounding property of the positive fixture (mutually exclusive positively weighted edge supports can still show strong negative correlation). We repaired the fixture using a genuine signed, disjoint structural alternative without relaxing any threshold. Preserve this initial failure history.

## Not yet established — blockers to production adoption
**Important provenance limit:** the R15 ledger still accepts caller-created `LegResult` objects. A forged caller could assert `FIRED` without running a control. Production use requires execution-attested, source-bound receipts (for example a pinned runner/JUnit chain); this local repair closes the logical false-green, not that separate V39/V40 physical provenance boundary.


1. This is a *successor research module*, not a drop-in semantic overwrite of V1; preserve V1 for provenance and explicitly bind V2 to a new versioned authority if approved.
2. It has **not** run against the source-authenticated current V5 optimizer/EMA harness. The inherited actual-harness planted-gradient tests must be independently rerun with refusal reason assertions and pre/post optimizer, EMA, Adam-moment and cursor byte comparisons.
3. It has **not** proved that historical Stage73R graph controls satisfy the prospective edge-union correlation rule. Historical Stage73R already has its own structural-integrity receipt and `NO_QUALIFIED_GRAPH_ADVANTAGE` conclusion. Do not reinterpret it through the new exploratory rule.
4. It has **not** proven raw-q invariance of the actual V5 reader/tokenizer. Claude's synthetic `Q_INTERVENTION_FULL_PIPELINE_V1.json` at `276a3e6e` remains a synthetic diagnostic; the production reader intervention is separate work.
5. New external biological evaluation has not executed and no teacher-target construction is scientifically selected.

**Next execution:** apply and source-bind the repaired ledger as a versioned developmental successor; run actual V5 harness negative-control state snapshots and the raw-q intervention through actual FULL104 reader, tokenizer and QC paths on permitted developmental data; only then proceed to a source-authenticated neural smoke test under existing restrictions.
