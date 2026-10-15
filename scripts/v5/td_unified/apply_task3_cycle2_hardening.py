from __future__ import annotations

from pathlib import Path

REGISTRY = Path("scripts/v5/td_unified/registry_v1.py")
MAIN = Path("tests/v5/td_unified/test_registry_v1.py")
SELF1 = Path("tests/v5/td_unified/test_registry_v1_self_audit1.py")
SELF2 = Path("tests/v5/td_unified/test_registry_v1_self_audit2.py")


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected one match, found {n}")
    return text.replace(old, new, 1)


text = REGISTRY.read_text(encoding="utf-8")
text = once(text, "from dataclasses import dataclass, replace\n", "import hashlib\nfrom dataclasses import dataclass, replace\n", "import hashlib")
text = once(
    text,
    '_IDENTITY_40_FIELDS = ("producer_code_sha", "executor_code_sha")\n',
    '_IDENTITY_40_FIELDS = ("producer_code_sha", "executor_code_sha")\n'
    '_DEPENDENCY_ROLE_BY_FIELD = {\n'
    '    "access_policy_sha": "ACCESS_POLICY",\n'
    '    "producer_policy_sha": "PRODUCER_POLICY",\n'
    '    "executor_policy_sha": "EXECUTOR_POLICY",\n'
    '    "schema_sha": "UNIT_SCHEMA",\n'
    '    "metric_sha": "METRIC_DEFINITION",\n'
    '    "reference_producer_sha": "REFERENCE_PRODUCER",\n'
    '    "falsifier_sha": "FALSIFIER_CONTROL",\n'
    '}\n',
    "dependency role map",
)
old_verify = '''def _verify_unit_dependencies(
    unit: RegistryUnit,
    dependency_verifier: Callable[[str], bool] | None,
    cache: MutableMapping[object, object] | None,
) -> list[str]:
    if dependency_verifier is None:
        return ["authenticated dependency verifier required; digest strings are not authority"]
    blockers: list[str] = []
    unit_key = unit.canonical_sha256()
    for field in _IDENTITY_64_FIELDS + _IDENTITY_40_FIELDS:
        sha = getattr(unit, field)
        key = ("dependency", unit_key, field, sha)
        if cache is not None and key in cache:
            ok = bool(cache[key])
        else:
            try:
                ok = dependency_verifier(sha) is True
            except Exception:
                ok = False
            if cache is not None:
                cache[key] = ok
        if not ok:
            blockers.append(f"dependency verification failed: {field}")
    return blockers
'''
new_verify = '''def _verify_unit_dependencies(
    unit: RegistryUnit,
    dependency_verifier: Callable[[str], object] | None,
    cache: MutableMapping[object, object] | None,
) -> list[str]:
    # Historical name retained for API compatibility.  This is an object/byte
    # resolver, never a trusted boolean callback.
    if dependency_verifier is None:
        return ["authenticated dependency object/byte resolver required; digest strings are not authority"]
    blockers: list[str] = []
    unit_key = unit.canonical_sha256()
    for field in _IDENTITY_64_FIELDS + _IDENTITY_40_FIELDS:
        sha = getattr(unit, field)
        key = ("dependency-object-v1", unit_key, field, sha)
        if cache is not None and key in cache:
            ok = bool(cache[key])
        else:
            ok = False
            try:
                obj = dependency_verifier(sha)
                if field in _IDENTITY_40_FIELDS:
                    if type(obj) is not bytes:
                        raise RegistryError(f"dependency {field} requires actual code bytes")
                    prefix = f"blob {len(obj)}\\0".encode("ascii")
                    observed = hashlib.sha1(prefix + obj).hexdigest()
                    if observed != sha:
                        raise RegistryError(f"dependency {field} Git blob identity mismatch")
                else:
                    if not isinstance(obj, Mapping):
                        raise RegistryError(f"dependency {field} requires actual canonical object")
                    observed = canonical_sha256(dict(obj))
                    if observed != sha:
                        raise RegistryError(f"dependency {field} canonical identity mismatch")
                    if field == "manifest_sha":
                        if obj.get("schema") != "TD_EXECUTION_MANIFEST_V1":
                            raise RegistryError("dependency manifest_sha schema mismatch")
                        bound_access = obj.get("access_policy_sha")
                        if bound_access is not None and bound_access != unit.access_policy_sha:
                            raise RegistryError("dependency manifest/access-policy binding mismatch")
                    else:
                        expected_role = _DEPENDENCY_ROLE_BY_FIELD.get(field)
                        if expected_role is None or obj.get("object_role") != expected_role:
                            raise RegistryError(f"dependency {field} role mismatch; expected {expected_role}")
                        if field == "access_policy_sha":
                            population = obj.get("population_authority")
                            if population is not None and population != unit.population_authority:
                                raise RegistryError("dependency access policy population authority mismatch")
                ok = True
            except Exception:
                ok = False
            if cache is not None:
                cache[key] = ok
        if not ok:
            blockers.append(f"dependency object/byte verification failed: {field}")
    return blockers
'''
text = once(text, old_verify, new_verify, "replace dependency verifier")
text = text.replace('dependency_verifier: Callable[[str], bool] | None', 'dependency_verifier: Callable[[str], object] | None')

