"""Degenerate-input tests for the V69 TF motif-annotation-supply contract (control C1).

The header of the real cisTarget annotation table is written as a '#'-prefixed
comment line, so the first column arrives named '#motif_id'. The producer strips
that marker. These tests prove the fix PARSES the header rather than LOOSENING the
gate: a table genuinely missing a required column must still fail closed, and the
failure must name the column.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "v69" / \
    "build_tf_annotation_supply_table_v1.py"
_spec = importlib.util.spec_from_file_location("v69_supply", _MOD)
sup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sup)

COLS = ["motif_id", "motif_name", "gene_name", "orthologous_gene_name",
        "similar_motif_id", "description"]


def _rows():
    r = []
    # TF_HI: 6 directly annotated motifs. TF_LO: 1. TF_NONE: only similarity.
    for i in range(6):
        r.append([f"m{i}", f"M{i}", "TF_HI", "None", "None",
                  "gene is directly annotated for motif"])
    r.append(["m100", "M100", "TF_LO", "None", "None",
              "gene is directly annotated for motif"])
    for i in range(3):
        r.append([f"m20{i}", f"M20{i}", "TF_NONE", "None", f"sim{i}",
                  "gene is annotated for similar motif"])
    r.append(["m300", "M300", "TF_ORTH", "FBgn0001", "None",
              "gene is orthologous to FBgn0001"])
    return pd.DataFrame(r, columns=COLS)


def _write(df, tmp_path, name="ann.tbl", hash_prefix=True):
    p = tmp_path / name
    out = df.copy()
    if hash_prefix:
        out = out.rename(columns={"motif_id": "#motif_id"})
    out.to_csv(p, sep="\t", index=False)
    return p


def test_pass_is_reachable_with_hash_prefixed_header(tmp_path):
    r = sup.build(_write(_rows(), tmp_path), tmp_path / "out")
    assert r["status"] == "PASS__ANNOTATION_SUPPLY_TABLE_BUILT"
    assert r["n_tfs"] == 4


def test_header_marker_is_parsed_not_ignored(tmp_path):
    """The '#'-prefixed and plain headers must give byte-identical results."""
    a = sup.build(_write(_rows(), tmp_path, "a.tbl", hash_prefix=True), tmp_path / "oa")
    b = sup.build(_write(_rows(), tmp_path, "b.tbl", hash_prefix=False), tmp_path / "ob")
    assert a["ordered_tf_digest"] == b["ordered_tf_digest"]
    assert a["n_annotation_rows"] == b["n_annotation_rows"] == 11


def test_genuinely_missing_column_still_fails_closed(tmp_path):
    """The gate must NOT have been loosened: a real absence must still stop the run."""
    df = _rows().drop(columns=["orthologous_gene_name"])
    with pytest.raises(sup.FailClosed) as e:
        sup.build(_write(df, tmp_path), tmp_path / "out")
    assert e.value.status == "FAIL__ANNOTATION_TABLE_COLUMNS_ABSENT"
    assert e.value.detail["missing_columns"] == ["orthologous_gene_name"]


def test_hash_prefix_does_not_smuggle_in_a_wrong_column(tmp_path):
    """Stripping '#' must not make '#gene_name_typo' satisfy 'gene_name'."""
    df = _rows().rename(columns={"gene_name": "gene_name_typo"})
    with pytest.raises(sup.FailClosed) as e:
        sup.build(_write(df, tmp_path), tmp_path / "out")
    assert e.value.status == "FAIL__ANNOTATION_TABLE_COLUMNS_ABSENT"
    assert "gene_name" in e.value.detail["missing_columns"]


def test_empty_table_fails_closed(tmp_path):
    with pytest.raises(sup.FailClosed) as e:
        sup.build(_write(_rows().iloc[0:0], tmp_path), tmp_path / "out")
    assert e.value.status == "FAIL__ANNOTATION_TABLE_EMPTY"


def test_supply_counts_distinguish_evidence_classes(tmp_path):
    r = sup.build(_write(_rows(), tmp_path), tmp_path / "out")
    df = pd.read_csv(r["output_path"]).set_index("tf_gene_symbol")
    assert df.loc["TF_HI", "n_distinct_motifs_direct"] == 6
    assert df.loc["TF_LO", "n_distinct_motifs_direct"] == 1
    assert df.loc["TF_NONE", "n_distinct_motifs_direct"] == 0
    assert df.loc["TF_NONE", "n_distinct_motifs_similarity"] == 3
    assert df.loc["TF_ORTH", "n_distinct_motifs_orthology"] == 1


def test_zero_direct_evidence_lands_in_stratum_zero(tmp_path):
    r = sup.build(_write(_rows(), tmp_path), tmp_path / "out")
    df = pd.read_csv(r["output_path"]).set_index("tf_gene_symbol")
    assert df.loc["TF_NONE", "annotation_supply_stratum"] == 0
    assert df.loc["TF_HI", "annotation_supply_stratum"] > 0


def test_unstratifiable_supply_fails_closed(tmp_path):
    """If every TF has identical supply the control has no stratification to offer."""
    rows = [[f"m{i}", f"M{i}", f"TF_{i}", "None", "None",
             "gene is directly annotated for motif"] for i in range(5)]
    df = pd.DataFrame(rows, columns=COLS)
    with pytest.raises(sup.FailClosed) as e:
        sup.build(_write(df, tmp_path), tmp_path / "out")
    assert e.value.status == "FAIL__ANNOTATION_SUPPLY_HAS_NO_USABLE_STRATIFICATION"
