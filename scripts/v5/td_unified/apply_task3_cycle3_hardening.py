from __future__ import annotations

from pathlib import Path

REGISTRY = Path("scripts/v5/td_unified/registry_v1.py")


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected one match, found {n}")
    return text.replace(old, new, 1)


text = REGISTRY.read_text(encoding="utf-8")
old = '''                    if field == "manifest_sha":
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
'''
new = '''                    if field == "manifest_sha":
                        if obj.get("schema") != "TD_EXECUTION_MANIFEST_V1":
                            raise RegistryError("dependency manifest_sha schema mismatch")
                        bound_access = obj.get("access_policy_sha")
                        if bound_access != unit.access_policy_sha:
                            raise RegistryError("dependency manifest/access-policy binding mismatch")
                        table_sha = obj.get("unit_execution_identity_table_sha")
                        if not _hex(table_sha, 64):
                            raise RegistryError("Task 2 manifest must bind exact unit execution identity table")
                        table_obj = dependency_verifier(table_sha)
                        if not isinstance(table_obj, Mapping):
                            raise RegistryError("Task 2 unit execution identity table object unavailable")
                        if canonical_sha256(dict(table_obj)) != table_sha:
                            raise RegistryError("Task 2 unit execution identity table digest mismatch")
                        if set(table_obj) != {"object_role", "table_schema", "units"}:
                            raise RegistryError("Task 2 unit execution identity table fields invalid")
                        if table_obj.get("object_role") != "UNIT_EXECUTION_IDENTITY_TABLE" or table_obj.get("table_schema") != "UNIT_EXECUTION_IDENTITY_TABLE_V1":
                            raise RegistryError("Task 2 unit execution identity table role/schema mismatch")
                        rows = table_obj.get("units")
                        if type(rows) is not list or not rows:
                            raise RegistryError("Task 2 unit execution identity table must be non-empty")
                        expected_fields = {
                            "unit_id", "producer_code_sha1", "executor_code_sha1",
                            "producer_policy_sha", "executor_policy_sha", "schema_sha",
                            "metric_sha", "reference_producer_sha", "falsifier_sha",
                        }
                        if any(type(row) is not dict or set(row) != expected_fields for row in rows):
                            raise RegistryError("Task 2 unit execution identity row fields invalid")
                        unit_rows = [row for row in rows if row.get("unit_id") == unit.unit_id]
                        if len(unit_rows) != 1:
                            raise RegistryError("Task 2 manifest must bind exactly one execution identity row for registry unit")
                        expected_row = {
                            "unit_id": unit.unit_id,
                            "producer_code_sha1": unit.producer_code_sha,
                            "executor_code_sha1": unit.executor_code_sha,
                            "producer_policy_sha": unit.producer_policy_sha,
                            "executor_policy_sha": unit.executor_policy_sha,
                            "schema_sha": unit.schema_sha,
                            "metric_sha": unit.metric_sha,
                            "reference_producer_sha": unit.reference_producer_sha,
                            "falsifier_sha": unit.falsifier_sha,
                        }
                        if unit_rows[0] != expected_row:
                            raise RegistryError("registry unit identities do not match exact Task 2 execution identity table row")
                    else:
                        expected_role = _DEPENDENCY_ROLE_BY_FIELD.get(field)
                        if expected_role is None or obj.get("object_role") != expected_role:
                            raise RegistryError(f"dependency {field} role mismatch; expected {expected_role}")
                        if field == "access_policy_sha":
                            population = obj.get("population_authority")
                            if population != unit.population_authority:
                                raise RegistryError("dependency access policy population authority mismatch or missing")
'''
text = once(text, old, new, "bind Task2 manifest table and access population authority")
REGISTRY.write_text(text, encoding="utf-8")
print("Applied Task 3 hostile cycle3 hardening")
