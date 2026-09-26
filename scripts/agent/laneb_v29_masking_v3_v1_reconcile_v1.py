"""Lane B V29 Task 2: reconcile the two V3 masking artifacts with the V1 closure.

This script NEVER casts, reclassifies or fabricates a V1 instance. It measures,
mechanically, what the closure actually reads off each masking parameter and
whether the V3 successor supplies it, so that the conflict can be classified as
either a NOMINAL typing conflict (same science, different class name) or a
SCIENTIFIC divergence (the V3 design deliberately removes something the closure
requires).

The distinction matters: a nominal conflict is safe to resolve with an explicitly
versioned successor closure; a scientific divergence is a design decision that
must be adjudicated on the science, not on the type system.
"""
from __future__ import annotations

import dataclasses
import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "agent"))

from laneb_v29_closure_root_extract_v1 import build_report as build_closure_graph  # noqa: E402

PAIRS = [
    {
        "root": "masking_rng_replay_authority_sha256",
        "closure_param": "masking_rng_replay",
        "v1": ("sea_ad_jepa.v5.masking_rng_replay_authority_v1", "MaskingRngReplayAuthorityV1"),
        "v3": ("sea_ad_jepa.v5.masking_rng_replay_authority_v3", "MaskingRngReplayAuthorityV3"),
        "v3_artifact": (
            "analysis/v5_full104_information_channel_redteam_20260920/evidence/"
            "phase_iv/MASKING_RNG_REPLAY_AUTHORITY_V3.json"
        ),
    },
    {
        "root": "masking_qualification_parameters_authority_sha256",
        "closure_param": "masking_qualification_parameters",
        "v1": (
            "sea_ad_jepa.v5.masking_qualification_parameters_authority_v1",
            "MaskingQualificationParametersAuthorityV1",
        ),
        "v3": (
            "sea_ad_jepa.v5.masking_qualification_parameters_authority_v3",
            "MaskingQualificationParametersAuthorityV3",
        ),
        "v3_artifact": (
            "analysis/v5_full104_information_channel_redteam_20260920/evidence/"
            "phase_iv/MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3.json"
        ),
    },
]


def _fields(cls):
    return [f.name for f in dataclasses.fields(cls)]


def _members(cls):
    """Every public attribute name the class exposes (fields + properties)."""
    out = set(_fields(cls))
    for name, value in vars(cls).items():
        if name.startswith("_"):
            continue
        if isinstance(value, property):
            out.add(name)
    return out


def analyse():
    graph = build_closure_graph()
    reads_by_param = {}
    for row in graph["roots"]:
        if row["closure_parameter"]:
            reads_by_param[row["closure_parameter"]] = row["attributes_read_by_closure"]

    results = []
    for pair in PAIRS:
        v1_mod, v1_name = pair["v1"]
        v3_mod, v3_name = pair["v3"]
        v1 = getattr(importlib.import_module(v1_mod), v1_name)
        v3 = getattr(importlib.import_module(v3_mod), v3_name)

        reads = reads_by_param.get(pair["closure_param"], [])
        # Attributes the closure calls as methods are part of the duck interface.
        method_reads = [a for a in reads if a in ("validate", "canonical_digest")]
        data_reads = [a for a in reads if a not in method_reads]

        v1_members = _members(v1)
        v3_members = _members(v3)

        supplied = [a for a in data_reads if a in v3_members]
        missing = [a for a in data_reads if a not in v3_members]

        v1_fields = set(_fields(v1))
        v3_fields = set(_fields(v3))

        artifact_path = ROOT / pair["v3_artifact"]
        artifact = None
        if artifact_path.exists():
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

        v3_validates = None
        v3_digest = None
        v3_declared = None
        if artifact:
            kwargs = {}
            for f in _fields(v3):
                if f in artifact:
                    kwargs[f] = artifact[f]
            try:
                obj = v3(**kwargs)
                obj.validate()
                v3_validates = True
                v3_digest = obj.canonical_digest()
            except Exception as exc:  # noqa: BLE001
                v3_validates = False
                v3_digest = "OWN_CLASS_VALIDATE_FAILED: %s" % exc
            for key in ("authority_sha256", "parameter_authority_sha256"):
                if key in artifact:
                    v3_declared = artifact[key]

        if missing:
            classification = "SCIENTIFIC_DIVERGENCE"
            rationale = (
                "V3 does not expose %d attribute(s) the closure compares: %s. "
                "Even with the isinstance check removed the closure would raise. "
                "This is a design decision, not a type mismatch."
                % (len(missing), ", ".join(missing))
            )
        else:
            classification = "NOMINAL_TYPING_CONFLICT"
            rationale = (
                "V3 exposes every attribute the closure compares (%s). The sole "
                "obstruction is the isinstance(%s) check." % (", ".join(data_reads) or "none", v1_name)
            )

        results.append(
            {
                "root": pair["root"],
                "closure_parameter": pair["closure_param"],
                "v1_class": v1_name,
                "v3_class": v3_name,
                "closure_data_attributes_read": data_reads,
                "closure_method_interface_read": sorted(method_reads),
                "v3_supplies": supplied,
                "v3_missing": missing,
                "v1_only_fields": sorted(v1_fields - v3_fields),
                "v3_only_fields": sorted(v3_fields - v1_fields),
                "shared_fields": sorted(v1_fields & v3_fields),
                "v3_is_field_superset_of_v1": v1_fields.issubset(v3_fields),
                "v3_subclasses_v1": issubclass(v3, v1),
                "v3_artifact_path": pair["v3_artifact"],
                "v3_artifact_exists": artifact is not None,
                "v3_artifact_own_class_validate": v3_validates,
                "v3_artifact_recomputed_digest": v3_digest,
                "v3_artifact_declared_digest": v3_declared,
                "v3_artifact_digest_agrees": (
                    v3_declared is not None and v3_declared == v3_digest
                ),
                "classification": classification,
                "rationale": rationale,
            }
        )

    return {
        "schema": "JEPA_LANEB_V29_MASKING_V3_V1_RECONCILIATION_V1",
        "prohibition_honoured": (
            "no cast, no reclassification, no fabricated V1 instance; "
            "the V3 objects are measured against the closure contract as they are"
        ),
        "pairs": results,
    }


def main():
    report = analyse()
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    text = json.dumps(report, indent=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print("wrote " + str(out))
    for pair in report["pairs"]:
        print()
        print("ROOT  " + pair["root"])
        print("  classification: " + pair["classification"])
        print("  closure reads : " + ", ".join(pair["closure_data_attributes_read"]))
        print("  v3 supplies   : " + ", ".join(pair["v3_supplies"]))
        print("  v3 MISSING    : " + (", ".join(pair["v3_missing"]) or "(none)"))
        print("  v3 subclasses v1: %s" % pair["v3_subclasses_v1"])
        print("  v3 field superset of v1: %s" % pair["v3_is_field_superset_of_v1"])
        print("  v3 artifact validates: %s" % pair["v3_artifact_own_class_validate"])
        print("  v3 artifact digest agrees: %s" % pair["v3_artifact_digest_agrees"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
