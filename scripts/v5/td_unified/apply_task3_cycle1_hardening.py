from __future__ import annotations

from pathlib import Path

REGISTRY = Path("scripts/v5/td_unified/registry_v1.py")
TESTS = Path("tests/v5/td_unified/test_registry_v1.py")
SELF1 = Path("tests/v5/td_unified/test_registry_v1_self_audit1.py")
SELF2 = Path("tests/v5/td_unified/test_registry_v1_self_audit2.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


text = REGISTRY.read_text(encoding="utf-8")

text = replace_once(
    text,
    "    if dependency_verifier is None:\n        return []\n    blockers: list[str] = []\n",
    "    if dependency_verifier is None:\n        return [\"authenticated dependency verifier required; digest strings are not authority\"]\n    blockers: list[str] = []\n",
    "require dependency verifier",
)

anchor = "    return obj\n\n\n@dataclass(frozen=True)\nclass RegistryUnit:"
helper = '''    return obj\n\n\ndef _actor_id(obj: Mapping[str, object], *, label: str) -> str:\n    actor_id = obj.get("actor_id")\n    if type(actor_id) is not str or not actor_id.strip():\n        raise RegistryError(f"{label} must declare a non-empty actor_id")\n    return actor_id\n\n\ndef _validate_requirement_evidence(requirement_class: str, obj: Mapping[str, object], *, label: str) -> None:\n    if obj.get("requirement_class") != requirement_class:\n        raise RegistryError(f"{label} evidence requirement_class mismatch")\n    if requirement_class == "PROCESS_ISOLATION":\n        required_true = (\n            "producer_process_isolated",\n            "harness_drives_finalization",\n            "reader_fit_values_out_of_process",\n            "protected_partitions_physically_absent",\n        )\n        missing = [name for name in required_true if obj.get(name) is not True]\n        if missing:\n            raise RegistryError(\n                f"PROCESS_ISOLATION evidence incomplete for {label}: " + ",".join(missing)\n            )\n    elif requirement_class == "CROSS_PROCESS_LEDGER_CUSTODY":\n        if obj.get("persistent_ledger") is not True:\n            raise RegistryError(f"{label} ledger persistence evidence missing")\n        if obj.get("signing_key_out_of_process") is not True:\n            raise RegistryError(f"{label} signing-key custody evidence missing")\n        if obj.get("key_custodian") != "HARNESS":\n            raise RegistryError(f"{label} key custody must be HARNESS")\n\n\n@dataclass(frozen=True)\nclass RegistryUnit:'''
text = replace_once(text, anchor, helper, "insert actor/evidence validators")

old_human = '''        if p.external_state == "SATISFIED" and p.requirement_class != "UNIT":\n            err = _authority_receipt_blocker(\n                p.evidence_receipt_sha, authority_object_resolver,\n                expected_role="PREREQUISITE_EVIDENCE", label=p.prerequisite_id,\n            )\n            if err:\n                blockers.append(err)\n'''
new_human = '''        if p.external_state == "SATISFIED" and p.requirement_class != "UNIT":\n            try:\n                evidence_obj = _resolve_object(\n                    p.evidence_receipt_sha, authority_object_resolver,\n                    expected_role="PREREQUISITE_EVIDENCE", label=p.prerequisite_id,\n                )\n                _validate_requirement_evidence(\n                    p.requirement_class, evidence_obj, label=p.prerequisite_id\n                )\n            except RegistryError as exc:\n                blockers.append(str(exc))\n'''
text = replace_once(text, old_human, new_human, "validate R1/R4 evidence content")

old_sig = '''    reviewer_identity: str | None,\n    prerequisite_evidence_verifier: Callable[[str], bool] | None = None,\n    authority_object_resolver: AuthorityObjectResolver | None = None,\n) -> TDQualificationRegistry:\n'''
new_sig = '''    reviewer_identity: str | None,\n    prerequisite_evidence_verifier: Callable[[str], bool] | None = None,\n    authority_object_resolver: AuthorityObjectResolver | None = None,\n    dependency_verifier: Callable[[str], bool] | None = None,\n    verification_cache: MutableMapping[object, object] | None = None,\n) -> TDQualificationRegistry:\n'''
text = replace_once(text, old_sig, new_sig, "extend promotion dependency authentication")

old_actor = '''    _resolve_object(\n        controller_identity, authority_object_resolver,\n        expected_role="QUALIFICATION_CONTROLLER", label="qualification controller",\n    )\n    if reviewer_identity is not None:\n        if reviewer_identity in {controller_identity, unit.producer_code_sha, unit.executor_code_sha}:\n            raise RegistryError("independent reviewer must differ from controller/producer/executor")\n        _resolve_object(\n            reviewer_identity, authority_object_resolver,\n            expected_role="INDEPENDENT_REVIEWER", label="independent reviewer",\n        )\n'''
new_actor = '''    controller_obj = _resolve_object(\n        controller_identity, authority_object_resolver,\n        expected_role="QUALIFICATION_CONTROLLER", label="qualification controller",\n    )\n    controller_actor = _actor_id(controller_obj, label="qualification controller")\n    if reviewer_identity is not None:\n        if reviewer_identity in {controller_identity, unit.producer_code_sha, unit.executor_code_sha}:\n            raise RegistryError("independent reviewer must differ from controller/producer/executor")\n        reviewer_obj = _resolve_object(\n            reviewer_identity, authority_object_resolver,\n            expected_role="INDEPENDENT_REVIEWER", label="independent reviewer",\n        )\n        reviewer_actor = _actor_id(reviewer_obj, label="independent reviewer")\n        if reviewer_actor == controller_actor:\n            raise RegistryError("independent reviewer actor must differ from qualification controller actor")\n'''
text = replace_once(text, old_actor, new_actor, "enforce actor-level independence")

old_ready = '''        result = derive_real_reference_ready(\n            unit_id, registry, authority_object_resolver=authority_object_resolver,\n        )\n'''
new_ready = '''        result = derive_real_reference_ready(\n            unit_id, registry,\n            dependency_verifier=dependency_verifier,\n            authority_object_resolver=authority_object_resolver,\n            verification_cache=verification_cache,\n        )\n'''
text = replace_once(text, old_ready, new_ready, "propagate dependency verifier into promotion")

old_human_stage = '''        blockers = _human_execution_blockers(unit_id, registry, authority_object_resolver)\n        if blockers:\n            raise RegistryError("HUMAN_EXECUTABLE prerequisites unresolved: " + "; ".join(blockers))\n    prereqs = tuple(\n'''
new_human_stage = '''        blockers = _human_execution_blockers(unit_id, registry, authority_object_resolver)\n        if blockers:\n            raise RegistryError("HUMAN_EXECUTABLE prerequisites unresolved: " + "; ".join(blockers))\n        prior_stage_receipts = tuple(\n            receipt for receipt in registry.promotions\n            if receipt.unit_id == unit_id and receipt.destination_stage is unit.qualification_stage\n        )\n        if not prior_stage_receipts:\n            raise RegistryError("current advanced stage lacks prior promotion history provenance")\n        dependency_blockers = _verify_unit_dependencies(unit, dependency_verifier, verification_cache)\n        if dependency_blockers:\n            raise RegistryError("HUMAN_EXECUTABLE dependency authentication failed: " + "; ".join(dependency_blockers))\n    prereqs = tuple(\n'''
text = replace_once(text, old_human_stage, new_human_stage, "require advanced-stage provenance")

REGISTRY.write_text(text, encoding="utf-8")


tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    'promoted=r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res)',
    'promoted=r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res,dependency_verifier=lambda _: True)',
    "positive REAL_REFERENCE_READY promotion verifier",
)
tests = replace_once(
    tests,
    'assert r.derive_real_reference_ready("G8",reg,verification_cache=cache).ready',
    'assert r.derive_real_reference_ready("G8",reg,dependency_verifier=lambda _: True,verification_cache=cache).ready',
    "positive cached readiness verifier",
)
TESTS.write_text(tests, encoding="utf-8")

