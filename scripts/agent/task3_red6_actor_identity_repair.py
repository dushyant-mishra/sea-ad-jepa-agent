#!/usr/bin/env python3
"""Historical one-shot Task 3 RED6 repair.

Adds exact producer/executor actor identities to RegistryUnit and enforces actor-level
A5 separation for promotion/revocation. Safe to re-run: exits without changing files
once the repair marker is present.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "scripts/v5/td_unified/registry_v1.py"
SCHEMA = ROOT / "schemas/target_discovery/unified_v1/td_qualification_registry_v1.json"
FIX = ROOT / "tests/v5/td_unified/registry_v1_dependency_fixtures.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected exactly one source block, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_registry() -> None:
    text = REG.read_text()
    if 'producer_actor_identity: str' in text and 'qualification controller actor must differ from producer/executor actors' in text:
        return
    text = replace_once(
        text,
        '    "manifest_sha", "access_policy_sha", "producer_policy_sha", "executor_policy_sha",\n    "schema_sha", "metric_sha", "reference_producer_sha", "falsifier_sha",\n',
        '    "manifest_sha", "access_policy_sha", "producer_actor_identity", "executor_actor_identity",\n    "producer_policy_sha", "executor_policy_sha", "schema_sha", "metric_sha",\n    "reference_producer_sha", "falsifier_sha",\n',
        'identity64 fields',
    )
    text = replace_once(
        text,
        '    "access_policy_sha": "ACCESS_POLICY",\n    "producer_policy_sha": "PRODUCER_POLICY",\n',
        '    "access_policy_sha": "ACCESS_POLICY",\n    "producer_actor_identity": "SCIENTIFIC_PRODUCER",\n    "executor_actor_identity": "SCIENTIFIC_EXECUTOR",\n    "producer_policy_sha": "PRODUCER_POLICY",\n',
        'dependency actor roles',
    )
    text = replace_once(
        text,
        '    producer_code_sha: str\n    executor_code_sha: str\n    producer_policy_sha: str\n',
        '    producer_code_sha: str\n    executor_code_sha: str\n    producer_actor_identity: str\n    executor_actor_identity: str\n    producer_policy_sha: str\n',
        'registry unit actor fields',
    )
    text = replace_once(
        text,
        '            "producer_code_sha": self.producer_code_sha,\n            "executor_code_sha": self.executor_code_sha,\n            "producer_policy_sha": self.producer_policy_sha,\n',
        '            "producer_code_sha": self.producer_code_sha,\n            "executor_code_sha": self.executor_code_sha,\n            "producer_actor_identity": self.producer_actor_identity,\n            "executor_actor_identity": self.executor_actor_identity,\n            "producer_policy_sha": self.producer_policy_sha,\n',
        'unit payload actor fields',
    )
    old_promo = '''    if controller_identity in {unit.producer_code_sha, unit.executor_code_sha}:\n        raise RegistryError("independent qualification controller required; producer/executor cannot self-qualify")\n    controller_obj = _resolve_object(\n        controller_identity, authority_object_resolver,\n        expected_role="QUALIFICATION_CONTROLLER", label="qualification controller",\n    )\n    controller_actor = _actor_id(controller_obj, label="qualification controller")\n    if reviewer_identity is not None:\n        if reviewer_identity in {controller_identity, unit.producer_code_sha, unit.executor_code_sha}:\n            raise RegistryError("independent reviewer must differ from controller/producer/executor")\n        reviewer_obj = _resolve_object(\n            reviewer_identity, authority_object_resolver,\n            expected_role="INDEPENDENT_REVIEWER", label="independent reviewer",\n        )\n        reviewer_actor = _actor_id(reviewer_obj, label="independent reviewer")\n        if reviewer_actor == controller_actor:\n            raise RegistryError("independent reviewer actor must differ from qualification controller actor")\n'''
    new_promo = '''    producer_actor_obj = _resolve_object(\n        unit.producer_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",\n    )\n    executor_actor_obj = _resolve_object(\n        unit.executor_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",\n    )\n    producer_actor = _actor_id(producer_actor_obj, label="scientific producer actor")\n    executor_actor = _actor_id(executor_actor_obj, label="scientific executor actor")\n    controller_obj = _resolve_object(\n        controller_identity, authority_object_resolver,\n        expected_role="QUALIFICATION_CONTROLLER", label="qualification controller",\n    )\n    controller_actor = _actor_id(controller_obj, label="qualification controller")\n    if controller_actor in {producer_actor, executor_actor}:\n        raise RegistryError("qualification controller actor must differ from producer/executor actors; self-qualification forbidden")\n    if reviewer_identity is not None:\n        if reviewer_identity == controller_identity:\n            raise RegistryError("independent reviewer must differ from controller")\n        reviewer_obj = _resolve_object(\n            reviewer_identity, authority_object_resolver,\n            expected_role="INDEPENDENT_REVIEWER", label="independent reviewer",\n        )\n        reviewer_actor = _actor_id(reviewer_obj, label="independent reviewer")\n        if reviewer_actor in {controller_actor, producer_actor, executor_actor}:\n            raise RegistryError("independent reviewer actor must differ from qualification controller/producer/executor actors")\n'''
    text = replace_once(text, old_promo, new_promo, 'promotion actor separation')
    old_rev = '''    if controller_identity in {unit.producer_code_sha, unit.executor_code_sha}:\n        raise RegistryError("independent revocation controller required")\n    _resolve_object(\n        controller_identity, authority_object_resolver,\n        expected_role="QUALIFICATION_CONTROLLER", label="revocation controller",\n    )\n'''
    new_rev = '''    producer_actor_obj = _resolve_object(\n        unit.producer_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",\n    )\n    executor_actor_obj = _resolve_object(\n        unit.executor_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",\n    )\n    controller_obj = _resolve_object(\n        controller_identity, authority_object_resolver,\n        expected_role="QUALIFICATION_CONTROLLER", label="revocation controller",\n    )\n    producer_actor = _actor_id(producer_actor_obj, label="scientific producer actor")\n    executor_actor = _actor_id(executor_actor_obj, label="scientific executor actor")\n    controller_actor = _actor_id(controller_obj, label="revocation controller")\n    if controller_actor in {producer_actor, executor_actor}:\n        raise RegistryError("independent revocation controller actor must differ from producer/executor actors")\n'''
    text = replace_once(text, old_rev, new_rev, 'revocation actor separation')
    REG.write_text(text)


def patch_schema() -> None:
    obj = json.loads(SCHEMA.read_text())
    unit = obj['$defs']['registryUnit']
    required = unit['required']
    for field in ('producer_actor_identity', 'executor_actor_identity'):
        if field not in required:
            insert_at = required.index('producer_policy_sha')
            required.insert(insert_at, field)
    props = unit['properties']
    props['producer_actor_identity'] = {'$ref': '#/$defs/sha64'}
    props['executor_actor_identity'] = {'$ref': '#/$defs/sha64'}
    SCHEMA.write_text(json.dumps(obj, indent=2) + '\n')


def patch_fixture() -> None:
    text = FIX.read_text()
    if 'producer_actor_identity' in text:
        return
    old = '''    semantic = {\n        "producer_policy_sha": _semantic("PRODUCER_POLICY", unit_id),\n'''
    new = '''    semantic = {\n        "producer_actor_identity": {"object_role": "SCIENTIFIC_PRODUCER", "actor_id": f"producer:{unit_id}", "unit_id": unit_id, "fixture": "TASK3_DEPENDENCY_BYTES_V1"},\n        "executor_actor_identity": {"object_role": "SCIENTIFIC_EXECUTOR", "actor_id": f"executor:{unit_id}", "unit_id": unit_id, "fixture": "TASK3_DEPENDENCY_BYTES_V1"},\n        "producer_policy_sha": _semantic("PRODUCER_POLICY", unit_id),\n'''
    text = replace_once(text, old, new, 'fixture actor identities')
    FIX.write_text(text)


if __name__ == '__main__':
    patch_registry()
    patch_schema()
    patch_fixture()
