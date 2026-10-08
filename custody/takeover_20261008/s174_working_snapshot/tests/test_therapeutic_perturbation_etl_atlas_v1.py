from pathlib import Path
import ast

SCRIPT = Path("analysis/therapeutic_perturbation_etl/scripts/build_perturbation_etl_atlas_v1.py")


def test_script_parses() -> None:
    ast.parse(SCRIPT.read_text(encoding="utf-8"))


def test_fail_closed_contract_present() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "--require-physical" in text
    assert "sha256_match" in text
    assert "PERTURBATION_DATASET_ETL_AND_READINESS" in text
    assert '"therapeutic_ranking": "OFF"' in text
    assert '"jepa_training": "OFF"' in text


def test_expected_study_universe_is_explicit() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for accession in (
        "GSE175721", "GSE178317", "GSE240609", "GSE241858",
        "GSE254205", "GSE293118", "GSE301119", "GSE311359",
    ):
        assert accession in text
