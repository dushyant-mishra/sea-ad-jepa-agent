"""CPU proof that the synthetic GPU follow-on keeps original science frozen.

No optimizer or CUDA work is performed by these tests.  Original Stage81A3
result, all original scripts, and historical checkpoints must remain intact.
"""
from __future__ import annotations
import ast
import hashlib
import math
from pathlib import Path
import statistics
import subprocess
import types
import typing
import unittest

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "scripts/v4/stage81a3_ipb_jepa_feasibility.py"
DERIVED = ROOT / "scripts/v4/stage81a3_ipb_jepa_only_postrepair_rerun_20261104.py"
FROZEN_ORIGINAL_GIT_BLOB = "49206efd40b8f7a69891d788f657fc5d44d9f687"
OLD_PARTIAL_RESULT_SHA256 = (
    "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308"
)


def function_text(path, name):
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    nodes = [x for x in module.body if isinstance(x, ast.FunctionDef) and x.name == name]
    assert len(nodes) == 1
    return ast.get_source_segment(source, nodes[0])


def get_gate():
    """Execute only the independent stdlib+numpy-shaped gate, no model imports."""
    source = DERIVED.read_text(encoding="utf-8")
    module = ast.parse(source)
    node = next(x for x in module.body if isinstance(x, ast.FunctionDef)
                and x.name == "postrepair_gate")
    ns = {
        "Any": typing.Any,
        "FIXTURES": ("balanced_multifactor", "dominant_axis_multifactor"),
        "SEEDS": (8114001, 8114002),
        "np": types.SimpleNamespace(
            median=statistics.median,
            isfinite=math.isfinite,
        ),
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]),
                 str(DERIVED), "exec"), ns)
    return ns["postrepair_gate"]


def example_runs():
    result = []
    for fixture in ("balanced_multifactor", "dominant_axis_multifactor"):
        for seed in (8114001, 8114002):
            result.append({
                "fixture": fixture, "seed": seed, "condition": "jepa_only",
                "training": {
                    "optimizer_updates": 500, "ema_updates": 500,
                    "nonfinite_loss_events": 0, "nonfinite_gradient_events": 0,
                    "target_gradient_events": 0, "gradscaler_skips": 0,
                    "cuda_oom_events": 0,
                },
                "final_metrics": {
                    "token_encoder_retention": .96,
                    "cell_retention": .91,
                    "masked_to_full": .85,
                    "masked_minus_visible_raw": .14,
                },
                "checkpoints": [{"readouts": {
                    "target_cell": {"mean_r2": .72},
                    "online_masked_cell": {"mean_r2": .62},
                }}],
                "references": {
                    "visible_60_percent_raw": {"mean_r2": .48},
                    "raw_pca160": {"mean_r2": .80},
                },
            })
    return result


class FrozenRerunContractTests(unittest.TestCase):
    def test_original_is_unchanged_git_blob(self):
        observed = subprocess.check_output([
            "git", "rev-parse",
            "HEAD:scripts/v4/stage81a3_ipb_jepa_feasibility.py"
        ], cwd=ROOT, text=True).strip()
        self.assertEqual(observed, FROZEN_ORIGINAL_GIT_BLOB)

    def test_source_compiles_and_does_not_rewrite_parent(self):
        original = ORIGINAL.read_text(encoding="utf-8")
        derived = DERIVED.read_text(encoding="utf-8")
        ast.parse(derived)
        self.assertIn(OLD_PARTIAL_RESULT_SHA256, derived)
        self.assertIn('CONDITIONS = ("jepa_only",)', derived)
        self.assertIn('CONDITIONS = ("ipb_jepa", "anchor_only")', original)
        self.assertNotIn('OUTPUT_JSON = Path("results/v4/stage81a3_ipb_jepa_feasibility.json")', derived)
        main = function_text(DERIVED, "main")
        self.assertNotIn("run_real_forward_smoke(", main)
        self.assertNotIn("append_documentation(", main)
        self.assertIn("if OUTPUT_JSON.exists():", main)
        self.assertIn("if not args.resume:", main)
        self.assertIn("resume rejected duplicate, invalid or off-schedule arm", main)
        self.assertIn("code_identity()", main)
        self.assertIn("torch.cuda.is_available()", main)
        self.assertIn("del kept", main)
        self.assertIn("atomic_json(OUTPUT_JSON, payload)", main)
        self.assertLess(
            derived.index('sys.path.insert(0, str(ROOT / "src"))'),
            derived.index('from scripts.v4.f1b_c3_training_successor_v2 import')
        )

    def test_model_gradient_and_ema_proof_not_removed(self):
        s = function_text(DERIVED, "train_run")
        self.assertIn('condition != "jepa_only"', s)
        self.assertIn('list(online.parameters()) + list(predictor.parameters())', s)
        self.assertIn('anchor = {"gene": torch.zeros((), device=device)}', s)
        self.assertNotIn("gene_anchor_loss(", s)
        self.assertNotIn("decoder(", s)
        self.assertIn("enforce_unscaled_gradients(online, predictor)", s)
        self.assertIn("enforce_adam_moments(optimizer, online, predictor)", s)
        self.assertIn("protected optimizer step did not advance exactly once", s)
        self.assertIn("_optimizer_step_value(optimizer, p)", s)
        self.assertIn("enforce_unscaled_gradients(online, predictor)", s)
        self.assertIn("scaler.scale(loss / ACCUMULATION).backward()", s)
        self.assertIn("controller.after_successful_optimizer_step(momentum=EMA)", s)
        self.assertNotIn("evaluate_final_molecular_information(", s)

    def test_good_planted_recovery_only_passes_when_all_gates_met(self):
        gate = get_gate()
        d = gate(example_runs())
        self.assertEqual(d["classification"],
                         "SYNTHETIC_ONLY_JEPA_ONLY_INFORMATION_RECOVERY_PASS")
        self.assertTrue(d["per_fixture_median_gates_pass"])

    def test_not_even_one_silent_bad_masked_student(self):
        data = example_runs()
        data[0]["final_metrics"]["masked_minus_visible_raw"] = -.2
        self.assertTrue(get_gate()(data)["classification"].endswith("FAIL"))

    def test_fixture_median_must_pass_old_historic_threshold(self):
        data = example_runs()
        data[0]["final_metrics"]["token_encoder_retention"] = .91
        data[1]["final_metrics"]["token_encoder_retention"] = .98
        self.assertTrue(get_gate()(data)["classification"].endswith("FAIL"))

    def test_partial_training_does_not_count_as_new_science(self):
        data = example_runs()
        data[0]["training"]["optimizer_updates"] = 499
        with self.assertRaisesRegex(RuntimeError, "500 protected"):
            get_gate()(data)

    def test_guard_failure_is_noncompensable(self):
        data = example_runs()
        data[0]["training"]["gradscaler_skips"] = 1
        with self.assertRaisesRegex(RuntimeError, "mechanical"):
            get_gate()(data)


if __name__ == "__main__":
    unittest.main()
