#!/usr/bin/env python3
"""One-shot asserted patcher for F1 review closeout batch 1.

This helper exists only because the connected GitHub API exposes whole-file
replacement, not hunk updates. Every transformation asserts the exact old text
or a unique regex match before writing; unexpected parallel edits make the CI
job fail rather than guessing. The helper is removed after the repair commits
are materialized.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one exact match, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def regex_once(path: str, pattern: str, replacement: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{path}: expected one regex match, found {count}")
    target.write_text(new, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- producer
replace_once(
    "scripts/v4/f1_real_producer_v1.py",
    '    "evidence_mask_authority": "scripts/v4/f1_evidence_mask_authority_v1.py",\n'
    '    "tests": "tests/test_f1_real_producer_replay_parity_v1.py",\n',
    '    "evidence_mask_authority": "scripts/v4/f1_evidence_mask_authority_v1.py",\n'
    '    "preflight_executor": "scripts/v4/contextual_target_f1_preflight_executor_v1.py",\n'
    '    "mechanics_validator": "scripts/v4/validate_f1_production_mechanics_acceptance_v1.py",\n'
    '    "tests": "tests/test_f1_real_producer_replay_parity_v1.py",\n')

replace_once(
    "scripts/v4/f1_real_producer_v1.py",
    'def run_production_sweep(*, authorization_path: str | Path | None = None,\n'
    '                         forward_engine: ForwardEngine | None = None,\n'
    '                         reader: Any = None,\n'
    '                         package_root_sha256: str | None = None,\n'
    '                         output_dir: Path | None = None,\n'
    '                         repo: Path = REPO,\n'
    '                         **kwargs: Any) -> dict[str, Any]:',
    'def run_production_sweep(*, authorization_path: str | Path | None = None,\n'
    '                         forward_engine: ForwardEngine | None = None,\n'
    '                         reader: Any = None,\n'
    '                         package_root_sha256: str | None = None,\n'
    '                         output_dir: Path | None = None,\n'
    '                         repo: Path = REPO,\n'
    '                         trusted_authorizations: Mapping[str, str] | None = None,\n'
    '                         **kwargs: Any) -> dict[str, Any]:')

replace_once(
    "scripts/v4/f1_real_producer_v1.py",
    '        expected_donor_count=LAWFUL_READER_FIT_DONORS,\n'
    '        expected_donor_roster_root=roster["roster_root"])\n',
    '        expected_donor_count=LAWFUL_READER_FIT_DONORS,\n'
    '        expected_donor_roster_root=roster["roster_root"],\n'
    '        trusted_authorizations=trusted_authorizations)\n')

replace_once(
    "scripts/v4/f1_real_producer_v1.py",
    '    return execute_authorized_sweep(\n'
    '        authorization=authorization, roster=roster, geometry=geometry,\n'
    '        adapter=forward_engine, reader=reader, output_dir=Path(output_dir), **kwargs)\n',
    '    result = execute_authorized_sweep(\n'
    '        authorization=authorization, roster=roster, geometry=geometry,\n'
    '        adapter=forward_engine, reader=reader, output_dir=Path(output_dir), **kwargs)\n'
    '    assignment_path = _resolve_from(\n'
    '        repo,\n'
    '        "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/"\n'
    '        "F1_QUERY_ASSIGNMENTS_2DRAW.csv")\n'
    '    capture_plan = plan_mechanics_capture(assignment_path)\n'
    '    result["completeness"] = verify_sweep_completeness(\n'
    '        result, planned_assignment_keys=capture_plan["assignment_keys"])\n'
    '    return result\n')

# ------------------------------------------------------------- authorization
replace_once(
    "scripts/v4/f1_execution_authorization_v1.py",
    'STOP_SCOPE = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_SCOPE"\n',
    'STOP_SCOPE = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_SCOPE"\n'
    'STOP_AUTHORIZATION_ISSUER_UNTRUSTED = "STOP_F1_AUTHORIZATION_ISSUER_UNTRUSTED"\n')

replace_once(
    "scripts/v4/f1_execution_authorization_v1.py",
    '    expected_donor_count: int,\n'
    '    expected_donor_roster_root: str,\n'
    ') -> dict[str, Any]:',
    '    expected_donor_count: int,\n'
    '    expected_donor_roster_root: str,\n'
    '    trusted_authorizations: Mapping[str, str] | None = None,\n'
    ') -> dict[str, Any]:')

replace_once(
    "scripts/v4/f1_execution_authorization_v1.py",
    '    _require(stated_root == recomputed, STOP_AUTHORIZATION_SELF_ROOT,\n'
    '             "stated %s but the body digests to %s" % (stated_root, recomputed))\n\n'
    '    _require(str(payload["package_root_sha256"]) == str(package_root_sha256),',
    '    _require(stated_root == recomputed, STOP_AUTHORIZATION_SELF_ROOT,\n'
    '             "stated %s but the body digests to %s" % (stated_root, recomputed))\n\n'
    '    # Self-consistency is not issuer authenticity. The caller must supply an\n'
    '    # independently trusted issuer->authorization-root mapping. There is no\n'
    '    # default and no self-trust path; until governance issues such a trust\n'
    '    # anchor, real execution remains unauthorized.\n'
    '    issuer = str(payload["issued_by"])\n'
    '    trusted = dict(trusted_authorizations or {})\n'
    '    trusted_root = trusted.get(issuer)\n'
    '    _require(trusted_root is not None, STOP_AUTHORIZATION_ISSUER_UNTRUSTED,\n'
    '             "issuer %r has no independent trusted authorization root" % issuer)\n'
    '    _require(str(trusted_root) == stated_root, STOP_AUTHORIZATION_ISSUER_UNTRUSTED,\n'
    '             "issuer %r is trusted for root %s, not supplied root %s"\n'
    '             % (issuer, trusted_root, stated_root))\n\n'
    '    _require(str(payload["package_root_sha256"]) == str(package_root_sha256),')

# -------------------------------------------------------------- runtime adapter
replace_once(
    "scripts/v4/f1_production_runtime_adapter_v1.py",
    'STOP_MAP_DIGEST_UNVERIFIED = "STOP_F1_MATCHED_NULL_MAP_DIGEST_UNVERIFIED"\n',
    'STOP_MAP_DIGEST_UNVERIFIED = "STOP_F1_MATCHED_NULL_MAP_DIGEST_UNVERIFIED"\n'
    'STOP_SOURCE_COUNTS_UNAUTHENTICATED = "STOP_F1_MATCHED_NULL_SOURCE_COUNTS_UNAUTHENTICATED"\n')

replace_once(
    "scripts/v4/f1_production_runtime_adapter_v1.py",
    'def resolve_authenticated_source_values(*, expected: Mapping[str, str],\n'
    '                                        raw_counts: Any, source_library: float,\n'
    '                                        row_locator: str, canonical_cell_id: str,\n'
    '                                        canonical_donor_id: str) -> VerifiedSourceValues:',
    'def resolve_authenticated_source_values(*, expected: Mapping[str, str],\n'
    '                                        raw_counts: Any, source_library: float,\n'
    '                                        row_locator: str, canonical_cell_id: str,\n'
    '                                        canonical_donor_id: str,\n'
    '                                        expected_counts_sha256: str) -> VerifiedSourceValues:')

replace_once(
    "scripts/v4/f1_production_runtime_adapter_v1.py",
    '    if str(canonical_donor_id) != str(expected["source_canonical_donor_id"]):\n'
    '        raise AssertionError("%s: donor %r is not the frozen source donor %r"\n'
    '                             % (STOP_NULL_SOURCE, canonical_donor_id,\n'
    '                                expected["source_canonical_donor_id"]))\n'
    '    return VerifiedSourceValues(',
    '    if str(canonical_donor_id) != str(expected["source_canonical_donor_id"]):\n'
    '        raise AssertionError("%s: donor %r is not the frozen source donor %r"\n'
    '                             % (STOP_NULL_SOURCE, canonical_donor_id,\n'
    '                                expected["source_canonical_donor_id"]))\n'
    '    observed_counts_sha256 = _counts_digest(raw_counts)\n'
    '    if str(expected_counts_sha256) != observed_counts_sha256:\n'
    '        raise AssertionError(\n'
    '            "%s: source %r raw counts digest %s, expected independently bound %s"\n'
    '            % (STOP_SOURCE_COUNTS_UNAUTHENTICATED, canonical_cell_id,\n'
    '               observed_counts_sha256, expected_counts_sha256))\n'
    '    return VerifiedSourceValues(')

regex_once(
    "scripts/v4/f1_production_runtime_adapter_v1.py",
    r'    def _construct\(self, \*, normalized_expression: Any, physical_state: Any,\n'
    r'                   evidence_visible: Any, query_index: int,\n'
    r'                   row_provenance: Sequence\[Mapping\[str, object\]\], role: str\) -> Any:\n'
    r'.*?\n    @staticmethod',
    '''    def _construct(self, *, normalized_expression: Any, physical_state: Any,
                   evidence_visible: Any, query_index: int,
                   row_provenance: Sequence[Mapping[str, object]], role: str) -> Any:
        import torch

        from sea_ad_jepa.v4.contextual_query_local import (
            construct_query_local_contextual_state,
        )

        width = int(np.asarray(physical_state).size)
        try:
            encoder_device = next(self.encoder.parameters()).device
        except (AttributeError, StopIteration):
            encoder_device = torch.device("cpu")

        # All tensors that participate in the encoder forward are constructed on
        # the encoder's actual device. This closes the CPU-tensor/GPU-module
        # mismatch while preserving the frozen dtypes and shapes.
        gene_ids = torch.arange(width, dtype=torch.long, device=encoder_device).unsqueeze(0)
        with torch.no_grad():
            return construct_query_local_contextual_state(
                encoder=self.encoder,
                gene_ids=gene_ids,
                normalized_expression=torch.as_tensor(
                    np.asarray(normalized_expression, dtype=np.float32),
                    device=encoder_device).reshape(1, width),
                physical_state=torch.as_tensor(
                    np.asarray(physical_state, dtype=np.uint8),
                    device=encoder_device).reshape(1, width),
                evidence_visible=torch.as_tensor(
                    np.asarray(evidence_visible, dtype=bool),
                    device=encoder_device).reshape(1, width),
                query_index=torch.as_tensor([int(query_index)], dtype=torch.long,
                                            device=encoder_device),
                row_provenance=list(row_provenance),
                encoder_source_sha256=self.encoder_source_sha256,
                tokenizer_source_sha256=self.tokenizer_source_sha256,
                model_state_sha256=self.model_state_sha256(),
                physical_state_authority_sha256=self.physical_state_authority_sha256,
                role=role)

    @staticmethod''')

# ------------------------------------------------------------ parity/adversarial tests
replace_once(
    "tests/test_f1_real_producer_replay_parity_v1.py",
    '    defaults.update(kwargs)\n'
    '    return authorization.validate_execution_authorization(body, **defaults)\n',
    '    defaults["trusted_authorizations"] = {\n'
    '        str(body["issued_by"]): str(body["authorization_root_sha256"])}\n'
    '    defaults.update(kwargs)\n'
    '    return authorization.validate_execution_authorization(body, **defaults)\n')

replace_once(
    "tests/test_f1_real_producer_replay_parity_v1.py",
    '    ok = adapter_module.resolve_authenticated_source_values(\n'
    '        expected=expected, raw_counts=counts, source_library=1000.0,\n'
    '        row_locator="src::R#1", canonical_cell_id="C1", canonical_donor_id="D1")',
    '    expected_counts_sha256 = adapter_module._counts_digest(counts)\n'
    '    ok = adapter_module.resolve_authenticated_source_values(\n'
    '        expected=expected, raw_counts=counts, source_library=1000.0,\n'
    '        row_locator="src::R#1", canonical_cell_id="C1", canonical_donor_id="D1",\n'
    '        expected_counts_sha256=expected_counts_sha256)')

replace_once(
    "tests/test_f1_real_producer_replay_parity_v1.py",
    '            adapter_module.resolve_authenticated_source_values(\n'
    '                expected=expected, raw_counts=counts, source_library=1000.0, **kwargs)\n',
    '            adapter_module.resolve_authenticated_source_values(\n'
    '                expected=expected, raw_counts=counts, source_library=1000.0,\n'
    '                expected_counts_sha256=expected_counts_sha256, **kwargs)\n\n'
    '    with pytest.raises(AssertionError, match="SOURCE_COUNTS_UNAUTHENTICATED"):\n'
    '        adapter_module.resolve_authenticated_source_values(\n'
    '            expected=expected, raw_counts=counts + 1.0, source_library=1000.0,\n'
    '            row_locator="src::R#1", canonical_cell_id="C1", canonical_donor_id="D1",\n'
    '            expected_counts_sha256=expected_counts_sha256)\n')

# Independent issuer/root attack: a self-consistent authorization must still be
# rejected when no external trust anchor authenticates that issuer/root pair.
anchor_test = '''\n\ndef test_self_consistent_authorization_from_untrusted_issuer_fails() -> None:\n    body = _authorization_body(issued_by="attacker")\n    with pytest.raises(PermissionError, match="AUTHORIZATION_ISSUER_UNTRUSTED"):\n        _validate(body, trusted_authorizations={})\n\n'''
path = ROOT / "tests/test_f1_real_producer_replay_parity_v1.py"
text = path.read_text(encoding="utf-8")
needle = "def test_a_valid_authorization_unlocks_the_frozen_source_without_editing_it() -> None:\n"
if needle not in text or "test_self_consistent_authorization_from_untrusted_issuer_fails" in text:
    raise RuntimeError("authorization adversarial-test insertion point missing or duplicate")
path.write_text(text.replace(needle, anchor_test + needle, 1), encoding="utf-8", newline="\n")

print("F1 review closeout batch 1 patch applied with all assertions satisfied")
