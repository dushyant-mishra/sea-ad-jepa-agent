import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "sea_ad_jepa" / "v4" / "foundation_residual_gates.py"

spec = importlib.util.spec_from_file_location("foundation_residual_gates_harmonization", MODULE)
G = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(G)


def test_noncanonical_subclass_strings_do_not_count_as_harmonized_broad_labels():
    rows = [
        {"matrix_id":"canonical","source":"SEA_AD","native_class":"x","broad_class":"Neuronal: GABAergic"},
        {"matrix_id":"subclass","source":"SEA_AD","native_class":"STR D2 MSNSubclass","broad_class":"STR D2 MSNSubclass"},
        {"matrix_id":"missing","source":"NPH52","native_class":"Astro","broad_class":""},
    ]
    out = {r["matrix_id"]: r for r in G.matrix_label_identifiability(rows)}
    assert out["canonical"]["broad_label_identifiability"] == "AVAILABLE"
    assert out["subclass"]["broad_label_available_fraction"] == 0.0
    assert out["subclass"]["broad_label_identifiability"] == "UNAVAILABLE"
    assert out["subclass"]["noncanonical_broad_labels"] == ["STR D2 MSNSubclass"]
    assert out["missing"]["broad_label_identifiability"] == "UNAVAILABLE"
