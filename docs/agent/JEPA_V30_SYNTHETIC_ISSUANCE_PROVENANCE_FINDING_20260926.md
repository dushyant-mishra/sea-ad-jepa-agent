# V30 synthetic source-provenance red-team — exact PR149 issuer

**Scope:** current V5 source-level negative control only. No real expression, physical evidence, protected outcomes, training, optimizer or teacher. Exact reviewed source head `938fe5d3a7288826fef86b2650fb3a9a21fd3794`; V25 `main` governance and V28 takeover unchanged.

## Question

Does `issue_training_authority_v1` independently prove that the supplied `closure_v2` was returned by the *actual* `validate_current_v5_authority_closure_v2` with live current source-backed authorities, or does it merely rehash a self-consistent mapping and accept an internally self-signed receipt? The preexecution and receipt functions recalculate digests but do not independently authenticate the object graph's origin. The issuer dynamically validates only the critical-test and runtime objects supplied.

A three-test synthetic diagnostic constructs **32 invented role hashes**, a synthetic critical object, a syntactically valid but fake-source `CurrentRuntimeSourceAuthorityV1`, a canonical-hashed closure mapping, preexecution and V2 teacher receipt. It calls the true issuer but **never** calls the live closure validator or supplies actual masking, teacher, measurement or geometry execution evidence. Control tests confirm corrupt receipt and corrupt closure hashes do fail as designed. A successful first test indicates a provenance gap in a caller-facing function **despite** its good internal-digest checks. It is not evidence of real training or access permission; B1 governance remains a separate off gate.

This is a dedicated review finding, not an instruction to relax source checks. A reviewer must determine the intended trust boundary; a safe successor may require an unforgeable signed/materialized closure receipt from the actually run validator or accept a live typed object graph that it revalidates on issuance. Preserve exact current 33 roots, current-vs-historical class compatibility, a separately approved B1 reader_fit contract, full parent-byte authentication, selected masking result, executed critical tests and independently reviewed production source. A field named `closure_digest`, a raw hex string or a hash invented by tests is never evidence of real biological qualification.

**Do not call test-green "B2 closed."** CI green means the diagnostic reproduced its own narrow result, not that this gap was fixed.
