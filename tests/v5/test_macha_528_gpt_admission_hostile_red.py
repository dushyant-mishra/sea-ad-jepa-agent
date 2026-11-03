"""Independent GPT RED-first audit of Macha #528 exact c1d85688: tests ONLY.

Neither source-admission wrapper nor original #528 tests are changed.
RED1: symlinked parent directory escapes supposedly confined data root.
RED2: --run-probe returns ADMITTED after output diverges from the pinned
      committed QC receipt; an output mismatch must not be a success.

These tests use tiny synthetic filesystem fixtures, NEVER a real H5AD, pathology,
outside-allowlist metadata or any learner. No source-rights authority granted.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from tests.v5.test_macha_specimen_qc_input_admission_v1 import A, Fixture


class GPT528SourceAdmissionRED(unittest.TestCase):
    def test_r01_parent_directory_symlink_escape_must_refuse(self):
        # The final H5AD file is not a symlink; its parent is. Both files retain
        # original bytes, size, mtime and receipt hashes, so only real-path
        # confinement—not incidental hash drift—can close this case.
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            root = Path(d)
            fixture = Fixture(root)
            outside_data = Path(outside) / "data"
            (root / "data").rename(outside_data)
            (root / "data").symlink_to(outside_data, target_is_directory=True)
            with self.assertRaises(A.AdmissionRefused, msg="admitted data via symlinked parent outside root"):
                fixture.admit()

    def test_r02_probe_output_mismatch_must_fail_closed(self):
        # Existing #528 fixture and the probe itself are SHA-pinned. The only
        # mismatch is the expected output vs the actual probe result; a mismatch
        # must not return a successful admission/replay receipt.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture = Fixture(root)
            probe = b"import json\nprint(json.dumps({'fixture': 1}))\n"
            fixture.write(A.PROBE, probe)
            pins = dict(fixture.pins, **{
                A.PROBE: hashlib.sha256(probe).hexdigest(),
                A.PROBE_OUTPUT: hashlib.sha256(b'{"fixture": 2}\n').hexdigest(),
            })
            with self.assertRaises(A.AdmissionRefused, msg="probe output differed but run returned an admitted receipt"):
                A.run_probe(root, root / "out.json", pins=pins)


if __name__ == "__main__":
    unittest.main()