marker = '\ndef promote_unit(\n'
provenance = '''
def _validate_current_stage_promotion_provenance(
    unit: RegistryUnit,
    registry: TDQualificationRegistry,
    resolver: AuthorityObjectResolver | None,
) -> PromotionReceipt:
    candidates = [
        receipt for receipt in registry.promotions
        if receipt.unit_id == unit.unit_id and receipt.destination_stage is unit.qualification_stage
    ]
    if len(candidates) != 1:
        raise RegistryError("current advanced stage requires exactly one verifiable prior promotion history receipt")
    receipt = candidates[0]
    if _STAGE_INDEX[receipt.destination_stage] != _STAGE_INDEX[receipt.source_stage] + 1:
        raise RegistryError("promotion receipt chain is not one canonical stage")
    if receipt.manifest_sha != unit.manifest_sha or receipt.access_policy_sha != unit.access_policy_sha:
        raise RegistryError("promotion receipt manifest/access provenance mismatch")
    predecessor = replace(unit, qualification_stage=receipt.source_stage)
    if receipt.unit_identity_sha != predecessor.canonical_sha256():
        raise RegistryError("promotion receipt unit identity does not match exact predecessor")
    if resolver is None:
        raise RegistryError("promotion provenance requires exact pre-registry resolver")
    try:
        snapshot = resolver(receipt.pre_registry_sha)
    except Exception as exc:
        raise RegistryError("promotion pre_registry authority resolution failed") from exc
    if not isinstance(snapshot, Mapping):
        raise RegistryError("promotion pre_registry provenance must resolve to registry object")
    if canonical_sha256(dict(snapshot)) != receipt.pre_registry_sha:
        raise RegistryError("promotion pre_registry provenance digest mismatch")
    if snapshot.get("schema") != "TD_QUALIFICATION_REGISTRY_V1":
        raise RegistryError("promotion pre_registry provenance schema mismatch")
    units = snapshot.get("units")
    if type(units) is not list:
        raise RegistryError("promotion pre_registry units malformed")
    prior_units = [obj for obj in units if isinstance(obj, Mapping) and obj.get("unit_id") == unit.unit_id]
    if len(prior_units) != 1 or dict(prior_units[0]) != predecessor.to_payload():
        raise RegistryError("promotion pre_registry unit identity/provenance mismatch")
    prereqs = snapshot.get("prerequisites")
    if type(prereqs) is not list:
        raise RegistryError("promotion pre_registry prerequisites malformed")
    relevant = [
        dict(obj) for obj in prereqs
        if isinstance(obj, Mapping)
        and obj.get("dependent_unit_id") == unit.unit_id
        and obj.get("gate") == receipt.destination_stage.value
    ]
    expected_ids = tuple(obj.get("prerequisite_id") for obj in relevant)
    expected_shas = tuple(canonical_sha256(obj) for obj in relevant)
    if receipt.prerequisite_ids != expected_ids or receipt.prerequisite_shas != expected_shas:
        raise RegistryError("promotion receipt prerequisite chain does not match pre_registry snapshot")
    _resolve_object(
        receipt.controller_identity, resolver,
        expected_role="QUALIFICATION_CONTROLLER", label="prior promotion controller",
    )
    if receipt.reviewer_identity is not None:
        _resolve_object(
            receipt.reviewer_identity, resolver,
            expected_role="INDEPENDENT_REVIEWER", label="prior promotion reviewer",
        )
    return receipt

'''
text = once(text, marker, provenance + marker, "insert promotion provenance validator")
old_prior = '''        prior_stage_receipts = tuple(
            receipt for receipt in registry.promotions
            if receipt.unit_id == unit_id and receipt.destination_stage is unit.qualification_stage
        )
        if not prior_stage_receipts:
            raise RegistryError("current advanced stage lacks prior promotion history provenance")
        dependency_blockers = _verify_unit_dependencies(unit, dependency_verifier, verification_cache)
'''
new_prior = '''        _validate_current_stage_promotion_provenance(unit, registry, authority_object_resolver)
        dependency_blockers = _verify_unit_dependencies(unit, dependency_verifier, verification_cache)
'''
text = once(text, old_prior, new_prior, "validate prior promotion chain")
REGISTRY.write_text(text, encoding="utf-8")

