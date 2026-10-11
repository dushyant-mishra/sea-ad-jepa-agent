# Target Discovery V2 Governance Qualification — 2026-10-11

This record is **synthetic/metadata-only governance evidence**. It creates no biological-value, corrected-replay, target-selection, representation-selection, TD60, Stage4, or training authority.

## Current qualified governance head

PR #275 branch:
`science/td-target-tournament-scaffold-20261011`

Exact qualified current head:
`0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`

GitHub Actions run:
`38183565983`

Job:
`114601031751`

Artifact:
`11718374988`

Artifact digest:
`sha256:585f7799e0aba4935b37b28319570025de67ecf73d9aa7523a5bf6abeb74de61`

Verified artifact contents:

- `HEAD=0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`
- `STATUS_BEFORE=[]`
- `197 passed in 0.31s`
- `STATUS_AFTER_TRACKED=[]`
- `PASS_WORKTREE_CLEAN_AFTER_FOCUSED_QUALIFICATION`
- Python 3.11.17
- numpy 2.4.6
- pandas 3.0.6
- scipy 1.17.1
- scikit-learn 1.9.1
- pytest 9.1.1

Terminal:

`PASS_FULL_SYNTHETIC_METADATA_ONLY_V2_AUTHENTICATED_REGISTRY_TO_ADJUDICATION_CHAIN_197_OF_197`

## Qualified prospective chain

`V2 contract + execution context + authenticated candidate×gate governance registry -> externally pinned V2 prefreeze -> exact gate-case coverage -> gate evidence artifact -> full candidate evidence manifest -> candidate receipt -> tournament adjudication`

The execution context freezes hashes for:

- overall executor code identity;
- gate-executor registry;
- gate-estimand registry;
- gate-decision-rule registry;
- population registry;
- donor registry;
- source registry;
- observation-operator registry;
- support registry;
- teacher/student evidence-rights registry;
- split registry;
- observation descriptor;
- corrected-replay evidence.

The authenticated gate-governance registry must cover every candidate×gate role in the frozen V2 contract exactly once. Each role binds one qualified gate executor, one estimand, and one decision rule. Candidate-manifest construction authenticates this registry against the frozen execution context, derives the per-gate executor/estimand/rule identities internally, requires the candidate's entire frozen gate set, and refuses free post-outcome expected maps.

The coverage layer remains coverage-only. It does not invent PASS/FAIL policy. Gate-specific executors own the prospectively frozen estimand and decision rule. `PASS`, `FAIL`, and `NOT_ESTIMABLE` remain distinct.

## Preserved RED→GREEN lineage

### V2 adjudicator
- frozen tests: `512da1f0fb9e5af130f11f2b1073451da61158d0`
- initial implementation: `31d1974465a3a5940688d4a9186d3002045adffe`, 10/10 green
- edge RED: `e3a5aedfa687881bd2f307ce2fb59450f6738ead`, 2 failed / 10 passed
- edge GREEN: `74c25f5d7f5827244dc8516e49e20e0034631432`, 12/12

### V2 prefreeze
- RED tests: `9c5d492c1555291a8be180f36871caa20ce819a3`
- RED workflow head: `af22e58fd90cded5a02bec6676650e1e0bedd0ad`, missing V2 prefreeze module
- GREEN implementation: `0b6989b31a3814ce22d463e6dbdc189dc340152c`, 174/174

### V2 case coverage
- RED tests: `c81f13e9777d24544ae454b2d9561d88f8c2155d`
- RED workflow head: `4026e1ee62d92eae40f32cd3cceaa011286563cc`, missing V2 coverage module
- GREEN implementation: `bf7e98bd8bf451826e92c6d6c87c747e7a4fb824`, 180/180

### V2 gate-evidence custody
- initial RED tests: `98f1a9cfc36a08da40e68c7dc87cdd6ea0ffa90a`
- RED workflow head: `52e22a77ae7fa81865da01a1bd384528f812a15d`, missing gate-evidence module
- initial GREEN: `b82196646a76f43f4c5a716fa5028198875f7255`, 187/187

### Executor / estimand / decision-rule freeze
- RED lineage: `1597712cc276493b26a2ac8ad826387d69cb1437`, then estimand-aware `60633a81965fede0bb06d0b6235946e1ce4e5c96`
- exact RED result: 22 failed / 167 passed
- GREEN production hardening: `74dc5bade9288bc845f44661063976ffc7f601a5`, 189/189

### Authenticated gate registry
- RED tests: `847bd4e9584b89f8b4697844d77fafe85d67ce93`
- RED workflow head: `2ea9179f3e8e7d0d4956ad9d97cfa2e151337d3a`, missing gate-registry module
- GREEN registry: `3bb4d0cf3736049106606b19af11a9c20490739e`, 195/195

### Removal of free-map bypass and full-gate-set enforcement
- RED test head: `b0bf7f361e19ff509574641e499da52301a4b47d`
- exact RED: 3 failed / 193 passed
- full-gate-set test hardening: `f7abadaa490fc208e0775deb92ad22fc7acbfd64`
- GREEN production fix: `87b8e72a4adcf3758738fad982ceeb7b0dce5222`, 197/197
- state-only current head `0cbe6244756df3d1b7ed1ef4e1643aae0f94e875` independently reran the same exact harness and remained 197/197 clean.

## Authority boundary

This work does **not** make any candidate a winner and does not authorize a real tournament. The real critical path remains:

`replacement G6 -> external G6 audit -> possible G7 -> external G7 audit -> separate corrected TD56/57B/57C/59 authority -> corrected replay -> frozen interpretation -> only then fresh explicit authority to instantiate a real V2 tournament context/registry/cases/executors.`

Current hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
