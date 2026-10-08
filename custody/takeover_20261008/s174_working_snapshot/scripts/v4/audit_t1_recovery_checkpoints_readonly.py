"""Read-only authenticated T1 checkpoint identity audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "exports" / "prod41k_teacher_t1_20260823" / "t1_run"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(update: int) -> dict:
    path = RUN / f"t1_checkpoint_u{update:04d}.pt"
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    online = checkpoint["online_encoder"]
    target = checkpoint["target_encoder"]
    expected_target_keys = {f"encoder.{key}" for key in online}
    target_keys = set(target)
    squared = 0.0
    for key, value in online.items():
        delta = value.detach().float() - target[f"encoder.{key}"].detach().float()
        squared += (delta.double() ** 2).sum().item()
    return {
        "update": update,
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "schema": checkpoint["schema"],
        "experiment_id": checkpoint["experiment_id"],
        "contract_sha256": checkpoint["contract_sha256"],
        "global_update_step": checkpoint["global_update_step"],
        "ema_update_count": checkpoint["ema_update_count"],
        "schedule_cursor": checkpoint["schedule_cursor"],
        "donor_primary_scheduler_cursor": checkpoint["donor_primary_scheduler_cursor"],
        "accumulation_position": checkpoint["accumulation_position"],
        "online_parameter_tensors": len(online),
        "target_parameter_tensors": len(target),
        "online_target_key_bijection": target_keys == expected_target_keys,
        "online_target_parameter_l2": squared**0.5,
    }


if __name__ == "__main__":
    print(json.dumps([audit(0), audit(205)], indent=2))
