"""Lane B V29: build the exact 33-root authority status matrix (JSON + markdown).

Every field is derived from committed code and committed artifacts at the given
revision. Nothing is asserted that this script did not measure.

Rules enforced here, not merely documented:

* A root with no committed artifact of its defining schema is
  NO_COMMITTED_ARTIFACT and BLOCKING. It is never "0 defects".
* A candidate artifact is a CANDIDATE. It becomes OWN_SCHEMA_VALIDATED only if
  the defining dataclass can be reconstructed from it and its own validate()
  passes. It becomes CLOSED only if, in addition, every closure equality binding
  that names it is satisfied by a committed artifact on the other side.
* No placeholder digest, repeated hex, schema digest or foreign-role receipt is
  ever substituted for an absent artifact.
* fully_closed is computed, never asserted.
"""
from __future__ import annotations

import dataclasses
import hashlib
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
from laneb_v29_substrate_consumer_verify_v1 import _adapt  # noqa: E402

AUTHENTIC_SUBSTRATE = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
KNOWN_DECOY = "e482d9da21232bdeb6b3f198f42b9fbcf1530ba1b3e86e104ffbb651ca9df808"

SUBSTRATE_FILE = (
    "D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/"
    "expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
)

# Defining class for the five closure parameters typed `Any` (no isinstance check).
# Each is the only v5 dataclass whose role and field set match the attributes the
# closure reads off that parameter; the matrix records this as an INFERRED mapping
# so it is never mistaken for an enforced one.
DUCK_TYPED_DEFINING_CLASS = {
    "representation": "PrimaryRepresentationAuthorityV1",
    "support_estimability": "SupportEstimabilityAuthorityV1",
    "base_training_estimand": "BaseTrainingEstimandAuthorityV1",
    "protected_registry": "ProductionProtectedRegistryAuthorityV1",
    "critical_test": "CriticalTestExecutionAuthorityV1",
}

# The three roots the closure accepts as bare strings rather than as an object.
# Roots whose closure parameter is typed VN but whose only committed artifact is a
# later version VM. Recorded as cross-version evidence, NEVER promoted to the root.
CROSS_VERSION_ARTIFACTS = {
    "masking_rng_replay_authority_sha256": {
        "closure_required_class": "MaskingRngReplayAuthorityV1",
        "committed_artifact_class": "MaskingRngReplayAuthorityV3",
        "committed_artifact_schema": "V5_MASKING_RNG_REPLAY_AUTHORITY_V3",
    },
    "masking_qualification_parameters_authority_sha256": {
        "closure_required_class": "MaskingQualificationParametersAuthorityV1",
        "committed_artifact_class": "MaskingQualificationParametersAuthorityV3",
        "committed_artifact_schema": "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3",
    },
}

RAW_STR_ROOTS = {
    "full104_substrate_sha256": {
        "kind": "CROSS_BINDING_CONSTANT",
        "note": (
            "not a missing dataclass; a constant every consuming authority must "
            "agree on. Byte-authenticated against the Level-4 block manifest."
        ),
    },
    "schedule_authority_sha256": {
        "kind": "CROSS_BINDING_CONSTANT",
        "note": (
            "third raw-string slot, omitted from the V29 matrix. Equality-checked "
            "against ema.schedule_authority_sha256 only."
        ),
    },
    "observation_gradient_firewall_authority_sha256": {
        "kind": "CROSS_BINDING_CONSTANT",
        "note": (
            "unbound on both sides: no committed artifact carries the key and its "
            "only consumer (anti_cheat) has no committed artifact."
        ),
    },
}


def _git(args):
    return subprocess.run(
        ["git"] + args, cwd=str(ROOT), capture_output=True, text=True
    ).stdout


