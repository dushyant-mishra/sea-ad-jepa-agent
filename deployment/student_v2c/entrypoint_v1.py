"""Bounded stdin/stdout V2C-only verifier, not an issuer or training entrypoint."""
from __future__ import annotations

import importlib.util
import json
import sys

MAX_INPUT_BYTES = 1_048_576
REFUSAL = b'{"authority_effect":"NONE","status":"REFUSED_STUDENT_V2C_FIXTURE"}\n'


def _reject_duplicate(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("duplicate JSON key")
        result[k] = v
    return result


def _reject_constant(_value):
    raise ValueError("nonfinite JSON token")


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
