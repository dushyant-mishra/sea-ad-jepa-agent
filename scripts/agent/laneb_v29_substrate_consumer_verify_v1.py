"""Lane B V29 Task 1: verify the FULL104 substrate root's DOWNSTREAM bindings.

The closure does not merely accept ``full104_substrate_sha256`` as a string. It
equality-checks that string against a named attribute on several consuming
authorities. This script enumerates those consumers FROM THE CLOSURE SOURCE (no
hand-written list), then for each consumer:

1. resolves the defining class,
2. finds committed artifacts of that class BY SCHEMA ROLE, never by filename,
3. reads the exact attribute the closure compares,
4. reports whether that attribute carries the authenticated substrate digest,
5. reconstructs the dataclass from the artifact and recomputes canonical_digest
   where every declared field is present.

Outcomes are explicit. A consumer with no committed artifact is reported as
NO_COMMITTED_ARTIFACT, which BLOCKS the substrate root. It is never silently
counted as passing, and an empty result is never reported as "0 defects".
"""
from __future__ import annotations

import dataclasses
import importlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

sys.path.insert(0, str(ROOT / "scripts" / "agent"))
from laneb_v29_closure_root_extract_v1 import build_report as build_closure_graph  # noqa: E402
from laneb_v29_schema_artifact_resolver_v1 import _class_schema_map  # noqa: E402

AUTHENTIC_SUBSTRATE = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
KNOWN_DECOY = "e482d9da21232bdeb6b3f198f42b9fbcf1530ba1b3e86e104ffbb651ca9df808"

# Closure parameters that are NOT isinstance-enforced still have a defining class
# in the project. These are resolved from the module that defines the schema the
# closure's own docstrings and sibling builders use. Each entry is justified in
# the deliverable; none is a guess used to manufacture a pass.
DUCK_TYPED_DEFINING_CLASS = {
    "representation": "PrimaryRepresentationAuthorityV1",
    "support_estimability": "SupportEstimabilityAuthorityV1",
    "base_training_estimand": "BaseTrainingEstimandAuthorityV1",
    "protected_registry": "ProductionProtectedRegistryAuthorityV1",
    "critical_test": "CriticalTestExecutionAuthorityV1",
}

# Some committed artifacts carry the defining schema label but are structured
# documents rather than flat instance serializations. Reaching the authority
# instance then requires an external adapter that decides which nested block
# fills which authority role. That adapter is trusted code living outside the
# artifact, so the binding is recorded as ADAPTER-mediated and never conflated
# with a self-authenticating artifact whose bytes ARE its canonical digest.
DOCUMENT_ADAPTERS = {
    "CanonicalAddressRegistryAuthorityV1": {
        "declared_digest_field": "canonical_authority_digest",
        "field_from_block": {
            "registry_sha256": ("ADDRESS_REGISTRY", "sha256"),
            "registry_row_count": ("ADDRESS_REGISTRY", "row_count"),
            "full104_block_manifest_sha256": ("FULL104_SUBSTRATE", "sha256"),
            "observation_state_sha256": ("OPERATOR_ADDRESS_OBSERVATION_STATE", "sha256"),
            "recovery_provenance": ("ADDRESS_REGISTRY", "recovery_provenance"),
            "informative_path": ("ADDRESS_REGISTRY", "informative_path"),
            "ordering_invariant": ("ADDRESS_REGISTRY", "ordering_invariant"),
            "identifier_invariant": ("ADDRESS_REGISTRY", "identifier_invariant"),
        },
        "field_from_top": ["authority_id", "training_authorized"],
    }
}


def _adapt(class_name, payload):
    """Apply a declared document adapter; return (kwargs, provenance) or (None, None)."""
    spec = DOCUMENT_ADAPTERS.get(class_name)
    if not spec:
        return None, None
    kwargs = {}
    for field, (block, key) in spec["field_from_block"].items():
        if block not in payload or key not in payload[block]:
            return None, None
        kwargs[field] = payload[block][key]
    for field in spec["field_from_top"]:
        if field not in payload:
            return None, None
        kwargs[field] = payload[field]
    return kwargs, spec


