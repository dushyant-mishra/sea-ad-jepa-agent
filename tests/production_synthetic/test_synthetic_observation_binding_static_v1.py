"""No-training, source-text-only regression tests for the historical binding audit."""
from __future__ import annotations

from pathlib import Path
import unittest

from scripts.production_synthetic import synthetic_observation_binding_static_v1 as A


class SourceOnlyBindingAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = A.read_pinned()

    def test_historical_handoff_and_unbound_registry(self):
        result = A.audit(self.sources)
        self.assertEqual(result["task3_authenticated_calibration_registry"], "EMPTY")
        self.assertEqual(result["actual_task3_to_generator_parameter_binding"], "NOT_VERIFIED__NO_AUTHORITY")
        self.assertEqual(len(result["task3_parameters"]), 7)
        self.assertFalse(result["optimizer_executed"])
        self.assertFalse(result["synthetic_world_generated"])

    def test_refuse_lost_v74_qc_consumption(self):
        altered = dict(self.sources)
        altered["observer"] = altered["observer"].replace("Q.by_operator()", "({}, {})", 1)
        self.assertNotEqual(altered["observer"], self.sources["observer"])
        with self.assertRaises(A.AuditRefusal):
            A.audit(altered)

    def test_refuse_false_task3_semantics_promotion(self):
        altered = dict(self.sources)
        altered["task3"] = altered["task3"].replace(
            "OBSERVATION_PARAMETER_SEMANTICS_BOUND = False",
            "OBSERVATION_PARAMETER_SEMANTICS_BOUND = True", 1)
        with self.assertRaises(A.AuditRefusal):
            A.audit(altered)

    def test_refuse_new_registry_import_or_parameter_use(self):
        altered = dict(self.sources)
        altered["observer"] += "\nOBS_DEPTH_SCALE = 1\n"
        with self.assertRaises(A.AuditRefusal):
            A.audit(altered)

    def test_refuse_fake_source_blob(self):
        self.assertNotEqual(A.git_blob_sha1(b"fake source"), A.FILES["qc"][1])

    def test_reader_is_source_only(self):
        source = (Path(A.__file__)).read_text()
        self.assertNotIn("import torch", source)
        self.assertNotIn("import numpy", source)
        self.assertNotIn("import subprocess", source)
        self.assertNotIn("from scripts.v64", source)
        self.assertNotIn("from scripts.v77", source)


if __name__ == "__main__":
    unittest.main()
