# Open review attacks after R5 — 2026-09-09

These attacks remain open until verified against committed code and real artifacts.

## 1. Public handle path attack

Question: can any public function still accept a caller-built `AuthenticatedSource` or handle-like object and produce a source-library proof?

Expected answer: no. Production proof must be path-owned via `prove_population_from_source_path`.

## 2. Detached technical values attack

Question: can any production path still accept detached `(source_library, projected_nonzero_count)` tuples or donor summaries and emit a technical-completeness package?

Expected answer: no. Detached values are fixture-only.

## 3. Cardinality-but-wrong-rows attack

Question: can a population raw-source authority with the right number of proofs but a different set of logical rows pass replay?

Expected answer: no. Logical index, expression row, cell ID, donor ID and source library must match the logical authority row-for-row.

## 4. Physical-plan bypass attack

Question: does the verified physical plan actually determine which counts payloads are consumed, or can a caller supply a payload map not implied by the plan?

Expected answer: the plan must constrain consumption. If the implementation only verifies the plan beside a separate arbitrary payload map, this remains a gap.

## 5. Replay-from-memory attack

Question: does replay verify disk artifacts independently, or does it reuse the same in-memory object returned by the run?

Expected answer: replay must read disk bytes and recompute roots.

## 6. Projection-universe attack

Question: can Q_DETECT be computed over 28,061 scoring features, 41,238 address-space features, or a one-position fixture while presenting as production?

Expected answer: no. Production Q_DETECT requires exactly 35,076 B1 projected scalar-measured addresses.

## 7. Pathology-leak attack

Question: do any emitted artifacts or allowed obs reads include Braak, Thal, CERAD, ADNC, AT8 numeric values, or other pathology values?

Expected answer: no. B2 and technical completeness remain pathology-blind.

## 8. Artifact-root attack

Question: are large outputs referenced by exact path, byte count, SHA-256, package root, and replay verdict?

Expected answer: yes. Console logs alone are not enough.