def _git_show(rev, path):
    proc = subprocess.run(
        ["git", "show", rev + ":" + path], cwd=str(ROOT), capture_output=True
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except Exception:
        return None


def _load_index(index_path):
    return json.loads(pathlib.Path(index_path).read_text(encoding="utf-8"))


def _resolve_class(class_name, classes):
    meta = classes.get(class_name)
    if not meta:
        return None, None
    module = importlib.import_module(meta["module"])
    return getattr(module, class_name, None), meta


def _recompute(cls, payload):
    """Reconstruct the dataclass from an artifact payload and digest it."""
    if cls is None or not dataclasses.is_dataclass(cls):
        return {"recomputed": None, "note": "defining class not a dataclass"}
    fields = [f.name for f in dataclasses.fields(cls)]
    missing = [f for f in fields if f not in payload]
    route = "DIRECT_INSTANCE_SERIALIZATION"
    if missing:
        kwargs, spec = _adapt(cls.__name__, payload)
        if kwargs is None:
            return {
                "recomputed": None,
                "route": "NONE",
                "note": "artifact missing declared fields and no declared adapter: "
                + ",".join(missing),
            }
        route = "EXTERNAL_DOCUMENT_ADAPTER"
    else:
        kwargs = dict((f, payload[f]) for f in fields)
        spec = None
    try:
        obj = cls(**kwargs)
        obj.validate()
        digest = obj.canonical_digest()
    except Exception as exc:  # noqa: BLE001 - the failure text is the finding
        return {"recomputed": None, "route": route, "note": "own-class validate() FAILED: %s" % exc}
    out = {
        "recomputed": digest,
        "route": route,
        "note": "own-class validate() PASSED and canonical_digest recomputed via "
        + route,
    }
    if spec:
        declared = payload.get(spec["declared_digest_field"])
        out["document_declared_digest"] = declared
        out["adapter_digest_agrees_with_document"] = declared == digest
        out["caveat"] = (
            "the role-to-field mapping lives in adapter code outside the artifact; "
            "this artifact's bytes are NOT its own canonical digest"
        )
    return out


def main():
    rev = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    index_path = sys.argv[2]
    out_path = pathlib.Path(sys.argv[3])

    graph = build_closure_graph()
    classes = _class_schema_map()
    index = _load_index(index_path)
    schema_to_paths = index["schema_to_paths"]

    substrate_row = None
    for row in graph["roots"]:
        if row["root"] == "full104_substrate_sha256":
            substrate_row = row
    if substrate_row is None:
        raise SystemExit("substrate root not found in closure graph")

    consumers = []
    for binding in substrate_row["downstream_equality_bindings"]:
        param = binding["consumer_param"]
        attr = binding["consumer_attribute"]
        # find the class for this consumer parameter
        class_name = None
        for row in graph["roots"]:
            if row["closure_parameter"] == param and row["isinstance_class"]:
                class_name = row["isinstance_class"]
        if class_name is None:
            class_name = DUCK_TYPED_DEFINING_CLASS.get(param)
        cls, meta = _resolve_class(class_name, classes) if class_name else (None, None)
        schema = meta["schema"] if meta else None
        paths = schema_to_paths.get(schema, []) if schema else []

        artifacts = []
        for path in paths:
            payload = _git_show(rev, path)
            if not isinstance(payload, dict):
                continue
            value = payload.get(attr)
            value_route = "TOP_LEVEL_FIELD"
            if value is None and cls is not None:
                adapted, _spec = _adapt(cls.__name__, payload)
                if adapted and attr in adapted:
                    value = adapted[attr]
                    value_route = "EXTERNAL_DOCUMENT_ADAPTER"
            if value == AUTHENTIC_SUBSTRATE:
                carries = (
                    "CARRIES_AUTHENTIC_SUBSTRATE"
                    if value_route == "TOP_LEVEL_FIELD"
                    else "CARRIES_AUTHENTIC_SUBSTRATE_VIA_DOCUMENT_ADAPTER"
                )
            elif value == KNOWN_DECOY:
                carries = "CARRIES_KNOWN_DECOY__REJECT"
            elif value is None:
                carries = "ATTRIBUTE_ABSENT"
            else:
                carries = "CARRIES_DIFFERENT_VALUE"
            artifacts.append(
                {
                    "path": path,
                    "closure_read_attribute": attr,
                    "attribute_resolution_route": value_route,
                    "observed_value": value,
                    "substrate_binding": carries,
                    "own_class_recompute": _recompute(cls, payload),
                    "declared_digest_fields": dict(
                        (k, v)
                        for k, v in payload.items()
                        if isinstance(v, str)
                        and k.endswith("sha256")
                        and k.startswith("authority")
                    ),
                }
            )

        if not artifacts:
            outcome = "NO_COMMITTED_ARTIFACT"
            blocking = True
        elif any(a["substrate_binding"] == "CARRIES_KNOWN_DECOY__REJECT" for a in artifacts):
            outcome = "DECOY_BINDING_PRESENT"
            blocking = True
        elif any(a["substrate_binding"] == "CARRIES_AUTHENTIC_SUBSTRATE" for a in artifacts):
            outcome = "ARTIFACT_CARRIES_AUTHENTIC_SUBSTRATE"
            blocking = False
        elif any(
            a["substrate_binding"] == "CARRIES_AUTHENTIC_SUBSTRATE_VIA_DOCUMENT_ADAPTER"
            for a in artifacts
        ):
            outcome = "CARRIES_AUTHENTIC_SUBSTRATE_VIA_DOCUMENT_ADAPTER"
            blocking = False
        else:
            outcome = "ARTIFACT_PRESENT_BUT_DOES_NOT_CARRY_SUBSTRATE"
            blocking = True

        consumers.append(
            {
                "consumer_parameter": param,
                "closure_read_attribute": attr,
                "attribute_access": binding["access"],
                "closure_line": binding["line"],
                "closure_failure_message": binding["message"],
                "defining_class": class_name,
                "defining_module": meta["module"] if meta else None,
                "class_enforcement": (
                    "ISINSTANCE_ENFORCED"
                    if any(
                        r["closure_parameter"] == param
                        and r["enforcement"] == "ISINSTANCE_ENFORCED"
                        for r in graph["roots"]
                    )
                    else "DUCK_TYPED_NO_CLASS_CHECK"
                ),
                "schema_searched": schema,
                "committed_candidates_found": len(artifacts),
                "artifacts": artifacts,
                "outcome": outcome,
                "blocks_substrate_root": blocking,
            }
        )

    satisfied = [c for c in consumers if not c["blocks_substrate_root"]]
    report = {
        "schema": "JEPA_LANEB_V29_SUBSTRATE_CONSUMER_BINDING_V1",
        "revision": subprocess.run(
            ["git", "rev-parse", rev], cwd=str(ROOT), capture_output=True, text=True
        ).stdout.strip(),
        "authentic_substrate_sha256": AUTHENTIC_SUBSTRATE,
        "known_decoy_sha256": KNOWN_DECOY,
        "closure_enforced_consumer_count": len(consumers),
        "consumers_with_authentic_binding": len(satisfied),
        "consumers_blocking": len(consumers) - len(satisfied),
        "substrate_root_closed": len(consumers) == len(satisfied) and len(consumers) > 0,
        "consumers": consumers,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote " + str(out_path))
    print(
        "consumers=%d authentic=%d blocking=%d closed=%s"
        % (
            len(consumers),
            len(satisfied),
            len(consumers) - len(satisfied),
            report["substrate_root_closed"],
        )
    )
    for c in consumers:
        print(
            "  %-34s %-38s %-42s %s"
            % (
                c["consumer_parameter"],
                c["closure_read_attribute"],
                str(c["defining_class"]),
                c["outcome"],
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
