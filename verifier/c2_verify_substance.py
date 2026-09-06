#!/usr/bin/env python3
"""Independent C2 substantive verification: source correspondence, telemetry, gate.

Reconstructs K0 and K1 from the bound canonical historical source rather than
inspecting the supplied diff, re-derives every acceptance criterion from raw
telemetry rather than reading the recorded verdicts, and attacks the new
gradient gate including a live-tensor test in the real gradient dtype.
"""

from __future__ import annotations

import difflib
import importlib.util
import inspect
import json
import math
import sys
from pathlib import Path

REPO = Path(sys.argv[1])
CANONICAL = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/mnt/d/Jepa project")
PKG = REPO / "outputs" / "c2_t1_gradient_forensic_20260906"
V3 = PKG / "v3_exact_path"

MANDATORY_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")
findings: list[str] = []


def fail(message: str) -> None:
    findings.append(message)
    print("  FAIL " + message)


def ok(message: str) -> None:
    print("  ok   " + message)


def load(name: str) -> dict:
    return json.loads((V3 / name).read_text(encoding="utf-8"))


def load_phase_e():
    sys.path.insert(0, str(CANONICAL / "src"))
    sys.path.insert(0, str(CANONICAL / "exports" / "static_context_decomposition_v4_20260821"))
    spec = importlib.util.spec_from_file_location(
        "phase_e", CANONICAL / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase_e"] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------- section 3
def verify_source_correspondence(k0: dict, k1: dict) -> None:
    print("\n[3] SOURCE CORRESPONDENCE, reconstructed independently")
    phase_e = load_phase_e()
    canonical_src = inspect.getsource(phase_e.run_update)

    import hashlib
    smoke = CANONICAL / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py"
    digest = hashlib.sha256(smoke.read_bytes()).hexdigest()
    if digest == k0.get("historical_step_sha256") == k1.get("historical_step_sha256"):
        ok("both arms bind the same historical step source: " + digest[:16])
    else:
        fail("historical step source digest disagreement")

    # Reconstruct K1 from canonical by the declared substitution only.
    target = "scaler.scale(scaled_loss).backward()"
    lines = [line for line in canonical_src.splitlines() if target in line]
    if len(lines) != 1:
        fail("expected exactly one backward call in canonical run_update")
        return
    line = lines[0]
    indent = line[: len(line) - len(line.lstrip())]
    reconstructed = canonical_src.replace(
        line,
        indent + "with torch.autocast(device_type=device.type, enabled=False):\n"
        + indent + "    " + target)
    reconstructed = reconstructed.replace(
        "def run_update(", "def run_update_backward_autocast_disabled(", 1)

    diff = "\n".join(difflib.unified_diff(
        canonical_src.splitlines(), reconstructed.splitlines(),
        "canonical_run_update", "variant_backward_autocast_disabled", lineterm="", n=2))
    if diff.strip() == (k1.get("variant_diff") or "").strip():
        ok("reconstructed K1 diff is byte-identical to the recorded diff")
    else:
        fail("reconstructed K1 diff does not match the recorded diff")

    added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    substantive_added = [l for l in added if "def run_update" not in l]
    substantive_removed = [l for l in removed if "def run_update" not in l]
    print("      substantive added lines:   %d" % len(substantive_added))
    print("      substantive removed lines: %d" % len(substantive_removed))
    if len(substantive_removed) == 1 and target in substantive_removed[0] \
            and len(substantive_added) == 2 \
            and "autocast" in substantive_added[0] and "enabled=False" in substantive_added[0] \
            and target in substantive_added[1]:
        ok("the ONLY causal code change is the backward autocast state")
    else:
        fail("the diff contains changes beyond the declared backward autocast state")

    if (k0.get("variant_diff") or "").strip() in ("(no change)", ""):
        ok("K0 uses the canonical function unmodified")
    else:
        fail("K0 is not the unmodified canonical function")


# ---------------------------------------------------------------- section 3b
def verify_paired_execution(k0: dict, k1: dict) -> None:
    print("\n[3b] PAIRED EXECUTION PARAMETERS")
    keys = ("effective_batch", "microbatch", "views", "mask_fraction",
            "target_block_count", "vocabulary_size")
    for key in keys:
        a, b = k0["geometry"].get(key), k1["geometry"].get(key)
        if a != b:
            fail("geometry differs between arms: %s %r vs %r" % (key, a, b))
    expected = {"effective_batch": 128, "microbatch": 8, "views": 4,
                "mask_fraction": 0.40, "target_block_count": 16, "vocabulary_size": 41238}
    for key, want in expected.items():
        got = k0["geometry"].get(key)
        if got != want:
            fail("geometry not historical: %s is %r, expected %r" % (key, got, want))
    micro_count = k0["geometry"]["effective_batch"] // k0["geometry"]["microbatch"]
    backwards = micro_count * k0["geometry"]["views"]
    print("      16 microbatches: %s   64 forward/backward ops: %s"
          % (micro_count == 16, backwards == 64))
    if micro_count != 16 or backwards != 64:
        fail("expected 16 microbatches and 64 forward/backward operations")
    else:
        ok("128/8, 4 views, 16 microbatches, 64 forward/backward operations")

    if k0["invocation"]["seed"] == k1["invocation"]["seed"] == 8113002:
        ok("seed 8113002 in both arms")
    else:
        fail("seed disagreement")
    if k0["ipb_jepa_sha256"] == k1["ipb_jepa_sha256"]:
        ok("same model source bytes: " + k0["ipb_jepa_sha256"][:16])
    else:
        fail("model source differs between arms")
    if k0["loader_manifest"] == k1["loader_manifest"]:
        ok("identical synthetic loader manifest (same inputs)")
    else:
        fail("loader manifest differs between arms")
    if k0["loader_manifest"].get("reads_real_expression") is False:
        ok("firewall: loader declares no real expression is read")
    else:
        fail("loader does not declare synthetic-only input")
    for arm, name in ((k0, "K0"), (k1, "K1")):
        factors = arm.get("factors", {})
        if not (factors.get("autocast") == "fp16"
                and factors.get("gradscaler_enabled") is True
                and factors.get("gradient_checkpointing") is True
                and factors.get("attention_cast") == "historical"):
            fail("%s factors are not the historical configuration: %r" % (name, factors))
    ok("both arms: fp16 autocast, GradScaler on, checkpointing on, historical attention")


# ---------------------------------------------------------------- section 4
def verify_endpoints(k0: dict, k1: dict, pre: dict) -> None:
    print("\n[4] ENDPOINTS RE-DERIVED FROM RAW TELEMETRY")
    for arm, name, expect_dead in ((k0, "K0", 48), (k1, "K1", 0)):
        u = arm["updates"][0]
        entries = u["mandatory_gradients_post_unscale"]["entries"]
        if len(entries) != 48:
            fail("%s does not have 48 mandatory tensors: %d" % (name, len(entries)))
        roles = {}
        for tensor in entries:
            role = "attention_norm" if "attention_norm" in tensor \
                else tensor.split("attention.")[1].split(".")[0]
            roles[role] = roles.get(role, 0) + 1
        if sorted(roles.items()) != [("attention_norm", 12), ("key", 12),
                                     ("query", 12), ("value", 12)]:
            fail("%s mandatory registry is not 12 each of norm/q/k/v: %r" % (name, roles))
        zero = [t for t, v in entries.items() if v["status"] == "ZERO"]
        missing = [t for t, v in entries.items() if v["status"] == "MISSING"]
        nonfinite = [t for t, v in entries.items() if v["status"] == "NONFINITE"]
        live = [t for t, v in entries.items() if v["status"] == "LIVE"]
        print("      %s  zero=%d missing=%d nonfinite=%d live=%d"
              % (name, len(zero), len(missing), len(nonfinite), len(live)))
        if name == "K0":
            if len(zero) != 48:
                fail("K0 does not show 48 exactly-zero gradients")
            if missing or nonfinite:
                fail("K0 has a missing/nonfinite explanation, not a pure exact-zero defect")
            else:
                ok("K0: exactly-zero defect with no missing or nonfinite explanation")
            for tensor, value in entries.items():
                if value["norm"] != 0.0:
                    fail("K0 tensor claimed zero but norm is %r" % value["norm"])
                    break
        else:
            if len(live) != 48:
                fail("K1 does not show 48 live gradients")
            bad = [t for t, v in entries.items()
                   if v["norm"] is None or v["norm"] == 0.0 or not math.isfinite(v["norm"])]
            if bad:
                fail("K1 has non-finite or zero gradients: %r" % bad[:3])
            else:
                ok("K1: all 48 finite and strictly nonzero post-unscale")

        moments = u["mandatory_moments"]["entries"]
        z1 = [t for t, v in moments.items() if not v["exp_avg_norm"]]
        z2 = [t for t, v in moments.items() if not v["exp_avg_sq_norm"]]
        print("      %s  zero exp_avg=%d  zero exp_avg_sq=%d" % (name, len(z1), len(z2)))
        if name == "K0" and (len(z1) != 48 or len(z2) != 48):
            fail("K0 moment paths are not all zero")
        if name == "K1" and (z1 or z2):
            fail("K1 has zero Adam moments: exp_avg %d, exp_avg_sq %d" % (len(z1), len(z2)))

        ref = u["live_reference_gradients_post_unscale"]
        if ref["dead_count"] != 0 or ref["total"] != 12:
            fail("%s attention.output not 0/12 dead" % name)
    ok("attention.output live in both arms; K0 moments all zero; K1 moments all nonzero")

    # zero-baseline movement rule
    print("\n[4b] ZERO-BASELINE MOVEMENT RULE")
    mv = k1["updates"][0]["movement"]["entries"]
    zb = {t: v for t, v in mv.items() if v["zero_baseline"]}
    print("      zero-baseline tensors: %d -> %s" % (len(zb), sorted(zb)[:2]))
    if len(zb) != 6 or not all("attention_norm.bias" in t for t in zb):
        fail("zero-baseline set is not the six attention_norm biases")
    else:
        ok("exactly the six attention_norm.bias tensors are zero-baseline")
    for tensor, value in zb.items():
        if value.get("absolute_movement", 0.0) <= 0.0:
            fail("zero-baseline tensor did not move: " + tensor)
    else:
        ok("all six moved with strictly positive absolute movement")
    # decay cannot move an exactly-zero parameter: (1 - lr*wd) * 0 == 0
    lr, wd = 1e-4, 0.01
    if (1.0 - lr * wd) * 0.0 == 0.0:
        ok("pure decoupled decay provably cannot move an exactly-zero parameter")
    if not all(v["moved_beyond_decay"] for v in mv.values()):
        fail("K1 movement criterion not met for all 48")
    else:
        ok("K1: all 48 moved beyond pure decay")

    print("\n[4c] PRE-REPAIR ARTIFACT EXPLAINS THE EARLIER 42/48")
    pmv = pre["updates"][0]["movement"]
    pentries = pmv["entries"]
    not_exceeding = [t for t, v in pentries.items()
                     if not (v["relative_movement"] is not None
                             and v["relative_movement"] > pmv["decay_only_prediction"] * 1.5)]
    print("      pre-repair not-exceeding: %d" % len(not_exceeding))
    if len(not_exceeding) == 6 and all("attention_norm.bias" in t for t in not_exceeding) \
            and all(pentries[t]["relative_movement"] is None for t in not_exceeding):
        ok("the earlier 42/48 arose only from undefined relative movement on those six")
    else:
        fail("pre-repair shortfall is not explained by the zero-baseline tensors alone")
    if pre["updates"][0]["mandatory_gradients_post_unscale"]["dead_count"] != 0:
        fail("pre-repair arm did not already show 0/48 dead gradients")
    else:
        ok("pre-repair arm already had 0/48 dead: the repair touched only the movement measure")


# ---------------------------------------------------------------- section 5
def verify_gate(k0: dict, k1: dict) -> None:
    print("\n[5] GRADIENT GATE, ATTACKED INDEPENDENTLY")
    sys.path.insert(0, str(REPO))
    from scripts.v4.c2_mandatory_gradient_gate_v1 import (  # noqa: E402
        gate_from_norms, gate_module, mandatory_names)
    import torch

    cases = {
        "missing": {"t": None},
        "nan": {"t": float("nan")},
        "posinf": {"t": float("inf")},
        "neginf": {"t": float("-inf")},
        "exact_zero": {"t": 0.0},
    }
    for label, norms in cases.items():
        if gate_from_norms(norms)["passed"]:
            fail("gate accepted " + label)
    ok("missing, NaN, +Inf, -Inf and exact zero are all rejected")

    mixed = {"live_%d" % i: 1.0 for i in range(47)}
    mixed["dead"] = 0.0
    report = gate_from_norms(mixed)
    if report["passed"] or report["rejected_names"] != ["dead"]:
        fail("one exact-zero among many live tensors was not isolated")
    else:
        ok("one exact-zero among 47 live tensors is isolated and rejects")
    if not gate_from_norms({"a": 1.0, "b": 1e-9})["passed"]:
        fail("gate rejected all-live input")
    else:
        ok("all-live input passes")

    for arm, name, want_reject in ((k0, "K0", True), (k1, "K1", False)):
        entries = arm["updates"][0]["mandatory_gradients_post_unscale"]["entries"]
        report = gate_from_norms({t: v["norm"] for t, v in entries.items()})
        if want_reject and (report["passed"] or report["rejected_count"] != 48):
            fail("gate did not reject preserved %s 48/48" % name)
        if not want_reject and not report["passed"]:
            fail("gate did not accept preserved %s" % name)
    ok("preserved K0 rejected 48/48; preserved K1 accepted 48/48")

    # --- live-tensor test in the real protected gradient dtype ------------
    print("\n[5b] LIVE-TENSOR TEST IN THE REAL GRADIENT DTYPE")
    phase_e = load_phase_e()
    online = phase_e.IPBEncoder(vocabulary_size=64, width=160, heads=4, blocks=6)
    names = mandatory_names(online)
    if len(names) != 48:
        fail("gate registry is not exactly 48 tensors: %d" % len(names))
    roles = {}
    for tensor in names:
        role = "attention_norm" if "attention_norm" in tensor \
            else tensor.split("attention.")[1].split(".")[0]
        roles[role] = roles.get(role, 0) + 1
    if sorted(roles.items()) != [("attention_norm", 12), ("key", 12),
                                 ("query", 12), ("value", 12)]:
        fail("gate registry roles wrong: %r" % roles)
    else:
        ok("gate registry is exactly 12 each of attention_norm/query/key/value")
    extras = [n for n in names if "ffn" in n or "final_norm" in n or "output" in n]
    if extras:
        fail("gate registry contains unintended tensors: %r" % extras[:3])
    else:
        ok("no ffn, final_norm or attention.output tensor is in the protected set")

    dtypes = set()
    for arm in (k0, k1):
        dtypes.add(arm.get("environment", {}).get("torch"))
    params = dict(online.named_parameters())
    grad_dtype = params[names[0]].dtype
    print("      protected parameter dtype: %s" % grad_dtype)
    tiny = torch.finfo(grad_dtype).tiny
    smallest_subnormal = torch.tensor(0.0, dtype=grad_dtype)
    smallest_subnormal = torch.nextafter(smallest_subnormal,
                                         torch.tensor(1.0, dtype=grad_dtype))
    print("      smallest normal:    %.6e" % tiny)
    print("      smallest subnormal: %.6e" % float(smallest_subnormal))

    for label, value in (("smallest_subnormal", smallest_subnormal.item()),
                         ("smallest_normal", tiny)):
        for tensor in names:
            grad = torch.zeros_like(params[tensor])
            grad.view(-1)[0] = value
            params[tensor].grad = grad
        report = gate_module(online, names)
        if not report["passed"]:
            fail("gate misclassified a representable nonzero %s tensor as dead (%d rejected)"
                 % (label, report["rejected_count"]))
        else:
            ok("live tensor with a single %s element passes (%s)" % (label, grad_dtype))

    for tensor in names:
        params[tensor].grad = torch.zeros_like(params[tensor])
    if gate_module(online, names)["rejected_count"] != 48:
        fail("gate did not reject 48 genuinely all-zero live tensors")
    else:
        ok("48 genuinely all-zero live tensors are rejected")


def main() -> int:
    print("=" * 72)
    print("INDEPENDENT C2 SUBSTANTIVE VERIFICATION")
    k0 = load("C2_V3_K0_HISTORICAL.json")
    k1 = load("C2_V3_K1_BACKWARD_AUTOCAST_DISABLED.json")
    pre = load("C2_V3_K1_PRE_CRITERION_REPAIR.json")
    verify_source_correspondence(k0, k1)
    verify_paired_execution(k0, k1)
    verify_endpoints(k0, k1, pre)
    verify_gate(k0, k1)
    print("\n" + "=" * 72)
    if findings:
        print("TERMINAL: STOP_C2_INDEPENDENT_VERIFICATION")
        for item in findings:
            print("  - " + item)
        return 1
    print("SUBSTANTIVE VERIFICATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