self1 = SELF1.read_text(encoding="utf-8")
self1 = replace_once(
    self1,
    'result=r.derive_real_reference_ready("G8",registry(dep,target,p),authority_object_resolver=lambda sha:eobj if sha==esha else None)',
    'result=r.derive_real_reference_ready("G8",registry(dep,target,p),authority_object_resolver=lambda sha:eobj if sha==esha else None,dependency_verifier=lambda _: True)',
    "self-audit1 external positive dependency verifier",
)
SELF1.write_text(self1, encoding="utf-8")

self2 = SELF2.read_text(encoding="utf-8")
self2 = replace_once(
    self2,
    'assert r.derive_real_reference_ready("G8", reg2, authority_object_resolver=lambda sha: good if sha == good_sha else None).ready',
    'assert r.derive_real_reference_ready("G8", reg2, authority_object_resolver=lambda sha: good if sha == good_sha else None, dependency_verifier=lambda _: True).ready',
    "self-audit2 evidence positive dependency verifier",
)
self2 = replace_once(
    self2,
    '                              authority_object_resolver=resolver)\n    assert promoted.units_by_id()["G8"].qualification_stage is QualificationStage.REAL_REFERENCE_READY',
    '                              authority_object_resolver=resolver, dependency_verifier=lambda _: True)\n    assert promoted.units_by_id()["G8"].qualification_stage is QualificationStage.REAL_REFERENCE_READY',
    "self-audit2 promotion positive dependency verifier",
)
self2 = replace_once(
    self2,
    '                              authority_object_resolver={csha:cobj,rsha:robj,esha:eobj}.get)\n    receipt = promoted.promotions[0]',
    '                              authority_object_resolver={csha:cobj,rsha:robj,esha:eobj}.get, dependency_verifier=lambda _: True)\n    receipt = promoted.promotions[0]',
    "self-audit2 promotion receipt positive dependency verifier",
)
SELF2.write_text(self2, encoding="utf-8")

print("Applied Task 3 hostile cycle1 hardening")
