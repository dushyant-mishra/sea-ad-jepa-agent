# V42 custody completion guide — seven ORIGINAL binary bytes still outside GitHub

Date 2026-09-26. Scope: preservation steps only, no scientific, training or protected-data authorization. The authoritative 18-file original size+SHA256 register is `docs/agent/chat-local-source-preservation-20260926/JEPA_CHAT_LOCAL_18_FILE_CUSTODY_MANIFEST_V42.json`. GitHub PR #174 already contains **11 exact originals (10 text files, 1 V33 11.9KB research ZIP)**; its hosted SHA256/Git-blob workflow checks those exact source bytes. The seven below remain manifest-only. No claim of remote possession is made.

| Remaining original | Original bytes | SHA256 |
|---|---:|---|
| `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` | 1,531,109 | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` |
| `expression.zip` | 3,599,456 | `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4` |
| `checkpoints.zip` | 71,356,460 | `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` |
| `t1_checkpoint_u0200.zip` | 233,729,581 | `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` |
| `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | 410,278,055 | `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` | 303,979,881 | `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` | 303,979,880 | `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875` |

**Why seven are not in Git:** four files exceed ordinary GitHub's 100MB Git file ceiling; historical checkpoints and foundation donor-level archives should not be silently stuffed into public Git history or treated as current FULL104 science; the present execution container has no direct outbound DNS; the authorized GitHub connector does not accept an attached local file path or upload Release assets. Although smaller bytes can sometimes be relayed through a temporary text encoding, using that for unclassified NPZ or donor metadata in this PUBLIC repo without verifying scientific data-release permissions would be an inappropriate irreversible disclosure. The V33 ZIP was source-only research and thus separately transferred, hashed and audited. No remaining binary is represented as uploaded.

**Recommended offline physical handoff** (on a computer with all seven actual original files after verifying data rights):

1. Obtain the actual **original** bytes, not just these hash strings. Ensure current provenance permits publishing each asset to this **public** repository; otherwise use an approved private versioned, access-controlled store. Treat the opaque NPZ as unclassified pending physical source-identity verification and treat all historical checkpoint weights as historical-only.
2. In the asset directory, run `sha256sum -- <original-filename>` (PowerShell `Get-FileHash <filename> -Algorithm SHA256`) and compare the FULL 64-character digest plus exact byte length with the committed machine manifest. Do not silently accept partial matches, copied inventory strings or hash-mismatched regenerated data.
3. Concatenate the two original discovery parts in `part001,part002` order and stream-SHA the result; expected **607,959,761 bytes** and SHA256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`. This exact physical check already passed in the original chat environment.
4. If external public release is approved, use an independently reviewed DRAFT versioned GitHub Release or other immutable artifact store that supports >100MB files, preserving exact original basenames and unmodified bytes. Do not add all ~1.3GB to Git history or overwrite existing assets in place. Record original vs remote size, full SHA256, URL and release/event receipt separately.
5. Only after separately fetching the actual remote bytes and verifying SHA/size should a reviewer **version** this manifest (e.g. V43), change each actual custody state from `MANIFEST_ONLY` to `UPLOADED_VERIFIED_REMOTE`, and run a second-party check. Updating a README, pasting an asset URL or replaying a SHA from the manifest is not proof of remote originals.

All current scientific gates remain OFF. Even physically authenticated storage does not qualify the contents as independent biology, actual all-donor model training or sealed outcome authority. Historical S9 claimed Windows environment defect was retracted: the Windows NumPy environment was valid with `<env>/Library/bin` on `PATH` before BLAS/LAPACK first call.
