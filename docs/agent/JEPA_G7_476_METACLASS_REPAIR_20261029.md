# G7 E3 #476 metaclass exact-type repair — October 29, 2026

**Scope:** narrow fixture mechanics, NOT G7 physical source qualification or V3 composition acceptance.

- Original PR #476 exact head: `26031df25b51087f2f3ec35a88eef2919d794c68`.
- Independent original Macha #482 review exact head: `58baa4f912c791866c1aae31eab797da9dca588a`.
- Macha reviewer test file unchanged: Git blob `fd98636f85967226af1605c376522865167c8706`.

Repaired `scripts/v5/td_real_g7_content_enforcement_v1.py` uses explicit `type(value) is ...` identity dispatch instead of type tuple membership in `_strict_json`, `_required_sources`, and the displacement scalar gate. Hostile metaclass `__eq__` methods must not run during the binder snapshot, content validation or fixture binding derivation. The original #482 suite executes byte-identically on Linux and Windows. Earlier physical R1/R1D/R2 hostile tests remain independently RED, not edited or reclassified.

## Explicit residual flaws / separation of concerns

- **Composition blocker:** the existing `adjudicate_g7_terminal_v3` may still be called directly without a binder-validated decision receipt; Macha #482's `test_characterize_v3_still_decides_pass_on_rows_the_binder_refuses` intentionally proves that weakness. This metaclass patch does **not** close it. A versioned composed `bind → immutable snapshot → decide` interface is a separate task, and must preserve the V3 decision law.
- **Physical issuer blockers:** R1 physical measurement identity, R1D donor/specimen independence, R2 normalization provenance remain RED; no source issuer is constructed here.
- **Authority:** fixture-only bytes and self-consistency cannot authorize human use, target selection, or JEPA training.

Do not promote based on author-CI alone. Independent reviewer should explicitly re-run the untouched Macha #482 tests, probe Unicode/numeric normalization and exception leakage at the exact source head, and audit eventual composed path.

**Standing state:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
