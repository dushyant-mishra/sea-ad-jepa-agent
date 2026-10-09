from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_canonical_nihcard_split_uses_dedicated_frozen_receipt():
    split=json.loads((ROOT/"results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json").read_text())
    doc=(ROOT/"docs/agent/V65_NIHCARD_RECOVERABILITY_SPLIT_AUTHORITY_20260930.md").read_text()
    assert split["seed"]==20260930
    assert split["donors"]=={"train":16,"validation":4,"test":4}
    assert "V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json" in doc
    assert "superseded for future execution" in doc
    assert "TEST" in doc

def test_promoter_contract_keeps_transcript_and_tss_denominators_distinct():
    t=(ROOT/"docs/agent/V65_PROMOTER_LEDGER_DENOMINATOR_CONTRACT_20260930.md").read_text()
    assert "644,292" in t
    assert "389,280" in t
    assert "PROMOTER_TRANSCRIPT_LEDGER" in t
    assert "EXACT_TSS_LEDGER" in t
    assert "TRANSCRIPT_TO_TSS_MEMBERSHIP" in t
    assert "NOT_MEASURED -> 0" in t

def test_first_recoverability_factor_is_atac_only_and_test_locked():
    t=(ROOT/"docs/agent/V65_FIRST_PRIVILEGED_FACTOR_RECOVERABILITY_EXECUTION_CONTRACT_20260930.md").read_text()
    assert "ATAC-only" in t
    assert "RNA must not enter privileged-factor construction" in t
    assert "Primary privileged rank is fixed at 16" in t
    assert "0, 2, 4, 8, 16" in t
    assert "cannot by itself assign `REGULATORY-PRIVATE`" in t
    assert "TEST remains unopened" in t
    assert "Stage 4 NOT AUTHORIZED" in t
