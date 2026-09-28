#!/usr/bin/env python3
"""Tests for the Lane A+F SEA-AD assay-origin audit.

The suite is deliberately built so that every check has a reachable failing
outcome. Each test names, in its docstring, what result would make it fail.

Test classes:
  * firewall     - the forbidden-field filter must FIRE on real pathology names
  * mutation     - deliberately corrupted inputs must be REJECTED, not tolerated
  * arithmetic   - selection_row offset algebra
  * realdata     - positive and negative controls against on-disk artifacts
"""
from __future__ import annotations

import csv
import gzip
import io
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import laneAF_identity_firewall_v1 as fw  # noqa: E402
import laneAF_seaad_assay_origin_audit_v1 as audit  # noqa: E402

MYELOID_NPZ = Path(r"D:/jepa_v5_outputs_20260925/myeloid_panel_masked_full/FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz")

# Every obs column name in the real SEA-AD h5ad files that must never survive
# into a joined frame in this lane. Taken verbatim from the on-disk obs keys.
REAL_FORBIDDEN_OBS_NAMES = [
    "Braak",
    "CERAD score",
    "Thal",
    "Overall AD neuropathological Change",
    "Cognitive Status",
    "Last MMSE Score",
    "Last CASI Score",
    "Last MOCA Score",
    "LATE",
    "Highest Lewy Body Disease",
    "Overall CAA Score",
    "Total microinfarcts in screening sections",
    "Arteriolosclerosis",
    "Atherosclerosis",
    "APOE Genotype",
    "Severely Affected Donor",
    "Continuous Pseudo-progression Score",
    "Interval from last MMSE in months",
    "Years of education",
]

REAL_ALLOWED_OBS_NAMES = [
    "exp_component_name",
    "method",
    "library_prep",
    "Donor ID",
    "Brain Region",
    "index",
]


class TestFirewallPositiveControl(unittest.TestCase):
    """FAILS IF: the filter lets a real pathology column through."""

    def test_each_real_forbidden_name_fires(self):
        for name in REAL_FORBIDDEN_OBS_NAMES:
            with self.subTest(column=name):
                hits = fw.forbidden_columns([name])
                self.assertEqual(len(hits), 1, "no rule fired for " + name)

    def test_join_frame_containing_braak_is_refused(self):
        frame_columns = ["cell_id", "donor_id", "method", "Braak"]
        with self.assertRaises(fw.ForbiddenFieldError) as ctx:
            fw.assert_identity_only(frame_columns, context="unit_positive_control")
        self.assertIn("Braak", str(ctx.exception))
        self.assertIn("braak", str(ctx.exception))

    def test_select_identity_columns_refuses_rather_than_silently_dropping(self):
        with self.assertRaises(fw.ForbiddenFieldError):
            fw.select_identity_columns(["cell_id", "CERAD score"], context="unit")


class TestFirewallNegativeControl(unittest.TestCase):
    """FAILS IF: the filter fires on a legitimate identity column.

    A filter that rejects everything would pass the positive control, so this
    test is the one that makes the positive control meaningful.
    """

    def test_allowed_identity_frame_passes(self):
        fw.assert_identity_only(REAL_ALLOWED_OBS_NAMES, context="unit_negative_control")

    def test_no_allowed_name_is_flagged(self):
        self.assertEqual(fw.forbidden_columns(REAL_ALLOWED_OBS_NAMES), [])

    def test_real_paired_export_header_passes(self):
        header = [
            "selection_row",
            "matrix_id",
            "donor_id",
            "cell_id",
            "library_token",
            "library_prep",
            "method",
            "assay_origin",
            "assay_origin_evidence",
            "atac_cell_id",
            "atac_row",
        ]
        fw.assert_identity_only(header, context="unit_export_header")


