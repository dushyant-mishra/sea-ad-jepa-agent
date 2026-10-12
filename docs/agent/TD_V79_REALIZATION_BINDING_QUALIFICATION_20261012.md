# TD × V79 realized-world binding qualification — 2026-10-12

Status: `PASS_TD_V79_REALIZATION_BINDING_V1__REALIZED_TRUTH_BOUND__NO_TARGET_CANDIDATE_RESULT__NO_TARGET_AUTHORITY`

Exact qualified code head: `4251882e39b4793695b26301434bf3c028ef7ea6`

Qualification workflow run: `38213858438`
Qualification job: `114693921885`

Result:
- `315 passed in 0.69s`
- tracked worktree clean after qualification
- artifact: `td-target-tournament-qualification-4251882e39b4793695b26301434bf3c028ef7ea6`
- artifact ID: `11730418572`
- artifact ZIP SHA-256: `a81604f142844314e6f34be7a11d97e8b5604ed1c484947e41ec45be34530eb3`

## Realized V79 authority now bound into target discovery

The target-discovery lane now pins the independently audited realization from V79 PR #297:
- realization audit head `bb8923562144a0b19a6d80795adf727986893ded`;
- realization authority head `cd6425b29f3fbd70b6d93351feb7c188f8b17cc8`;
- Contract V2 SHA-256 `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`;
- root world-set manifest SHA-256 `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`;
- realized-world directory digest `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`;
- complete 498-file ledger SHA-256 `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`;
- audit-freeze receipt SHA-256 `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`;
- blinded-fit index SHA-256 `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`.

`results/target_discovery/synthetic_crosswalk/TD_V79_REALIZATION_BINDING_V1.json` records the exact Q00-Q11 world name → opaque world ID → truth-manifest SHA → scientific-truth SHA → blinded-fit-manifest SHA mapping. `scripts/v5/td_v79_realization_binding_v1.py` validates those bindings fail-closed and supplies the exact world evidence pin future synthetic candidate receipts must use.

The binding also pins semantic truth paths needed by the target-discovery crosswalk: donor SD/effects, new-donor effects, source effects, class effects, quadratic depth, support, detection prevalence, positive-tail sigma, and operator offsets.

## Q10/Q11 paired counterfactual

The physical realization matches the prospectively frozen target-discovery use of Q10/Q11. Q10 and Q11 have the same design SHA and support SHA and identical non-operator truth outputs. Q11 adds only the two operator-offset truth arrays. Therefore the realized pair can later test observation-operator sensitivity without silently changing the non-operator planted truth.

## Boundary

This qualification authenticates the realized synthetic truth substrate only. It does **not** claim that any C1/C2/C3/C4/C6/C5 target candidate has passed a synthetic test.

At this point:
- realized V79 truth is available and audited;
- target discovery is bound to the exact realized worlds;
- synthetic target-candidate result receipts are still absent;
- current-V79 `NOT_ESTIMABLE` claims remain `NOT_ESTIMABLE` for missing shared-multigene, relational, query-conditioned, composite-increment and regulatory/chromatin truth;
- synthetic PASS cannot establish human biological truth or rescue real FAIL / real NOT_ESTIMABLE;
- applicable synthetic FAIL may falsify a target candidate once a prospectively valid candidate evaluation is executed;
- no corrected biological replay, target selection, representation selection, TD60, Stage 4 or training is authorized.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
