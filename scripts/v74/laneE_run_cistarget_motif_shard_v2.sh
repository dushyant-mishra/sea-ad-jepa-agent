#!/usr/bin/env bash
# V74 LANE E: successor to scripts/v69/run_cistarget_motif_shard_v1.sh.
#
# WHAT CHANGED AND WHY
# --------------------
# v1 records wall_clock_seconds with no record of what else was running. A timing field
# whose value silently depends on the rest of the machine reads as a measurement but is
# not one -- the same class of defect as a provenance record describing an execution
# that did not happen. The 512-motif pilot was first read as a shard-size effect for
# exactly this reason.
#
# v2 makes the machine condition a MEASURED FIELD of the shard receipt, against
# thresholds passed in as ARGUMENTS so they must be fixed before the run.
#
# WHICH INSTRUMENT, AND WHY NOT THE OBVIOUS ONE
# ---------------------------------------------
# Windows `Win32_Processor.LoadPercentage` is NOT usable as a contention test on this
# machine, and the calibration is recorded here because a plausible-looking statistic
# built on it produced a false contention finding.
#
#   Measured with ONLY this lane's container running and every other lane held:
#     LoadPercentage 77-96 (median ~87), container CPUPerc ~750% with NCPU=16.
#     Container share of the host = 750/16 = ~47 points.
#     "Unexplained" = 87 - 47 = ~40 points -- ON A VERIFIABLY QUIET MACHINE.
#
# The host has 8 physical cores and 16 logical processors. Eight single-threaded
# workers get spread across the logical processors, so Windows counts far more than
# eight of them as non-idle, and LoadPercentage runs well above the container's actual
# share. The "unexplained points" statistic therefore has a large positive offset at
# zero contention and cannot distinguish a quiet machine from a busy one.
#
# v2 tests contention with instruments that are calibrated:
#
#   C1  OTHER CONTAINERS. docker ps, sampled throughout. Binary and reliable. A
#       sibling lane running a container is the dominant contention mode here.
#   C2  CONTAINER CPU SHARE. The share this container actually achieves, compared with
#       the share it achieves when alone. This uses only docker's own accounting and
#       needs no host-load reading at all. The quiet-machine reference is MEASURED on
#       a held-quiet run and passed in, not assumed.
#   C3  NON-DOCKER HOST CPU WORK. The increase in cumulative CPU-seconds across all
#       host processes that are not Docker, over the run, as a fraction of machine
#       capacity (wall x logical_processors). This catches a sibling lane doing work
#       outside a container -- pytest, merges, git.
#
# LoadPercentage is still recorded, explicitly labelled as context and not as a test.
#
# The shard's PASS/FAIL status depends only on shard completeness and motif-axis
# correctness. Outputs are deterministic and digest-identical regardless of load, so a
# contended run still produces a VALID shard whose TIMING is not a clean measurement.
# Those are separate claims and v2 keeps them separate.
#
# The scoring command is unchanged: it invokes the v1 shard driver inside the container.
#
# Usage (from the HOST):
#   laneE_run_cistarget_motif_shard_v2.sh <shard_id> <frozen_list> <start> <count> \
#        <fasta> <out_dir_name> <threads> <min_median_container_cpu_pct> \
#        <max_nondocker_cpu_fraction>
set -uo pipefail

SHARD_ID="${1:?shard id}"
FROZEN_LIST="${2:?frozen motif list (container path)}"
START="${3:?1-based start}"
COUNT="${4:?count}"
FASTA="${5:?region fasta (container path)}"
OUT_NAME="${6:?output dir NAME under the scratch root}"
THREADS="${7:-8}"
MIN_MEDIAN_CONTAINER_CPU="${8:?declare BEFORE the run: minimum median container CPUPerc}"
MAX_NONDOCKER_FRACTION="${9:?declare BEFORE the run: max non-Docker CPU fraction}"

