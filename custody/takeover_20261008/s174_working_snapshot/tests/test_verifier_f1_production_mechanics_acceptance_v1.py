"""Independent adversarial verification for the F1 mechanics acceptance gate.

Expected identities and synthetic values are reconstructed here from the frozen
contract.  No production helper is used to produce an expected value.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.v4 import validate_f1_production_mechanics_acceptance_v1 as subject


CANONICAL = Path("/mnt/d/Jepa project") if Path("/mnt/d/Jepa project").is_dir() else Path("D:/Jepa project")
ASSIGNMENTS = CANONICAL / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
DEDUP = CANONICAL / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_EXECUTION_DEDUP_MAP.csv"
NULLS = CANONICAL / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv"
ARTIFACT = Path("outputs/contextual_teacher_target_v1_f1_production_mechanics_acceptance_20260903/F1_MECHANICS_FINALIZER_FAILCLOSED.json")
EVIDENCE = (20, 40, 60, 80, 100)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def identity(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def line_root(values) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


class IndependentF1MechanicsVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ASSIGNMENTS.open("r", encoding="utf-8-sig", newline="") as handle:
            raw = list(csv.DictReader(handle))
        cls.assignments = [{
            "assignment_key": row["assignment_key_sha256"],
            "cell": row["canonical_cell_id"],
            "donor": row["donor_id"],
            "source": row["source"],
            "operator": int(row["operator_index"]),
            "program": row["program"],
            "draw": int(row["draw_replicate"]),
            "q": int(row["selected_query_address"]),
            "row_authority": row["evaluation_row_authority_sha256"],
        } for row in raw]
        with NULLS.open("r", encoding="utf-8-sig", newline="") as handle:
            cls.nulls = {row["recipient_canonical_cell_id"]: row["source_canonical_cell_id"] for row in csv.DictReader(handle)}

    def test_a_b_full_identity_and_dedup_are_independently_reconstructed(self):
        first_seen = []
        seen = set()
        for row in self.assignments:
            key = (row["cell"], row["q"])
            if key not in seen:
                seen.add(key)
                first_seen.append(key)
        with DEDUP.open("r", encoding="utf-8-sig", newline="") as handle:
            dedup = [(row["canonical_cell_id"], int(row["selected_query_address"])) for row in csv.DictReader(handle)]
        # The frozen contract makes assignment first-appearance the compute
        # order; the accepted dedup CSV is an authority over membership, not
        # the ordering authority.
        self.assertEqual(set(first_seen), set(dedup))
        self.assertEqual(len(dedup), len(set(dedup)))
        self.assertEqual((len(self.assignments), len(first_seen), len(self.assignments) - len(first_seen)), (44496, 43108, 1388))

        authority = {
            "accepted_real_forward_root": subject.ACCEPTED_FORWARD_ROOT,
            "assignment_sha256": subject.ASSIGNMENT_SHA,
            "dedup_sha256": subject.DEDUP_SHA,
            "matched_null_sha256": subject.NULL_SHA,
        }
        expected_ids = []
        for cell, query in first_seen:
            expected_ids.append(identity({"authority": authority, "role": "teacher", "recipient": cell, "q": query}))
            for level in EVIDENCE:
                expected_ids.append(identity({"authority": authority, "role": "correct_student", "recipient": cell, "q": query, "evidence_level": level}))
                expected_ids.append(identity({"authority": authority, "role": "matched_null_student", "recipient": cell, "q": query, "evidence_level": level, "null_source": self.nulls[cell]}))
        observed = subject.build_identity_topology(self.assignments, self.nulls, authority)
        self.assertEqual(len(expected_ids), 474188)
        self.assertEqual(len(set(expected_ids)), 474188)
        self.assertEqual(observed["ordered_identity_root_sha256"], line_root(expected_ids))

    def test_c_full_synthetic_values_schema_and_topology(self):
        required = {
            "cell", "donor", "source", "operator", "program", "replicate", "evidence",
            "query_address", "assignment_key", "evaluation_row_authority", "assignment_authority_sha256",
            "mask_authority", "model_checkpoint", "sketch", "forward_identity_sha256",
            "A", "direct_delta", "qid_margin", "qid_win",
        }
        count = 0
        cache = {}
        for row in self.assignments:
            for level in EVIDENCE:
                record = subject.synthetic_record(row, level)
                prefix = f"{row['cell']}|{row['q']}|{level}|"
                def unit(label):
                    raw = hashlib.sha256((prefix + label).encode("utf-8")).digest()[:8]
                    return int.from_bytes(raw, "big") / 18446744073709551616.0
                a, direct, margin = 2 * unit("A") - 1, 2 * unit("direct") - 1, 2 * unit("qid") - 1
                expected = (a, a - direct, margin, 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5)
                observed = tuple(record[key] for key in ("A", "direct_delta", "qid_margin", "qid_win"))
                self.assertEqual(set(record), required)
                self.assertEqual(observed, expected)
                compute_key = (row["cell"], row["q"], level)
                if compute_key in cache:
                    self.assertEqual(cache[compute_key], observed)
                else:
                    cache[compute_key] = observed
                count += 1
        self.assertEqual(count, 222480)
        self.assertEqual(len(cache), 215540)
        self.assertEqual(len({(row["donor"], row["operator"]) for row in self.assignments}), 1400)

    def test_d_resume_is_byte_exact_and_fail_closed_on_bounded_shards(self):
        # Filesystem-safe IDs isolate AtomicShardStore semantics from the
        # separate Windows filename defect in the implementer-authored tests.
        shard_rows = {
            "d0_00": [("a0|20", np.asarray([1.0, 2.0, 3.0, 4.0], np.float64)),
                       ("a1|20", np.asarray([5.0, 6.0, 7.0, 8.0], np.float64))],
            "d1_01": [("a2|20", np.asarray([9.0, 10.0, 11.0, 12.0], np.float64))],
        }
        with tempfile.TemporaryDirectory() as temporary:
            result = subject.exercise_shard_resume(Path(temporary), shard_rows, "membership", "forward")
        self.assertTrue(result["ordered_bytes_exact"])
        self.assertTrue(result["valid_shards_reused"])
        self.assertEqual(result["semantic_root_uninterrupted"], result["semantic_root_resumed"])
        self.assertTrue(all(result["attacks_rejected"].values()))

    def test_d_portable_filenames_preserve_logical_shard_reconciliation(self):
        shard_rows = {
            "donor:0|00": [("a0|20", np.asarray([1.0, 2.0, 3.0, 4.0], np.float64))],
            "donor/1|01": [("a1|20", np.asarray([5.0, 6.0, 7.0, 8.0], np.float64))],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subject.reuse_or_exercise_shards(root, shard_rows, "membership", "forward")
            marker = json.loads((root / "COMPLETE.json").read_text(encoding="utf-8"))
            physical = sorted(path.stem for path in (root / "uninterrupted").glob("*.npz"))
        expected_physical = sorted(
            "shard_" + hashlib.sha256(("logical-shard|" + logical).encode("utf-8")).hexdigest()
            for logical in shard_rows
        )
        self.assertEqual(marker["shards"], sorted(shard_rows))
        self.assertEqual(physical, expected_physical)
        self.assertEqual(len(set(physical)), len(shard_rows))
        self.assertTrue(all(name.startswith("shard_") and len(name) == 70 for name in physical))

    def test_e_finalizer_rejects_shape_preserving_membership_attack(self):
        shards = ["d0|00", "d1|01", "d2|02"]
        forwards = ["f0", "f1", "f2", "f3"]
        effects = ["e0", "e1", "e2", "e3", "e4"]
        expected = subject.make_expected_finalization(shards, forwards, effects, "commit")
        actual = {"shard_ids": shards, "forward_ids": forwards, "effect_ids": effects, "implementation_commit": "commit"}
        subject.validate_finalization(expected, actual)
        attacks = (
            {**actual, "shard_ids": shards[:-1] + [shards[0]]},
            {**actual, "forward_ids": forwards[:-1] + [forwards[0]]},
            {**actual, "shard_ids": list(reversed(shards))},
            {**actual, "forward_ids": list(reversed(forwards))},
        )
        for attacked in attacks:
            with self.assertRaises(RuntimeError):
                subject.validate_finalization(expected, attacked)

    def test_e_finalizer_rejects_shape_preserving_effect_attack(self):
        expected = subject.make_expected_finalization(["d0|00"], ["f0"], ["e0", "e1", "e2"], "commit")
        actual = {"shard_ids": ["d0|00"], "forward_ids": ["f0"], "effect_ids": ["e0", "e1", "e2"], "implementation_commit": "commit"}
        attacks = (
            {**actual, "effect_ids": ["e0", "e1", "e0"]},
            {**actual, "effect_ids": ["e2", "e1", "e0"]},
            expected.as_dict(),
        )
        for attacked in attacks:
            with self.assertRaises(RuntimeError):
                subject.validate_finalization(expected, attacked)

    def test_e_checked_in_finalizer_is_bound_to_implementation_commit(self):
        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        implementation = artifact["expected"]["implementation_commit"]
        head = subject.git_head()
        subject.preflight_finalizer.git_output("merge-base", "--is-ancestor", implementation, head)
        runner = "scripts/v4/validate_f1_production_mechanics_acceptance_v1.py"
        implementation_blob = subject.preflight_finalizer.git_output("rev-parse", f"{implementation}:{runner}")
        current_blob = subject.preflight_finalizer.git_output("hash-object", runner)
        self.assertEqual(implementation_blob, current_blob)

    def test_e_artifact_roots_are_independently_recomputed_from_exact_memberships(self):
        first_seen = []
        seen = set()
        for row in self.assignments:
            key = (row["cell"], row["q"])
            if key not in seen:
                seen.add(key)
                first_seen.append(key)
        authority = {
            "accepted_real_forward_root": subject.ACCEPTED_FORWARD_ROOT,
            "assignment_sha256": subject.ASSIGNMENT_SHA,
            "dedup_sha256": subject.DEDUP_SHA,
            "matched_null_sha256": subject.NULL_SHA,
        }
        forward_ids = []
        for cell, query in first_seen:
            forward_ids.append(identity({"authority": authority, "role": "teacher", "recipient": cell, "q": query}))
            for level in EVIDENCE:
                forward_ids.append(identity({"authority": authority, "role": "correct_student", "recipient": cell, "q": query, "evidence_level": level}))
                forward_ids.append(identity({"authority": authority, "role": "matched_null_student", "recipient": cell, "q": query, "evidence_level": level, "null_source": self.nulls[cell]}))
        shard_ids = sorted({f"{row['donor']}|{row['operator']:02d}" for row in self.assignments})
        effect_ids = [f"{row['assignment_key']}|{level}" for row in self.assignments for level in EVIDENCE]
        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))["expected"]
        self.assertEqual((len(shard_ids), len(forward_ids), len(effect_ids)), (1400, 474188, 222480))
        self.assertEqual(artifact["membership_root"], line_root(shard_ids))
        self.assertEqual(artifact["forward_root"], line_root(forward_ids))
        self.assertEqual(artifact["effect_root"], line_root(effect_ids))


if __name__ == "__main__":
    unittest.main()
