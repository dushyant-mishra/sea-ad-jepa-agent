# V36 independent guard-side issuer provenance repair — non-authorizing

2026-09-26. **Stacked on PR #161** at aa98a3882b41185536e4b1d37cdf3e6b7d19fa83 (which is stacked on V30 PR #156). This does not update main or current approved training policy. Protected/full FULL104 outcomes remain unopened; training OFF; zero of 33 current authority roots fully closed.

## Historical reason this is not a repeat

V30 PR #156 physically demonstrated that the final issuer accepted a coherent but invented hash envelope. V34 PR #161 repaired the issuer by invoking the actual live typed closure validator. V34's own independent self-audit discovered **a distinct downstream bypass**: anyone could instantiate `CurrentTrainingAuthorityV1` directly, compute its public self-hash, and pass it with a matching receipt to `install_current_optimizer_guard_v3`. The old guard checked the token and receipt, not whether any source-validated issuer ever issued the token. V34's synthetic optimizer tests deliberately reproduced this as a mechanically passing fixture. V36 addresses this **new guard-side seam** without re-running historical T1/C2, QID, Stage81A3 or sealed outcomes.

## Versioned repair

The production guard installer and dataclass constructor now require the complete live closure object, typed preexecution object, original critical/runtime objects, and exact `closure_inputs` mapping. Before registering **any** optimizer hooks, the guard invokes the *real* V34 issuer on those live inputs, checks the reissued token digest against the presented token, and checks the expected closure/preexecution roots. The same live issuer check is repeated when arming a step and immediately before the optimizer pre-hook. A mutation, replacement, missing root, or replayed caller-provided digest fails closed; an existing guard cannot silently switch to a separately reconstructed evidence object, even when digests agree. Legacy checksum-only calls are rejected before optimizer hook registration.

No cryptographic key or externally signed proof is fabricated. Reissuing from the authenticated graph in-process is the chosen trust boundary. This is **not** proof that source-byte validators verify every external artifact; physical source manifests and execution evidence remain separate gates.

## Independent negative and mechanical tests

Six V36 red-team tests check: (1) hand-forged public token rejected with no live graph/no registered hooks; (2) full set of *fake* role names and self-consistent hashes rejected by the unmocked production graph validator; (3) public guard class constructor cannot bypass live-issuer requirement; (4) a test-only issuer spy yielding a different but internally coherent token is rejected; (5) live-issuer failure after initial installation is rechecked before arming, without cursor advance; and (6) an otherwise matching second installer cannot splice in different evidence objects. The seven original V34 provenance tests remain unchanged. The seven preexisting V5 preexecution/optimizer tests now **explicitly mock only the guard's issuer import**, strictly to exercise cursor mechanics; the real issuer remains unmocked in the V34 negative tests. They cannot count as live B1/B2 authority positives.

The V36 workflow uses `pipefail`, requires exactly 20 tests across V34/V36/V5 files, and zero failed/errored/skipped cases; independent existing runtime and V26 synthetic mechanics workflows must also pass.

## What is still *not* closed

- A positive path using all authentic **real** typed V5 scientific authority objects and source bytes is unavailable: current V5 roots are not fully closed. **Do not** manufacture one to make CI green.
- The generator/validator of each upstream authority must independently authenticate original external physical data, critical tests and immutable source/runtime bytes, not merely digest assertions from callers.
- Because the guard now revalidates the full graph at install/arm/pre-hook, future performance optimization requires separate qualification of an authenticated immutable cached proof and rollback/restart behavior; never remove the live checks merely for speed.
- This is source/CPU synthetic evidence, not GPU training, biological target qualification, masking qualification, Morabito causal validation, protected confirmation or permission for production.
- V32 uploaded research ZIPs and V35 physically rerun 15 V4 tests on PRs #159/#162 are parallel non-authorizing research lanes, not parents of B2 issuance.
