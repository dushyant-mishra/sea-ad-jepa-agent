"""Executable Linux container boundary tests; source #514/#515 remains unchanged.

These tests establish narrow properties of an ephemeral Docker fixture only,
not a certified hostile multi-tenant isolation deployment or human source rights.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from deployment.student_v2c.build_context_v1 import produce_context, git_blob_sha1, EXPECTED_BLOB, SOURCE
from scripts.v5.td_unified import observation_d1_base_only_student_v2c_fixture_v1 as P
from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as V

IMAGE = "jepa-student-v2c-fixture:test"


def _policy():
    return {
        "query_address_id": "ENSG_Q",
        "base_evidence_rights": ["BASE"],
        "address_rights": {"ENSG_A": "BASE", "ENSG_Q": "QUERY"},
        "operator_states": {"OP": {"ENSG_A": "MEASURED_SCALAR", "ENSG_Q": "MEASURED_SCALAR"}},
        "cell_roster": [
            {"cell_id": "C1", "donor_id": "D1", "source_id": "S1", "operator_id": "OP"}
        ],
    }


def _view():
    return P.produce_d1_base_only_student_v2c_fixture(
        base_observations=[{"cell_id": "C1", "base_counts": {"ENSG_A": 7}}],
        expected_policy=_policy(),
    )


class StudentV2CContainerFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="student-v2c-build-")
        cls.context = Path(cls.temp.name) / "only-public-verifier"
        cls.manifest = produce_context(cls.context)
        result = subprocess.run(
            ["docker", "build", "--tag", IMAGE, str(cls.context)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode:
            raise AssertionError("Docker build failed: " + result.stdout[-2000:] + result.stderr[-3000:])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def _flags(self):
        return [
            "--read-only", "--network", "none", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "1",
            "--memory", "256m", "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=8m",
        ]

    def _run(self, data=b"", extra=None):
        cmd = ["docker", "run", "--rm", "-i", *self._flags()]
        if extra:
            cmd += ["--entrypoint", "python", IMAGE, "-I", "-S", "-B", "-c", extra]
        else:
            cmd.append(IMAGE)
        return subprocess.run(cmd, input=data, capture_output=True, timeout=30)

    def test_01_expected_exact_frozen_verifier_and_minimal_build_context(self):
        self.assertEqual(git_blob_sha1(SOURCE.read_bytes()), EXPECTED_BLOB)
        self.assertEqual(self.manifest["source_blob_sha1"], EXPECTED_BLOB)
        self.assertEqual(
            {p.name for p in self.context.iterdir()},
            {"student_v2c.py", "entrypoint.py", "Dockerfile", "manifest.json"},
        )
        for item in ("teacher", "observation_normalization_view_v2_bound_content_v1.py",
                     "observation_d1_base_only_student_v2c_fixture_v1.py"):
            self.assertFalse((self.context / item).exists())
        sha = hashlib.sha256((self.context / "student_v2c.py").read_bytes()).hexdigest()
        self.assertEqual(sha, self.manifest["student_verifier_sha256"])
        self.assertFalse(self.manifest["real_training_authorized"])

    def test_02_exact_composed_fixture_receipt_still_matches_standalone_verifier(self):
        request = {"student_view": _view(), "expected_policy": _policy()}
        result = self._run(json.dumps(request).encode("utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr[-1000:])
        actual = json.loads(result.stdout)
        expected = V.validate_student_v2c(student_view=request["student_view"],
                                          expected_policy=request["expected_policy"])
        self.assertEqual(actual, expected)
        self.assertEqual(actual["authority_effect"], "NONE")
        self.assertFalse(actual["real_training_authorized"])
        self.assertFalse(actual["source_rights_issuer_authenticated"])

    def test_03_legacy_teacher_and_project_imports_unreachable_in_image(self):
        script = (
            "import importlib.util,os; "
            "assert importlib.util.find_spec('scripts') is None; "
            "assert not os.path.exists('/opt/student/observation_d1_base_only_student_v2c_fixture_v1.py'); "
            "assert sorted(os.listdir('/opt/student'))=="
            "['entrypoint.py','manifest.json','student_v2c.py']; "
            "print('VERIFIER_ONLY')"
        )
        result = self._run(extra=script)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertEqual(result.stdout.strip(), b"VERIFIER_ONLY")

    def test_04_read_only_root_and_no_private_host_paths(self):
        script = (
            "import os; "
            "assert not os.path.exists('/mnt/teacher'); "
            "assert not os.path.exists('/home/runner/work'); "
            "\ntry: open('/opt/student/probe','wb')"
            "\nexcept OSError: print('ROOT_WRITE_DENIED')"
            "\nelse: raise RuntimeError('ROOT_WRITE_ALLOWED')"
        )
        result = self._run(extra=script)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertIn(b"ROOT_WRITE_DENIED", result.stdout)

    def test_05_process_creation_denied_by_actual_pid_limit(self):
        script = (
            "import subprocess;"
            "\ntry: subprocess.run(['/bin/true'],check=True,timeout=2)"
            "\nexcept OSError: print('FORK_DENIED')"
            "\nelse: raise RuntimeError('PROCESS_SPAWN_ALLOWED')"
        )
        result = self._run(extra=script)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertEqual(result.stdout.strip(), b"FORK_DENIED")

    def test_06_external_network_connect_denied(self):
        script = (
            "import socket;"
            "\ntry: socket.create_connection(('1.1.1.1', 53),timeout=0.3)"
            "\nexcept OSError: print('NETWORK_DENIED')"
            "\nelse: raise RuntimeError('NETWORK_ALLOWED')"
        )
        result = self._run(extra=script)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertEqual(result.stdout.strip(), b"NETWORK_DENIED")

    def test_07_docker_runtime_has_expected_restriction_flags(self):
        result = subprocess.run(
            ["docker", "create", *self._flags(), IMAGE], capture_output=True,
            text=True, check=True, timeout=30,
        )
        cid = result.stdout.strip()
        try:
            r = subprocess.run(
                ["docker", "inspect", cid], capture_output=True, text=True, check=True, timeout=30
            )
            obj = json.loads(r.stdout)[0]
            h = obj["HostConfig"]
            self.assertEqual(h["NetworkMode"], "none")
            self.assertTrue(h["ReadonlyRootfs"])
            self.assertEqual(h["PidsLimit"], 1)
            self.assertEqual(h["CapDrop"], ["ALL"])
            self.assertIn("no-new-privileges", h["SecurityOpt"])
            self.assertEqual(h["Memory"], 256 * 1024 * 1024)
            self.assertEqual(h["Binds"], None)
            self.assertEqual(obj["Config"]["User"], "65534:65534")
        finally:
            subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=30)

    def test_08_uniform_refusal_for_teacher_role_malformed_json_and_duplicate_key(self):
        view = _view()
        view["view_kind"] = "TEACHER_RICHER_RIGHTS"
        payloads = [
            json.dumps({"student_view": view, "expected_policy": _policy()}).encode(),
            b'{"student_view":NaN,"expected_policy":{}}',
            b'{"student_view":{},"student_view":{},"expected_policy":{}}',
            b'{"student_view":{},"expected_policy":{}}' + b" " * 1_048_576,
        ]
        expected = b'{"authority_effect":"NONE","status":"REFUSED_STUDENT_V2C_FIXTURE"}\n'
        for raw in payloads:
            with self.subTest(raw_length=len(raw)):
                result = self._run(raw)
                self.assertEqual(result.returncode, 2, result.stderr[-1500:])
                self.assertEqual(result.stdout, expected)

    def test_09_no_other_modules_in_python_import_namespace(self):
        # This is a packaging and sys.path test, not proof against kernel escape.
        script = (
            "import sys; "
            "assert all(not p.startswith('/home/runner') for p in sys.path); "
            "assert '/opt/student' not in sys.path; "
            "print('ISOLATED_IMPORT_ROOT')"
        )
        result = self._run(extra=script)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertEqual(result.stdout.strip(), b"ISOLATED_IMPORT_ROOT")


if __name__ == "__main__":
    unittest.main()
