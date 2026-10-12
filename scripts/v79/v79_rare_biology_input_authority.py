from __future__ import annotations

import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED = {
    "v6r5a_program_weights",
    "foundation_41k_50k_expression",
    "gse174367_morabito",
    "gse214979",
    "gse272082",
    "stage75_79_regulatory",
    "spatial_context",
    "gse178317",
    "v79_q00_q11",
}


def validate(doc: dict) -> dict:
    if doc.get("schema") != "v79-rare-biology-input-authority-v1":
        raise ValueError("schema mismatch")
    for key in ("training_authorized", "q00_q11_mutation_authorized", "pathology_used"):
        if doc.get(key) is not False:
            raise ValueError(f"{key} must be false")
    assets = doc.get("assets")
    if not isinstance(assets, dict) or not _REQUIRED.issubset(assets):
        raise ValueError("required assets missing")
    for name, asset in assets.items():
        sha = asset.get("sha256")
        if asset.get("sha256_required", False) and (not isinstance(sha, str) or not _SHA.fullmatch(sha)):
            raise ValueError(f"{name} sha256 invalid")
        roles = asset.get("allowed_roles", [])
        if not isinstance(roles, list) or any(not isinstance(role, str) for role in roles):
            raise ValueError(f"{name} allowed_roles invalid")

    morabito = assets["gse174367_morabito"]
    if morabito.get("pairing") != "separate_nuclei_donor_level":
        raise ValueError("Morabito must remain separate-nuclei donor-level evidence")
    if "target_selection" in morabito["allowed_roles"]:
        raise ValueError("Morabito target_selection is forbidden")

    if assets["v79_q00_q11"]["allowed_roles"] != ["measurement_statistical_qualification"]:
        raise ValueError("Q00-Q11 can only qualify the measurement/statistical layer")

    if any("causal" in role.lower() for role in assets["stage75_79_regulatory"]["allowed_roles"]):
        raise ValueError("regulatory assets cannot claim causal truth")

    return doc
