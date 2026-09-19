Report written: `D:/jepa_inv_20260919/CLAUDE_FULL104_INVENTORY_AND_GAP_REPORT_20260919.md` (SHA `d7e32c68…`). Nothing was recomputed, no terminal outcome opened, nothing deleted.

**Two corrections to things I told you earlier.**

You were right about the GPU — **RTX 3080 Laptop, 16 GB free, idle and healthy.** I'd checked `torch.cuda` inside the `base` conda environment, which has a CPU-only PyTorch build. That says nothing about the hardware. Worse: the project has its own environment, `sea-ad-jepa`, with Python 3.11, torch 2.7.0+cu128 and CUDA working. Every test run I've reported to you over the last three days ran in `base` (Python 3.9, numpy 1.24) — **not** the project's environment. That's a real provenance gap. `sea-ad-jepa` is missing only `pytest`.

**The main inventory finding: there is nothing to reuse.** All seven current derived artifacts are absent — no census receipts, no split, no eligibility, no census authority, no calibration cache, no shakedown receipt, no runtime directories. The code to build them is all present on this head; it has simply never been run.

The only pre-existing derived file is **my own** **`pass1.npz`** **from 2026-09-17**, sitting in the session scratchpad. It happens to contain all six arrays the new verifier needs, but it predates the physical-binding trust boundary entirely → `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

**Assets.** Level-4 manifest and observation state both hash-MATCH. I found the canonical registry too — and its location is worth knowing: it's `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv`. The bytes are exactly right, but the filename says "Stage81A2R candidate" and the path contains `stage81`, which is on your own runtime denylist. It's not a real spillover problem (that list only screens runtime *output* paths), but anyone applying the project's anti-spillover instinct would reject it on sight. It nearly fooled me. Worth recording its exact path in the asset authority.

The **V0 and V1 parent files are not on this machine** — I hash-checked 40 candidates. Those are needed only for F13, not for the census.

**F13 / F14 / F15, short version.** The representation routing module is complete and correct — it binds the V0/V1 hashes and the `[0:256)` value / `[256:512)` visibility split properly — but **nothing consumes it**; its only importer is its own builder script. Geometry authorities exist as empty scaffolding with no frozen instance. There is **no executable V5 training path at all**, and every historical carryover seam I checked is clean: `PROTECTED_48`, `128x8`, `.996` EMA all zero occurrences; the V4 imports are confined to files named "inactive" and "prototype."

**Spillover: clean.** The runtime envelope implements a real denylist plus forbidden exact hashes.

Nothing is blocked from running now. Before the physical pass1 verifier, I'd settle which environment is canonical — that decision should be made once and recorded, not inherited by accident.

**Bash **Read completed registry sweep result

IN

```
grep -E "scanned|MATCH:" "C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/tasks/bj7t7wbmg.output" 2>/dev/null
```

svg

OUT

```
  scanned 53067 candidate files
  MATCH: ['D:\\Jepa project\\exports\\foundation_calibration_bundle_20260824\\contracts\\address_namespace.csv']
```

*Background command "Wait for registry hash hunt" completed (exit code 0)*

The sweep found a **second copy** — same bytes, better location. Confirming both.

**Bash **Confirm duplicate registry copies

IN

```
cd "D:/Jepa project" && python -c "
import hashlib,pathlib
T='7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd'
for rel in ['exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv','results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv']:
    p=pathlib.Path(rel); h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<22),b''): h.update(c)
    d=h.hexdigest()
    print('  %-6s %10d B  %s' % ('MATCH' if d==T else 'no', p.stat().st_size, rel))
print()
print('  -> two byte-identical copies of the canonical registry')
"; echo; head -2 "exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv"; echo; grep -i "address_namespace" "exports/foundation_calibration_bundle_20260824/BUNDLE_SHA256_MANIFEST.csv" 2>/dev/null | head -2
```

svg

OUT

```
  MATCH    24946770 B  exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv
  MATCH    24946770 B  results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv

  -> two byte-identical copies of the canonical registry

molecular_address_index,molecular_address_id,identity_class,current_ensembl_gene_id,legacy_source_exact_id,source_native_anchor,symbol,biotype,identity_authority,identity_evidence,measurement_support_provenance,contributing_source_feature_count,contributing_source_families,contributing_source_dataset_ids,registry_semantic_hash
0,ENSG00000000003,current_exact,ENSG00000000003,,,TSPAN6,protein_coding,source_native,EXACT_CURRENT_ENSEMBL|SOURCE_EXACT,stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz#ENSG00000000003,9,HVS|NPH52|SEA-AD,HVS_COMMON|NPH52::Astro_data_arranged_updatedId_final_batches.qs|NPH52::Endo_data_arranged_updatedId_final_batches.qs|NPH52::ExN_data_arranged_updatedId_final_batches.qs|NPH52::InN_data_arranged_updatedId_final_batches.qs|NPH52::MG_data_arranged_updatedId_final_batches.qs|NPH52::OPC_data_arranged_updatedId_final_batches.qs|NPH52::Oligo_data_arranged_updatedId_final_batches.qs|SEA_AD_COMMON,5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff

contracts/address_namespace.csv,24946770,7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd,"41,238-address canonical namespace",D:\Jepa project\results\v4\stage81a2r_foundation_molecular_address_registry_candidate.csv
```

Fully resolved, and my earlier flag was wrong. The bundle manifest itself declares the canonical home:

svg

```
contracts/address_namespace.csv, 24946770, 7d61ed7b…, "41,238-address canonical namespace",
  source: D:\Jepa project\results\v4\stage81a2r_foundation_molecular_address_registry_candidate.csv

