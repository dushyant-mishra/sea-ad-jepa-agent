from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(str(ROOT / "scripts" / "v5" / "td_unified" / "apply_task0_b1_b5_repairs_v2.py"), run_name="__main__")

# B2 requires exact identities for the specifically authority-bearing calibration/audit
# records identified by independent review. A generic historical audit wrapper may
# legitimately be custody-only with exact payload identity unavailable. Keep the
# strong rule for authenticated calibration authority, but do not misclassify the
# PR322 navigation wrapper as scientific authority merely because its historical
# authority_basis names an exact audit/receipt mode.
validator = ROOT / "scripts" / "v5" / "td_unified" / "premerger_migration_task0.py"
text = validator.read_text(encoding="utf-8")
old = '''        authority = str(record.get("current_authority", ""))
        basis = record.get("authority_basis")
        if authority.startswith("AUTHENTICATED_CALIBRATION") or basis in {"EXACT_COMMIT_AND_AUTHENTICATED_AUDIT_OR_RECEIPT", "AUTHENTICATED_CALIBRATION_RECEIPT"}:
            raise ValueError(f"authority-bearing identity cannot be unavailable for {label}")
'''
new = '''        authority = str(record.get("current_authority", ""))
        if authority.startswith("AUTHENTICATED_CALIBRATION"):
            raise ValueError(f"authority-bearing identity cannot be unavailable for {label}")
'''
if old not in text:
    raise RuntimeError("expected over-broad exact-identity authority check not found")
validator.write_text(text.replace(old, new), encoding="utf-8")