# Test migration: only positive authority cases get actual dependency objects/bytes.
main = MAIN.read_text(encoding="utf-8")
main = once(main, 'from scripts.v5.td_unified.canonical_v1 import canonical_sha256\n', 'from scripts.v5.td_unified.canonical_v1 import canonical_sha256\nfrom tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq\n', 'main fixture import')
main = once(main, '''def test_historical_promotion_receipt_remains_immutable_after_revocation():
    r=_r(); u,ref=_unit(r),_unit(r,"REF"); reg=_registry(r,[u,ref],[_prereq(r)]); c,rv,res=_actors()
    promoted=r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res,dependency_verifier=lambda _: True)
    old=promoted.promotions[0]
    revoked=r.revoke_or_supersede(promoted,"G8",ActiveLineageStatus.REVOKED_BY_DEFECT,reason_class="DEFECT",controller_identity=c,authority_object_resolver=res)
    assert revoked.promotions[0]==old
    assert revoked.units_by_id()["G8"].active_lineage_status is ActiveLineageStatus.REVOKED_BY_DEFECT
''', '''def test_historical_promotion_receipt_remains_immutable_after_revocation():
    r=_r(); u,ref,deps=verified_pair(r); p=verified_prereq(r,u,ref); reg=_registry(r,[u,ref],[p]); c,rv,res=_actors()
    promoted=r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res,dependency_verifier=deps.get)
    old=promoted.promotions[0]
    revoked=r.revoke_or_supersede(promoted,"G8",ActiveLineageStatus.REVOKED_BY_DEFECT,reason_class="DEFECT",controller_identity=c,authority_object_resolver=res)
    assert revoked.promotions[0]==old
    assert revoked.units_by_id()["G8"].active_lineage_status is ActiveLineageStatus.REVOKED_BY_DEFECT
''', 'historical promotion positive')
main = once(main, '''def test_recursive_verification_cache_invalidates_on_dependency_identity_change():
    r=_r(); calls=[]
    def verify(sha): calls.append(sha); return True
    dep,ref=_unit(r),_unit(r,"REF"); reg=_registry(r,[dep,ref],[_prereq(r)]); cache={}
    assert r.derive_real_reference_ready("G8",reg,dependency_verifier=verify,verification_cache=cache).ready
    changed=r.replace_unit(reg,r.reidentify_unit(ref,metric_sha="9"*64))
    assert not r.derive_real_reference_ready("G8",changed,dependency_verifier=verify,verification_cache=cache).ready
    assert calls
''', '''def test_recursive_verification_cache_invalidates_on_dependency_identity_change():
    r=_r(); calls=[]; dep,ref,deps=verified_pair(r); p=verified_prereq(r,dep,ref); reg=_registry(r,[dep,ref],[p]); cache={}
    def verify(sha): calls.append(sha); return deps.get(sha)
    assert r.derive_real_reference_ready("G8",reg,dependency_verifier=verify,verification_cache=cache).ready
    changed=r.replace_unit(reg,r.reidentify_unit(ref,metric_sha="9"*64))
    assert not r.derive_real_reference_ready("G8",changed,dependency_verifier=verify,verification_cache=cache).ready
    assert calls
''', 'cache positive')
main = once(main, '''def test_cached_ready_result_cannot_survive_manifest_or_access_change():
    r=_r(); dep,ref=_unit(r),_unit(r,"REF"); reg=_registry(r,[dep,ref],[_prereq(r)]); cache={}
    assert r.derive_real_reference_ready("G8",reg,dependency_verifier=lambda _: True,verification_cache=cache).ready
    assert not r.derive_real_reference_ready("G8",r.replace_unit(reg,_unit(r,"G8",manifest="e"*64)),verification_cache=cache).ready
''', '''def test_cached_ready_result_cannot_survive_manifest_or_access_change():
    r=_r(); dep,ref,deps=verified_pair(r); p=verified_prereq(r,dep,ref); reg=_registry(r,[dep,ref],[p]); cache={}
    assert r.derive_real_reference_ready("G8",reg,dependency_verifier=deps.get,verification_cache=cache).ready
    assert not r.derive_real_reference_ready("G8",r.replace_unit(reg,_unit(r,"G8",manifest="e"*64)),dependency_verifier=deps.get,verification_cache=cache).ready
''', 'cached ready positive')
MAIN.write_text(main, encoding="utf-8")

