#!/usr/bin/env python3
"""Controller-side materialization of V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1.json.

Authority: PR #317 controller comment 6137248929 (staged first-opaque-world 88-fit smoke at a61437ba; same 1,056-record ledger).
The fit_seed_ledger is produced only by the frozen scripts/v79/v79_v2_core_seed_ledger.build_seed_ledger, with the
contract, root manifest and blinded index loaded exactly as prepare_v79_v2_core_qualification_campaign.prepare loads
them. No seed is typed, derived differently, reordered or edited. Nothing about world identity is printed; the
controller root manifest stays outside fit custody (prepare() re-derives the ledger and refuses any difference).

usage: materialize_execution_authorization.py <repo root at 559a1c10> <package dir> <output json>
"""
import hashlib
import json
import sys
from pathlib import Path

root, package_dir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(root / "scripts" / "v79"))
import v79_v2_core_fit_contract as FC  # noqa: E402
import v79_v2_core_fit_surface as F  # noqa: E402
import v79_v2_core_launch as L  # noqa: E402
import v79_v2_core_qualification_custody as C  # noqa: E402
import v79_v2_core_seed_ledger as S  # noqa: E402

if out.exists():
    raise SystemExit(f"STOP: authorization already exists: {out}")
contract_path = root / "results/v79/v2_core_qualification" / L.FINAL_CONTRACT_NAME
contract = L.require_launch_authority(contract_path, root=root)
assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == FC.SOURCE_CONTRACT_SHA256 == \
    "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
index = F.load_blinded_index(package_dir, expected_mode="QUALIFICATION_TRUTH_FREEZE",
                             expected_root_manifest_sha=F.QUALIFICATION_ROOT_MANIFEST_SHA256,
                             expected_index_sha=F.QUALIFICATION_INDEX_SHA256)
root_manifest = json.loads((package_dir / F.ROOT_MANIFEST_NAME).read_text(encoding="utf-8"))
ledger = S.build_seed_ledger(contract, root_manifest, index.index)
auth = {"schema": C.AUTH_SCHEMA,
        "qualification_campaign_authorized": True,
        "benchmark_controller_pass": True,
        "contract_sha256": FC.SOURCE_CONTRACT_SHA256,
        "blinded_index_sha256": F.QUALIFICATION_INDEX_SHA256,
        "fit_seed_ledger": ledger,
        "scoring_authorized": False,
        "training_authorized": False,
        "controller_authority": "PR #317 comment 6137248929",
        "execution_head": "a61437ba284e9e75b0557157ad68e56eacd8f8fe",
        "seed_ledger_source": "scripts/v79/v79_v2_core_seed_ledger.build_seed_ledger at a61437ba (controller-side)"}
C.sanitize_execution_authorization(auth, expected_seed_ledger=ledger)   # same check prepare() applies
out.parent.mkdir(parents=True, exist_ok=True)
raw = (json.dumps(auth, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
out.write_bytes(raw)
print(json.dumps({"fit_seed_ledger_entries": len(ledger), "unique_fit_ids": len({x["fit_id"] for x in ledger}),
                  "authorization_sha256": hashlib.sha256(raw).hexdigest(), "path": str(out)}))
