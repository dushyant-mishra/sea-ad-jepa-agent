import json, subprocess, sys
from pathlib import Path

CAL=Path('/mnt/data/jepa_replay_audit/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip')
TD=Path('/mnt/data/jepa_replay_audit/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip')
SCRIPT=Path('/mnt/data/jepa_replay_audit/repo_candidate/scripts/v5/build_td_relational_replay_manifest.py')

def test_rebuild_manifest(tmp_path):
    out_csv=tmp_path/'manifest.csv'; out_json=tmp_path/'receipt.json'
    subprocess.run([sys.executable,str(SCRIPT),'--calibration-zip',str(CAL),'--td-artifacts-zip',str(TD),'--manifest-out',str(out_csv),'--receipt-out',str(out_json)],check=True)
    r=json.loads(out_json.read_text())
    assert r['status']=='PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST'
    assert r['common_core_rows']==17186
    assert r['replay_addresses']==9216
    assert r['manifest_sha256']=='4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660'
    assert all(r['validation'].values())
