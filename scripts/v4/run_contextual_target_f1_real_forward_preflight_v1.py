"""WSL-only real-reader/query-safe resource preflight for contextual-target F1."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import psutil
import scipy
import torch

HERE = Path(__file__).resolve()
WORKTREE = HERE.parents[2]
CANONICAL = Path(os.environ.get("JEPA_CANONICAL_ROOT", "/mnt/d/Jepa project")).resolve()
sys.path.insert(0, str(WORKTREE / "src"))
sys.path.insert(0, str(WORKTREE / "scripts/v4"))

from contextual_target_f1_preflight_core_v1 import (
    BLOCK_MANIFEST_SHA,
    CHECKPOINT_SHA,
    CONSTRUCTOR_SHA,
    ENCODER_SHA,
    FLOAT32_RULE,
    NAMESPACE_SEMANTIC_ROOT,
    STATE_SHA,
    TOKENIZER_SHA,
    MaterializedFixtureReader,
    canonical_json_sha,
    comparison,
    evidence_mask,
    forward_identity,
    lean_query_local,
    load_encoder,
    meminfo,
    peak_rss_bytes,
    sha256_file,
    swap_used,
    tensor_sha,
)
from contextual_target_f1_preflight_executor_v1 import AtomicShardStore, benchmark_repetitions, full_geometry, power_ladder, select_smallest_near_best
from contextual_target_v1_f0_slow_reference import slow_true_singleton_reference
from sea_ad_jepa.v4.contextual_query_local import construct_query_local_contextual_state, _module_state_sha256

FROZEN = WORKTREE / "docs/agent/f1_real_reader_forward_executor_preflight_20260903"
PACKAGE = WORKTREE / "outputs/contextual_teacher_target_v1_f1_real_reader_forward_executor_preflight_20260903"
RUN_ID = "F1_REAL_READER_FORWARD_EXECUTOR_PREFLIGHT_20260903"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def authority_fields() -> dict[str, str]:
    binding = json.loads((FROZEN / "F1_PREFLIGHT_AUTHORITY_BINDING.json").read_text(encoding="utf-8"))
    repository_commit = os.environ.get("JEPA_PREFLIGHT_COMMIT", "")
    if len(repository_commit) != 40 or any(char not in "0123456789abcdef" for char in repository_commit):
        raise RuntimeError("JEPA_PREFLIGHT_COMMIT must be an exact lowercase Git SHA")
    source_paths = {
        "constructor": WORKTREE / "src/sea_ad_jepa/v4/contextual_query_local.py",
        "encoder": WORKTREE / "src/sea_ad_jepa/v4/ipb_jepa.py",
        "tokenizer": WORKTREE / "src/sea_ad_jepa/v4/gene_tokenizer.py",
    }
    expected_lf = {"constructor": CONSTRUCTOR_SHA, "encoder": ENCODER_SHA, "tokenizer": TOKENIZER_SHA}
    executed = {}
    for name, path in source_paths.items():
        raw = path.read_bytes()
        normalized = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        if normalized != expected_lf[name]:
            raise RuntimeError(f"{name} scientific source differs beyond checkout line endings")
        executed[f"{name}_executed_bytes_sha256"] = hashlib.sha256(raw).hexdigest()
    return {
        "repository_commit": repository_commit,
        "reader_split_sha256": binding["authorities"]["split"]["sha256"],
        "row_lineage_sha256": binding["authorities"]["row_lineage"]["sha256"],
        "evidence_mask_sha256": binding["authorities"]["evidence_contract"]["sha256"],
        "assignment_sha256": binding["authorities"]["assignments"]["sha256"],
        "dedup_sha256": binding["authorities"]["dedup"]["sha256"],
        "matched_null_sha256": binding["authorities"]["null_map"]["sha256"],
        "query_safe_target_sha256": sha256_file(WORKTREE / "scripts/v4/contextual_target_f1_preflight_core_v1.py"),
        **executed,
    }


def freeze_forward_root() -> dict[str, object]:
    reader = MaterializedFixtureReader(CANONICAL, WORKTREE)
    authority = authority_fields()
    records = []
    for index, record in enumerate(reader.fixture["selected"]):
        role = str(record["role"])
        identity = forward_identity(authority, record, role, RUN_ID, f"technical-{index:04d}")
        records.append({"logical_index": index, "role": role, "recipient": record["canonical_cell_id"], "null_source": record.get("null_source_cell") if role == "matched_null_student" else None, "query": int(record["q"]), "evidence_level": int(record["evidence_level"]), "forward_identity_sha256": identity})
    result = {
        "schema": "f1-preflight-real-forward-root-v1",
        "result_state": "FROZEN_PRE_RESULT",
        "run_id": RUN_ID,
        "authority": authority,
        "checkpoint_sha256": CHECKPOINT_SHA,
        "encoder_sha256": ENCODER_SHA,
        "tokenizer_sha256": TOKENIZER_SHA,
        "mechanics_contract_sha256": sha256_file(WORKTREE / "src/sea_ad_jepa/v4/contracts.py"),
        "executed_source_byte_identity": {key: value for key, value in authority.items() if key.endswith("_executed_bytes_sha256")},
        "constructor_sha256": CONSTRUCTOR_SHA,
        "namespace_semantic_root": NAMESPACE_SEMANTIC_ROOT,
        "observation_state_sha256": STATE_SHA,
        "reader_core_sha256": sha256_file(WORKTREE / "scripts/v4/contextual_target_f1_preflight_core_v1.py"),
        "executor_sha256": sha256_file(WORKTREE / "scripts/v4/contextual_target_f1_preflight_executor_v1.py"),
        "runner_sha256": sha256_file(HERE),
        "reader_plan_root_sha256": reader.plan["reader_plan_root_sha256"],
        "fixture_membership_root_sha256": reader.fixture["membership_root_sha256"],
        "dtype": "float32",
        "autocast": False,
        "physical_read_plan": "FULL104_LEVEL4_SORTED_BLOCK_V1",
        "model_facing_keys": ["normalized_values", "observation_states"],
        "identity_sidecar_excluded_from_model": True,
        "cache_rule": "teacher only reusable when every identity field matches; correct and null never collide",
        "records": records,
    }
    result["real_forward_root_sha256"] = canonical_json_sha(result)
    write_json(FROZEN / "F1_PREFLIGHT_REAL_FORWARD_ROOT.json", result)
    return result


def fixture_cell_ids(reader: MaterializedFixtureReader) -> list[str]:
    return [row["canonical_cell_id"] for row in reader.plan["reader_rows"]]


def role_records(reader: MaterializedFixtureReader, role: str) -> list[dict[str, object]]:
    return [row for row in reader.fixture["selected"] if row["role"] == role]


def read_fixture(reader: MaterializedFixtureReader, workers: int, reader_block: int, prefetch: int, reverse: bool = False):
    ids = fixture_cell_ids(reader)
    chunks = [ids[start:start + reader_block] for start in range(0, len(ids), reader_block)]
    start = time.perf_counter()
    payloads = []
    sidecars = []
    physical_blocks = 0
    if prefetch <= 1:
        for chunk in chunks:
            payload, sidecar, timing = reader.read(chunk, workers=workers, reverse_physical=reverse)
            payloads.append(payload)
            sidecars.extend(sidecar)
            physical_blocks += int(timing["physical_blocks"])
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=prefetch) as pool:
            futures = [pool.submit(reader.read, chunk, workers, reverse) for chunk in chunks]
            for future in futures:
                payload, sidecar, timing = future.result()
                payloads.append(payload)
                sidecars.extend(sidecar)
                physical_blocks += int(timing["physical_blocks"])
    values = np.concatenate([item["normalized_values"] for item in payloads], axis=0)
    states = np.concatenate([item["observation_states"] for item in payloads], axis=0)
    model = {"normalized_values": values, "observation_states": states}
    by_cell = {cell: index for index, cell in enumerate(ids)}
    return model, sidecars, by_cell, {"reader_seconds": time.perf_counter() - start, "physical_block_reads": physical_blocks, "reader_chunks": len(chunks)}


def prepare_chunk(record_chunk, role, model, by_cell, pin):
    values, states, masks, queries, provenance = [], [], [], [], []
    start = time.perf_counter()
    for record in record_chunk:
        recipient = str(record["canonical_cell_id"])
        value_cell = str(record["null_source_cell"]) if role == "matched_null_student" else recipient
        recipient_index = by_cell[recipient]
        value_index = by_cell[value_cell]
        state = model["observation_states"][recipient_index]
        query = int(record["q"])
        if role == "teacher":
            visible = state == 1
            visible = visible.copy()
            visible[query] = False
        else:
            visible = evidence_mask(state, str(record["row_locator"]), query, int(record["evidence_level"]))
        values.append(model["normalized_values"][value_index])
        states.append(state)
        masks.append(visible)
        queries.append(query)
        provenance.append({"canonical_cell_id": recipient, "donor_id": record["donor"], "source": record["source"], "operator_index": int(record["operator"]), "reader_partition": "reader_fit", "foundation_split": "foundation/train", "pathology": False, "external": False, "physical_state_row_sha256": tensor_sha(torch.from_numpy(state)), "query_address": query})
    arrays = (np.stack(values).astype(np.float32, copy=False), np.stack(states).astype(np.uint8, copy=False), np.stack(masks).astype(np.bool_, copy=False), np.asarray(queries, dtype=np.int64))
    tensors = [torch.from_numpy(array) for array in arrays]
    if pin:
        tensors = [tensor.pin_memory() for tensor in tensors]
    return tensors, provenance, time.perf_counter() - start


def candidate(batch: int, workers: int, reader_block: int, prefetch: int, pin: bool, reader_only: bool) -> dict[str, object]:
    before = meminfo()
    faults_before = resource.getrusage(resource.RUSAGE_SELF)
    reader = MaterializedFixtureReader(CANONICAL, WORKTREE)
    try:
        if reader_only:
            latest: dict[str, object] = {}

            def read_operation() -> None:
                model, _, by_cell, metrics = read_fixture(reader, workers, reader_block, prefetch)
                latest.update({"model": model, "by_cell": by_cell, "metrics": metrics})

            benchmark = benchmark_repetitions(read_operation, units=len(reader.rows))
            after = meminfo()
            faults_after = resource.getrusage(resource.RUSAGE_SELF)
            return {"safe": swap_used(after) <= swap_used(before) and peak_rss_bytes() <= 0.8 * before["MemAvailable"], "median_throughput": benchmark["median_throughput"], "throughput_unit": "rows_per_second", "configuration": reader_block, "batch": batch, "workers": workers, "reader_block": reader_block, "prefetch": prefetch, "pin": pin, "warmups": benchmark["warmups"], "timed_repetitions": benchmark["timed_repetitions"], "repetitions": benchmark["repetitions"], "reader": latest["metrics"], "peak_rss_bytes": peak_rss_bytes(), "candidate_start_memavailable_bytes": before["MemAvailable"], "swap_before_bytes": swap_used(before), "swap_after_bytes": swap_used(after), "minor_faults_delta": faults_after.ru_minflt - faults_before.ru_minflt, "major_faults_delta": faults_after.ru_majflt - faults_before.ru_majflt, "cuda_peak_allocated_bytes": 0, "cuda_peak_reserved_bytes": 0, "cuda_total_bytes": torch.cuda.get_device_properties(0).total_memory}
        model, _, by_cell, read_metrics = read_fixture(reader, workers, reader_block, prefetch)
        device = torch.device("cuda")
        encoder = load_encoder(CANONICAL, device)
        model_state = _module_state_sha256(encoder)
        role_samples = {role: role_records(reader, role) for role in ("teacher", "correct_student", "matched_null_student")}
        repetitions = []
        role_times = {role: [] for role in role_samples}
        torch.cuda.reset_peak_memory_stats()
        for repetition in range(4):
            total_count = 0
            h2d_seconds = 0.0
            constructor_seconds = 0.0
            model_seconds = 0.0
            reduction_seconds = 0.0
            rep_start = time.perf_counter()
            for role, records in role_samples.items():
                role_start = time.perf_counter()
                for offset in range(0, len(records), batch):
                    tensors, _, prep = prepare_chunk(records[offset:offset + batch], role, model, by_cell, pin)
                    constructor_seconds += prep
                    torch.cuda.synchronize()
                    move_start = time.perf_counter()
                    x, state, visible, query = [tensor.to(device, non_blocking=pin) for tensor in tensors]
                    torch.cuda.synchronize()
                    h2d_seconds += time.perf_counter() - move_start
                    _, timing = lean_query_local(encoder, x, state, visible, query, "teacher" if role == "teacher" else "student")
                    model_seconds += timing["model_forward_seconds"]
                    reduction_seconds += timing["target_context_reduction_seconds"]
                    total_count += len(query)
                torch.cuda.synchronize()
                if repetition:
                    role_times[role].append(time.perf_counter() - role_start)
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - rep_start
            if repetition:
                repetitions.append({"elapsed_seconds": elapsed, "query_identities": total_count, "throughput": total_count / elapsed, "h2d_seconds": h2d_seconds, "constructor_seconds": constructor_seconds, "model_forward_seconds": model_seconds, "target_context_reduction_seconds": reduction_seconds})
        after = meminfo()
        faults_after = resource.getrusage(resource.RUSAGE_SELF)
        total_vram = torch.cuda.get_device_properties(0).total_memory
        peak_reserved = torch.cuda.max_memory_reserved()
        peak_allocated = torch.cuda.max_memory_allocated()
        median_rate = statistics.median(row["throughput"] for row in repetitions)
        safe = peak_reserved <= 0.85 * total_vram and swap_used(after) <= swap_used(before) and peak_rss_bytes() <= 0.8 * before["MemAvailable"] and math.isfinite(median_rate)
        return {"safe": bool(safe), "median_throughput": median_rate, "throughput_unit": "query_identities_per_second", "configuration": batch, "batch": batch, "workers": workers, "reader_block": reader_block, "prefetch": prefetch, "pin": pin, "warmups": 1, "timed_repetitions": 3, "repetitions": repetitions, "role_seconds_median": {role: statistics.median(times) for role, times in role_times.items()}, "role_counts": {role: len(rows) for role, rows in role_samples.items()}, "reader": read_metrics, "peak_rss_bytes": peak_rss_bytes(), "candidate_start_memavailable_bytes": before["MemAvailable"], "swap_before_bytes": swap_used(before), "swap_after_bytes": swap_used(after), "minor_faults_delta": faults_after.ru_minflt - faults_before.ru_minflt, "major_faults_delta": faults_after.ru_majflt - faults_before.ru_majflt, "cuda_peak_allocated_bytes": peak_allocated, "cuda_peak_reserved_bytes": peak_reserved, "cuda_total_bytes": total_vram, "model_state_sha256": model_state}
    except torch.cuda.OutOfMemoryError as error:
        after = meminfo()
        return {"safe": False, "failure": "CUDA_OOM", "error": str(error), "configuration": batch, "batch": batch, "workers": workers, "reader_block": reader_block, "prefetch": prefetch, "pin": pin, "peak_rss_bytes": peak_rss_bytes(), "candidate_start_memavailable_bytes": before["MemAvailable"], "swap_before_bytes": swap_used(before), "swap_after_bytes": swap_used(after), "cuda_peak_allocated_bytes": torch.cuda.max_memory_allocated(), "cuda_peak_reserved_bytes": torch.cuda.max_memory_reserved(), "cuda_total_bytes": torch.cuda.get_device_properties(0).total_memory}


def parity() -> dict[str, object]:
    reader = MaterializedFixtureReader(CANONICAL, WORKTREE)
    model, _, by_cell, read_metrics = read_fixture(reader, 0, len(reader.rows), 1)
    device = torch.device("cuda")
    encoder = load_encoder(CANONICAL, device)
    model_sha = _module_state_sha256(encoder)
    before = model_sha
    comparisons = []
    logical_outputs = {}
    for record in reader.fixture["selected"]:
        role = str(record["role"])
        tensors, provenance, _ = prepare_chunk([record], role, model, by_cell, False)
        x, state, visible, query = [tensor.to(device) for tensor in tensors]
        gene_ids = torch.arange(41238, device=device).expand(1, -1)
        semantic_role = "teacher" if role == "teacher" else "student"
        with torch.no_grad():
            current, _ = lean_query_local(encoder, x, state, visible, query, semantic_role)
            reference = slow_true_singleton_reference(encoder=encoder, gene_ids=gene_ids, normalized_expression=x, physical_state=state, evidence_visible=visible, query_index=query, row_provenance=provenance, role=semantic_role)
        fields = {name: comparison(current[name], reference[name]) for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")}
        comparisons.append({"cell": record["canonical_cell_id"], "q": int(record["q"]), "role": role, "fields": fields, "pass": all(item["pass"] for item in fields.values())})
        key = (record["canonical_cell_id"], int(record["q"]), int(record["evidence_level"]), role)
        logical_outputs[key] = current["contextual_state"][0].detach().cpu().numpy().copy()

    # Reverse query order within each role, execute in multi-query chunks, and
    # restore frozen logical identities. This jointly checks permutation/inverse
    # restoration and singleton-versus-batched output parity.
    restored_outputs = {}
    for role in ("teacher", "correct_student", "matched_null_student"):
        reordered = list(reversed(role_records(reader, role)))
        for offset in range(0, len(reordered), 7):
            chunk = reordered[offset:offset + 7]
            tensors, _, _ = prepare_chunk(chunk, role, model, by_cell, False)
            x, state, visible, query = [tensor.to(device) for tensor in tensors]
            current, _ = lean_query_local(encoder, x, state, visible, query, "teacher" if role == "teacher" else "student")
            for position, record in enumerate(chunk):
                key = (record["canonical_cell_id"], int(record["q"]), int(record["evidence_level"]), role)
                restored_outputs[key] = current["contextual_state"][position].detach().cpu().numpy().copy()
    permutation_keys_exact = list(logical_outputs) == [
        (record["canonical_cell_id"], int(record["q"]), int(record["evidence_level"]), str(record["role"]))
        for record in reader.fixture["selected"]
    ]
    chunk_parity_exact = set(restored_outputs) == set(logical_outputs) and all(
        np.array_equal(logical_outputs[key], restored_outputs[key])
        and logical_outputs[key].tobytes() == restored_outputs[key].tobytes()
        for key in logical_outputs
    )

    # Metamorphic checks on one lawful record from each source.
    metamorphic = []
    for source in ("HVS", "NPH52", "SEA_AD"):
        record = next(row for row in reader.fixture["selected"] if row["source"] == source and row["role"] != "matched_null_student")
        role = str(record["role"])
        tensors, _, _ = prepare_chunk([record], role, model, by_cell, False)
        x, state, visible, query = [tensor.to(device) for tensor in tensors]
        base, _ = lean_query_local(encoder, x, state, visible, query, "teacher" if role == "teacher" else "student")
        xq = x.clone(); xq[0, query[0]] += 7.0
        q_changed, _ = lean_query_local(encoder, xq, state, visible, query, "teacher" if role == "teacher" else "student")
        nonq = int(torch.nonzero(visible[0], as_tuple=False).flatten()[0])
        xn = x.clone(); xn[0, nonq] += 7.0
        nonq_changed, _ = lean_query_local(encoder, xn, state, visible, query, "teacher" if role == "teacher" else "student")
        metamorphic.append({"source": source, "x_q_only_unchanged": bool(torch.equal(base["contextual_state"], q_changed["contextual_state"])), "lawful_non_q_changes": bool(not torch.equal(base["contextual_state"], nonq_changed["contextual_state"]))})

    # Physical read reversal must restore the exact logical model inputs.
    normal, _, _, _ = read_fixture(reader, 0, len(reader.rows), 1, False)
    reversed_read, _, _, _ = read_fixture(reader, 0, len(reader.rows), 1, True)
    read_order_exact = np.array_equal(normal["normalized_values"], reversed_read["normalized_values"]) and np.array_equal(normal["observation_states"], reversed_read["observation_states"])
    roles = reader.fixture["selected"]
    correct = next(row for row in roles if row["role"] == "correct_student")
    null = next(row for row in roles if row["role"] == "matched_null_student")
    authority = authority_fields()
    correct_root = forward_identity(authority, correct, "correct_student", RUN_ID, "identity-test")
    null_as_correct = dict(null); null_as_correct["canonical_cell_id"] = correct["canonical_cell_id"]; null_as_correct["q"] = correct["q"]; null_as_correct["evidence_level"] = correct["evidence_level"]
    null_as_correct["null_source_cell"] = null["null_source_cell"]
    null_root = forward_identity(authority, null_as_correct, "matched_null_student", RUN_ID, "identity-test")
    status = all(row["pass"] for row in comparisons) and all(row["x_q_only_unchanged"] and row["lawful_non_q_changes"] for row in metamorphic) and read_order_exact and permutation_keys_exact and chunk_parity_exact and correct_root != null_root and _module_state_sha256(encoder) == before
    result = {"schema": "f1-preflight-query-safe-parity-v1", "status": "PASS" if status else "STOP_F1_PREFLIGHT_QUERY_SAFE_PARITY_FAILURE", "fixture_membership_root_sha256": reader.fixture["membership_root_sha256"], "comparison_rule": dict(FLOAT32_RULE), "all_fixture_records_compared_to_independent_slow_reference": len(comparisons) == len(reader.fixture["selected"]), "comparisons": comparisons, "metamorphic": metamorphic, "query_permutation_inverse_restoration_exact": permutation_keys_exact, "forward_batch_chunk_parity_exact": chunk_parity_exact, "batch_chunk_size_tested": 7, "physical_read_order_restored_exactly": bool(read_order_exact), "correct_vs_null_identity_distinct": correct_root != null_root, "model_state_unchanged": _module_state_sha256(encoder) == before, "reader": read_metrics, "biological_metrics_computed": False}
    write_json(PACKAGE / "F1_PREFLIGHT_QUERY_SAFE_PARITY.json", result)
    return result


def run_subprocess(extra: list[str]) -> dict[str, object]:
    env = dict(os.environ)
    env["JEPA_CANONICAL_ROOT"] = str(CANONICAL)
    command = [sys.executable, str(HERE), "candidate", *extra]
    completed = subprocess.run(command, cwd=WORKTREE, env=env, capture_output=True, text=True, timeout=1800)
    if completed.returncode:
        raise RuntimeError(f"candidate failed {completed.returncode}: {completed.stderr[-2000:]}")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def environment_authentication() -> tuple[dict[str, object], dict[str, object]]:
    gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free", "--format=csv,noheader,nounits"], text=True).strip().split(",")
    info = meminfo()
    stat = os.statvfs(CANONICAL)
    env = {"schema": "f1-preflight-wsl-environment-v1", "status": "PASS", "wsl_kernel": platform.release(), "platform": platform.platform(), "python_executable": sys.executable, "python_version": sys.version, "numpy": np.__version__, "scipy": scipy.__version__, "torch": torch.__version__, "torch_cuda_runtime": torch.version.cuda, "cudnn": torch.backends.cudnn.version(), "cuda_available": torch.cuda.is_available(), "gpu": gpu[0].strip(), "driver": gpu[1].strip(), "total_vram_mib": int(gpu[2]), "free_vram_mib": int(gpu[3]), "cpu_physical_cores": psutil.cpu_count(logical=False), "cpu_logical_cores": psutil.cpu_count(logical=True), "memtotal_bytes": info["MemTotal"], "memavailable_bytes": info["MemAvailable"], "swap_total_bytes": info["SwapTotal"], "swap_used_bytes": swap_used(info), "filesystem_type": subprocess.check_output(["stat", "-f", "-c", "%T", str(CANONICAL)], text=True).strip(), "free_storage_bytes": stat.f_bavail * stat.f_frsize, "data_path": str(CANONICAL / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4"), "worktree_path": str(WORKTREE), "same_canonical_mount": str(CANONICAL).startswith("/mnt/d/"), "source_hashes": {path.relative_to(WORKTREE).as_posix(): sha256_file(path) for path in (WORKTREE / "scripts/v4/contextual_target_f1_preflight_core_v1.py", WORKTREE / "scripts/v4/contextual_target_f1_preflight_executor_v1.py", HERE, WORKTREE / "src/sea_ad_jepa/v4/contextual_query_local.py", WORKTREE / "src/sea_ad_jepa/v4/ipb_jepa.py", WORKTREE / "src/sea_ad_jepa/v4/gene_tokenizer.py", WORKTREE / "src/sea_ad_jepa/v4/contracts.py")}}
    snapshot = {"schema": "f1-preflight-resource-snapshot-v1", "captured_before_benchmark": True, "gpu": {"name": env["gpu"], "driver": env["driver"], "total_vram_mib": env["total_vram_mib"], "free_vram_mib": env["free_vram_mib"]}, "cpu": {"physical": env["cpu_physical_cores"], "logical": env["cpu_logical_cores"]}, "ram": {"total": env["memtotal_bytes"], "available": env["memavailable_bytes"]}, "swap": {"total": env["swap_total_bytes"], "used": env["swap_used_bytes"]}, "storage_free_bytes": env["free_storage_bytes"]}
    write_json(PACKAGE / "F1_PREFLIGHT_WSL_ENVIRONMENT_AUTHENTICATION.json", env)
    write_json(PACKAGE / "F1_PREFLIGHT_RESOURCE_SNAPSHOT.json", snapshot)
    return env, snapshot


def orchestrate() -> dict[str, object]:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    env, snapshot = environment_authentication()
    p = parity()
    if p["status"] != "PASS":
        raise RuntimeError(p["status"])
    reader = MaterializedFixtureReader(CANONICAL, WORKTREE)
    role_capacity = min(len(role_records(reader, role)) for role in ("teacher", "correct_student", "matched_null_student"))
    rows = []
    for batch in power_ladder(role_capacity):
        result = run_subprocess(["--batch", str(batch), "--workers", "0", "--reader-block", str(len(reader.rows)), "--prefetch", "1"])
        result.update({"stage": "gpu_batch", "configuration": batch})
        rows.append(result)
        if not result["safe"]:
            break
    selected_batch = int(select_smallest_near_best([row for row in rows if row["stage"] == "gpu_batch"])["configuration"])

    reader_rows = []
    for block in [value for value in (selected_batch * (2 ** i) for i in range(16)) if value <= len(reader.rows)]:
        result = run_subprocess(["--batch", str(selected_batch), "--workers", "0", "--reader-block", str(block), "--prefetch", "1", "--reader-only"])
        result.update({"stage": "reader_block", "configuration": block})
        reader_rows.append(result); rows.append(result)
    selected_block = int(select_smallest_near_best(reader_rows)["configuration"])

    max_workers = max(1, int(env["cpu_physical_cores"]) - 2)
    worker_candidates = [0] + [value for value in power_ladder(max_workers) if value <= max_workers]
    if max_workers not in worker_candidates:
        worker_candidates.append(max_workers)
    worker_rows = []
    for workers in worker_candidates:
        result = run_subprocess(["--batch", str(selected_batch), "--workers", str(workers), "--reader-block", str(selected_block), "--prefetch", "1", "--reader-only"])
        result.update({"stage": "workers", "configuration": workers})
        worker_rows.append(result); rows.append(result)
    selected_workers = int(select_smallest_near_best(worker_rows)["configuration"])

    chunk_count = math.ceil(len(reader.rows) / selected_block)
    prefetch_rows = []
    for prefetch in power_ladder(chunk_count):
        result = run_subprocess(["--batch", str(selected_batch), "--workers", str(selected_workers), "--reader-block", str(selected_block), "--prefetch", str(prefetch), "--reader-only"])
        result.update({"stage": "prefetch", "configuration": prefetch})
        prefetch_rows.append(result); rows.append(result)
    selected_prefetch = int(select_smallest_near_best(prefetch_rows)["configuration"])

    pin_rows = []
    for pin in (False, True):
        args = ["--batch", str(selected_batch), "--workers", str(selected_workers), "--reader-block", str(selected_block), "--prefetch", str(selected_prefetch)]
        if pin: args.append("--pin")
        result = run_subprocess(args)
        result.update({"stage": "pinning", "configuration": int(pin)})
        pin_rows.append(result); rows.append(result)
    selected_pin = bool(select_smallest_near_best(pin_rows)["configuration"])
    final_args = ["--batch", str(selected_batch), "--workers", str(selected_workers), "--reader-block", str(selected_block), "--prefetch", str(selected_prefetch)]
    if selected_pin: final_args.append("--pin")
    final = run_subprocess(final_args)
    final.update({"stage": "final_stability", "configuration": selected_batch})
    rows.append(final)
    if not final["safe"]:
        raise RuntimeError("STOP_F1_PREFLIGHT_RESOURCE_SELECTION_UNRESOLVED")

    csv_path = PACKAGE / "F1_PREFLIGHT_RESOURCE_LADDER.csv"
    compact = []
    for row in rows:
        compact.append({key: row.get(key) for key in ("stage", "configuration", "safe", "median_throughput", "throughput_unit", "batch", "workers", "reader_block", "prefetch", "pin", "peak_rss_bytes", "candidate_start_memavailable_bytes", "swap_before_bytes", "swap_after_bytes", "cuda_peak_allocated_bytes", "cuda_peak_reserved_bytes", "cuda_total_bytes")})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(compact[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(compact)
    selection = {"schema": "f1-preflight-resource-selection-v1", "status": "PASS", "prospective_rule": "smallest safe configuration with median throughput >=95% fastest safe", "selected": {"forward_batch": selected_batch, "reader_block": selected_block, "workers": selected_workers, "prefetch": selected_prefetch, "pinned_memory": selected_pin}, "fixture_membership_root_sha256": reader.fixture["membership_root_sha256"], "historical_batch_constant_used": False, "final_stability": final}
    write_json(PACKAGE / "F1_PREFLIGHT_RESOURCE_SELECTION.json", selection)
    role_rates = {role: final["role_counts"][role] / final["role_seconds_median"][role] for role in final["role_counts"]}
    write_json(PACKAGE / "F1_PREFLIGHT_ROLE_THROUGHPUT.json", {"schema": "f1-preflight-role-throughput-v1", "rates_query_identities_per_second": role_rates, "selected_configuration": selection["selected"]})
    geometry = full_geometry()
    forward_seconds = geometry["teacher_forwards"] / role_rates["teacher"] + geometry["correct_forwards"] / role_rates["correct_student"] + geometry["null_forwards"] / role_rates["matched_null_student"]
    median_rep = sorted(final["repetitions"], key=lambda row: row["throughput"])[1]
    multiplier = geometry["total_expensive_forwards"] / sum(final["role_counts"].values())
    projection = {"schema": "f1-preflight-runtime-projection-v1", "geometry": geometry, "selected_configuration": selection["selected"], "role_rates": role_rates, "T_forward_seconds": forward_seconds, "T_io_seconds": final["reader"]["reader_seconds"] * multiplier, "T_reduce_seconds": median_rep["target_context_reduction_seconds"] * multiplier, "T_commit_seconds": 0.0, "T_finalization_seconds": 0.0}
    projection["T_total_projected_seconds"] = sum(projection[key] for key in ("T_forward_seconds", "T_io_seconds", "T_reduce_seconds", "T_commit_seconds", "T_finalization_seconds"))
    projection["T_total_projected_hours"] = projection["T_total_projected_seconds"] / 3600.0
    write_json(PACKAGE / "F1_PREFLIGHT_RUNTIME_PROJECTION.json", projection)
    return {"status": "PASS_RESOURCE_AND_PARITY", "selection": selection["selected"], "projection_hours": projection["T_total_projected_hours"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("freeze-root")
    candidate_parser = sub.add_parser("candidate")
    candidate_parser.add_argument("--batch", type=int, required=True)
    candidate_parser.add_argument("--workers", type=int, required=True)
    candidate_parser.add_argument("--reader-block", type=int, required=True)
    candidate_parser.add_argument("--prefetch", type=int, required=True)
    candidate_parser.add_argument("--pin", action="store_true")
    candidate_parser.add_argument("--reader-only", action="store_true")
    sub.add_parser("parity")
    sub.add_parser("orchestrate")
    args = parser.parse_args()
    if args.command == "freeze-root": result = freeze_forward_root()
    elif args.command == "candidate": result = candidate(args.batch, args.workers, args.reader_block, args.prefetch, args.pin, args.reader_only)
    elif args.command == "parity": result = parity()
    else: result = orchestrate()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
