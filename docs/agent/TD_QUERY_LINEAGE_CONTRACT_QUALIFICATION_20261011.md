# Query-lineage graph contract qualification — 2026-10-11

Status: `Q_LINEAGE_GRAPH_COMPLETE_AND_TYPED__TRANSITIVE_LEAKAGE_GUARD_PRESERVED__NO_AUTHORITY`

TDD sequence:
- RED: `006ef3f83a8187646cf280d7e1a0577918de93e4` — inherited guard produced 5 failed / 6 passed under graph-completeness attacks.
- GREEN: `b7b794e9f2d8cb97ef8693659dc6b958128e263b` — 11 passed / 0 failed / 0 errors.

Exact current Git blobs:
- `scripts/v5/td_query_information_guard.py`: `3ca60c5f82b7b07f5f6123a52e7b50f9027a6ebe`
- `tests/v5/test_td_query_information_guard.py`: `849cfd9b65fadd0c54dfb9f534bcdddc413b4c98`

## Existing scientific semantics preserved

The guard still permits q-address conditioning while rejecting:

- direct q-scalar input to the student;
- transitive q-scalar ancestry through derived/QC/normalization nodes into the student;
- q-bearing target normalization;
- dependency cycles.

A separately declared teacher-only q auxiliary sink remains permitted because teacher access to q can be a prospectively declared auxiliary experiment rather than student leakage.

## Closed fail-open structural weakness

The inherited guard trusted the caller's `roles` mapping. A dependency-graph parent could be omitted from `roles`, making its information role invisible. Role-only nodes, arbitrary role labels, malformed parent collections, duplicate parent edges and non-string/NUL-bearing node identities were also accepted.

The repaired guard now requires:

- graph and roles are mappings over **exactly the same node set**;
- every node name is a nonempty NUL-free string;
- every parent list is a list of unique declared node names;
- no undeclared dependency parent can appear;
- every node role belongs to the frozen vocabulary:
  `student_sink`, `target_normalization_sink`, `teacher_aux_sink`, `q_scalar`, `q_scalar_descendant`, `q_address`, `lawful_evidence`, `teacher_non_q_evidence`, `derived`;
- structural validation happens before acyclicity or leakage traversal.

This prevents a q-bearing dependency from becoming invisible merely because the caller omitted or relabeled its role.

## Harness accounting

Previous focused science harness: 101 green, including the old 6-test q-lineage suite.

Current q-lineage suite: 11 green, replacing those 6.

Current focused synthetic/metadata-only science harness:
`106 passed / 0 failed / 0 errors`

## Authority boundary

This helper operates only on an abstract dependency graph. It opens no biological values/files and creates no target, representation, corrected replay, Stage4 or training authority.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_106_GREEN__QUERY_LINEAGE_GRAPH_COMPLETE_AND_TYPED__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
