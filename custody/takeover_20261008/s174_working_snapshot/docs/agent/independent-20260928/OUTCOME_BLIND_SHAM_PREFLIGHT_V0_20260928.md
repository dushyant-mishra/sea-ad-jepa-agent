# Independent outcome-blind sham-selection structural preflight v0

**Status:** PROPOSED *metadata preflight only*, independently implemented locally on 2026-09-28. It does not choose real sham genes, establish nuisance exchangeability, authenticate a real dataset merely from a claimed digest, or authorize protected readout extraction, teacher/student training or opening the full FULL104 substrate.

**Rationale:** The full six-directed v7 test nominally requires 199 real-gene sham draws per directed pair. Its null is only credible if the real shams reproduce the tested program's technical capture mechanism *conditional on the controls*. Our separate synthetic experiment showed that identical marginal variance can coexist with severe residual-nuisance imbalance. Gene availability and selection provenance must be auditable **before** any readout is opened. A passed structural preflight is necessary scaffolding, not scientific sufficiency.

## What v0 physically checks

The script `sham_preflight_v0.py` accepts a JSON manifest for **one source** and requires:

- The six exact frozen directed comparisons; precisely 199 sham quadruples per comparison in the proposed manifest (1,194 quadruple records). Every quadruple contains four unique canonical addresses, and no quadruple is duplicated within one directed test. A real analysis must independently establish the promised null-draw independence; structural uniqueness is not sufficient.
- All selected sham genes exclude the three query+partner panels, the six historical readouts (**including exposed CSF1R and availability-exposed LPL**), the eight original housekeeping references and all 19 nuisance genes: 48 distinct excluded addresses in the current 29+19 authority. A ledger update changing CSF1R's *exposure status* must not change this ban-set.
- Every proposed sham gene has source-specific feature-axis verification and explicitly measured availability (never a missing-feature placeholder zero); the decoder identity, source identifier and referenced gene evidence must match the manifest.
- Fit/evaluation donors are disjoint; both genome-level and quadruple-level selection metrics are marked fitting-only; permitted data kinds exclude evaluation readouts, held-out outcome associations and new unreviewed inputs. The JSON schema is exact, so an extra outcome-bearing field is rejected.
- Mandatory finite fit-only per-gene abundance, zero fraction, a documented capture-*proxy* slope and a fit-only within-quadruple coherence statistic. **There are intentionally no matching tolerances** in this v0: those are scientific choices requiring a prospectively frozen design, not thresholds to invent after viewing data.
- A strict JSON loader rejects duplicate object keys and JavaScript-style NaN/Infinity; output refuses success on absent source/decoder/code digests, invalid seed or incomplete gene evidence.
- Reports gene reuse across sham draws and exact-quadruple reuse across directed pairs, without misrepresenting low reuse as proof of biological independence.

The synthetic demo populated **1,194 candidate quadruples, 4,776 distinct gene slots, six fit donors and three evaluation donors** solely to stress the code. These fabricated addresses/metrics have **no real gene significance** and are **not a required distinct-gene count** for a future real design.

## Physical tests

**26/26** adversarial/schema tests pass, including forbidden CSF1R/LPL/query/nuisance genes, missing/duplicate quadruples and IDs, structurally absent genes, a forged decoder identifier, evaluation donor used in matching, hidden outcome-bearing input fields, nonfinite metrics and duplicate raw JSON keys. Four additional/earlier independent V7 statistical tests brought the final combined suite to **67/67**, zero skips, zero failures or errors.

Commands:

```bash
python -m pytest -q --junitxml=pytest_results_combined.xml test_six_pair_decision_v7_redteam.py test_sham_preflight_v0.py
python sham_preflight_v0.py --synthetic-demo
python sham_preflight_v0.py --manifest FROZEN_SELECTION_MANIFEST.json --out-json preflight_result.json
```

**Scientific precondition still open:** develop and freeze a real-gene quadruple matching and assessment method using fitting donors only; independently authenticate actual gene-axis mappings and selection-execution logs on Claude's machine; evaluate whether real genes carry comparable residual capture and ambient nuisance. A preflight PASS alone must never be translated into a biological qualification, because fit-only capture-*proxy* slopes cannot prove nuisance exchangeability in held-out donors.
