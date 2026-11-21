# Post-TD five-RED scoped code repair — November 2, 2026

**State:** GPT-authored repair candidate, exact source `064bf2a23e0063c26072988d83626a5e24542878` on [PR #525](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/525). **Macha independent review PENDING.** No real training/target/Stage4 promotion. Original #351 `2abcb9fe156eac340ff12adff9426ed38d929e3e` and #517 `0bf0de060e6cb13496fb95e193deb63591258ceb` remain immutable.

## Exact work done

Changed **one existing source module** `scripts/v5/jepa_post_td_harness_contract_v1.py`, plus one test file and one GitHub Actions workflow. PR base is #351 branch, since this historical post-TD module does not exist on current flat main. **Do not merge stacked historical ancestry.**

1. Matched-compute comparator now refuses nonfinite, negative or non-comparable budget/FLOP/count values, boolean count aliases, and infinite/NaN/invalid tolerances. The old NaN `> tolerance` bypass is removed.
2. Synthetic preflight snapshots complete portfolio and architecture plan JSON before use, recomputes the SHA for each original content payload (excluding the declared digest field), and enforces explicit false authority fields and placeholder-only semantics. A consistent SHA-256 is **not an external signature or evidence-rights issuer**, and no real training permitted.
3. Teacher-evidence constructor requires exact nonnegative integer gene addresses, without coercing `True`, `1.0` or `"1"` into molecular address 1. Preserves lawful q-blind exclusion.
4. The five reviewer assertions from #517 were reused as **ordinary passing regression checks** in a new file; original #517 deliberately expected-RED test file and its original CI remain unchanged. Additional hostile tests cover recomputed-but-forbidden authority flags, tampered output semantics, invalid numerical domains and aliasing.

## Exact-head qualification

- Original inherited post-TD harness [41576266854](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41576266854): SUCCESS.
- Original C4/C6 [41576266905](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41576266905): SUCCESS.
- New original-five-plus-extended review tests [41576266869](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41576266869): Python **3.11 and 3.12 both SUCCESS**. All three workflows success at head `064bf2a23e0063c26072988d83626a5e24542878`.
- Earlier candidate head `227b0a2b45db08ac40619c44416a88879e140579` failed only inherited test's precise text expectation `"not bound"` for a now correctly rejected corrupted plan, **not behavior**; minimal error wording repair `064bf2a` preserved inherited test unchanged, reran all workflows green. Original failing CI [41576171596](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41576171596) is retained as evidence.

## Required next gates

- **Macha independent code review**, explicitly with hostile numerics, SHA/JSON self-rehash and authority-off checks, original RED conservation, valid-q control and no-trainer claim. [Review request on #525](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/525#issuecomment-6595206216).
- Only after acceptance, selective flat-main source/test/workflow landing. No bulk historical merge or self-review. 
- Separate source-rights external issuer (#513), cumulative Unified Task4 qualification (#465 limited acceptance), and real source→existing CaseBundle integration remain untouched and mandatory before biological claims.

**Authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
