# JEPA V2 private pair-coherence preflight / G7 source boundary — 2026-10-29

**Classification:** `FIXTURE_PAIR_MECHANICS_ONLY__NO_G7_V2_AUTHORITY__NO_TRAINING`.

Base: draft PR #502 `0789247cdbbdfca671613b020865aba958dfd699`. This branch is independent from Macha's upstream #474 A4 assignment and from a later tests-only Macha adversarial review of #502. Only a **new module, new tests, CI and this document** are changed; neither the V2 producer/consumer code nor original Macha #481 tests are edited.

## Exact responsibility

`validate_private_v2_pair_coherence(student_view=..., teacher_view=...)`:

1. Private execution actor snapshots both published V2 bound-content views as exact built-in JSON trees before comparisons and validates both against the same process-local, cooperative rights registry.
2. Requires the **student base-rights role** and **teacher richer-rights role**, identical frozen query, address/right roster and base rights, and a teacher-rights selection covering the full source-mapped roster.
3. Requires equal cell/address coverage and row identity (source, donor, operator, address, evidence right). Previously visible student base measured values **and D1 covariate** must be byte-value equal in the teacher view. A student-withheld scalar must become a measured scalar in the fully enriched teacher view; structural-unmeasured and collision-unresolved states must not be recoded.
4. Returns a constant fixture-only yes/no receipt with explicit false attestation and authorization flags. Returns **neither teacher nor student digest**, query count, row count, per-cell values or teacher data, avoiding a new small-domain teacher commitment in student-visible bytes.
5. **Does not certify the two views were produced from the same physical source.** A deliberate positive counterexample uses student and teacher views from distinct synthetic worlds with different q counts: both views and pair receipt are coherent, while source identity remains false. This cannot be fixed without an independent off-view issuer/custody contract.

## Physical G7 V1 incompatibility — do not conflate

The original `q_excluded_depth_v1.py` returns V1-named `library_size` in `g7_atoms` even though its quantity is **base-rights-normalization depth**, not a physical whole-library total. Higher-rights teacher counts can legitimately exceed D1; the current G7 E3 V1 atom validator enforces a physical `count <= library_size` law.

**Do not convert V2 `base_rights_normalization_depth` into G7 V1 `library_size` or issue a V1 content PASS from this pair gate.** A separate, versioned, independently reviewed G7 E3 V2 content law needs external physical-unit and rights evidence, trustworthy donor/specimen mapping, a calibrated reference/known-truth issuer and the mandatory E3→V3 composed path (draft #500). Neither the producer's cell ID, donor ID, SHA nor the pair's coherent rows authenticates those facts.

## Still blocked

- **A4:** zero-base refusals leak hidden query mass in upstream #474; owned by Macha, independently RED.
- **R1/R1D:** unique physical measurement and donor-vs-specimen identity not proven by row labels.
- **R2:** source-feature alias closure, off-ledger counts, q-dependent QC/selection, physical vs D1 depth not independently attested.
- **D2:** source residual depth OFF, and physical G7 V1 `library_size` semantics unchanged.
- **Issuer:** cooperative process-local `_VIEW_BINDINGS` is not external/durable and is mutable by hostile code in the same interpreter.
- **Biology:** no candidate-neutral Task4 generator, hidden-truth benchmark or real target qualification.

**Standing state:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
