"""Extra finding (beyond the nine listed items): G6/G7 read the Sample-A freeze with dtype=str, so sample_row must be
ordered numerically. A text sort puts "10" before "2" and the frozen order check then refuses the real 25,000-row
Sample A, which would spend the immutable attempt on a spurious failure. Synthetic frames only."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
V5 = ROOT / "scripts" / "v5"
SCRIPTS = {"g6": "materialize_td_relational_corrected_sampleA_v2.py", "g7": "audit_td_relational_g7_s174_overlap_v2.py"}


def load(key):
    spec = importlib.util.spec_from_file_location(f"order_{key}", V5 / SCRIPTS[key])
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def frame(n_rows, order):
    """Rows in the given file order, with the real Sample-A freeze schema (every column G6 requires) and, like the
    real file, no physical global_row."""
    sources = (["HVS"] * 3 + ["SEA_AD"] * (n_rows - 6) + ["NPH52"] * 3)
    rows = [{"sample": "A_NATURAL_MIXTURE", "sample_row": str(i), "source": sources[i], "matrix_id": f"{sources[i]}::m",
             "operator_index": "0", "local_row": str(i), "donor_id": f"donor_{i % 4}", "cell_id": f"c{i}"}
            for i in order]
    rows.append({"sample": "B_COVERAGE_DISCOVERY", "sample_row": "0", "source": "HVS", "matrix_id": "HVS::m",
                 "operator_index": "0", "local_row": "0", "donor_id": "donor_b", "cell_id": "b0"})
    out = pd.DataFrame(rows).astype(str)
    assert "global_row" not in out.columns
    return out


@pytest.mark.parametrize("key", ["g6", "g7"])
@pytest.mark.parametrize("n_rows", [12, 1000])
def test_text_sample_rows_are_ordered_numerically(monkeypatch, key, n_rows):
    m = load(key)
    monkeypatch.setattr(m, "N_SAMPLE_A", n_rows)
    monkeypatch.setattr(m, "SOURCE_COUNTS", {"HVS": 3, "NPH52": 3, "SEA_AD": n_rows - 6})
    order = list(range(n_rows))[::-1]  # file order deliberately not the frozen order
    selected = m.select_sample_a(frame(n_rows, order)) if key == "g7" else m.select_sample_a(frame(n_rows, order),
                                                                                              enforce_geometry=True)
    assert selected.sample_row.astype(int).tolist() == list(range(n_rows))
    assert selected.cell_id.tolist() == [f"c{i}" for i in range(n_rows)]


@pytest.mark.parametrize("key", ["g6", "g7"])
def test_a_genuinely_missing_row_is_still_refused(monkeypatch, key):
    m = load(key)
    monkeypatch.setattr(m, "N_SAMPLE_A", 12)
    monkeypatch.setattr(m, "SOURCE_COUNTS", {"HVS": 3, "NPH52": 3, "SEA_AD": 6})
    f = frame(13, list(range(13)))
    f = f[f.sample_row != "7"]  # 12 rows with the right source counts, but row 7 missing and row 12 present
    with pytest.raises(RuntimeError, match="order"):
        m.select_sample_a(f) if key == "g7" else m.select_sample_a(f, enforce_geometry=True)
