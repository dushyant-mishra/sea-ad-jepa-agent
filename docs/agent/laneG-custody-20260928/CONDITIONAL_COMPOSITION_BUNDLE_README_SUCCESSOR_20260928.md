# Conditional-composition portable bundle — corrected successor README (2026-09-28)

**Record type:** SUCCESSOR. This does not replace or edit the historical README inside the
bundle. The historical README is preserved byte-identical
(`README.md`, 1907 bytes, sha256 `9037f6385f3949e9016be2939148685cd8986b79d9cdc2e97bf65505bee8799e`).
Read this file instead of it.

**Authored by:** lane `laneG-custody-20260928`, from worktree `D:/jepa_wt_laneG-custody_20260928`
at base commit `c7e31ab5aacb59091ca3d26f0fcf8d71f3a2eddd`.

---

## 1. What the bundle is and where it lives

| item | value |
|---|---|
| container archive | `JEPA_CHAT_LOCAL_ONLY_EVIDENCE_20260928.zip` |
| container sha256 | `83ab489570ffd863a6a9c9e54ebc85cd84e0c769948f15e27427a7d3137da873` (recomputed 2026-09-28; matches the V47 custody manifest) |
| container bytes | 415682 |
| local copy verified at | `C:/Users/dushy/Downloads/JEPA_CHAT_LOCAL_ONLY_EVIDENCE_20260928.zip` |
| bundle path inside archive | `chat_local_evidence/jepa_conditional_composition_cpu_20260928/` |
| bundle files | 30 |

The bundle's own inventory is `SHA256_MANIFEST.json` (schema `JEPA_NEW_PORTABLE_BUNDLE_SHA256_V1`),
which lists 30 files and excludes itself.

---

## 2. THE DEFECT — a file the manifest promises is not in the directory

`SHA256_MANIFEST.json` declares:

```json
"composition_synthetic_v1.py": { "size": 7711,
  "sha256": "989702cfbe78b151b410b625bf1a59cdf83577ac92827e65f0e8f08c5f0a8058" }
```

**That file is not in the bundle directory.** It was packaged into the *sibling*
bundle directory `chat_local_evidence/JEPA_LOCAL_COMPLETION_20260928/`.

Two shipped files import it **by module name**, so they can only work if the module is
importable — not merely present somewhere on disk:

- `test_new_workstream.py`, line 8 — `from composition_synthetic_v1 import generate,evaluate,prep_group,run,seed_for,binomial_ci`
- `composition_grid_v1.py`, line 7 — `from composition_synthetic_v1 import generate,evaluate,seed_for,binomial_ci`

The historical README's first two reproduction commands therefore both fail.

### 2.1 Exact failing command and exact failure (reproduced, not inferred)

Run from the extracted bundle directory:

```
cd .../chat_local_evidence/jepa_conditional_composition_cpu_20260928
python -m pytest -q -p no:cacheprovider test_new_workstream.py test_v5_static_source_probe.py test_census_logic_redteam.py test_census_protected_probe.py
```

Observed on 2026-09-28 with `C:/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe`:

```
=================================== ERRORS ====================================
___________________ ERROR collecting test_new_workstream.py ___________________
ImportError while importing test module '...\jepa_conditional_composition_cpu_20260928\test_new_workstream.py'.
Traceback:
test_new_workstream.py:8: in <module>
    from composition_synthetic_v1 import generate,evaluate,prep_group,run,seed_for,binomial_ci
E   ModuleNotFoundError: No module named 'composition_synthetic_v1'
=========================== short test summary info ===========================
ERROR test_new_workstream.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 3.72s
```

Collection is interrupted, so **all four documented test files fail to run**, not just one.
The second documented command, `python composition_grid_v1.py --reps 80 --out grid_rerun.json`,
fails the same way at import time.

### 2.2 A second, separate path defect (recorded, not fixed here)

`nph52_sensor_reliability_v1.py:12` and `nph52_sensor_cluster_bootstrap.py:10` both contain

```python
sys.path.insert(0,'/mnt/data/jepa_gene_control_pilot_20260927')
from pilot_screen import load, HOUSE, PROGRAM, RESERVED
```

`/mnt/data/...` is the ChatGPT chat-environment filesystem and does not exist on this machine.
These two scripts are the optional real-NPH52 sensor path, which the historical README already
gates behind "supply the original August24 archives"; they are outside the offline
reproducibility block and are **not** repaired by the shim below. Anyone running them must
point that path at a local copy of the `jepa_gene_control_pilot_20260927` bundle.

---

## 3. THE FIX

A fail-closed loader shim is provided at

```
docs/agent/laneG-custody-20260928/conditional_composition_bundle_shim/composition_synthetic_v1.py
```

Put that directory on `PYTHONPATH`. `import composition_synthetic_v1` then resolves to the
shim, which finds the real implementation file, **verifies its SHA-256 equals the digest the
bundle's own manifest asserts** (`989702cf...`), loads it by path, and re-exports its public
namespace. If the implementation is missing, or present with a different digest, the shim
raises `ImportError` and names what it searched. It never substitutes an unverified copy.

The historical bundle directory is **not modified**. Nothing is copied into it.

### 3.1 Corrected reproduction commands

