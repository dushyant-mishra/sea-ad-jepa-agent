from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))

import td_relational_successor_readiness_v1 as R


def test_gate_identity_hashes_qualification_boundary_and_disk_firewall():
    binding=R.build_relational_gate_binding(ROOT)
    decision=set(binding['decision_files'])
    required={
        'scripts/v5/td_test_qualification_package_v1.py',
        'scripts/v5/td_relational_successor_synthetic_adapter_v1.py',
        'scripts/v5/td_relational_successor_qualification_runner_v1.py',
        'scripts/v5/td_relational_successor_disk_runner_v1.py',
    }
    assert required <= decision
