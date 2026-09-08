# D1 real-data source inventory

Status: `D1_SOURCE_DISCOVERY_COMPLETE__PRODUCTION_TEACHER_STILL_BLOCKED`

Date: 2026-09-07

This inventory records real-data artifacts and hashes recovered during D1 planning. It does not authorize a historical checkpoint for D1 and does not convert auxiliary samples into production derivation authority.

## Full production population authority

The lawful fit-population target is:

- 104 fit donors;
- 4,553,407 fit cells;
- 42 operators;
- HVS 198,718 cells;
- NPH52 236,476 cells;
- SEA_AD 4,118,213 cells;
- 41,238 Molecular Ledger addresses.

These totals are consistent between the historical Phase-2 numeric authority and the recovered calibration-bundle metadata.

## Recovered calibration bundle

Uploaded artifact:

`FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`

Outer SHA-256:

`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Important contained authorities:

- `contracts/production_loader_manifest.json`
  - file SHA-256: `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`
  - semantic hash: `5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff`
  - asset registry: `24af817cbea5ea9da37eea851cb97c1d58bcc91bcd08682c4772fcd9c7e5c59f`
  - collision authority: `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`
  - foundation split registry: `35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433`
  - NPH sample manifest: `f8294152075d6d2123b13136adb5a6017543bcf0b62951be40938a06740893bb`
  - molecular registry: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
  - supplemental authority: `16f4b62565d483bb4d77bb653f300dd1515df0423877b7dd36eb2545d89aedb1`
  - support authority: `ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa`

Recovered metadata/support file SHA-256 values:

- `metadata/FOUNDATION_METADATA_DONOR.csv`:
  `c9cbe47d4727aabec8a0c3fed5474c2dab4f9f2b8848357e08b0cec6ef044508`
- `metadata/FOUNDATION_METADATA_OPERATOR.csv`:
  `d5ead72b682c0d8ac81e8c8f700d473b8c0a407b077294e41ec616a604078ac6`
- `metadata/FOUNDATION_METADATA_SOURCE.csv`:
  `1e441f1a007c2d50bdce19893738bd0b56300c993a6a49c6188a64f54ddc7bba`
- `support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv`:
  `8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da`
- `support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`:
  `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

These are real-data provenance/support inputs. They do not themselves provide a mechanically healthy trained teacher.

## Recovered real 50,000-cell discovery sample

Uploaded auxiliary artifact:

`expression.zip`

Outer SHA-256:

`1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`

Contained sample-freeze facts:

- 25,000 Sample-A rows;
- 25,000 Sample-B rows;
- disjoint;
- fit donors 104;
- held-out expression not read;
- DEV expression not read;
- SEALED expression not read;
- pathology not read.

Hashes:

- `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`:
  `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
- `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`:
  `c0f1f68fd3af9b95479fdc05536533481bd42710bc67a94a1c4996d4e4fe3b39`
- recorded 50k expression NPZ SHA-256:
  `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`
- cells: 50,000;
- addresses: 41,238;
- nnz: 246,702,069;
- normalization: `log1p(raw_count*10000/full_source_library) exactly once`.

This 50k sample is **auxiliary only** for D1 v1: I/O, schema, replay, throughput, and estimator mechanics. It cannot select full-population production adaptive values under the new D1 authority.

## Recovered split full-expression archive

The uploaded split archive manifest records:

- complete archive bytes: 607,959,761;
- complete archive SHA-256:
  `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`;
- part001 SHA-256:
  `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`;
- part002 SHA-256:
  `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`.

The parts were concatenated and the complete archive SHA-256 independently reproduced exactly. The archive contains the 50k `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz`, not the full 4,553,407-cell production population.

## Historical checkpoints are not D1 production teachers

Historical u10-u205 training is already classified `TRAINING_MECHANICS_DEFECT_INHERITED`. Therefore historical checkpoint archives, including any u200/u205 derivative, must not be used as the healthy teacher for production D1 parameter derivation.

A future mechanically healthy teacher must come from the repaired successor path after its required review/qualification and must be byte/root-bound before D1 production execution.

## Source-role conclusion

For D1 implementation now:

- use the full-fit metadata, loader, Molecular Ledger, and support authorities to build/audit the production population reader;
- the 50k expression archive may exercise the reader/streaming interface but cannot generate production adaptive parameter values;
- synthetic fixtures may test mathematics only;
- teacher-dependent production values remain `WAIT_HEALTHY_TRAINED_TEACHER`.
