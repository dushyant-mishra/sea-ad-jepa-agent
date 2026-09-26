# V32 exact local asset manifest — 2026-09-26

This manifest documents actual files in the chat container. **Successor transfer status, 2026-09-26:** all three small V32 research ZIPs are now physically uploaded at `docs/agent/v32-downloads/` at verified commit `04ccf242b6494e4c2aae558e0a8a3944b85edd8d`. The historical August calibration bundle and large expression/Morabito/FULL104 datasets remain external and are not implied uploaded. Preserve the original local checksums as transfer receipts; independently rehash downloaded bytes before executing on another machine.

| File | SHA-256 | Scope |
|---|---|---|
| JEPA_TEACHER_TARGET_V4_NONAUTHORIZING_RESEARCH_PACKAGE_20260926.zip | 349b6ef604084b9c5220f91f9382e6875ce37e34314bf94aa08023725e8f50b4 | Complete local V4 code/tests/results/report |
| STAGE75_PILOT_COVERAGE_AUDIT_20260926.zip | 7cde16dcf1300a1a3012bb4f7b547efa553b48290db45e503d9f5794ae1e9439 | Local pilot crosswalk code, 33-symbol CSV, summary JSON and README |
| FOUNDATION_CALIBRATION_BUNDLE_20260824.zip | 07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444 | Historical 41,238-address namespace; not current V5 registry |

V4 research package internal exact member byte digests are recorded in chat-local `JEPA_TEACHER_TARGET_V4_PACKAGE_MANIFEST_20260926.json`. The underlying historical discovery expression archive and original 30GB+ FULL104 dataset are **not** being committed again. Original Morabito H5 files are **not** available in this container.

Verified local commands: `cd /mnt/data && python -m unittest -v test_teacher_target_raw_adapter_v3 test_teacher_target_visible_only_adapter_v4` -> 15 tests PASS. `python /mnt/data/stage75_coverage_audit/audit_stage75_pilot.py` -> 27 targets, 7 TFs, 2 ambiguous HLA symbols, 0 missing symbols. These tests do not validate the current live V5 consumer.

Historical committed sources:
- `results/reports/stage72a_external_multiomic_grn_resource_eligibility_audit_report_v1.md`
- `results/reports/stage72b_external_morabito_micro_pvm_grn_construction_report_v1.md`
- `results/tables/stage75_integrated_tf_target_summary_v1.csv` (Git blob fd0f8e12c1161629f53f568f30cbc0bf8e3ff1a1)
- `results/reports/stage75_integrated_evidence_manifest_v1.json`

All three small V32 research ZIPs are now committed on PR #159. The GitHub binary fetch at `04ccf242` returned exact sizes and matching published Git blob identities: combined `d5433975def9fc51551be3f608948b3a1809a999`, V4 `d38a446ca365c53a806f9d05645053737b5da7aa`, Stage75 `ec2be3cef08af4bf887a9286cbabefb3b2b53f29`. SHA-256 remains the download verification key; GitHub presence does not establish local GPU availability.

Final chat-local transfer bundle: `JEPA_V32_COMPLETE_LOCAL_EVIDENCE_AND_HANDOFF_20260926.zip`, 36,717 bytes, SHA-256 `d49c7a1bba1e48f21fdf8fceb92e8c1176a3c309c2c662249099d6c109b5dc79`. Its members were re-read and rehashed after creation. This bundle **is now committed** as `docs/agent/v32-downloads/JEPA_V32_COMPLETE_LOCAL_EVIDENCE_AND_HANDOFF_20260926.zip` on PR #159. Download and verify the original digest before use.
