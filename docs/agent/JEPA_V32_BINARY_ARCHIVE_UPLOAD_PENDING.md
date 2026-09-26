# V32 binary-archive transfer — PENDING

The following **exact** small ZIP archives have been verified in the originating ChatGPT environment but have **not yet been pushed to GitHub**. The GitHub connector's binary create_blob action cannot directly consume a container-local file path. Do not claim that a manifest or script is the archive itself.

| Archive | Size | SHA-256 | ZIP entries | CRC |
|---|---:|---|---:|---|
| JEPA_TEACHER_TARGET_V4_NONAUTHORIZING_RESEARCH_PACKAGE_20260926.zip | 29,224 | 349b6ef604084b9c5220f91f9382e6875ce37e34314bf94aa08023725e8f50b4 | 14 | PASS |
| STAGE75_PILOT_COVERAGE_AUDIT_20260926.zip | 6,226 | 7cde16dcf1300a1a3012bb4f7b547efa553b48290db45e503d9f5794ae1e9439 | 4 | PASS |

The local files exist in the originating conversation's /mnt/data and are also embedded byte-for-byte in JEPA_V32_COMPLETE_LOCAL_EVIDENCE_AND_HANDOFF_20260926.zip (outer SHA-256 d49c7a1bba1e48f21fdf8fceb92e8c1176a3c309c2c662249099d6c109b5dc79). **A new chat does not inherit mounted local files.** Transfer the ZIPs through the originating conversation download links or to Claude's laptop; do not silently substitute another historical copy.

On a laptop with a clean checkout of this branch and both ZIPs physically present, run:
```bash
python scripts/agent/upload_v32_research_archives.py --source-dir /path/to/downloaded/files
git diff --cached --stat
git commit -m "research: add exact V32 teacher-target and Stage75 nonauthorizing archives"
git push origin handoff/jepa-v32-teacher-stage75-local-evidence-20260926
```
The uploader refuses wrong branch, dirty tree, incorrect SHA-256/size, bad ZIP CRC, unsafe members, and wrong member count. It does not push automatically. After upload, independently fetch GitHub blob bytes and verify the two original SHA-256 digests. Keep both archives in `research/non_authorizing/v32_20260926/` and never promote their historical findings to current FULL104 scientific qualification.
