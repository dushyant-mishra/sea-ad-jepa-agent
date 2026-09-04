from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.v4 import validate_f1_production_mechanics_acceptance_v1 as subject


PACKAGE = Path("outputs/contextual_teacher_target_v1_f1_production_mechanics_acceptance_20260903")
SOAK = "F1_MECHANICS_WSL_GPU_STABILITY_SOAK.json"
RUNTIME = "F1_MECHANICS_RUNTIME_PROJECTION.json"


class IndependentTelemetryRepairTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.output = Path(self.temporary.name) / "package"
        shutil.copytree(PACKAGE, self.output)

    def tearDown(self):
        self.temporary.cleanup()

    def load(self, name):
        return json.loads((self.output / name).read_text(encoding="utf-8"))

    def save(self, name, value):
        (self.output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def assert_independent_stop(self):
        result = subject.independent_validation(self.output)
        self.assertNotEqual(result["status"], "PASS")

    def test_a1_pass_label_cannot_hide_swap(self):
        soak = self.load(SOAK); soak["end"]["pswpout"] += 1; soak["windows"][-1]["pswpout"] += 1
        self.save(SOAK, soak); self.assert_independent_stop()

    def test_a2_pass_label_cannot_hide_model_change(self):
        soak = self.load(SOAK); soak["model_hash_after"] = "changed"; soak["windows"][-1]["model_hash"] = "changed"
        self.save(SOAK, soak); self.assert_independent_stop()

    def test_a3_pass_label_cannot_hide_cuda_ceiling(self):
        soak = self.load(SOAK); soak["windows"][-1]["cuda_reserved"] = 16_000_000_000
        self.save(SOAK, soak); self.assert_independent_stop()

    def test_a4_pass_label_cannot_hide_rss_ceiling(self):
        soak = self.load(SOAK); soak["windows"][-1]["rss"] = soak["windows"][0]["mem_available"]
        self.save(SOAK, soak); self.assert_independent_stop()

    def test_a5_pass_label_cannot_hide_continuous_fd_growth(self):
        soak = self.load(SOAK)
        for index, row in enumerate(soak["windows"]): row["fds"] = 20 + index
        self.save(SOAK, soak); self.assert_independent_stop()

    def test_a6_pass_label_cannot_hide_projected_rss_exhaustion(self):
        soak = self.load(SOAK)
        for index, row in enumerate(soak["windows"]): row["rss"] = 1_000_000_000 + index * 1_000_000_000
        self.save(SOAK, soak); self.assert_independent_stop()

    def test_a7_pass_label_cannot_hide_zero_or_nonfinite_throughput(self):
        for value in (0.0, float("nan")):
            soak = self.load(SOAK); soak["windows"][2]["throughput"] = value
            self.save(SOAK, soak); self.assert_independent_stop()
            shutil.copy2(PACKAGE / SOAK, self.output / SOAK)

    def test_a8_pass_label_cannot_hide_output_error_or_digest_mismatch(self):
        soak = self.load(SOAK); soak["windows"][2]["errors"] = 1
        self.save(SOAK, soak); self.assert_independent_stop()
        shutil.copy2(PACKAGE / SOAK, self.output / SOAK)
        soak = self.load(SOAK); soak["output_digest_stable"] = False
        self.save(SOAK, soak); self.assert_independent_stop()

    def test_a9_runtime_point_or_range_mutation_is_rejected(self):
        for key in ("point_seconds", "range_seconds"):
            runtime = self.load(RUNTIME); runtime[key] = runtime[key] + 1 if key == "point_seconds" else [runtime[key][0], runtime[key][1] + 1]
            self.save(RUNTIME, runtime); self.assert_independent_stop()
            shutil.copy2(PACKAGE / RUNTIME, self.output / RUNTIME)

    def test_a10_runtime_component_double_count_is_rejected(self):
        runtime = self.load(RUNTIME); extra = runtime["physical_reader_seconds"]
        runtime["point_seconds"] += extra; runtime["point_hours"] = runtime["point_seconds"] / 3600.0
        runtime["range_seconds"] = [value + extra for value in runtime["range_seconds"]]
        runtime["range_hours"] = [value / 3600.0 for value in runtime["range_seconds"]]
        self.save(RUNTIME, runtime); self.assert_independent_stop()

    def test_pass_result_is_json_serializable(self):
        result = subject.independent_validation(self.output)
        self.assertEqual(result["status"], "PASS")
        json.dumps(result, sort_keys=True)


if __name__ == "__main__":
    unittest.main()