class TestFirewallMutationControl(unittest.TestCase):
    """FAILS IF: a renamed / disguised forbidden column slips through.

    These are the mutations an accidental refactor or an upstream schema
    rename would actually produce.
    """

    MUTATIONS = [
        "braak_stage",
        "BRAAK",
        "Braak-Stage",
        "braakStage",
        "cerad_score",
        "CERAD_Score",
        "thal_phase",
        "adnc",
        "ADNC_score",
        "cognitive_status",
        "mmse_total",
        "casi_score",
        "donor_pathology_score",
        "at8_density",
        "amyloid_beta_load",
        "teacher_latent_0",
        "relational_target_outcome",
        "td60_score",
        "x_scvi",
        "n_counts",
        "total_counts",
        "source_library",
    ]

    def test_every_mutation_is_caught(self):
        for name in self.MUTATIONS:
            with self.subTest(column=name):
                self.assertTrue(
                    fw.forbidden_columns([name]),
                    "mutation not caught: " + name,
                )

    def test_whitelist_blocks_unknown_non_forbidden_column(self):
        """An unlisted column that no rule matches must still be refused."""
        self.assertEqual(fw.forbidden_columns(["Multiome_Linked_peaks"]), [])
        with self.assertRaises(fw.ForbiddenFieldError):
            fw.assert_identity_only(["cell_id", "Multiome_Linked_peaks"], context="unit_mutation")

    def test_shard_reader_refuses_a_corrupted_header(self):
        """A lineage shard carrying Braak must make read_shard raise."""
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as handle:
            handle.write(b"canonical_cell_id,donor_id,source_row,Braak\n")
            handle.write(b"AAA-L8XR_1-1,H1,0,Braak V\n")
        tmp = Path(__file__).resolve().parent / "_mutation_shard_tmp.csv.gz"
        tmp.write_bytes(buffer.getvalue())
        original = audit.SHARD_DIR
        try:
            audit.SHARD_DIR = tmp.parent
            renamed = tmp.parent / "part-operator-99.csv.gz"
            renamed.write_bytes(tmp.read_bytes())
            with self.assertRaises(fw.ForbiddenFieldError):
                audit.read_shard(99)
        finally:
            audit.SHARD_DIR = original
            for path in (tmp, tmp.parent / "part-operator-99.csv.gz"):
                if path.exists():
                    path.unlink()


class TestLibraryTokenParsing(unittest.TestCase):
    """FAILS IF: the library token parser mishandles suffixes containing hyphens."""

    def test_three_field_identifier(self):
        cell = "AAACAGCCACTGGCTG-L8XR_231221_02_D02-1322484698"
        self.assertEqual(audit.library_token(cell), "L8XR_231221_02_D02")
        self.assertEqual(audit.library_prefix(audit.library_token(cell)), "L8XR")

    def test_suffix_with_extra_hyphens(self):
        cell = "AAACCCAAGACCAAAT-L8HX_230803_02_D08-NY-TX4091-2"
        self.assertEqual(audit.library_token(cell), "L8HX_230803_02_D08")
        self.assertEqual(audit.library_prefix(audit.library_token(cell)), "L8HX")

    def test_degenerate_inputs_do_not_fabricate_a_token(self):
        self.assertEqual(audit.library_token(""), "")
        self.assertEqual(audit.library_token("NOHYPHEN"), "")
        self.assertEqual(audit.library_token("ONLY-ONE"), "")
        self.assertEqual(audit.library_prefix(""), "")


class TestSelectionRowArithmetic(unittest.TestCase):
    """FAILS IF: offsets are not the running sum in ascending operator order."""

    def test_offsets_are_exclusive_prefix_sums(self):
        rows = [
            {"operator_index": "2", "row_count": "30", "source": "X"},
            {"operator_index": "0", "row_count": "10", "source": "X"},
            {"operator_index": "1", "row_count": "20", "source": "X"},
        ]
        offsets, total = audit.selection_row_offsets(rows)
        self.assertEqual(offsets, {0: 0, 1: 10, 2: 30})
        self.assertEqual(total, 60)

    def test_real_lineage_total_matches_published_full104_size(self):
        index_rows = audit.read_lineage_index()
        _offsets, total = audit.selection_row_offsets(index_rows)
        self.assertEqual(total, 4553407)


