# V77 bounded synthetic mutation rehearsal — audited execution record

Date: 2026-10-08
Status: **PASS / SYNTHETIC-ONLY / NON-PRODUCTION / NO TRAINING AUTHORITY**

## Exact audited head

Implementation branch: `impl/v77-bounded-synthetic-mutation-20261007`

Final audited head:

`8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

This head is stacked on the preregistered contract head:

`71a3d6d84a36e1812ffd776153d48948bd8b945c`

The preregistered contract is:

`docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`

## Exact CI evidence

Shared qualification workflow:

- run `37712331253`
- conclusion: SUCCESS

Joined V77 + runtime workflow:

- run `37712331165`
- conclusion: SUCCESS
- job `113100879103`
- focused suite: **51 passed in 9.87 s**
- independent custody rerun of the successful rehearsal: **1 passed in 3.41 s**

## RED -> GREEN audit history

The implementation was not accepted on its first GREEN-looking result.

Self-audit found missing custody guarantees. A RED checkpoint was committed at:

`f0de464fcf921c14a96ef75df806075cc5b69da2`

Run `37711581663` produced:

- **45 passed**
- **5 failed**

The five failures were the intended uncovered contract requirements:

1. no exact restored-state digest proof after checkpoint load;
2. no durable failure receipt;
3. wrong-runtime / wrong-values failures left no custody record;
4. q-safety proof replay failure left no custody record;
5. the same rehearsal run identity could be executed again under a different output filename.

The minimal repair was committed at:

`6f9f51704431825c4d95649944c7613a77c4dcf6`

It added run-identity custody, fail-closed failure receipts, and physical restore-and-compare of student, predictor, teacher, optimizer and checkpoint state. No update mathematics or architecture was changed.

A final direct missing-provenance adversary was then added, producing final head `8dabe9ef...` and the 51-test GREEN result above.

## Successful rehearsal receipt

Success verdict:

`PASS__ONE_SYNTHETIC_GUARDED_UPDATE_PHYSICALLY_BOUND__NON_PRODUCTION`

The final CI custody run recorded:

- optimizer step: `0 -> 1`
- teacher presentations: `0 -> 2`
- online/student parameters changed: true
- predictor parameters changed: true
- teacher parameters changed: true
- optimizer state changed: true
- typed continuation persisted: true
- deterministic restored-state verification: true
- `execution_authorized=false`
- `training_authorized=false`
- `production_promotable=false`
- test-only EMA half-life: `1000` successful base-cell presentations

Exact identities:

- adapter source SHA-256: `15092b16d1a71241e8e5883ff228b5d89595073d79e8df70adaf63641103c4d6`
- joined runtime source SHA-256: `5a820949a9fc9264461a43488847ce89ad5ef17b5125561aa577bfbfd8148f33`
- mutation runtime source SHA-256: `f1bb0f5615206ffa4239aa7e09d95f8d82ced4e8920d83c85867ee62d3c62857`
- batch scientific identity: `213a07a136020b16ea62e3754bfd2f4e5789317d2d1c68781ce2bf7f85cc39d5`
- physical bindings: `24110c202d85945d865fb4c43f5bf278de1b6d15c8565c3df466ab71eadde8fb`
- q-safety proof: `7cd9fac2e222ce650bc808dc8a13cdfc8c9367f5191baf2073afbbf3f94f446f`
- EMA configuration: `V5_PRESENTATION_EMA:6d0e321b897246c1d1e32209c2d59c85c071a1862b0dcdf856542a6237d1eb20`
- completed guard receipt: `452da0f0d79dad7cad2625fff0496b3dd87b763928fdfd10d2b421dd95093293`
- EMA completion proof: `e50f3829bcbf50d684e5ee526559c2222ab1b7d8f7fd8a3633097de2a04965ef`
- typed continuation artifact: `8db05a5fb0ec0f996c949b384af1359d0ddd9c38bc85eb5267ddb8bef5b7c550`

Pre/post and restored-state equality:

- checkpoint before: `7e6e8c275ab43e518b47f59d162a72ee10e27347db027d61bc7607d4533d75f7`
- checkpoint after/restored: `e5611c0d92c5dd8835836d9c838dd32344cb133647d63953e5a3a428fc7d2222`
- online after/restored: `effeca5e904029bea6847df60fd2e88d671d0b7c86918965a7f4b409e56e9a20`
- predictor after/restored: `b51d3d4b3feb23e340c1d3cfe78408708211ce736ede0a36c47fc12ddab225f8`
- teacher after/restored: `3478c6be6cef2a28413c197fcf84baad06180f8320df9828a43e2df231cb0b48`
- optimizer after/restored: `e723a7ab311933b3da66834a86f25fac495b9ca41e1036954d5f6b0cda541700`

## Mandatory adversary crosswalk

The preregistered contract required the following before accepting PASS:

1. missing physical binding proof -> direct bounded-rehearsal rejection test;
2. wrong consumed values -> direct bounded-rehearsal rejection test;
3. wrong adapter digest -> direct bounded-rehearsal rejection test;
4. wrong runtime digest -> direct bounded-rehearsal rejection test;
5. q-safety proof replay from another batch -> direct bounded-rehearsal rejection test;
6. nonfinite / GradScaler-skipped optimizer step -> canonical guard regression in the same workflow proves no completed step and no EMA;
7. EMA before proven optimizer completion -> canonical guard regression rejects `run_ema` before completion;
8. second optimizer step under the same rehearsal identity -> direct run-identity custody rejection, even with a different output filename;
9. weak/V1 base runtime proof cannot promote -> shared-interface V2 regression rejects the old base-only proof;
10. EMA configuration drift on restart -> typed continuation regression rejects changed half-life/configuration;
11. child reload exact -> fresh modules are restored from the persisted child checkpoint and all student/predictor/teacher/optimizer/checkpoint digests are compared exactly;
12. authorization flags -> successful receipt remains `training_authorized=false` and `production_promotable=false`.

Failed attempts also preserve a run-identity custody receipt with verdict:

`FAIL__NO_COMPLETED_MUTATION_CONTINUATION`

A retry requires a new run identity. A failed or completed run identity cannot silently be reused.

## What this PASS means

It proves one thing only:

**The currently joined synthetic V77 -> shared qualification -> canonical V5 path can execute exactly one physically guarded synthetic optimizer update, advance EMA only after proven optimizer completion, persist the typed continuation, and restore the exact resulting state.**

It does not prove biological validity, useful representations, a production EMA half-life, real-data safety, or permission for a second update.

## What remains off

Unchanged:

- real-data training
- Stage A execution
- TEST
- Morabito
- 500K
- Stage 4
- production EMA selection
- target freeze
- representation freeze
- threshold selection

## Next scientific gate

Do **not** spend the next step adding more optimizer updates.

The corrected S174 replay shows a biological structural gap: no replayed synthetic arm reproduces the real contribution of broad cell class to pooled correlation. Corrected T5 is about `0.74`; replayed arms are about `1.02–1.21` because the current hidden substate design is independent of cell class.

The next synthetic design must therefore test class-conditioned/shared biological structure while still jointly accounting for expression dependence, detection dependence, abundance, depth and topology. It must not tune only to T5 or to one pooled correlation statistic.

Corrected pooled bootstrap intervals remain uncertainty diagnostics, not pass/fail qualification targets, until S159 is resolved.