SCRATCH=C:/jepa_scratch/v74_laneE
OUT_HOST="$SCRATCH/$OUT_NAME"
IMG=scenicplus:1.0a2-container.1
LOGDIR="$SCRATCH/logs"
SAMPLE="$LOGDIR/$SHARD_ID.resource_samples.jsonl"
BASELINE="$LOGDIR/$SHARD_ID.idle_baseline.jsonl"
DRIVERLOG="$LOGDIR/$SHARD_ID.driver.log"
LOGICAL_PROCESSORS=16
mkdir -p "$OUT_HOST" "$LOGDIR"

nondocker_cpu_seconds() {
  powershell -NoProfile -Command "
    \$p = Get-Process -ErrorAction SilentlyContinue |
          Where-Object { \$_.ProcessName -notmatch '(?i)docker|vmmem|wsl|vmwp' }
    [math]::Round((\$p | Measure-Object -Property CPU -Sum).Sum, 2)" 2>/dev/null | tr -d '\r'
}

{
  echo "### V74 LANE E shard driver v2"
  echo "### THRESHOLDS DECLARED BEFORE THE RUN (passed as arguments):"
  echo "###   min_median_container_cpu_pct = $MIN_MEDIAN_CONTAINER_CPU"
  echo "###   max_nondocker_cpu_fraction   = $MAX_NONDOCKER_FRACTION"
  sha256sum "$0" 2>/dev/null || true
  echo "### $SHARD_ID start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "### containers running before launch:"
  docker ps --format '{{.Names}}' | sed 's/^/###   /'
} > "$DRIVERLOG"

# ---- idle baseline: one minute before anything of ours starts ---------------------
: > "$BASELINE"
for _ in $(seq 1 12); do
  L=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average" 2>/dev/null | tr -d '\r')
  printf '{"utc":"%s","host_cpu_load_pct":"%s","nondocker_cpu_seconds":"%s","containers":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${L:-NA}" "$(nondocker_cpu_seconds)" \
    "$(docker ps --format '{{.Names}}' 2>/dev/null | tr '\n' ',')" >> "$BASELINE"
  sleep 5
done
echo "### idle baseline captured, $(wc -l < "$BASELINE") samples" >> "$DRIVERLOG"

START_EPOCH=$(date -u +%s)

# ---- sampler ----------------------------------------------------------------------
: > "$SAMPLE"
(
  while true; do
    TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    S=$(docker stats --no-stream --format '{{.CPUPerc}}|{{.MemUsage}}' "$SHARD_ID" 2>/dev/null || echo "NA|NA")
    L=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average" 2>/dev/null | tr -d '\r')
    OTHERS=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -v "^$SHARD_ID$" | tr '\n' ',')
    printf '{"utc":"%s","container_cpu_pct":"%s","container_mem":"%s","host_cpu_load_pct":"%s","nondocker_cpu_seconds":"%s","other_containers":"%s"}\n' \
      "$TS" "${S%%|*}" "${S##*|}" "${L:-NA}" "$(nondocker_cpu_seconds)" "$OTHERS" >> "$SAMPLE"
    sleep 30
  done
) &
SAMPLER=$!
trap 'kill $SAMPLER 2>/dev/null || true' EXIT

MSYS_NO_PATHCONV=1 docker run --rm --name "$SHARD_ID" \
  -v "D:/jepa_v5_outputs_20260925/v69_scenicplus:/data:ro" \
  -v "$SCRATCH:/scratch" \
  "$IMG" bash /scratch/shared/immutable_scripts/run_cistarget_motif_shard_v1.sh \
    "$SHARD_ID" "$FROZEN_LIST" "$START" "$COUNT" "$FASTA" \
    "/scratch/$OUT_NAME" "$THREADS" >> "$DRIVERLOG" 2>&1
RC=$?
kill $SAMPLER 2>/dev/null || true
END_EPOCH=$(date -u +%s)
echo "### $SHARD_ID docker exit=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DRIVERLOG"