class TestRealDataPositiveControl(unittest.TestCase):
    """FAILS IF: the selection_row authority does not reproduce cell identity
    recorded by an artifact this lane did not produce.

    The myeloid panel npz was written by a different workstream and carries its
    own selection_row, cell_id, donor_id and matrix_id arrays for 187,909
    nuclei. This test resolves every one of those selection_row values against
    PHASE2_METADATA_SELECTION_LEVEL4.csv.gz and requires exact agreement on all
    three identity fields.

    HISTORY: an earlier version of this lane derived selection_row from the
    order in which the 42 per-operator lineage shards concatenate. This test
    failed it with 170,336 of 170,528 SEA-AD rows disagreeing, which is how the
    wrong authority was found. A test that could not fail would have shipped it.
    """

    @classmethod
    def setUpClass(cls):
        if not MYELOID_NPZ.exists():
            raise unittest.SkipTest("myeloid identity artifact not present")
        if not audit.SELECTION_MANIFEST.exists():
            raise unittest.SkipTest("FULL104 selection manifest not present")
        payload = np.load(MYELOID_NPZ, allow_pickle=True)
        cls.selection_rows = payload["selection_row"].astype(np.int64)
        cls.cell_ids = payload["cell_id"].astype(str)
        cls.donor_ids = payload["donor_id"].astype(str)
        cls.matrix_ids = payload["matrix_id"].astype(str)
        cls.sources = payload["source"].astype(str)

    def test_selection_rows_reproduce_cell_identity(self):
        wanted = {}
        for position, value in enumerate(self.selection_rows):
            wanted[int(value)] = position
        self.assertEqual(len(wanted), len(self.selection_rows))
        seen = 0
        mismatched = []
        total_rows = 0
        with gzip.open(audit.SELECTION_MANIFEST, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            i_sel = header.index("selection_row")
            i_cell = header.index("canonical_cell_id")
            i_donor = header.index("donor_id")
            i_matrix = header.index("matrix_id")
            i_source = header.index("source")
            for row in reader:
                total_rows += 1
                selection_row = int(row[i_sel])
                position = wanted.get(selection_row)
                if position is None:
                    continue
                seen += 1
                if (
                    row[i_cell] != self.cell_ids[position]
                    or row[i_donor] != self.donor_ids[position]
                    or row[i_matrix] != self.matrix_ids[position]
                    or row[i_source] != self.sources[position]
                ):
                    mismatched.append((selection_row, row[i_cell], self.cell_ids[position]))
        self.assertEqual(total_rows, 4553407)
        self.assertEqual(seen, 187909)
        self.assertEqual(mismatched[:5], [], "selection_row -> identity disagreement")
        self.assertEqual(len(mismatched), 0)

    def test_shard_order_is_NOT_the_selection_order(self):
        """FAILS IF: the discarded assumption would have worked anyway.

        Keeps the positive control above from looking like a tautology: it
        shows the shard-concatenation index really does disagree with the
        selection_row authority, so agreeing with the authority is informative.
        """
        index_rows = audit.read_lineage_index()
        offsets, _total = audit.selection_row_offsets(index_rows)
        agree = 0
        checked = 0
        for record in index_rows:
            if record["source"] != "SEA_AD" or record["matrix_id"] != "sea_ad_lec_rna_final_2026":
                continue
            operator_index = int(record["operator_index"])
            shard = audit.read_shard(operator_index)
            offset = offsets[operator_index]
            lookup = {int(v): i for i, v in enumerate(self.selection_rows)}
            for local in range(0, len(shard["cell_id"]), 997):
                position = lookup.get(offset + local)
                if position is None:
                    continue
                checked += 1
                if shard["cell_id"][local] == self.cell_ids[position]:
                    agree += 1
        self.assertGreater(checked, 0, "control did not exercise any row")
        self.assertEqual(agree, 0, "shard order unexpectedly matched the selection order")


class TestRealDataNegativeControl(unittest.TestCase):
    """FAILS IF: the ATAC join fabricates pairings where none can exist.

    LEC is 100% Multiome GEX in FULL104 and there is no LEC ATAC object at all,
    so the correct answer for every LEC nucleus is "unmatched". A join that
    matched on barcode alone, or that fell back to donor identity, would
    produce a large non-zero count here.
    """

    @classmethod
    def setUpClass(cls):
        if not audit.ATAC_PATH.exists():
            raise unittest.SkipTest("ATAC object not present")
        cls.atac_rows, cls.atac_meta = audit.load_atac_multiome_index()

    def test_atac_multiome_population_is_as_published(self):
        self.assertEqual(self.atac_meta["atac_multiome_nuclei"], 138118)
        self.assertEqual(self.atac_meta["atac_duplicate_identifiers"], 0)

    def test_non_mtg_multiome_cells_do_not_match(self):
        index_rows = audit.read_lineage_index()
        target = [r for r in index_rows if r["matrix_id"] == "sea_ad_lec_rna_final_2026"]
        self.assertEqual(len(target), 1)
        shard = audit.read_shard(int(target[0]["operator_index"]))
        matched = sum(1 for cell in shard["cell_id"] if cell in self.atac_rows)
        self.assertEqual(matched, 0)

    def test_barcode_only_matching_would_have_matched_many(self):
        """Shows the negative control above is not vacuous.

        If the join key were the bare 16bp barcode instead of the full
        identifier, a large number of LEC nuclei WOULD collide with MTG ATAC
        nuclei. This asserts that the weaker key is genuinely dangerous, which
        is what makes the exact-identifier result meaningful.
        """
        index_rows = audit.read_lineage_index()
        target = [r for r in index_rows if r["matrix_id"] == "sea_ad_lec_rna_final_2026"][0]
        shard = audit.read_shard(int(target["operator_index"]))
        atac_barcodes = {key.split("-", 1)[0] for key in self.atac_rows}
        collisions = sum(1 for cell in shard["cell_id"] if cell.split("-", 1)[0] in atac_barcodes)
        self.assertGreater(collisions, 10000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
