from __future__ import annotations

from dataclasses import replace

from scripts.v5.td_unified.authority_v1 import QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified import registry_v1 as r
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq


def _registry(dep, ref, p):
    return r.TDQualificationRegistry((dep, ref), (p,), (), ())


def test_minimal_manifest_label_cannot_substitute_for_task2_per_unit_binding():
    dep, ref, objects = verified_pair(r)
    p = verified_prereq(r, dep, ref)
    # Strip the manifest down to the fields current GREEN2 accepts.
    minimal = {"schema": "TD_EXECUTION_MANIFEST_V1", "access_policy_sha": dep.access_policy_sha}
    minimal_sha = canonical_sha256(minimal)
    forged_dep = replace(dep, manifest_sha=minimal_sha)
    forged_ref = replace(ref, manifest_sha=minimal_sha)
    forged_p = replace(
        p,
        dependent_unit_sha=forged_dep.canonical_sha256(),
        prerequisite_unit_sha=forged_ref.canonical_sha256(),
        manifest_sha=minimal_sha,
    )
    forged_objects = dict(objects)
    forged_objects[minimal_sha] = minimal
    result = r.derive_real_reference_ready(
        "G8", _registry(forged_dep, forged_ref, forged_p),
        dependency_verifier=forged_objects.get,
    )
    assert not result.ready
    assert any("unit execution" in b.lower() or "task 2" in b.lower() or "manifest" in b.lower() for b in result.blockers)


def test_registry_unit_must_equal_exact_task2_execution_identity_table_row():
    dep, ref, objects = verified_pair(r)
    p = verified_prereq(r, dep, ref)
    # The dependency objects themselves remain valid, but the manifest-bound table
    # intentionally binds a different metric identity for G8.
    table_sha = objects[dep.manifest_sha]["unit_execution_identity_table_sha"]
    table = dict(objects[table_sha])
    rows = [dict(row) for row in table["units"]]
    rows[0]["metric_sha"] = ref.metric_sha
    bad_table = {**table, "units": rows}
    bad_table_sha = canonical_sha256(bad_table)
    bad_manifest = dict(objects[dep.manifest_sha])
    bad_manifest["unit_execution_identity_table_sha"] = bad_table_sha
    bad_manifest_sha = canonical_sha256(bad_manifest)
    forged_dep = replace(dep, manifest_sha=bad_manifest_sha)
    forged_ref = replace(ref, manifest_sha=bad_manifest_sha)
    forged_p = replace(
        p,
        dependent_unit_sha=forged_dep.canonical_sha256(),
        prerequisite_unit_sha=forged_ref.canonical_sha256(),
        manifest_sha=bad_manifest_sha,
    )
    forged_objects = dict(objects)
    forged_objects[bad_table_sha] = bad_table
    forged_objects[bad_manifest_sha] = bad_manifest
    result = r.derive_real_reference_ready(
        "G8", _registry(forged_dep, forged_ref, forged_p),
        dependency_verifier=forged_objects.get,
    )
    assert not result.ready
    assert any("execution identity" in b.lower() or "table" in b.lower() or "metric" in b.lower() for b in result.blockers)


def test_access_policy_population_authority_cannot_be_omitted():
    dep, ref, objects = verified_pair(r)
    p = verified_prereq(r, dep, ref)
    access = dict(objects[dep.access_policy_sha])
    access.pop("population_authority")
    access_sha = canonical_sha256(access)
    manifest = dict(objects[dep.manifest_sha])
    manifest["access_policy_sha"] = access_sha
    manifest_sha = canonical_sha256(manifest)
    forged_dep = replace(dep, access_policy_sha=access_sha, manifest_sha=manifest_sha)
    forged_ref = replace(ref, access_policy_sha=access_sha, manifest_sha=manifest_sha)
    forged_p = replace(
        p,
        dependent_unit_sha=forged_dep.canonical_sha256(),
        prerequisite_unit_sha=forged_ref.canonical_sha256(),
        manifest_sha=manifest_sha,
        access_policy_sha=access_sha,
    )
    forged_objects = dict(objects)
    forged_objects[access_sha] = access
    forged_objects[manifest_sha] = manifest
    result = r.derive_real_reference_ready(
        "G8", _registry(forged_dep, forged_ref, forged_p),
        dependency_verifier=forged_objects.get,
    )
    assert not result.ready
    assert any("population authority" in b.lower() or "access policy" in b.lower() for b in result.blockers)
