"""The V79 contract on disk is exactly what its generator produces, its firewall and sampling constants are the
ones the code enforces, it binds a passing custody receipt, and its files are LF-only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_contract as K  # noqa: E402
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402


def test_committed_contract_is_what_the_generator_produces():
    c = K.build()
    assert json.loads(K.JSON_OUT.read_text(encoding="utf-8")) == json.loads(json.dumps(c))
    assert K.MD_OUT.read_bytes().decode("utf-8") == K.render(c)


def test_contract_constants_are_the_enforced_ones():
    c = K.build()
    assert c["firewall"]["allowed_meta_fields"] == list(FW.ALLOWED_META_FIELDS)
    assert c["firewall"]["allowed_split_columns"] == list(FW.ALLOWED_SPLIT_COLUMNS)
    assert c["firewall"]["denied_field_patterns"] == list(FW.DENY_FIELD_PATTERNS)
    assert c["broad_class"]["primary_map"] == FW.CLASS_MAP
    assert c["data"]["gene_population"]["seed"] == DA.GENE_SAMPLE_SEED
    assert c["status"] == "FROZEN_BEFORE_ANY_REAL_DATA_INFERENCE"


def test_contract_binds_a_passing_custody_receipt():
    c = K.build()
    rec = json.loads(K.CUSTODY.read_text(encoding="utf-8"))
    assert rec["terminal"] == c["data"]["custody_receipt"]["required_terminal"]
    assert c["data"]["custody_receipt"]["sha256"] == K.sha_file(K.CUSTODY)
    assert rec["universe"]["equal_to_frozen"] and rec["universe"]["size"] == 14417


def test_lane_files_are_lf_only():
    for p in [K.JSON_OUT, K.MD_OUT, *sorted((ROOT / "scripts" / "v79").glob("*.py")),
              *sorted((ROOT / "tests" / "v79").glob("*.py"))]:
        assert b"\r\n" not in p.read_bytes(), p
