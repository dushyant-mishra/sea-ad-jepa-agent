"""Synthetic red team for the all-104 PHYSICAL block-source binding.

The fixtures here deliberately mirror the REAL Level-4 geometry, which is where
the PR #124 repair went wrong:

* the block manifest carries a per-block ``source`` column holding
  ``HVS`` / ``NPH52`` / ``SEA_AD`` -- this is the physical source assertion;
* the per-row ``source_library`` column holds an integer LIBRARY SIZE, not a
  cohort label;
* ``expression_row`` is a parent-matrix row index, not ``0..n-1``, so it must
  never be used to index a block's CSR rows.

A fixture that puts ``"HVS"`` into ``source_library`` does not test the physical
contract, it tests a construction that does not exist on disk.
"""
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import scipy.sparse as sp

SCRIPT = (Path(__file__).resolve().parents[1] /
          "analysis/v5_full104_information_channel_redteam_20260920/scripts/"
          "qualify_all104_block_source_binding_v1.py")
spec = importlib.util.spec_from_file_location("n1_block_source_binding_test_only", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SyntheticBlockSourceBinding(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.blocks = self.root / "level4"
        self.blocks.mkdir()
        self.out = self.root / "result.json"
        self.p1 = self.root / "pass1.npz"
        self.art = self.root / "corrected.npz"

        # donors A(HVS) B(NPH52) C(SEA_AD); cells 0..3 -> donors A,B,B,C
        self.donors = ["A", "B", "C"]
        self.src = np.array([0, 1, 2], dtype=np.int64)
        self.cd = np.array([0, 1, 1, 2], dtype=np.int64)
        self.core = np.array([0, 2], dtype=np.int64)
        # Blocks are single-source on disk, so the fixture is too. Library sizes
        # are integers and expression_row is a parent-matrix index, as on disk.
        self.block_sources = ["HVS", "NPH52", "SEA_AD"]
        self.meta = [
            [{"selection_row": "0", "canonical_cell_id": "c0", "donor_id": "A",
              "expression_row": "40021", "primary_row_weight": "1", "source_library": "28005"}],
            [{"selection_row": "1", "canonical_cell_id": "c1", "donor_id": "B",
              "expression_row": "40155", "primary_row_weight": "1", "source_library": "13304"},
             {"selection_row": "2", "canonical_cell_id": "c2", "donor_id": "B",
              "expression_row": "51002", "primary_row_weight": "1", "source_library": "9124"}],
            [{"selection_row": "3", "canonical_cell_id": "c3", "donor_id": "C",
              "expression_row": "51377", "primary_row_weight": "1", "source_library": "7536"}],
        ]
        self.counts = [
            sp.csr_matrix(np.array([[2, 0, 0, 0]], dtype=np.int64)),
            sp.csr_matrix(np.array([[0, 0, 4, 0], [0, 0, 0, 0]], dtype=np.int64)),
            sp.csr_matrix(np.array([[1, 0, 3, 0]], dtype=np.int64))]
        self.make_art()
        np.savez(self.p1, cell_donor=self.cd, core=self.core,
                 duniq=np.array(self.donors, dtype=object))
        self.make_blocks()


    def make_art(self, source_override=None, src_of_cell_override=None):
        donor_src = self.src if source_override is None else source_override
        soc = donor_src[self.cd] if src_of_cell_override is None else src_of_cell_override
        np.savez(self.art, core=self.core, duniq=np.array(self.donors, dtype=object),
                 donor_src=donor_src,
                 source_names=np.array(["HVS", "NPH52", "SEA_AD"], dtype=object),
                 src_of_cell=soc)

    def make_blocks(self):
        manifest = self.blocks / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
        items = []
        for k, (meta, mat, src) in enumerate(zip(self.meta, self.counts, self.block_sources)):
            mp = self.blocks / f"b{k}.csv"
            cp = self.blocks / f"b{k}.npz"
            with mp.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=mod._META_COLUMNS)
                w.writeheader()
                w.writerows(meta)
            sp.save_npz(cp, mat, compressed=True)
            items.append(dict(block_key=str(k), source=src, meta_path=mp.name,
                              meta_sha256=sha(mp), counts_path=cp.name, counts_sha256=sha(cp)))
        with manifest.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(items[0]))
            w.writeheader()
            w.writerows(items)

    def run_it(self, expect=None, row_alignment=False):
        overrides = {
            "EXPECTED_ARTIFACT_SHA256": sha(self.art),
            "EXPECTED_ARTIFACT_BYTES": self.art.stat().st_size,
            "EXPECTED_PASS1_SHA256": sha(self.p1),
            "EXPECTED_MANIFEST_SHA256": sha(self.blocks / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
            "EXPECTED_CELLS": 4, "EXPECTED_DONORS": 3, "EXPECTED_CORE": 2,
            "EXPECTED_BLOCKS": len(self.meta), "N_LEDGER": 4,
            "EXPECTED_SOURCE_DONORS": (1, 1, 1),
            "EXPECTED_SOURCE_CELLS": (1, 2, 1),
        }
        command = ["x", "--level4-root", str(self.blocks), "--artifact", str(self.art),
                   "--pass1", str(self.p1), "--out", str(self.out)]
        if row_alignment:
            command.append("--check-row-alignment")
        with patch.multiple(mod, **overrides), patch.object(sys, "argv", command), \
                contextlib.redirect_stdout(io.StringIO()):
            if expect:
                with self.assertRaises(SystemExit) as err:
                    mod.main()
                self.assertIn(expect, str(err.exception))
                if expect != "STOP_OUTPUT_EXISTS":
                    self.assertFalse(self.out.exists())
            else:
                self.assertEqual(mod.main(), 0)
                obj = json.loads(self.out.read_text())
                self.assertEqual(obj["verdict"], "ALL104_BLOCK_SOURCE_BINDING_PASS")
                self.assertEqual(obj["blocks_verified"], len(self.meta))
                self.assertEqual(obj["blocks_skipped"], 0)
                self.assertEqual(obj["cells_accounted_exactly_once"], 4)
                self.assertTrue(obj["every_selection_row_filled_exactly_once"])
                self.assertTrue(obj["source_library_is_never_a_cohort_name"])
                self.assertFalse(obj["protected_outcome_opened"])
                self.assertFalse(obj["training_authorized"])
                return obj

    # ---- positive ---------------------------------------------------------
    def test_positive_and_output_collision(self):
        obj = self.run_it()
        self.assertEqual(obj["source_cell_census"], [1, 2, 1])
        self.run_it("STOP_OUTPUT_EXISTS")

    def test_positive_with_row_alignment(self):
        obj = self.run_it(row_alignment=True)
        self.assertEqual(obj["blocks_row_alignment_verified"], len(self.meta))

    # ---- the PR #124 defect, pinned ---------------------------------------
    def test_source_library_holding_a_cohort_name_is_rejected(self):
        # This is the construction PR #124's fixture assumed. It does not exist
        # on disk, and if it ever did it would be a contract violation.
        self.meta[0][0]["source_library"] = "HVS"
        self.make_blocks()
        self.run_it("source_library carries a cohort NAME")

    def test_numeric_source_library_is_not_treated_as_a_source(self):
        # The real column. Must NOT trip the source binding.
        self.meta[0][0]["source_library"] = "999999"
        self.make_blocks()
        self.run_it()

    # ---- genuine provenance adversaries -----------------------------------
    def test_block_source_relabeled_without_donor_swap_rejected(self):
        self.block_sources[0] = "SEA_AD"      # donor A is registered HVS
        self.make_blocks()
        self.run_it("physical source mismatch vs corrected donor registry")

    def test_donor_source_registry_permuted_rejected(self):
        self.make_art(source_override=np.array([1, 0, 2], dtype=np.int64))
        self.run_it("physical source mismatch")

    def test_src_of_cell_tampered_rejected(self):
        soc = self.src[self.cd].copy()
        soc[0] = 2
        self.make_art(src_of_cell_override=soc)
        self.run_it("cell->donor->source invariant mismatch")

    def test_unknown_physical_source_rejected(self):
        self.block_sources[0] = "UNREGISTERED"
        self.make_blocks()
        self.run_it("unknown physical source")

    # ---- identity-space closure -------------------------------------------
    def test_duplicate_selection_row_rejected(self):
        self.meta[1][0]["selection_row"] = "0"
        self.make_blocks()
        self.run_it("selection_row")

    def test_missing_cell_rejected(self):
        self.meta[2] = []
        self.make_blocks()
        self.run_it("cells consumed")

    def test_donor_swap_vs_pass1_rejected(self):
        self.meta[1][0]["donor_id"] = "C"
        self.make_blocks()
        self.run_it("donor identity mismatch vs pass1")

    def test_metadata_hash_mismatch_rejected(self):
        mp = self.blocks / "b0.csv"
        mp.write_text(mp.read_text() + "\n", encoding="utf-8")
        self.run_it("metadata hash mismatch")

    # ---- row alignment can actually fail ----------------------------------
    def test_row_misalignment_detected(self):
        # Swap the two CSR rows of block 1 without touching metadata: row 0 then
        # carries more ledger mass than its own library size allows.
        self.meta[1][0]["source_library"] = "1"
        self.make_blocks()
        self.run_it("row misalignment", row_alignment=True)


if __name__ == "__main__":
    unittest.main()