Step 1 — extract BOTH bundle directories from the container archive:

```python
import zipfile
z = zipfile.ZipFile('JEPA_CHAT_LOCAL_ONLY_EVIDENCE_20260928.zip')
z.extractall('.', members=[n for n in z.namelist() if n.startswith((
    'chat_local_evidence/jepa_conditional_composition_cpu_20260928/',
    'chat_local_evidence/JEPA_LOCAL_COMPLETION_20260928/'))])
```

Step 2 — put the shim directory on `PYTHONPATH`:

```
export PYTHONPATH="<repo>/docs/agent/laneG-custody-20260928/conditional_composition_bundle_shim"
```

Step 3 — run the documented steps from the bundle directory:

```
cd chat_local_evidence/jepa_conditional_composition_cpu_20260928
python -m pytest -q -p no:cacheprovider test_new_workstream.py test_v5_static_source_probe.py test_census_logic_redteam.py test_census_protected_probe.py
python "$PYTHONPATH/composition_synthetic_v1.py" --reps 120 --cells 120 --out <outdir>/composition_rerun.json
python composition_grid_v1.py --reps 80 --out <outdir>/grid_rerun.json
python thinning_identifiability_v1.py --n 100000 --out <outdir>/thinning_rerun.json
python census_logic_redteam_v1.py
python census_protected_early_filter_probe_v1.py
```

Two notes on the commands:

- The historical README writes reruns into the bundle directory (`--out composition_rerun.json`).
  Write them to a separate output directory instead, so the historical evidence directory stays
  byte-identical.
- `python composition_synthetic_v1.py ...` must invoke the shim explicitly by path (as above), or
  be run with the shim directory as the working directory. Running the bare name inside the bundle
  directory still fails, because the file genuinely is not there. The shim delegates to the real
  implementation's CLI via `runpy`, so the documented flags behave identically.

Alternative if you cannot set `PYTHONPATH`: copy the shim (or the verified implementation itself)
into your own scratch copy of the bundle. Do not copy it into an evidence directory you intend to
cite.

---

## 4. Verification actually performed (2026-09-28)

Interpreter: `C:/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe`.
Working copy extracted to `D:/jepa_v5_outputs_20260925/out_laneG-custody/extracted/`.
Reruns written to `D:/jepa_v5_outputs_20260925/out_laneG-custody/rerun/`.

| step | before fix | after fix |
|---|---|---|
| documented 4-file pytest | `ModuleNotFoundError`, collection interrupted, 0 tests run | **39 passed** |
| `composition_grid_v1.py --reps 80` | import error at line 7 | exit 0, 20 grid rows |
| `composition_synthetic_v1.py --reps 120 --cells 120` | file absent | exit 0, 5 scenarios |
| `thinning_identifiability_v1.py --n 100000` | exit 0 (no dependency) | exit 0 |
| `census_logic_redteam_v1.py` | exit 0 (no dependency) | exit 0 |
| `census_protected_early_filter_probe_v1.py` | exit 0 (no dependency) | exit 0 |

**39 passed** is the same count the bundle's own `TEST_EXECUTION_FINAL.txt` records for
"[new workstream tests]" — so the fix restores the documented behaviour rather than merely
silencing the error.

Numerical agreement with the committed reference JSON:

- `composition_sensitivity_grid_80rep.json` — 6 of 20 rows byte-identical; the other 14 differ in
  **one field only**, `exact95ci`, at a maximum relative difference of `6.5e-16` (1–2 ULP of a
  Beta quantile, i.e. a SciPy build difference). Every integer count, `rate`, `total` and
  `significant_and_recurrent` value reproduces **exactly**.
- `composition_120rep_120cells.json` — differs only in `donor_p_below05_95ci` (max relative
  `3.6e-16`) and `both_rule_95ci` (relative `0`, last-bit only). Every rate and median
  reproduces exactly.

No decision-relevant number changed.

### 4.1 The shim's refusal paths were tested and can actually fire

Both failure branches were exercised, so the digest check is not a check that cannot fail:

- implementation unreachable → `ImportError` listing every path searched;
- implementation present but tampered (one comment line appended, sha256
  `c2ee691c7bb5dde1d3023ec80c6e87b8251ef303b382678d002055c1b8664143`) → `ImportError` with
  `found but DIGEST MISMATCH (refused)`.

---

## 5. Governance — unchanged and re-affirmed

- `TRAINING=OFF` for scientific neural training.
- **No protected outcome was opened by this verification.** `census_protected_early_filter_probe_v1.py`
  and `test_census_protected_probe.py` mention the six reserved addresses
  `[2810, 4748, 10846, 13734, 14980, 26659]`, but they use them only as integer indices in a
  fabricated `np.bincount` poison fixture of 9 synthetic entries. No real expression matrix, no
  real donor, and no reserved readout value is read by any command in section 3.1.
- The conditional-composition route remains **developmental, not qualified**: per the V47 handoff
  it requires a differential-capture negative arm before any biological interpretation. Fixing an
  import path changes nothing about that status.
- Restoring the ability to *run* these synthetic stress tests does not make their conclusions
  production authority. `composition_synthetic_v1.py` states in its own docstring that the frozen
  real v7 was not executed and that its statistic is an exploratory toy, not frozen v7.
