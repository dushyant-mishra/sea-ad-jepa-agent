from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

PASS_IDENTITY_TERMINAL = "PASS_FULL_READER_4553407_ROW_IDENTITY_CLOSURE"

@dataclass(frozen=True)
class DimensionAuthorityGuardV2:
    metadata_sha256: str
    production_loader_manifest_sha256: str
    cells: int = 4_553_407
    donors: int = 104
    shards: int = 42
    addresses: int = 41_238

    def validate(self, receipt: Mapping[str, object]) -> dict[str, object]:
        if receipt.get("expression_location_terminal") != PASS_IDENTITY_TERMINAL:
            raise RuntimeError("STOP_D_AUTHORITY_FULL_EXPRESSION_ROW_IDENTITY_NOT_CLOSED")
        if receipt.get("metadata_sha256") != self.metadata_sha256:
            raise RuntimeError("STOP_D_AUTHORITY_METADATA_MISMATCH")
        if receipt.get("production_loader_manifest_sha256") != self.production_loader_manifest_sha256:
            raise RuntimeError("STOP_D_AUTHORITY_LOADER_MANIFEST_MISMATCH")
        if int(receipt.get("cells", -1)) != self.cells or int(receipt.get("reader_fit_identity_rows_matched", -1)) != self.cells:
            raise RuntimeError("STOP_D_AUTHORITY_POPULATION_ROW_CLOSURE_MISMATCH")
        if int(receipt.get("unique_stable_keys", -1)) != self.cells:
            raise RuntimeError("STOP_D_AUTHORITY_STABLE_KEY_CLOSURE_MISMATCH")
        if int(receipt.get("donors", -1)) != self.donors:
            raise RuntimeError("STOP_D_AUTHORITY_DONOR_CLOSURE_MISMATCH")
        if int(receipt.get("shards_bound", -1)) != self.shards or int(receipt.get("addresses", -1)) != self.addresses:
            raise RuntimeError("STOP_D_AUTHORITY_SHARD_OR_ADDRESS_CLOSURE_MISMATCH")
        if receipt.get("population_mode") != "FULL_READER_FIT_STREAM":
            raise RuntimeError("STOP_D_AUTHORITY_NOT_FULL_READER_FIT")
        if receipt.get("estimand") != "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR":
            raise RuntimeError("STOP_D_AUTHORITY_ESTIMAND_MISMATCH")
        if receipt.get("null_geometry") != "FULL_REFIT_EVERY_REPLICATE":
            raise RuntimeError("STOP_D_AUTHORITY_NULL_GEOMETRY_MISMATCH")
        if receipt.get("sampled_stratum_cap") not in (None, "NONE"):
            raise RuntimeError("STOP_D_AUTHORITY_SAMPLED_STRATUM_CAP_FORBIDDEN")
        for key, stop in [
            ("synthetic_data_used", "STOP_D_AUTHORITY_SYNTHETIC_OR_UNKNOWN"),
            ("pathology_used", "STOP_D_AUTHORITY_PATHOLOGY_OR_UNKNOWN"),
            ("checkpoint_outcomes_used", "STOP_D_AUTHORITY_CHECKPOINT_ADAPTATION_OR_UNKNOWN"),
        ]:
            if receipt.get(key) is not False:
                raise RuntimeError(stop)
        ds = int(receipt.get("D_shared", -1))
        dp = int(receipt.get("D_private", -1))
        do = int(receipt.get("D_obs", -1))
        dt = int(receipt.get("D_total", -1))
        if min(ds, dp, do, dt) < 0 or dt != ds + dp:
            raise RuntimeError("STOP_D_AUTHORITY_DIMENSION_ARITHMETIC")
        return {"passed": True, "D_shared": ds, "D_private": dp, "D_total": dt, "D_obs": do}
