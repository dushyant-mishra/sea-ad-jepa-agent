from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

PASS_FULL104_TERMINAL = "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE"

@dataclass(frozen=True)
class DimensionAuthorityGuardV3:
    metadata_sha256: str
    block_manifest_sha256: str = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
    materialization_contract_sha256: str = "612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17"
    materialization_audit_sha256: str = "9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf"
    cells: int = 4_553_407
    donors: int = 104
    operators: int = 42
    matrices: int = 42
    blocks: int = 8_915
    addresses: int = 41_238

    def validate(self, receipt: Mapping[str, object]) -> dict[str, object]:
        if receipt.get("expression_binding_terminal") != PASS_FULL104_TERMINAL:
            raise RuntimeError("STOP_D_AUTHORITY_FULL104_EXPRESSION_NOT_CLOSED")
        if receipt.get("metadata_sqlite_sha256") != self.metadata_sha256:
            raise RuntimeError("STOP_D_AUTHORITY_METADATA_MISMATCH")
        if receipt.get("block_manifest_sha256") != self.block_manifest_sha256:
            raise RuntimeError("STOP_D_AUTHORITY_BLOCK_MANIFEST_MISMATCH")
        if receipt.get("materialization_contract_sha256") != self.materialization_contract_sha256:
            raise RuntimeError("STOP_D_AUTHORITY_MATERIALIZATION_CONTRACT_MISMATCH")
        if receipt.get("materialization_audit_sha256") != self.materialization_audit_sha256:
            raise RuntimeError("STOP_D_AUTHORITY_MATERIALIZATION_AUDIT_MISMATCH")
        expected = {
            "cells": self.cells,
            "donors": self.donors,
            "operators": self.operators,
            "matrices": self.matrices,
            "blocks": self.blocks,
            "addresses": self.addresses,
        }
        for key, value in expected.items():
            if int(receipt.get(key, -1)) != value:
                raise RuntimeError(f"STOP_D_AUTHORITY_{key.upper()}_MISMATCH")
        if int(receipt.get("cross_ledger_identity_mismatches", -1)) != 0:
            raise RuntimeError("STOP_D_AUTHORITY_CROSS_LEDGER_IDENTITY_MISMATCH")
        if int(receipt.get("cross_ledger_missing_cells", -1)) != 0:
            raise RuntimeError("STOP_D_AUTHORITY_CROSS_LEDGER_MISSING_CELLS")
        if receipt.get("test_fixture_mode") is not False:
            raise RuntimeError("STOP_D_AUTHORITY_TEST_FIXTURE_OR_UNKNOWN")
        if receipt.get("synthetic_data_used") is not False:
            raise RuntimeError("STOP_D_AUTHORITY_SYNTHETIC_OR_UNKNOWN")
        if receipt.get("pathology_used") is not False:
            raise RuntimeError("STOP_D_AUTHORITY_PATHOLOGY_OR_UNKNOWN")
        if receipt.get("checkpoint_outcomes_used") is not False:
            raise RuntimeError("STOP_D_AUTHORITY_CHECKPOINT_ADAPTATION_OR_UNKNOWN")
        if receipt.get("population_mode") != "FULL_READER_FIT_STREAM":
            raise RuntimeError("STOP_D_AUTHORITY_NOT_FULL_READER_FIT")
        if receipt.get("estimand") != "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR":
            raise RuntimeError("STOP_D_AUTHORITY_ESTIMAND_MISMATCH")
        if receipt.get("null_geometry") != "FULL_REFIT_EVERY_REPLICATE":
            raise RuntimeError("STOP_D_AUTHORITY_NULL_GEOMETRY_MISMATCH")
        if receipt.get("sampled_stratum_cap") not in (None, "NONE"):
            raise RuntimeError("STOP_D_AUTHORITY_SAMPLED_STRATUM_CAP_FORBIDDEN")
        ds = int(receipt.get("D_shared", -1))
        dp = int(receipt.get("D_private", -1))
        dt = int(receipt.get("D_total", -1))
        do = int(receipt.get("D_obs", -1))
        if min(ds, dp, dt, do) < 0 or dt != ds + dp:
            raise RuntimeError("STOP_D_AUTHORITY_DIMENSION_ARITHMETIC")
        return {"passed": True, "D_shared": ds, "D_private": dp, "D_total": dt, "D_obs": do}