python - "$OUT_HOST/$SHARD_ID.shard.json" "$SAMPLE" "$BASELINE" \
         "$MIN_MEDIAN_CONTAINER_CPU" "$MAX_NONDOCKER_FRACTION" \
         "$LOGICAL_PROCESSORS" "$((END_EPOCH-START_EPOCH))" <<'PY'
import json, statistics, sys
from pathlib import Path

(receipt, sample, baseline, min_med_cpu, max_nd_frac,
 logical, elapsed) = sys.argv[1:8]
min_med_cpu, max_nd_frac = float(min_med_cpu), float(max_nd_frac)
logical, elapsed = int(logical), int(elapsed)


def load(p):
    rows = []
    for ln in Path(p).read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return rows


def num(v):
    try:
        return float(str(v).rstrip("%"))
    except (TypeError, ValueError):
        return None


def pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    return round(s[min(len(s) - 1, int(q * len(s)))], 1)


base_rows = load(baseline)
base_load = [x for x in (num(r.get("host_cpu_load_pct")) for r in base_rows) if x is not None]
base_nd = [x for x in (num(r.get("nondocker_cpu_seconds")) for r in base_rows) if x is not None]

rows = load(sample)
ccpu, hload, nd, mem, others = [], [], [], [], set()
for r in rows:
    c = num(r.get("container_cpu_pct"))
    if c is not None:
        ccpu.append(c)
    h = num(r.get("host_cpu_load_pct"))
    if h is not None:
        hload.append(h)
    n = num(r.get("nondocker_cpu_seconds"))
    if n is not None:
        nd.append(n)
    m = r.get("container_mem", "")
    if "MiB /" in m:
        mem.append(float(m.split("MiB")[0]))
    elif "GiB /" in m:
        mem.append(float(m.split("GiB")[0]) * 1024)
    o = (r.get("other_containers") or "").strip(",")
    if o:
        others.update(x for x in o.split(",") if x)

# C3: non-Docker CPU work over the run, as a fraction of machine capacity.
nd_delta = (max(nd) - min(nd)) if len(nd) >= 2 else None
capacity = elapsed * logical
nd_fraction = (round(nd_delta / capacity, 5)
               if (nd_delta is not None and capacity > 0) else None)

med_ccpu = round(statistics.median(ccpu), 1) if ccpu else None

c1 = (len(others) == 0)
c2 = (med_ccpu is not None and med_ccpu >= min_med_cpu)
c3 = (nd_fraction is not None and nd_fraction <= max_nd_frac)
met = bool(c1 and c2 and c3)

