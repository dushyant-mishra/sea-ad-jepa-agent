from __future__ import annotations

import hashlib

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256


def git_blob_sha1(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(prefix + raw).hexdigest()


def _semantic(role: str, unit_id: str) -> dict[str, object]:
    return {"object_role": role, "unit_id": unit_id, "fixture": "TASK3_DEPENDENCY_BYTES_V1"}


def _core(unit_id: str):
    producer_code = f"producer-code:{unit_id}:v1\n".encode()
    executor_code = f"executor-code:{unit_id}:v1\n".encode()
    semantic = {
        "producer_policy_sha": _semantic("PRODUCER_POLICY", unit_id),
        "executor_policy_sha": _semantic("EXECUTOR_POLICY", unit_id),
        "schema_sha": _semantic("UNIT_SCHEMA", unit_id),
        "metric_sha": _semantic("METRIC_DEFINITION", unit_id),
        "reference_producer_sha": _semantic("REFERENCE_PRODUCER", unit_id),
        "falsifier_sha": _semantic("FALSIFIER_CONTROL", unit_id),
    }
    objects: dict[str, object] = {
        git_blob_sha1(producer_code): producer_code,
        git_blob_sha1(executor_code): executor_code,
    }
    identities: dict[str, str] = {
        "producer_code_sha": git_blob_sha1(producer_code),
        "executor_code_sha": git_blob_sha1(executor_code),
    }
    for field, obj in semantic.items():
        sha = canonical_sha256(obj)
        identities[field] = sha
        objects[sha] = obj
    return identities, objects


def _row(unit_id: str, identities: dict[str, str]) -> dict[str, object]:
    return {
        "unit_id": unit_id,
        "producer_code_sha1": identities["producer_code_sha"],
        "executor_code_sha1": identities["executor_code_sha"],
        "producer_policy_sha": identities["producer_policy_sha"],
        "executor_policy_sha": identities["executor_policy_sha"],
        "schema_sha": identities["schema_sha"],
        "metric_sha": identities["metric_sha"],
        "reference_producer_sha": identities["reference_producer_sha"],
        "falsifier_sha": identities["falsifier_sha"],
    }


def _shared_surface(rows: list[dict[str, object]], *, population_authority: str, lane: str):
    access = {
        "object_role": "ACCESS_POLICY",
        "policy_schema": "TASK3_FIXTURE_ACCESS_POLICY_V1",
        "population_authority": population_authority,
        "lane": lane,
    }
    access_sha = canonical_sha256(access)
    table = {
        "object_role": "UNIT_EXECUTION_IDENTITY_TABLE",
        "table_schema": "UNIT_EXECUTION_IDENTITY_TABLE_V1",
        "units": rows,
    }
    table_sha = canonical_sha256(table)
    manifest = {
        "schema": "TD_EXECUTION_MANIFEST_V1",
        "fixture": "TASK3_DEPENDENCY_BYTES_V1",
        "lane": lane,
        "access_policy_sha": access_sha,
        "unit_execution_identity_table_sha": table_sha,
    }
    manifest_sha = canonical_sha256(manifest)
    return access_sha, access, table_sha, table, manifest_sha, manifest


def _build_unit(r, unit_id: str, identities: dict[str, str], *, manifest_sha: str, access_sha: str,
                stage, status, population_authority: str, claim_scope: str):
    return r.RegistryUnit(
        unit_id=unit_id,
        qualification_stage=stage,
        active_lineage_status=status,
        authority_scope=f"UNIT:{unit_id}",
        authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha=manifest_sha,
        access_policy_sha=access_sha,
        population_authority=population_authority,
        claim_scope=claim_scope,
        **identities,
    )


def verified_unit(
    r,
    unit_id: str = "G8",
    *,
    stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
    status=ActiveLineageStatus.ACTIVE,
    population_authority: str = "AUTHENTICATED_READER_SPLIT",
    claim_scope: str = "POOLED_DONOR_LEVEL",
    lane: str = "DEFAULT",
):
    identities, objects = _core(unit_id)
    access_sha, access, table_sha, table, manifest_sha, manifest = _shared_surface(
        [_row(unit_id, identities)], population_authority=population_authority, lane=lane
    )
    objects.update({access_sha: access, table_sha: table, manifest_sha: manifest})
    unit = _build_unit(
        r, unit_id, identities, manifest_sha=manifest_sha, access_sha=access_sha,
        stage=stage, status=status, population_authority=population_authority, claim_scope=claim_scope,
    )
    return unit, objects


def verified_pair(r, *, dep_id: str = "G8", ref_id: str = "REF", dep_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
                  ref_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED, ref_status=ActiveLineageStatus.ACTIVE,
                  population_authority: str = "AUTHENTICATED_READER_SPLIT", claim_scope: str = "POOLED_DONOR_LEVEL"):
    dep_ids, dep_objects = _core(dep_id)
    ref_ids, ref_objects = _core(ref_id)
    access_sha, access, table_sha, table, manifest_sha, manifest = _shared_surface(
        [_row(dep_id, dep_ids), _row(ref_id, ref_ids)], population_authority=population_authority, lane="PAIR"
    )
    dep = _build_unit(
        r, dep_id, dep_ids, manifest_sha=manifest_sha, access_sha=access_sha,
        stage=dep_stage, status=ActiveLineageStatus.ACTIVE,
        population_authority=population_authority, claim_scope=claim_scope,
    )
    ref = _build_unit(
        r, ref_id, ref_ids, manifest_sha=manifest_sha, access_sha=access_sha,
        stage=ref_stage, status=ref_status,
        population_authority=population_authority, claim_scope=claim_scope,
    )
    objects = dict(dep_objects)
    objects.update(ref_objects)
    objects.update({access_sha: access, table_sha: table, manifest_sha: manifest})
    return dep, ref, objects


def verified_prereq(r, dep, ref, *, pid="P1", gate="REAL_REFERENCE_READY",
                    required_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
                    requirement_class="UNIT", external_state="SATISFIED", evidence_receipt_sha="9"*64,
                    content_required=False, content_validated=True, content_validation_receipt_sha=None):
    return r.PrerequisiteRecord(
        prerequisite_id=pid,
        dependent_unit_id=dep.unit_id,
        dependent_unit_sha=dep.canonical_sha256(),
        prerequisite_unit_id=ref.unit_id,
        prerequisite_unit_sha=ref.canonical_sha256(),
        required_stage=required_stage,
        required_lineage_status=ActiveLineageStatus.ACTIVE,
        manifest_sha=dep.manifest_sha,
        access_policy_sha=dep.access_policy_sha,
        gate=gate,
        content_required=content_required,
        content_validated=content_validated,
        content_validation_receipt_sha=content_validation_receipt_sha,
        requirement_class=requirement_class,
        external_state=external_state,
        evidence_receipt_sha=evidence_receipt_sha,
    )


def dependency_resolver(objects: dict[str, object]):
    return objects.get
