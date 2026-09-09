import hashlib
import importlib.util
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts" / "v5_anticheat" / "build_full_reader_expression_location_manifest_v2.py"
SPEC = importlib.util.spec_from_file_location("location_builder", PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_stem_matches_frozen_loader_naming_rule():
    matrix = "HVS::19cd530b-622c-4bd8-b738-dbf169412cb0"
    assert MOD.shard_stem(matrix) == hashlib.sha256(
        f"corrected|{matrix}".encode()
    ).hexdigest()[:16]


def test_source_semantics_are_matrix_bound():
    assert MOD.infer_source("HVS::x") == "HVS"
    assert MOD.infer_source("NPH52::matrix::x") == "NPH52"
    assert MOD.infer_source("sea_ad_mtg_rna_final_2026") == "SEA_AD"