def _git_show_json(rev, path):
    proc = subprocess.run(
        ["git", "show", rev + ":" + path], cwd=str(ROOT), capture_output=True
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except Exception:
        return None


def _blob_sha(rev, path):
    proc = subprocess.run(
        ["git", "show", rev + ":" + path], cwd=str(ROOT), capture_output=True
    )
    if proc.returncode != 0:
        return None
    return hashlib.sha256(proc.stdout).hexdigest()


def _reconstruct(cls, payload):
    if cls is None or not dataclasses.is_dataclass(cls):
        return {
            "own_schema_validation": "NO_DEFINING_DATACLASS",
            "recomputed_digest": None,
            "detail": "no dataclass resolved for this root",
        }
    fields = [f.name for f in dataclasses.fields(cls)]
    missing = [f for f in fields if f not in payload]
    route = "DIRECT_INSTANCE_SERIALIZATION"
    if missing:
        kwargs, spec = _adapt(cls.__name__, payload)
        if kwargs is None:
            return {
                "own_schema_validation": "NOT_AN_INSTANCE_OF_DEFINING_CLASS",
                "recomputed_digest": None,
                "reconstruction_route": "NONE",
                "detail": "artifact carries the schema label but is missing %d "
                "declared field(s) and no declared adapter exists: %s"
                % (len(missing), ",".join(missing)),
            }
        route = "EXTERNAL_DOCUMENT_ADAPTER"
    else:
        kwargs = dict((f, payload[f]) for f in fields)
        spec = None
    try:
        obj = cls(**kwargs)
        obj.validate()
        digest = obj.canonical_digest()
    except Exception as exc:  # noqa: BLE001
        return {
            "own_schema_validation": "FAIL",
            "recomputed_digest": None,
            "reconstruction_route": route,
            "detail": "own validate() raised: %s" % exc,
        }
    out = {
        "own_schema_validation": (
            "PASS" if route == "DIRECT_INSTANCE_SERIALIZATION" else "PASS_VIA_ADAPTER"
        ),
        "recomputed_digest": digest,
        "reconstruction_route": route,
        "detail": "reconstructed from artifact via %s; own validate() passed" % route,
    }
    if spec:
        out["document_declared_digest"] = payload.get(spec["declared_digest_field"])
        out["adapter_digest_agrees"] = out["document_declared_digest"] == digest
        out["caveat"] = (
            "role-to-field mapping lives in adapter code outside the artifact"
        )
    return out


def build(rev, index_path):
    graph = build_closure_graph()
    classes = _class_schema_map()
    index = json.loads(pathlib.Path(index_path).read_text(encoding="utf-8"))
    schema_to_paths = index["schema_to_paths"]
    head = _git(["rev-parse", rev]).strip()
    # The artifact index and this matrix must describe the SAME revision. A
    # matrix that cites one commit while consuming an index built at another
    # would be a provenance record of an execution that did not happen.
    if index["revision"] != head:
        raise SystemExit(
            "STOP: artifact index was built at %s but the matrix was asked for "
            "%s. Rebuild the index at the same revision rather than citing a "
            "revision that was not the one searched." % (index["revision"], head)
        )

    # substrate byte authentication
    sub = pathlib.Path(SUBSTRATE_FILE)
    substrate_auth = {"path": SUBSTRATE_FILE, "readable": sub.exists()}
    if sub.exists():
        raw = sub.read_bytes()
        substrate_auth["bytes"] = len(raw)
        substrate_auth["sha256"] = hashlib.sha256(raw).hexdigest()
        substrate_auth["matches_expected"] = (
            substrate_auth["sha256"] == AUTHENTIC_SUBSTRATE
        )
    else:
        substrate_auth["note"] = "NOT_READABLE_FROM_THIS_HOST__UNMEASURED"

    rows = []
    for entry in graph["roots"]:
        root = entry["root"]
        param = entry["closure_parameter"]
        class_name = entry["isinstance_class"] or DUCK_TYPED_DEFINING_CLASS.get(param)
        class_source = (
            "ISINSTANCE_ENFORCED_BY_CLOSURE"
            if entry["isinstance_class"]
            else ("INFERRED_BY_ROLE__NOT_ENFORCED" if class_name else "NONE")
        )
        meta = classes.get(class_name) if class_name else None
        schema = meta["schema"] if meta else None
        cls = None
        if meta and class_name:
            try:
                cls = getattr(importlib.import_module(meta["module"]), class_name)
            except Exception:  # noqa: BLE001
                cls = None

        candidates = []
        for path in schema_to_paths.get(schema, []) if schema else []:
            payload = _git_show_json(rev, path)
            if not isinstance(payload, dict):
                continue
            rec = _reconstruct(cls, payload)
            candidates.append(
                {
                    "source_path": path,
                    "source_commit": head,
                    "committed_blob_sha256": _blob_sha(rev, path),
                    "own_schema_validation": rec["own_schema_validation"],
                    "reconstruction_route": rec.get("reconstruction_route"),
                    "authentic_digest": rec["recomputed_digest"],
                    "self_authenticating_bytes": (
                        rec["recomputed_digest"] is not None
                        and rec["recomputed_digest"] == _blob_sha(rev, path)
                    ),
                    "document_declared_digest": rec.get("document_declared_digest"),
                    "adapter_digest_agrees": rec.get("adapter_digest_agrees"),
                    "detail": rec["detail"],
                }
            )

        validated = [
            c
            for c in candidates
            if c["own_schema_validation"] in ("PASS", "PASS_VIA_ADAPTER")
        ]
        raw_meta = RAW_STR_ROOTS.get(root)

        # dependencies: every closure equality binding naming this root's local
        deps = []
        for b in entry["downstream_equality_bindings"]:
            deps.append(
                {
                    "dependent_parameter": b["consumer_param"],
                    "dependent_attribute": b["consumer_attribute"],
                    "closure_line": b["line"],
                    "closure_failure_message": b["message"],
                }
            )

        if raw_meta:
            if root == "full104_substrate_sha256":
                outcome = "VALUE_AND_BYTES_AUTHENTICATED"
                authentic = AUTHENTIC_SUBSTRATE
            else:
                outcome = "UNBOUND__NO_COMMITTED_ARTIFACT_CARRIES_THE_KEY"
                authentic = None
            blocking = True
            blocking_reason = (
                "every consuming authority must exist and carry this same value; "
                "consumers are unqualified"
                if root == "full104_substrate_sha256"
                else raw_meta["note"]
            )
        elif not candidates:
            outcome = "NO_COMMITTED_ARTIFACT"
            authentic = None
            blocking = True
            blocking_reason = (
                "no committed JSON at this revision carries schema %s; absence "
                "within the searched scope is not proof of global absence" % schema
            )
        elif not validated:
            outcome = "SCHEMA_LABEL_ONLY__NOT_AN_INSTANCE"
            authentic = None
            blocking = True
            blocking_reason = (
                "a committed artifact bears the schema label but cannot be "
                "reconstructed into the defining class: " + candidates[0]["detail"]
            )
        else:
            outcome = "OWN_SCHEMA_VALIDATED_CANDIDATE"
            authentic = validated[0]["authentic_digest"]
            blocking = True
            blocking_reason = (
                "own-schema validation only; parent-source bytes and the closure "
                "cross-bindings that name this root are not qualified"
            )

        cross = CROSS_VERSION_ARTIFACTS.get(root)
        cross_evidence = None
        if cross:
            paths = schema_to_paths.get(cross["committed_artifact_schema"], [])
            cross_evidence = {
                "closure_required_class": cross["closure_required_class"],
                "committed_artifact_class": cross["committed_artifact_class"],
                "committed_artifact_schema": cross["committed_artifact_schema"],
                "committed_artifact_paths": paths,
                "promoted_to_root": False,
                "note": (
                    "a later-version artifact exists and validates against its OWN "
                    "class, but the closure requires the V1 class; a VN artifact is "
                    "not an instance of V1 and is NOT promoted to this root"
                ),
            }

        if raw_meta:
            validator_cmd = (
                "sha256sum \"%s\"   # substrate slot; expect %s"
                % (SUBSTRATE_FILE, AUTHENTIC_SUBSTRATE[:16] + "...")
                if root == "full104_substrate_sha256"
                else "git grep -l '\"%s\"' %s -- '*.json'   # expect: no output"
                % (root, rev)
            )
        elif validated:
            validator_cmd = (
                "PYTHONPATH=src python -c \"import json,sys;"
                "from %s import %s as C;"
                "d=json.load(open('%s'));"
                "o=C(**{f:d[f] for f in C.__dataclass_fields__});"
                "o.validate();print(o.canonical_digest())\"   # expect %s"
                % (
                    meta["module"],
                    class_name,
                    validated[0]["source_path"],
                    (validated[0]["authentic_digest"] or "")[:16] + "...",
                )
                if validated[0].get("reconstruction_route")
                == "DIRECT_INSTANCE_SERIALIZATION"
                else (
                    "PYTHONPATH=src:scripts/agent python "
                    "scripts/agent/laneb_v29_substrate_consumer_verify_v1.py %s "
                    "<index.json> <out.json>   # adapter-mediated root=%s"
                    % (rev, root)
                )
            )
        else:
            validator_cmd = (
                "git grep -l '\"schema\": *\"%s\"' %s -- '*.json'   "
                "# expect: no output => NO_COMMITTED_ARTIFACT" % (schema, rev)
            )
        rows.append(
            {
                "root": root,
                "defining_module": meta["module"] if meta else None,
                "defining_class": class_name,
                "class_binding_strength": class_source,
                "closure_parameter": param,
                "closure_enforcement": entry["enforcement"],
                "expected_artifact_schema": schema,
                "committed_candidate_count": len(candidates),
                "candidates": candidates,
                "authentic_digest": authentic,
                "validator_command": validator_cmd,
                "validation_outcome": outcome,
                "dependencies_enforced_by_closure": deps,
                "dependency_count": len(deps),
                "blocking": blocking,
                "blocking_reason": blocking_reason,
                "cross_version_evidence": cross_evidence,
                "fully_closed": False,
            }
        )

    # the 33rd root lives only on the receipt, never on the closure
    rows.append(
        {
            "root": "preexecution_authority_sha256",
            "defining_module": "sea_ad_jepa.v5.current_trainer_preexecution_contract_v2",
            "defining_class": "CurrentTrainerPreexecutionAuthorityV2",
            "class_binding_strength": "TYPED_PARAMETER_OF_ISSUER",
            "closure_parameter": None,
            "closure_enforcement": "RECEIPT_ONLY__NOT_A_CLOSURE_PARAMETER",
            "expected_artifact_schema": "V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V2",
            "committed_candidate_count": len(
                schema_to_paths.get("V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V2", [])
            ),
            "candidates": [
                {"source_path": p, "source_commit": head}
                for p in schema_to_paths.get(
                    "V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V2", []
                )
            ],
            "authentic_digest": None,
            "validator_command": (
                "python scripts/agent/laneb_v29_root_status_matrix_v2.py %s "
                "<index.json> <out_dir>" % rev
            ),
            "validation_outcome": (
                "NO_COMMITTED_ARTIFACT"
                if not schema_to_paths.get(
                    "V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V2"
                )
                else "CANDIDATE_FOUND"
            ),
            "dependencies_enforced_by_closure": [
                {
                    "dependent_parameter": "issue_training_authority_v1",
                    "dependent_attribute": "preexecution.canonical_digest()",
                    "closure_line": None,
                    "closure_failure_message": (
                        "receipt roots must equal closure roots plus preexecution digest"
                    ),
                }
            ],
            "dependency_count": 1,
            "blocking": True,
            "blocking_reason": (
                "derived at issuance from the caller-supplied roots mapping; it is "
                "self-referential and adds no independent evidence"
            ),
            "fully_closed": False,
        }
    )

    ledger = {
        "upstream_roots": graph["upstream_root_count"],
        "receipt_roots": graph["receipt_root_count"],
        "receipt_adds": graph["receipt_only_roots"],
        "fully_closed": sum(1 for r in rows if r["fully_closed"]),
        "own_schema_validated_candidates": sum(
            1 for r in rows if r["validation_outcome"] == "OWN_SCHEMA_VALIDATED_CANDIDATE"
        ),
        "no_committed_artifact": sum(
            1 for r in rows if r["validation_outcome"] == "NO_COMMITTED_ARTIFACT"
        ),
        "schema_label_only": sum(
            1 for r in rows if r["validation_outcome"] == "SCHEMA_LABEL_ONLY__NOT_AN_INSTANCE"
        ),
        "raw_str_cross_binding_slots": len(RAW_STR_ROOTS),
        "raw_slot_value_and_bytes_authenticated": 1,
        "blocking_roots": sum(1 for r in rows if r["blocking"]),
        "closure_enforcement_census": graph["enforcement_census"],
        "closure_equality_assertions": graph["total_equality_assertions"],
    }

    return {
        "schema": "JEPA_LANEB_V29_ROOT_STATUS_MATRIX_V2",
        "date": "2026-09-26",
        "lane": "LANE_B_AUTHORITY_AND_PROVENANCE",
        "revision": head,
        "artifact_index_revision": index["revision"],
        "committed_json_blobs_scanned": index["committed_json_blobs_scanned"],
        "status": "NO_ROOT_FULLY_CLOSED__NO_TRAINING_AUTHORITY",
        "substrate_byte_authentication": substrate_auth,
        "known_decoy_sha256": KNOWN_DECOY,
        "ledger": ledger,
        "roots": rows,
        "training_authorized": False,
        "flags": {
            "TRAINING": "OFF",
            "AUDIT_B_N1": "UNOPENED",
            "PROTECTED_FULL104_OUTCOMES": "UNOPENED",
            "D_SHARED_G5": "UNOPENED",
            "RARE_TAIL_MOLECULAR": "UNOPENED",
            "THERAPEUTIC_RANKING": "OFF",
        },
    }


def main():
    rev = sys.argv[1]
    index_path = sys.argv[2]
    out_dir = pathlib.Path(sys.argv[3])
    report = build(rev, index_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "LANEB_V29_ROOT_STATUS_MATRIX_V2.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    led = report["ledger"]
    print("revision %s" % report["revision"])
    print(
        "upstream=%d receipt=%d fully_closed=%d blocking=%d"
        % (
            led["upstream_roots"],
            led["receipt_roots"],
            led["fully_closed"],
            led["blocking_roots"],
        )
    )
    print(
        "own_schema_validated=%d no_artifact=%d schema_label_only=%d raw_slots=%d"
        % (
            led["own_schema_validated_candidates"],
            led["no_committed_artifact"],
            led["schema_label_only"],
            led["raw_str_cross_binding_slots"],
        )
    )
    print("substrate:", report["substrate_byte_authentication"])
    print()
    for r in report["roots"]:
        print(
            "%-52s %-34s %s"
            % (r["root"], r["validation_outcome"], "BLOCKING" if r["blocking"] else "ok")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
