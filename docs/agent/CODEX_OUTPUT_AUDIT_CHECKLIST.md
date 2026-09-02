# CODEX_OUTPUT_AUDIT_CHECKLIST.md

When Codex returns, do NOT immediately generate the next command.

Audit in this order:

1. AUTHORITY
- Did it use the real canonical project?
- Did it verify the production address-space authority?
- Did any old 4,096 mechanism assumption displace production semantics?

2. TOPOLOGY
- Was Windows/WSL path translation correct?
- Did it accidentally use a second clone?
- Were environment pivots logged?

3. FIREWALL
- TRAIN only?
- No pathology?
- No DEV/SEALED RNA?

4. MEASUREMENT SEMANTICS
- measured zero preserved?
- structural missing distinct?
- collision unresolved distinct?
- artificial mask only on measured scalar?

5. TARGET COMPUTATION GRAPH
- exact teacher/student evidence?
- queried scalar leakage?
- stop-gradient boundaries?
- address identity path?
- hidden-RNA reconstruction reintroduced anywhere?

6. BIOLOGY
- broad + weak + local + core+halo + rare/innovation?
- lower tails shown?
- 1%/5% support and donor recurrence?
- aggregate mean hiding failures?

7. IDENTIFIABILITY
- N_eff / physical support / retained evidence analyzed?
- representation loss separated from insufficient evidence?

8. FALSIFICATIONS
- permutation?
- identity-only?
- evidence-only?
- donor leakage?
- source/operator shortcut?

9. MULTI-AGENT QUALITY
- critics independent/scoped?
- dissent preserved?
- did any critic identify a fatal contradiction?
- did agents waste tokens rereading irrelevant history?

10. DECISION
Classify contradictions vs local history as:
- true reproduction failure
- runtime/implementation difference
- expected real-data difference
- new scientific evidence
- invalid/leaky result

Only then decide:
- ADVANCE
- REPAIR ONE DEFECT
- RUN ONE FALSIFICATION
- STOP

Generate the next Codex prompt only after this audit.
