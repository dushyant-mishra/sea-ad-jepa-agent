import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "build_td_bayesian_historical_ledger.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_bayes_ledger", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_case_rows_never_carry_historical_verdict_labels():
    m = load_module()
    text = (
        "panel,source,split,half,observed,null_p95,margin_p95,pass\n"
        "0,HVS,0,0,0.64,0.54,0.10,True\n"
    )
    rows = m.parse_case_table(text, stage="TD57B", source_path="fixture.csv")
    assert len(rows) == 1
    assert "pass" not in rows[0]
    assert "verdict" not in rows[0]
    assert rows[0]["margin"] == pytest.approx(0.10)


def test_cross_stage_rows_share_substrate_source_root_but_not_stage_source_block():
    m = load_module()
    a = m.decorate_dependencies({"stage": "TD57B", "source": "HVS", "panel": 0, "split": 0, "half": 0})
    b = m.decorate_dependencies({"stage": "TD59", "source": "HVS", "panel": 0, "split": 0, "half": 0})
    assert a["substrate_source_root"] == b["substrate_source_root"]
    assert a["stage_source_block"] != b["stage_source_block"]


def test_duplicate_case_identity_is_rejected_before_block_aggregation():
    m = load_module()
    row = m.decorate_dependencies(
        {
            "stage": "TD57B",
            "source": "HVS",
            "panel": 0,
            "split": 0,
            "half": 0,
            "margin": 0.1,
            "model_eligible": True,
        }
    )
    with pytest.raises(ValueError, match="duplicate case identity"):
        m.aggregate_stage_source_blocks([row, dict(row)])


def test_related_cases_collapse_to_one_stage_source_replication_block():
    m = load_module()
    rows = []
    for panel, split, half, margin in [
        (0, 0, 0, 0.10),
        (0, 0, 1, 0.12),
        (1, 1, 0, 0.08),
        (1, 1, 1, 0.14),
    ]:
        rows.append(
            m.decorate_dependencies(
                {
                    "stage": "TD57B",
                    "source": "HVS",
                    "panel": panel,
                    "split": split,
                    "half": half,
                    "margin": margin,
                    "model_eligible": True,
                }
            )
        )
    blocks = m.aggregate_stage_source_blocks(rows)
    assert len(blocks) == 1
    assert blocks[0]["stage_source_block"] == "TD57B::HVS"
    assert blocks[0]["n_related_cases"] == 4
    assert blocks[0]["block_margin_median"] == pytest.approx(0.11)
    assert blocks[0]["effective_replication_units"] == 1


def test_td57c_markdown_rows_are_explicitly_rounded_and_not_fit_eligible():
    m = load_module()
    md = """
HVS Panel 0:
- split0/half0 observed 0.5370370; null p95 0.5555556 -> FAIL
- split0/half1 observed 0.5872340; null p95 0.5864549 -> PASS
- split1/half0 observed 0.5416667; null p95 0.5806452 -> FAIL
- split1/half1 observed 0.5872340; null p95 0.5833333 -> PASS
"""
    rows = m.parse_td57c_result_markdown(md, source_path="TD57C_RESULT.md")
    assert len(rows) == 4
    assert all(r["stage"] == "TD57C" for r in rows)
    assert all(r["source"] == "HVS" for r in rows)
    assert all(r["evidence_precision"] == "rounded_result_markdown_7dp" for r in rows)
    assert all(r["model_eligible"] is False for r in rows)
    assert all("verdict" not in r and "pass" not in r for r in rows)


def test_receipt_blocks_fit_until_exact_td57c_cases_are_supplied():
    m = load_module()
    rows = [
        m.decorate_dependencies(
            {
                "stage": "TD57B",
                "source": "HVS",
                "panel": 0,
                "split": 0,
                "half": 0,
                "margin": 0.1,
                "model_eligible": True,
                "evidence_precision": "committed_case_table",
            }
        ),
        m.decorate_dependencies(
            {
                "stage": "TD57C",
                "source": "HVS",
                "panel": 0,
                "split": 0,
                "half": 0,
                "margin": -0.02,
                "model_eligible": False,
                "evidence_precision": "rounded_result_markdown_7dp",
            }
        ),
    ]
    receipt = m.build_receipt(rows)
    assert receipt["status"] == "BLOCKED_EXACT_TD57C_CASE_VALUES_REQUIRED"
    assert receipt["historical_verdict_labels_used_for_fit"] is False
    assert receipt["corrected_replay_ingested"] is False
    assert receipt["fit_authorized"] is False
