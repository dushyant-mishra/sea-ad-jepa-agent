# F1 real reader / forward / executor preflight contract

Status: prospective, pre-result engineering authority. This contract permits only a mechanics preflight. It does not authorize real F1 adjudication, biological interpretation, training, optimizer or EMA activity, or access to reader-validation, reader-oracle, DEV, SEALED, or pathology data.

## Frozen inputs and scope

The implementation must hash-bind the current F0 constructor/root, protected-program weights, 41,238-address namespace, observation-state authority, reader split, FULL104 row lineage, frozen F1 assignments, compute-dedup authority, matched-null map, evidence-mask authority, u0 qualification checkpoint, encoder, tokenizer, reader implementation, and accepted evidence-trend authority. Ambiguity or mismatch fails closed.

Only lawful reader-fit rows selected by the metadata-only fixture rule below may be opened. The only allowed outputs from expression/model execution are technical parity, timing, memory, resource, identity, resume, schema, and sufficient-statistic equivalence records. Per-cell biological values, representations, predictions, effects, program scores, or candidate outcomes must not be published.

## Resource fields

Record WSL distribution/kernel, Python, NumPy, SciPy, PyTorch, CUDA runtime, cuDNN, GPU name/driver/total and free VRAM, CPU logical and physical cores, total and available RAM, swap total/used and before/after counters, filesystem type/free space, process peak RSS, CUDA allocated/reserved/peak memory, reader/constructor/H2D/model/reduction timing, role-specific throughput, page faults where available, and exact imported source hashes. WSL must access the canonical bytes through `/mnt/d/Jepa project`.

## Metadata-only technical fixture

Fixture membership is derived before expression access from the frozen 43,108 unique `(cell,q)` compute identities plus donor/source/operator metadata, physical/evidence support counts, context lengths, and deterministic SHA-256 ordering only. It must cover all 42 operators, all three sources, all five evidence levels, teacher/correct/matched-null roles, and low/median/high context-support strata within each source where present. Within each required stratum choose the lexicographically smallest SHA-256 of the canonical tuple `(canonical_cell_id,q,donor,source,operator,evidence_level,role,null_source_cell,context_support_count)` encoded as UTF-8 with field separators. Satisfy coverage first, then deduplicate identical `(cell,q)` pairs. Freeze every selected identity and a membership root. No expression, H/S/T, program value, or outcome may influence membership.

Before expression access, publish a hash-bound justification enumerating exact rows/shards, reader-fit legality, why frozen summaries cannot establish real-path mechanics, absence of protected partitions, and the non-conclusion-bearing output boundary.

## Evidence and forward semantics

Reuse the authenticated 20/40/60/80/100 evidence-mask algorithm unchanged. Physical observation state and artificial evidence masking remain distinct; measured zero remains evidence; q identity remains present while q scalar is withheld where required; frozen query, assignment, and null identities remain unchanged.

The real-forward root binds model/checkpoint, encoder/tokenizer, constructor, namespace, reader, observation states, evidence masks, assignment/null/dedup identities, dtype/device/determinism, role, recipient/null source, and semantic snapshot. Cache identity must distinguish all of these. Only an identical teacher-rich target may be reused across evidence levels; correct and null student forwards may never collide.

All forwards use `torch.no_grad()`, no backward, no optimizer, no EMA, and unchanged scientific dtype/model semantics.

## Query-safe parity

The production path must agree with the authenticated slow/reference semantics under the frozen F0 tolerance authority. Required metamorphic checks are: x_q-only scalar intervention leaves the query-safe target/context invariant; lawful non-q intervention changes the lawful contextual route; query permutation restores exactly after inverse permutation; forward batch/chunk changes preserve outputs within authority; physical read-order permutation restores identity; correct and matched-null roles remain distinct and cannot share cache identity. Any failure is terminal.

## Mechanical resource ladders

Every candidate runs in a fresh subprocess on the identical frozen fixture, with one untimed warmup and three timed repetitions.

- Forward/query batch: powers of two `1,2,4,...` until the next exceeds fixture capacity or a hard safety failure occurs.
- Reader block: powers-of-two multiples of the selected forward batch until fixture exhaustion or a hard safety failure.
- Workers: `0,1,2,4,8,...` not exceeding `max(1, physical_cores-2)`, plus that exact maximum if absent.
- Prefetch: `1,2,4,...` while RAM-safe; then pinning OFF and ON at selected prefetch geometry.

At each stage select the smallest safe configuration whose median throughput is at least 95% of the fastest safe configuration. No biology metric may participate. Candidate generation and stopping are mechanical and prospective.

## Safety limits

A candidate is unsafe if CUDA OOM occurs, peak torch reserved VRAM exceeds 85% of detected total VRAM, swap activity increases, process peak RSS exceeds 80% of MemAvailable measured at candidate start, outputs/counts are non-finite or incomplete, hashes/identity/firewall fail, or storage/reader integrity fails. Linux page cache is not swap. An unsafe subprocess cannot contaminate later candidates.

## Executor, resume, and sufficient statistics

Freeze exact full-run geometry from the 44,496 assignment population while treating deduplication as computation-only: inference remains over all assignments with hierarchy assignment -> program -> cell -> donor and equal donor weight. The adjudicator, not evaluator, derives paired design variance `(Z0-Z1)^2/4`.

Use block/shard execution with atomic generations, membership/order/source/forward/dtype roots, CURRENT pointer, narrow stale-generation cleanup, and exact resume. A bounded test must compare uninterrupted versus interrupted/resumed ordered bytes, then attack stale membership, forward root, dtype, and order. All attacks must be rejected or recomputed according to the frozen identity.

The production evaluator may emit only the predeclared minimal sufficient-statistic schema. Validate it independently against direct bounded calculations, including duplicate assignments, donor/cell weights, two draws, evidence levels, roles, and nulls. Estimate total storage from measured bytes before full execution; no full F1 execution is authorized here.

## Required artifacts

The package must contain exactly the 25 named preflight artifacts in the controlling command: authority binding, expression justification, evidence-mask binding, fixture binding, WSL authentication, resource snapshot, real-forward root, reader call graph, query-safe parity, resource ladder/selection/role throughput, runtime projection, executor plan, shard-resume test, sufficient-statistics schema/parity, storage envelope, firewall audit, independent validation, five-lens review, source/package manifests and root, and external-review handoff.

## Fail-closed conditions

Use the controlling STOP names for head/live-gate, authority, model/reader ambiguity, evidence-mask, WSL authentication, real-forward root, query-safe parity, resource selection, context budget, executor parity, resume, sufficient statistics, firewall, and independent validation failures. Engineering implementation may be repaired prospectively without changing scientific semantics; any scientific-authority change requires a stop and new authorization.

Success ends only at `PASS_F1_REAL_READER_FORWARD_EXECUTOR_PREFLIGHT_AWAITING_EXTERNAL_REVIEW`. Real F1 remains forbidden.
