from __future__ import annotations

from pathlib import Path

REGISTRY = Path("scripts/v5/td_unified/registry_v1.py")
SELF1 = Path("tests/v5/td_unified/test_registry_v1_self_audit1.py")
SELF2 = Path("tests/v5/td_unified/test_registry_v1_self_audit2.py")


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected one match, found {n}")
    return text.replace(old, new, 1)


text = REGISTRY.read_text(encoding="utf-8")
anchor = '''    elif requirement_class == "CROSS_PROCESS_LEDGER_CUSTODY":
        if obj.get("persistent_ledger") is not True:
            raise RegistryError(f"{label} ledger persistence evidence missing")
        if obj.get("signing_key_out_of_process") is not True:
            raise RegistryError(f"{label} signing-key custody evidence missing")
        if obj.get("key_custodian") != "HARNESS":
            raise RegistryError(f"{label} key custody must be HARNESS")


@dataclass(frozen=True)
class RegistryUnit:
'''
replacement = '''    elif requirement_class == "CROSS_PROCESS_LEDGER_CUSTODY":
        if obj.get("persistent_ledger") is not True:
            raise RegistryError(f"{label} ledger persistence evidence missing")
        if obj.get("signing_key_out_of_process") is not True:
            raise RegistryError(f"{label} signing-key custody evidence missing")
        if obj.get("key_custodian") != "HARNESS":
            raise RegistryError(f"{label} key custody must be HARNESS")


def _validate_content_validation_receipt(
    prerequisite: "PrerequisiteRecord",
    resolver: AuthorityObjectResolver | None,
) -> None:
    receipt = _resolve_object(
        prerequisite.content_validation_receipt_sha or "",
        resolver,
        expected_role="CONTENT_VALIDATION_RECEIPT",
        label=prerequisite.prerequisite_id + " content",
    )
    expected_fields = {
        "object_role", "receipt_schema", "prerequisite_id", "content_identity_sha",
        "validator_identity_sha", "status",
    }
    if set(receipt) != expected_fields:
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt fields invalid")
    if receipt.get("receipt_schema") != "CONTENT_VALIDATION_RECEIPT_V1":
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt schema mismatch")
    if receipt.get("prerequisite_id") != prerequisite.prerequisite_id:
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt prerequisite mismatch")
    if receipt.get("content_identity_sha") != prerequisite.prerequisite_unit_sha:
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt identity mismatch")
    validator_sha = receipt.get("validator_identity_sha")
    _resolve_object(
        validator_sha if type(validator_sha) is str else "",
        resolver,
        expected_role="CONTENT_VALIDATOR",
        label=prerequisite.prerequisite_id + " content validator",
    )
    if receipt.get("status") != "QUALIFIED":
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt is not QUALIFIED")


@dataclass(frozen=True)
class RegistryUnit:
'''
text = once(text, anchor, replacement, "insert content validation receipt validator")

old_external = '''        if p.requirement_class != "UNIT" and p.external_state == "SATISFIED":
            err = _authority_receipt_blocker(
                p.evidence_receipt_sha, authority_object_resolver,
                expected_role="PREREQUISITE_EVIDENCE", label=p.prerequisite_id,
            )
            if err:
                pb.append(err)
'''
new_external = '''        if p.requirement_class != "UNIT" and p.external_state == "SATISFIED":
            try:
                evidence_obj = _resolve_object(
                    p.evidence_receipt_sha, authority_object_resolver,
                    expected_role="PREREQUISITE_EVIDENCE", label=p.prerequisite_id,
                )
                _validate_requirement_evidence(p.requirement_class, evidence_obj, label=p.prerequisite_id)
            except RegistryError as exc:
                pb.append(str(exc))
'''
text = once(text, old_external, new_external, "bind external evidence requirement class")

old_content = '''            else:
                err = _authority_receipt_blocker(
                    p.content_validation_receipt_sha, authority_object_resolver,
                    expected_role="CONTENT_VALIDATION_RECEIPT", label=p.prerequisite_id + " content",
                )
                if err:
                    pb.append(err)
'''
new_content = '''            else:
                try:
                    _validate_content_validation_receipt(p, authority_object_resolver)
                except RegistryError as exc:
                    pb.append(str(exc))
'''
text = once(text, old_content, new_content, "bind content validation receipt in readiness")

old_human_content = '''            else:
                err = _authority_receipt_blocker(
                    p.content_validation_receipt_sha, authority_object_resolver,
                    expected_role="CONTENT_VALIDATION_RECEIPT", label=p.prerequisite_id + " content",
                )
                if err:
                    blockers.append(err)
'''
new_human_content = '''            else:
                try:
                    _validate_content_validation_receipt(p, authority_object_resolver)
                except RegistryError as exc:
                    blockers.append(str(exc))
'''
text = once(text, old_human_content, new_human_content, "bind content validation receipt in human gate")
REGISTRY.write_text(text, encoding="utf-8")

for path in (SELF1, SELF2):
    t = path.read_text(encoding="utf-8")
    old = 'obj={"object_role":"PREREQUISITE_EVIDENCE","marker":marker}; return canonical_sha256(obj),obj'
    if old in t:
        t = t.replace(old, 'obj={"object_role":"PREREQUISITE_EVIDENCE","requirement_class":"EXTERNAL_CONTROL","marker":marker}; return canonical_sha256(obj),obj', 1)
    else:
        old2 = 'obj = {"object_role": role, "marker": marker}'
        if old2 in t:
            t = t.replace(old2, 'obj = {"object_role": role, "requirement_class": "EXTERNAL_CONTROL", "marker": marker}', 1)
        else:
            raise SystemExit(f"evidence helper pattern not found in {path}")
    path.write_text(t, encoding="utf-8")

print("Applied Task 3 hostile cycle4 hardening")
