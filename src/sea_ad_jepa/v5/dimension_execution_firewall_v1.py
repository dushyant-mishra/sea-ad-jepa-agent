from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


class DimensionExecutionStop(RuntimeError):
    pass


FORBIDDEN_HISTORICAL_FINAL_EXECUTORS = {
    "scripts/v4/validate_full104_phase2_empirical_null_refit.py",
    "scripts/v4/correct_full104_phase2_shared_selection_with_refit_null.py",
    "scripts/v4/independent_validate_full104_phase2_shared_level.py",
}

REQUIRED_MATCHING = {
    "donor",
    "operator",
    "Q_DEPTH",
    "Q_DETECT",
    "support_measurability",
}


@dataclass(frozen=True)
class DimensionExecutionFirewallV1:
    cells: int = 4_553_407
    donors: int = 104
    operators: int = 42
    addresses: int = 41_238

    def validate(self, receipt: Mapping[str, object]) -> dict[str, object]:
        if receipt.get("population_mode") != "FULL_READER_FIT_STREAM":
            raise DimensionExecutionStop("STOP_D_EXECUTION_NOT_FULL_READER_FIT")
        for key, expected in {
            "reader_fit_rows_used": self.cells,
            "unique_stable_keys_used": self.cells,
            "donors_used": self.donors,
            "operators_used": self.operators,
            "addresses": self.addresses,
        }.items():
            if int(receipt.get(key, -1)) != expected:
                raise DimensionExecutionStop(f"STOP_D_EXECUTION_{key.upper()}_MISMATCH")

        if receipt.get("expression_binding_terminal") not in {
            "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
            "PASS_FULL_READER_4553407_ROW_IDENTITY_CLOSURE",
        }:
            raise DimensionExecutionStop("STOP_D_EXECUTION_EXPRESSION_BINDING_NOT_CLOSED")

        for key in ("sampled_stratum_cap", "cells_per_stratum_cap", "row_cap"):
            value = receipt.get(key)
            if value not in (None, "NONE", 0):
                raise DimensionExecutionStop(f"STOP_D_EXECUTION_SAMPLED_SUBSTRATE:{key}")

        if receipt.get("full_null_geometry_refit") is not True:
            raise DimensionExecutionStop("STOP_D_EXECUTION_NULL_NOT_FULL_REFIT")
        if receipt.get("null_geometry") != "FULL_REFIT_EVERY_REPLICATE":
            raise DimensionExecutionStop("STOP_D_EXECUTION_NULL_GEOMETRY_MISMATCH")

        matching = receipt.get("matched_null_preserves")
        if not isinstance(matching, Sequence) or isinstance(matching, (str, bytes)):
            raise DimensionExecutionStop("STOP_D_EXECUTION_MATCHING_UNDECLARED")
        if not REQUIRED_MATCHING.issubset(set(map(str, matching))):
            raise DimensionExecutionStop("STOP_D_EXECUTION_MATCHING_INCOMPLETE")

        if receipt.get("null_replicates_derived_from_error_budget") is not True:
            raise DimensionExecutionStop("STOP_D_EXECUTION_NULL_REPLICATES_NOT_PRECISION_DERIVED")
        if receipt.get("donor_resamples_derived_from_error_budget") is not True:
            raise DimensionExecutionStop("STOP_D_EXECUTION_BOOTSTRAP_REPLICATES_NOT_PRECISION_DERIVED")
        for key in ("null_replicates", "donor_resamples"):
            value = receipt.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise DimensionExecutionStop(f"STOP_D_EXECUTION_INVALID_{key.upper()}")

        scripts = receipt.get("final_authority_scripts")
        if not isinstance(scripts, Sequence) or isinstance(scripts, (str, bytes)):
            raise DimensionExecutionStop("STOP_D_EXECUTION_SCRIPT_LEDGER_MISSING")
        used = set(map(str, scripts))
        forbidden = sorted(used & FORBIDDEN_HISTORICAL_FINAL_EXECUTORS)
        if forbidden:
            raise DimensionExecutionStop(
                "STOP_D_EXECUTION_HISTORICAL_DIAGNOSTIC_PROMOTED:" + ",".join(forbidden)
            )

        for key, terminal in (
            ("synthetic_data_used", "STOP_D_EXECUTION_SYNTHETIC_OR_UNKNOWN"),
            ("pathology_used", "STOP_D_EXECUTION_PATHOLOGY_OR_UNKNOWN"),
            ("checkpoint_outcomes_used", "STOP_D_EXECUTION_CHECKPOINT_ADAPTATION_OR_UNKNOWN"),
        ):
            if receipt.get(key) is not False:
                raise DimensionExecutionStop(terminal)

        boundary = receipt.get("search_boundary_supported")
        d_shared = receipt.get("D_shared")
        if boundary is True:
            if d_shared not in (None, "UNRESOLVED"):
                raise DimensionExecutionStop("STOP_D_EXECUTION_BOUNDARY_SELECTED_AS_D")
            if receipt.get("terminal") != "EXPAND_SEARCH_ENVELOPE":
                raise DimensionExecutionStop("STOP_D_EXECUTION_BOUNDARY_WITHOUT_EXPANSION")
            return {
                "passed": True,
                "terminal": "PASS_D_EXECUTION_REQUIRES_SEARCH_EXPANSION",
                "D_shared": None,
            }
        if boundary is not False:
            raise DimensionExecutionStop("STOP_D_EXECUTION_BOUNDARY_STATUS_UNKNOWN")

        for key in ("D_shared", "D_private", "D_total", "D_obs"):
            value = receipt.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise DimensionExecutionStop(f"STOP_D_EXECUTION_INVALID_{key.upper()}")
        if int(receipt["D_total"]) != int(receipt["D_shared"]) + int(receipt["D_private"]):
            raise DimensionExecutionStop("STOP_D_EXECUTION_DIMENSION_ARITHMETIC")
        if int(receipt.get("contiguous_prefix_supported_through", -1)) != int(receipt["D_shared"]):
            raise DimensionExecutionStop("STOP_D_EXECUTION_NONCONTIGUOUS_SHARED_SELECTION")

        return {
            "passed": True,
            "terminal": "PASS_V5_FULL_STREAM_DIMENSION_EXECUTION_FIREWALL_V1",
            "D_shared": int(receipt["D_shared"]),
            "D_private": int(receipt["D_private"]),
            "D_total": int(receipt["D_total"]),
            "D_obs": int(receipt["D_obs"]),
        }