cond = {
    "THRESHOLDS_DECLARED_BEFORE_THE_RUN": {
        "min_median_container_cpu_pct": min_med_cpu,
        "max_nondocker_cpu_fraction_of_machine_capacity": max_nd_frac,
        "no_other_containers": True,
        "declared_how": ("Passed as command-line arguments and echoed into the driver "
                         "log before the run started, so they could not be chosen "
                         "after seeing the distribution."),
    },
    "INSTRUMENT_CALIBRATION": {
        "win32_LoadPercentage_is_NOT_used_as_the_test": True,
        "why": ("On this machine, with 8 physical cores, 16 logical processors and "
                "every other lane held, LoadPercentage read 77-96 while the container "
                "held ~750% CPUPerc, i.e. ~47 of 16 logical-processor points. The "
                "'unexplained load' that statistic implies is ~40 points AT ZERO "
                "CONTENTION, because eight single-threaded workers are spread across "
                "sixteen logical processors and Windows counts far more than eight as "
                "non-idle. A contention test built on it fires on a quiet machine."),
        "what_is_used_instead": [
            "C1 other containers (docker ps, sampled)",
            "C2 container CPU share against a MEASURED quiet-machine reference",
            "C3 non-Docker host CPU-seconds consumed over the run",
        ],
    },
    "C1_other_containers": {"other_containers_seen": sorted(others), "pass": c1},
    "C2_container_cpu_share": {
        "median_container_cpu_pct": med_ccpu,
        "p10_container_cpu_pct": pct(ccpu, 0.10),
        "max_container_cpu_pct": max(ccpu) if ccpu else None,
        "threshold": min_med_cpu,
        "pass": c2,
    },
    "C3_nondocker_host_cpu": {
        "nondocker_cpu_seconds_delta": nd_delta,
        "run_seconds": elapsed,
        "machine_capacity_cpu_seconds": capacity,
        "fraction_of_capacity": nd_fraction,
        "threshold": max_nd_frac,
        "pass": c3,
        "limitation": ("Processes that both start and exit between two samples are not "
                       "counted. The measure is a lower bound on competing non-Docker "
                       "work, so it can under-report contention; it is paired with C1 "
                       "and C2 for that reason."),
    },
    "context_not_a_test": {
        "host_cpu_load_pct_median": round(statistics.median(hload), 1) if hload else None,
        "host_cpu_load_pct_max": max(hload) if hload else None,
        "idle_baseline_before_launch": {
            "n_samples": len(base_rows),
            "host_cpu_load_pct_median": (round(statistics.median(base_load), 1)
                                         if base_load else None),
            "host_cpu_load_pct_max": max(base_load) if base_load else None,
            "nondocker_cpu_seconds_delta_over_the_baseline_minute": (
                round(max(base_nd) - min(base_nd), 2) if len(base_nd) >= 2 else None),
            "containers_running": sorted({
                x for r in base_rows for x in (r.get("containers") or "").strip(",").split(",") if x}),
        },
    },
    "container_peak_mem_mib": round(max(mem), 1) if mem else None,
    "peak_memory_is_SAMPLED_not_a_high_water_mark": True,
    "n_samples": len(rows),
    "QUIET_MACHINE_CONDITION_MET": met,
    "timing_measurement_class": (
        "CLEAN__QUIET_MACHINE" if met
        else "NOT_A_CLEAN_MEASUREMENT__CONTENDED__TIMING_IS_AN_UPPER_BOUND_ONLY"),
    "what_the_class_does_and_does_not_affect": (
        "It governs the TIMING fields only. Outputs are deterministic and "
        "digest-identical regardless of machine load, so a contended run still yields a "
        "valid shard. Validity of the data and validity of the timing are separate "
        "claims, reported separately."),
    "self_measurement_bias_disclosed": (
        "The sampler costs CPU -- one docker stats call, one CIM query, one docker ps "
        "and one Get-Process sweep per sample -- and that cost lands in C3, so C3 is "
        "biased toward reporting MORE competing work than there is. The bias makes the "
        "test conservative, not permissive."),
}

p = Path(receipt)
if not p.exists():
    print(json.dumps({"status": "FAIL__NO_SHARD_RECEIPT_TO_AUGMENT",
                      "expected": str(p)}, indent=2))
    sys.exit(4)
rec = json.loads(p.read_text(encoding="utf-8"))
rec["machine_condition"] = cond
with open(p, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(rec, fh, indent=2)
    fh.write("\n")
back = json.loads(p.read_text(encoding="utf-8"))
mc = back["machine_condition"]
print(json.dumps({"shard_status": back.get("status"),
                  "wall_clock_seconds": back.get("wall_clock_seconds"),
                  "QUIET_MACHINE_CONDITION_MET": mc["QUIET_MACHINE_CONDITION_MET"],
                  "timing_measurement_class": mc["timing_measurement_class"],
                  "C1": mc["C1_other_containers"],
                  "C2": mc["C2_container_cpu_share"],
                  "C3": mc["C3_nondocker_host_cpu"],
                  "context_not_a_test": mc["context_not_a_test"]}, indent=2))
PY
echo "SHARD_V2_DONE rc=$RC" >> "$DRIVERLOG"
exit $RC
