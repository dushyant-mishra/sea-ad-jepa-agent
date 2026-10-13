"""Apply one weakening mutation at a time to a scratch worktree, run the tests that must catch it, restore.

A mutation is KILLED when at least one of its target tests fails. Every mutation must be killed.
"""
import json
import subprocess
import sys
from pathlib import Path

WT = Path(sys.argv[1]); PY = sys.argv[2]; OUT = Path(sys.argv[3])
ORCH = "scripts/v79/run_v79_v2_core_scoring_orchestrator.py"
AUTH = "scripts/v79/v79_v2_core_score_authority.py"
T = "tests/v79/test_v79_v2_core_score_orchestrator.py::"

MUTATIONS = [
    ("guard_disabled", ORCH,
     "        if not self.armed or self._hash_only:\n            return\n        p = _norm(path)",
     "        return\n        p = _norm(path)",
     [T + "test_truth_guard_blocks_reads_before_barrier_and_permits_hash_only",
      T + "test_internal_truth_read_during_authentication_is_blocked_by_the_executable_barrier"]),
    ("loader_ignores_barrier", ORCH,
     "    if not isinstance(barrier, TruthBarrier) or not barrier.crossed:\n        _barrier_refuse(\"controller truth requested before the barrier was crossed\")\n",
     "",
     [T + "test_truth_loader_refuses_until_every_authentication_step_is_recorded_in_order"]),
    ("truth_tree_hash_check_removed", ORCH,
     "        if hash_only_sha256(p) != rledger[rel]:\n            _refuse(\"truth_tree\", f\"controller-truth bytes differ from the realization ledger: {rel}\")\n",
     "",
     [T + "test_truth_set_must_match_the_frozen_realization_authority[self_consistent_world_change]"]),
    ("realization_receipt_sha_removed", ORCH,
     "    if hashlib.sha256(rraw).hexdigest() != A.REALIZATION_AUDIT_RECEIPT_SHA256:\n        _refuse(\"realization_authority\", \"realization audit receipt SHA-256 differs from the frozen receipt\")\n",
     "",
     [T + "test_truth_set_must_match_the_frozen_realization_authority[resealed_realization_receipt]"]),
    ("not_diagnosed_check_removed", ORCH,
     "    if not_diagnosed != set(A.NOT_DIAGNOSED_FIT_IDS) or other != {\"COMPLETE\"}:",
     "    if False:",
     [T + "test_frozen_not_diagnosed_fits_cannot_be_dropped_refit_or_reclassified[reclassified_to_complete]",
      T + "test_frozen_not_diagnosed_fits_cannot_be_dropped_refit_or_reclassified[complete_reclassified_to_not_diagnosed]"]),
    ("fit_identity_set_removed", ORCH,
     "    if campaign_ids != expected_ids:",
     "    if False:",
     [T + "test_fit_identity_set_must_equal_the_frozen_1056_fit_queue[substituted]"]),
    ("output_exists_check_removed", ORCH,
     "    if os.path.lexists(out_dir):\n        _refuse(\"output_guard\", f\"output directory already exists (write-once): {out_dir}\")\n",
     "",
     [T + "test_existing_output_directory_is_a_write_once_failure_before_truth"]),
    ("truth_cross_identity_removed", ORCH,
     "            _refuse(\"truth_cross_identity\", f\"truth manifest for {oid} does not cross-link to its blinded fit manifest/index\")",
     "            pass",
     [T + "test_truth_manifest_must_cross_link_to_the_blinded_index_after_the_barrier"]),
    ("custody_executor_head_unchecked", ORCH,
     "    if custody.receipt.get(\"executor_code_head\") != A.CAMPAIGN_CODE_SHA:",
     "    if False:",
     [T + "test_custody_prepared_for_another_executor_head_fails_before_truth_access"]),
    ("campaign_code_head_syntactic_only", AUTH,
     "    if rec.get(\"code_sha\")!=CAMPAIGN_CODE_SHA:",
     "    if not _git_sha(rec.get(\"code_sha\")):",
     [T + "test_load_completed_campaign_requires_exact_frozen_code_head_and_custody",
      T + "test_campaign_code_sha_mismatch_fails_before_truth_access"]),
    ("result_ledger_hash_check_removed", ORCH,
     "        if actual != sha or p.stat().st_size != size:",
     "        if False:",
     [T + "test_result_ledger_mismatch_fails_before_truth_access[draw_file_bytes]"]),
    ("receipt_written_before_outputs_verified", ORCH,
     "        step[0] = \"input_reverification\"\n        _reverify_inputs(ctx, auth_state)\n",
     "",
     [T + "test_input_changed_during_scoring_prevents_the_final_receipt"]),
    ("cli_executing_code_location_unchecked", ORCH,
     "    _require_clean(root)\n    _require_executing_code_in(root)\n",
     "    _require_clean(root)\n",
     [T + "test_cli_refuses_when_executing_code_is_not_the_authorized_checkout"]),
]

results = []
for name, rel, old, new, tests in MUTATIONS:
    path = WT / rel; original = path.read_bytes(); text = original.decode("utf-8")
    if text.count(old) != 1:
        results.append({"mutation": name, "status": "MUTATION_NOT_APPLICABLE", "count": text.count(old)}); continue
    if not tests:
        results.append({"mutation": name, "status": "NO_TARGET_TEST"}); continue
    path.write_bytes(text.replace(old, new).encode("utf-8"))
    try:
        proc = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no", *tests],
                              cwd=WT, capture_output=True, text=True, env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"})
        tail = [l for l in proc.stdout.splitlines() if "passed" in l or "failed" in l][-1:]
        results.append({"mutation": name, "status": "KILLED" if proc.returncode != 0 else "SURVIVED", "summary": tail})
    finally:
        path.write_bytes(original)
    print(json.dumps(results[-1]), flush=True)

OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
required = [r for r in results if r["status"] not in ("NO_TARGET_TEST",)]
print("ALL_REQUIRED_MUTATIONS_KILLED" if all(r["status"] == "KILLED" for r in required) else "SOME_MUTATIONS_SURVIVED_OR_NOT_APPLICABLE")
