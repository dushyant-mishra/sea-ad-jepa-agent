"""Offline hostile tests for public E2G reference metadata classification."""
import importlib.util
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/regulatory/audit_e2g_public_reference_tracks_v1.py"
spec = importlib.util.spec_from_file_location("e2g_ref_probe", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def example(label, model="scE2G", url="https://example.org/track.bedpe?token=SENSITIVE"):
    return {"cellType":label, "modelType":model,"e2gPredictionsUrl":url,
            "study":"fixture", "cellTypeId":"fixture", "studyId":"fixture",
            "dataset":"fixture"}

def test_scientific_classification_and_overclaim_guards():
    r = m.summarize([example("Macrophages 1"),
                     example("adult microglia", "ENCODE-rE2G"),
                     example("brain"), example("unrelated")])
    assert r["categories"] == {"brain_context":1,"explicit_microglia":1,
                               "macrophage_context":1}
    assert r["source_context_authority"]["adult_human_microglia_proven"] is False
    assert r["source_context_authority"]["target_selection"] is False
    assert len(r["selected_rows"]) == 3
    assert r["selected_rows"][0]["context_role"] == "explicit_microglia"
    assert "SENSITIVE" not in str(r)

def test_unknown_and_malicious_urls_not_fetched_or_leaked():
    x = m.summarize([example("Monocytes",url="http://127.0.0.1/path?q=secret")])
    info = x["selected_rows"][0]["e2g_prediction_url"]
    assert info["https"] is False
    assert info["host"] == "127.0.0.1"
    assert "secret" not in str(x)

def test_fail_closed_bad_api_shape():
    with pytest.raises(ValueError):
        m.summarize({"x":3})
    with pytest.raises(ValueError):
        m.summarize([42])
    with pytest.raises(ValueError):
        m.summarize([{"cellType":123}])

@pytest.mark.parametrize("label,expected", [
    ("Microglia","explicit_microglia"),
    ("Inflammatory macrophage", "macrophage_context"),
    ("CD14-positive monocyte", "monocyte_context"),
    ("brain pericyte", "brain_context"),
    ("astrocyte of the hippocampus", "brain_context"),
    ("HMC3 line",None),
])
def test_roles(label, expected):
    assert m.category(label)==expected
