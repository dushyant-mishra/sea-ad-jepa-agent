from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

PASS_LOCATION_TERMINALS = {
    "PASS_D1_V2_EXPRESSION_LOCATION_BINDING",
    "PASS_FULL_READER_TARGET_QUALIFICATION_EXPRESSION_PREFLIGHT",
    "PASS_42_OF_42_PHYSICAL_SHARDS_BOUND",
}


@dataclass(frozen=True)
class DimensionAuthorityGuardV1:
    metadata_sha256: str
    cells: int
    donors: int
    require_full_reader_fit: bool
    require_equal_donor_weighting: bool
    require_full_refit_null: bool

    def validate(self, receipt: Mapping[str, object]) -> dict[str, object]:
        if receipt.get("metadata_sha256") != self.metadata_sha256:
            raise RuntimeError("STOP_D_AUTHORITY_METADATA_MISMATCH")
        if int(receipt.get("cells", -1)) != self.cells or int(
            receipt.get("donors", -1)
        ) != self.donors:
            raise RuntimeError("STOP_D_AUTHORITY_POPULATION_MISMATCH")
        if (
            self.require_full_reader_fit
            and receipt.get("population_mode") != "FULL_READER_FIT_STREAM"
        ):
            raise RuntimeError("STOP_D_AUTHORITY_NOT_FULL_READER_FIT")
        if receipt.get("expression_location_terminal") not in PASS_LOCATION_TERMINALS:
            raise RuntimeError("STOP_D_AUTHORITY_FULL_EXPRESSION_NOT_BOUND")
        if (
            self.require_equal_donor_weighting
            and receipt.get("estimand") != "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR"
        ):
            raise RuntimeError("STOP_D_AUTHORITY_ESTIMAND_MISMATCH")
        if (
            self.require_full_refit_null
            and receipt.get("null_geometry") != "FULL_REFIT_EVERY_REPLICATE"
        ):
            raise RuntimeError("STOP_D_AUTHORITY_NULL_GEOMETRY_MISMATCH")
        if receipt.get("sampled_stratum_cap") not in (None, "NONE"):
            raise RuntimeError("STOP_D_AUTHORITY_SAMPLED_STRATUM_CAP_FORBIDDEN")
        if receipt.get("synthetic_data_used") is not False:
            raise RuntimeError("STOP_D_AUTHORITY_SYNTHETIC_OR_UNKNOWN")
        if receipt.get("pathology_used") is not False:
            raise RuntimeError("STOP_D_AUTHORITY_PATHOLOGY_OR_UNKNOWN")
        if receipt.get("checkpoint_outcomes_used") is not False:
            raise RuntimeError("STOP_D_AUTHORITY_CHECKPOINT_ADAPTATION_OR_UNKNOWN")

        d_shared = int(receipt.get("D_shared", -1))
        d_private = int(receipt.get("D_private", -1))
        d_obs = int(receipt.get("D_obs", -1))
        d_total = int(receipt.get("D_total", -1))
        if min(d_shared, d_private, d_obs, d_total) < 0 or d_total != d_shared + d_private:
            raise RuntimeError("STOP_D_AUTHORITY_DIMENSION_ARITHMETIC")
        return {
            "passed": True,
            "D_shared": d_shared,
            "D_private": d_private,
            "D_total": d_total,
            "D_obs": d_obs,
        }
