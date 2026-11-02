"""Bounded stdin/stdout V2C-only verifier, not an issuer or training entrypoint."""
from __future__ import annotations

import importlib.util
import json
import os
import sys

MAX_INPUT_BYTES = 1_048_576
REFUSAL = b'{"authority_effect":"NONE","status":"REFUSED_STUDENT_V2C_FIXTURE"}\n'
_RUNTIME_UID = 65534
_MEMORY_LIMIT = 256 * 1024 * 1024
_SYSTEM_FS = frozenset(("proc", "sysfs", "tmpfs", "devpts", "mqueue", "cgroup", "cgroup2"))
_ENGINE_FILES = frozenset(("/etc/resolv.conf", "/etc/hostname", "/etc/hosts"))
# Exact engine mount points (Docker defaults plus its masked/read-only paths). A
# prefix rule would admit a host tmpfs bound under /dev, /proc or /sys.
_SYSTEM_MOUNTS = frozenset((
    "/proc", "/dev", "/dev/pts", "/dev/mqueue", "/dev/shm", "/sys", "/sys/fs/cgroup",
    "/proc/asound", "/proc/acpi", "/proc/interrupts", "/proc/kcore", "/proc/keys",
    "/proc/latency_stats", "/proc/timer_list", "/proc/timer_stats", "/proc/sched_debug",
    "/proc/scsi", "/sys/firmware", "/sys/devices/virtual/powercap", "/proc/bus",
    "/proc/fs", "/proc/irq", "/proc/sys", "/proc/sysrq-trigger",
))


def _reject_duplicate(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("duplicate JSON key")
        result[k] = v
    return result


def _reject_constant(_value):
    raise ValueError("nonfinite JSON token")


def _read_text(path):
    try:
        with open(path, encoding="ascii") as handle:
            return handle.read().strip()
    except (OSError, UnicodeDecodeError):
        return None


def _runtime_restricted():
    """True only if the documented launch restrictions are observable from inside.

    Fail-closed for the DEFAULT entrypoint when a launcher omits or weakens a
    flag. Not an attestation: an --entrypoint override or a hostile Docker
    operator bypasses it, and the receipt still does not say where it ran.
    """
    if (os.getuid() != _RUNTIME_UID or os.getgid() != _RUNTIME_UID
            or not set(os.getgroups()) <= {_RUNTIME_UID}):
        return False
    status = {}
    for line in (_read_text("/proc/self/status") or "").splitlines():
        key, _, value = line.partition(":")
        status[key] = value.strip()
    if any(status.get(k) != "0000000000000000"
           for k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")):
        return False
    if status.get("NoNewPrivs") != "1" or status.get("Seccomp") != "2":
        return False
    try:
        if sorted(os.listdir("/sys/class/net")) != ["lo"]:
            return False
        if [p for p in os.listdir("/proc") if p.isdigit()] != [str(os.getpid())]:
            return False
    except OSError:
        return False
    mounts = _read_text("/proc/self/mountinfo")
    if not mounts:
        return False
    for line in mounts.splitlines():
        fields = line.split()
        if "-" not in fields:
            return False
        sep = fields.index("-")
        point, options, fstype = fields[4], set(fields[5].split(",")), fields[sep + 1]
        if point == "/" or point in _ENGINE_FILES:
            ok = "ro" in options
        elif point == "/tmp":
            ok = fstype == "tmpfs" and {"nosuid", "nodev", "noexec"} <= options
        elif point in _SYSTEM_MOUNTS:
            ok = fstype in _SYSTEM_FS
        elif point.startswith("/sys/fs/cgroup/"):
            ok = fstype == "cgroup"
        else:
            ok = False  # any bind mount, volume or extra tmpfs elsewhere
        if not ok:
            return False
    pids = _read_text("/sys/fs/cgroup/pids.max") or _read_text("/sys/fs/cgroup/pids/pids.max")
    memory = (_read_text("/sys/fs/cgroup/memory.max")
              or _read_text("/sys/fs/cgroup/memory/memory.limit_in_bytes"))
    return (pids == "1" and memory is not None and memory.isdigit()
            and int(memory) <= _MEMORY_LIMIT)


def _load_verifier():
    path = "/opt/student/student_v2c.py"
    spec = importlib.util.spec_from_file_location("standalone_student_v2c", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("verifier unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    # No private source paths, external registries, issuer keys or teacher input.
    try:
        if not _runtime_restricted():
            raise RuntimeError("documented launch restrictions not observed")
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if not raw or len(raw) > MAX_INPUT_BYTES:
            raise ValueError("request too large")
        request = json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=_reject_duplicate,
            parse_constant=_reject_constant,
        )
        if type(request) is not dict or set(request) != {"student_view", "expected_policy"}:
            raise ValueError("unsupported request shape")
        verifier = _load_verifier()
        receipt = verifier.validate_student_v2c(
            student_view=request["student_view"], expected_policy=request["expected_policy"]
        )
        if (type(receipt) is not dict or receipt.get("authority_effect") != "NONE"
            or receipt.get("real_training_authorized") is not False):
            raise ValueError("unexpected authority claim")
        sys.stdout.write(json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        return 0
    except Exception:
        # No error details or exception tracebacks are exposed to caller.
        sys.stdout.buffer.write(REFUSAL)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