```

Correcting the report.

**Bash **Correct registry finding in report

IN

````
AW="D:/jepa_inv_20260919"; cd "$AW" && python - <<'PY'
import pathlib, hashlib
p=pathlib.Path('CLAUDE_FULL104_INVENTORY_AND_GAP_REPORT_20260919.md')
s=p.read_text(encoding='utf-8')

old="| Canonical registry | `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv` | 24,946,770 B | `7d61ed7b…e4fd` | **MATCH** |"
new="""| Canonical registry (canonical home) | `exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv` | 24,946,770 B | `7d61ed7b…e4fd` | **MATCH** |
| Canonical registry (upstream source copy) | `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv` | 24,946,770 B | `7d61ed7b…e4fd` | **MATCH** (byte-identical duplicate) |"""
assert s.count(old)==1
s=s.replace(old,new)

old2="""### Canonical registry location — flag

The registry whose bytes match the declared current authority `7d61ed7b…` lives at
`results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv`. Its
filename marks it as a **Stage81A2R candidate**, and its path contains `stage81`,
which is on the runtime `FORBIDDEN_PATH_FRAGMENTS` denylist.

This is not a spillover defect — the denylist screens only runtime *output* paths,
and the file's bytes are exactly the declared authority. But the naming is
actively misleading: the current canonical address registry is stored under a
historical Stage81 candidate filename. Anyone applying the project's own
anti-spillover instinct would reject it on sight. Recommend recording the exact
path in the runtime-asset authority so it is not mistaken for historical material,
or copying it to a current-named path and re-binding."""
new2="""### Canonical registry — resolved, no flag

A full content-hash sweep (53,067 candidate files) found **two byte-identical
copies** of `7d61ed7b…`. The canonical home is inside the foundation calibration
bundle, and the bundle's own manifest declares it explicitly:

```
contracts/address_namespace.csv,24946770,7d61ed7b…e4fd,
  "41,238-address canonical namespace",
  source: D:\\Jepa project\\results\\v4\\stage81a2r_foundation_molecular_address_registry_candidate.csv
```

So `exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv`
is the properly-named, manifest-declared canonical registry, and the
`stage81a2r…candidate.csv` file is its recorded upstream source. Use the bundle
path. Header confirms the expected schema (`molecular_address_index,
molecular_address_id, identity_class, current_ensembl_gene_id, …,
registry_semantic_hash`).

An earlier draft of this report flagged the Stage81A2R filename as a misleading
canonical location. That flag was based on an incomplete name-only search and is
**withdrawn**: the correctly-named copy existed all along and is declared in the
bundle manifest."""
assert s.count(old2)==1
s=s.replace(old2,new2)

old3="""2. **Canonical registry LOCATED** (see B) at
   `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv`,
   bytes matching `7d61ed7b…` exactly. The census entrypoint takes `--registry`
   as a required argument and the path is not declared in code, so this path must
   be supplied explicitly."""
new3="""2. **Canonical registry LOCATED** (see B) at
   `exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv`,
   bytes matching `7d61ed7b…` exactly and declared as such in the bundle manifest.
   The census entrypoint takes `--registry` as a required argument and the path is
   not declared in code, so this path must be supplied explicitly."""
assert s.count(old3)==1
s=s.replace(old3,new3)

old4="""- **Canonical registry stored under a Stage81A2R candidate filename**, inside a
  path fragment the project's own runtime denylist rejects. Correct bytes, wrong
  signal. Governance item."""
new4="""- **Canonical registry path should be recorded in the runtime-asset authority.**
  It is not declared in code and exists in two byte-identical copies; the
  manifest-declared canonical home is the bundle's `contracts/address_namespace.csv`."""
assert s.count(old4)==1
s=s.replace(old4,new4)

old5="""and record the registry's exact path in the runtime-asset authority so its
Stage81A2R filename is not mistaken for historical material. Locating the V0/V1
parents is needed only for F13."""
new5="""and record the registry's exact path in the runtime-asset authority, since it is
supplied by hand and exists in two places. Locating the V0/V1 parents is needed
only for F13."""
assert s.count(old5)==1
s=s.replace(old5,new5)

p.write_text(s,encoding='utf-8')
print('report corrected')
print('SHA:',hashlib.sha256(p.read_bytes()).hexdigest())
PY
````

svg

OUT

```
report corrected
SHA: 3aaa1509bf6c9987fd93677c9f53e3191d6def63ea8cb7e0e5132126bee7412d
Shell cwd was reset to d:\Jepa project
```

The background hash sweep finished and corrected me. Report updated (SHA `3aaa1509…`).

**I was wrong about the registry.** There are two byte-identical copies. The canonical one is `exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv`, and the bundle's own manifest declares it as the "41,238-address canonical namespace" — naming the `stage81a2r…candidate.csv` file as its upstream source. So the properly-named copy existed all along; I'd only searched by filename and found the source copy first. My "misleading Stage81A2R filename" flag is withdrawn.

Use the bundle path. Header schema confirms it: `molecular_address_index, molecular_address_id, identity_class, current_ensembl_gene_id, …, registry_semantic_hash`.

That closes the last inventory unknown except the V0/V1 parents, which matter only for F13.

Nothing else changes: no current derived artifacts exist, the GPU is fine, and the environment question (`base` vs `sea-ad-jepa`) is still the thing I'd settle before running anything.