s1 = SELF1.read_text(encoding="utf-8")
s1 = once(s1, 'from scripts.v5.td_unified import registry_v1 as r\n', 'from scripts.v5.td_unified import registry_v1 as r\nfrom tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq\n', 'self1 fixture import')
s1 = once(s1, '''def test_external_evidence_positive_control_requires_exact_receipt_resolution():
    dep,target=unit(),unit("REF"); esha,eobj=evidence(); p=prereq(dep,target,requirement_class="EXTERNAL_CONTROL",evidence_receipt_sha=esha)
    result=r.derive_real_reference_ready("G8",registry(dep,target,p),authority_object_resolver=lambda sha:eobj if sha==esha else None)
    assert result.ready
''', '''def test_external_evidence_positive_control_requires_exact_receipt_resolution():
    dep,target,deps=verified_pair(r); esha,eobj=evidence(); p=verified_prereq(r,dep,target,requirement_class="EXTERNAL_CONTROL",evidence_receipt_sha=esha)
    result=r.derive_real_reference_ready("G8",registry(dep,target,p),authority_object_resolver=lambda sha:eobj if sha==esha else None,dependency_verifier=deps.get)
    assert result.ready
''', 'self1 evidence positive')
SELF1.write_text(s1, encoding="utf-8")

s2 = SELF2.read_text(encoding="utf-8")
s2 = once(s2, 'from scripts.v5.td_unified import registry_v1 as r\n', 'from scripts.v5.td_unified import registry_v1 as r\nfrom tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq\n', 'self2 fixture import')
s2 = once(s2, '''def test_evidence_receipt_must_resolve_to_exact_role_tagged_object():
    dep, target = unit(), unit("REF")
    good_sha, good = evidence(); bad_sha, bad = evidence("METRIC_DEFINITION", "spoof")
    p = prereq(dep, target, evidence_sha=bad_sha); reg = registry(dep, target, p)
    result = r.derive_real_reference_ready("G8", reg, authority_object_resolver=lambda sha: bad if sha == bad_sha else None)
    assert not result.ready
    assert any("role" in b.lower() for b in result.blockers)
    p2 = prereq(dep, target, evidence_sha=good_sha); reg2 = registry(dep, target, p2)
    assert r.derive_real_reference_ready("G8", reg2, authority_object_resolver=lambda sha: good if sha == good_sha else None).ready
''', '''def test_evidence_receipt_must_resolve_to_exact_role_tagged_object():
    dep, target, deps = verified_pair(r)
    good_sha, good = evidence(); bad_sha, bad = evidence("METRIC_DEFINITION", "spoof")
    p = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=bad_sha); reg = registry(dep, target, p)
    result = r.derive_real_reference_ready("G8", reg, authority_object_resolver=lambda sha: bad if sha == bad_sha else None, dependency_verifier=deps.get)
    assert not result.ready
    assert any("role" in b.lower() for b in result.blockers)
    p2 = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=good_sha); reg2 = registry(dep, target, p2)
    assert r.derive_real_reference_ready("G8", reg2, authority_object_resolver=lambda sha: good if sha == good_sha else None, dependency_verifier=deps.get).ready
''', 'self2 evidence role positive')
s2 = once(s2, '''def test_controller_and_reviewer_are_resolved_objects_not_digest_strings():
    dep, target = unit(), unit("REF"); esha, eobj = evidence(); p = prereq(dep, target, evidence_sha=esha)
    reg = registry(dep, target, p)
    csha, cobj = actor("QUALIFICATION_CONTROLLER", "C1")
    rsha, robj = actor("INDEPENDENT_REVIEWER", "R1")
    with pytest.raises(r.RegistryError, match="resolver|controller.*object|authority object"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity=csha, reviewer_identity=rsha,
                       prerequisite_evidence_verifier=lambda _: True)
    resolver = {csha:cobj, rsha:robj, esha:eobj}.get
    promoted = r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                              controller_identity=csha, reviewer_identity=rsha,
                              authority_object_resolver=resolver)
    assert promoted.units_by_id()["G8"].qualification_stage is QualificationStage.REAL_REFERENCE_READY
''', '''def test_controller_and_reviewer_are_resolved_objects_not_digest_strings():
    dep, target, deps = verified_pair(r); esha, eobj = evidence(); p = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=esha)
    reg = registry(dep, target, p)
    csha, cobj = actor("QUALIFICATION_CONTROLLER", "C1")
    rsha, robj = actor("INDEPENDENT_REVIEWER", "R1")
    with pytest.raises(r.RegistryError, match="resolver|controller.*object|authority object"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity=csha, reviewer_identity=rsha,
                       prerequisite_evidence_verifier=lambda _: True)
    resolver = {csha:cobj, rsha:robj, esha:eobj}.get
    promoted = r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                              controller_identity=csha, reviewer_identity=rsha,
                              authority_object_resolver=resolver, dependency_verifier=deps.get)
    assert promoted.units_by_id()["G8"].qualification_stage is QualificationStage.REAL_REFERENCE_READY
''', 'self2 participant positive')
s2 = once(s2, '''def test_promotion_receipt_explicitly_binds_prerequisite_record_identities():
    dep, target = unit(), unit("REF"); esha, eobj = evidence(); p = prereq(dep, target, evidence_sha=esha)
    reg = registry(dep, target, p)
    csha, cobj = actor("QUALIFICATION_CONTROLLER", "C1"); rsha, robj = actor("INDEPENDENT_REVIEWER", "R1")
    promoted = r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                              controller_identity=csha, reviewer_identity=rsha,
                              authority_object_resolver={csha:cobj,rsha:robj,esha:eobj}.get)
    receipt = promoted.promotions[0]
    assert receipt.prerequisite_shas == (p.canonical_sha256(),)
''', '''def test_promotion_receipt_explicitly_binds_prerequisite_record_identities():
    dep, target, deps = verified_pair(r); esha, eobj = evidence(); p = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=esha)
    reg = registry(dep, target, p)
    csha, cobj = actor("QUALIFICATION_CONTROLLER", "C1"); rsha, robj = actor("INDEPENDENT_REVIEWER", "R1")
    promoted = r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                              controller_identity=csha, reviewer_identity=rsha,
                              authority_object_resolver={csha:cobj,rsha:robj,esha:eobj}.get,
                              dependency_verifier=deps.get)
    receipt = promoted.promotions[0]
    assert receipt.prerequisite_shas == (p.canonical_sha256(),)
''', 'self2 receipt positive')
SELF2.write_text(s2, encoding="utf-8")

print("Applied Task 3 hostile cycle2 hardening")
