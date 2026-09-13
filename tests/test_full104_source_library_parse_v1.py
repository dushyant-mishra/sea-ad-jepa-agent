import importlib.util
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[1] / "scripts" / "v5_anticheat" / "bind_full104_expression_blocks_v4.py"
spec = importlib.util.spec_from_file_location("full104_bind_v4", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_real_nph_integral_float_text_is_accepted():
    assert m._parse_positive_integral_source_library("61129.0") == 61129
    assert m._parse_positive_integral_source_library("1487.0") == 1487


@pytest.mark.parametrize(
    "value",
    ["61129.5", "0.0", "-1.0", "nan", "inf", "-inf", "", "abc"],
)
def test_non_integral_non_positive_non_finite_or_invalid_library_is_rejected(value):
    with pytest.raises(RuntimeError, match="STOP_FULL104_BLOCK_META_VALUE_SEMANTICS"):
        m._parse_positive_integral_source_library(value)
