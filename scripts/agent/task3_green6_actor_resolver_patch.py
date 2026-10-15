#!/usr/bin/env python3
"""Historical one-shot production patch for RED6 actor dependency resolution.

Producer/executor actor identities are unit dependencies, so they may resolve through
Task 3's authenticated dependency resolver. Qualification controller/reviewer objects
remain authority-object-resolver inputs. This preserves separation of roles while
avoiding a second actor authority store.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "scripts/v5/td_unified/registry_v1.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected one source block, found {text.count(old)}")
    return text.replace(old, new, 1)


if __name__ == "__main__":
    text = PATH.read_text()
    helper_anchor = '''def _actor_id(obj: Mapping[str, object], *, label: str) -> str:\n    actor_id = obj.get("actor_id")\n    if type(actor_id) is not str or not actor_id.strip():\n        raise RegistryError(f"{label} must declare a non-empty actor_id")\n    return actor_id\n\n\n'''
    helper = helper_anchor + '''def _resolve_unit_actor(\n    expected_sha: str,\n    authority_object_resolver: AuthorityObjectResolver | None,\n    dependency_verifier: Callable[[str], object] | None,\n    *,\n    expected_role: str,\n    label: str,\n) -> Mapping[str, object]:\n    """Resolve a unit-bound actor through either authenticated object surface.\n\n    Unit actor identity is a scientific dependency; controller/reviewer identities are\n    separate qualification authority objects. A resolver returning None is not authority.\n    """\n    def combined(sha: str):\n        if authority_object_resolver is not None:\n            obj = authority_object_resolver(sha)\n            if obj is not None:\n                return obj\n        if dependency_verifier is not None:\n            return dependency_verifier(sha)\n        return None\n    return _resolve_object(expected_sha, combined, expected_role=expected_role, label=label)\n\n\n'''
    text = replace_once(text, helper_anchor, helper, "unit actor resolver helper")

    old = '''    producer_actor_obj = _resolve_object(\n        unit.producer_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",\n    )\n    executor_actor_obj = _resolve_object(\n        unit.executor_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",\n    )\n'''
    new = '''    if destination_stage is QualificationStage.HUMAN_EXECUTABLE and reviewer_identity is None:\n        raise RegistryError("independent reviewer required for HUMAN_EXECUTABLE")\n    producer_actor_obj = _resolve_unit_actor(\n        unit.producer_actor_identity, authority_object_resolver, dependency_verifier,\n        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",\n    )\n    executor_actor_obj = _resolve_unit_actor(\n        unit.executor_actor_identity, authority_object_resolver, dependency_verifier,\n        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",\n    )\n'''
    text = replace_once(text, old, new, "promotion unit actor resolution")
    # Remove the later duplicate reviewer-none check now handled before actor resolution.
    text = text.replace('''    if destination_stage is QualificationStage.HUMAN_EXECUTABLE:\n        if reviewer_identity is None:\n            raise RegistryError("independent reviewer required for HUMAN_EXECUTABLE")\n''', '''    if destination_stage is QualificationStage.HUMAN_EXECUTABLE:\n''', 1)

    old_rev = '''    producer_actor_obj = _resolve_object(\n        unit.producer_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",\n    )\n    executor_actor_obj = _resolve_object(\n        unit.executor_actor_identity, authority_object_resolver,\n        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",\n    )\n'''
    new_rev = '''    producer_actor_obj = _resolve_unit_actor(\n        unit.producer_actor_identity, authority_object_resolver, dependency_verifier,\n        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",\n    )\n    executor_actor_obj = _resolve_unit_actor(\n        unit.executor_actor_identity, authority_object_resolver, dependency_verifier,\n        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",\n    )\n'''
    # revoke_or_supersede needs a dependency resolver kwarg to authenticate unit actors.
    sig_old = '''def revoke_or_supersede(\n    registry: TDQualificationRegistry,\n    unit_id: str,\n    new_status: ActiveLineageStatus,\n    *,\n    reason_class: str,\n    controller_identity: str,\n    successor_unit_id: str | None = None,\n    requalification_scope: tuple[str, ...] = (),\n    authority_object_resolver: AuthorityObjectResolver | None = None,\n) -> TDQualificationRegistry:\n'''
    sig_new = '''def revoke_or_supersede(\n    registry: TDQualificationRegistry,\n    unit_id: str,\n    new_status: ActiveLineageStatus,\n    *,\n    reason_class: str,\n    controller_identity: str,\n    successor_unit_id: str | None = None,\n    requalification_scope: tuple[str, ...] = (),\n    authority_object_resolver: AuthorityObjectResolver | None = None,\n    dependency_verifier: Callable[[str], object] | None = None,\n) -> TDQualificationRegistry:\n'''
    text = replace_once(text, sig_old, sig_new, "revocation dependency verifier signature")
    text = replace_once(text, old_rev, new_rev, "revocation unit actor resolution")
    PATH.write_text(text)
