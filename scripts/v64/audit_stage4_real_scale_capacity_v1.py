#!/usr/bin/env python3
"""Will the pipeline physically fit at real scale? S97, from my own self-audit lane.

The closeout records real-scale runtime and memory as UNMEASURED. That is honest but it
is also the kind of unknown that turns into a failed overnight run, and the executor
materialises dense metacell-by-feature matrices and a design tensor whose size nobody has
checked. This computes the footprint from the DECLARED SHAPES of the real substrate -- the
dictionary lengths, the donor count, the T5 row count -- and compares it with the memory
this machine actually has.

It reads shapes, never values: no payload is materialised, no statistic is computed, and
nothing here is a step toward execution. The numbers are arithmetic on sizes, so they are
a calculation and are labelled as one, not as a measured peak.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402

GB = 1024.0 ** 3


def main() -> int:
    # shapes only, read from one shard's dictionaries and the availability header
    p = "D:/jepa_v5_outputs_20260925/v64_phase_b/PHASE_B_SUBSTRATE_s00.npz"
    av = "D:/jepa_v5_outputs_20260925/v64_phase_b/PHASE_B_T3_T4_AVAILABILITY.npz"
    with np.load(p, allow_pickle=True) as d:
        n_g = int(len(d["genes"]))
        n_iv = int(len(d["interval_start"]))
        n_pairs = int(len(d["pair_keys"]))
    with np.load(av, allow_pickle=True) as a:
        n_mc = int(a["t3_shape"][0])
    n_donors = 282
    n_cells = n_donors * n_pairs

    items = [
        ("dense RNA  [metacell x gene]", n_mc * n_g * 4),
        ("dense ATAC [metacell x interval]", n_mc * n_iv * 4),
        ("RNA availability (unpacked bool)", n_mc * n_g),
        ("ATAC availability (unpacked bool)", n_mc * n_iv),
        ("correlation grid [donor x pair] f8", n_cells * 8),
        ("status grid [donor x pair] i1", n_cells * 1),
        ("design tensor [donor x pair x 14] f8", n_cells * 14 * 8),
        ("flat design view (reshape, may copy)", n_cells * 14 * 8),
        ("masked design copy X[measured]", n_cells * 14 * 8),
        ("residual vector", n_cells * 8),
        ("ridge fold slices (approx 4/5 of X)", n_cells * 14 * 8 * 0.8),
    ]
    total = sum(v for _, v in items)
    worst = total + max(v for _, v in items)

    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        phys_total, phys_avail = int(m.ullTotalPhys), int(m.ullAvailPhys)
    except Exception:                                                # noqa: BLE001
        phys_total = phys_avail = None

    print("real-scale shapes: %d metacells, %d genes, %d intervals, %d pairs, "
          "%d donors" % (n_mc, n_g, n_iv, n_pairs, n_donors))
    print("                   %s (donor, pair) cells" % format(n_cells, ","))
    print("")
    for name, v in items:
        print("  %-44s %8.3f GB" % (name, v / GB))
    print("  %-44s %8.3f GB" % ("SUM OF LIVE ALLOCATIONS", total / GB))
    print("  %-44s %8.3f GB" % ("PLAUSIBLE PEAK (sum + largest transient)", worst / GB))
    if phys_total:
        print("")
        print("  machine physical memory                      %8.3f GB" % (phys_total / GB))
        print("  available right now                          %8.3f GB" % (phys_avail / GB))

    fits = None if phys_total is None else worst < 0.8 * phys_avail
    findings = []
    dom = max(items, key=lambda kv: kv[1])
    findings.append(
        "The design tensor dominates: %s (donor, pair) cells x 14 terms x 8 bytes is "
        "%.2f GB, and the implementation holds up to three of them live at once -- the "
        "tensor, its flattened view and the boolean-masked copy the ridge is fitted on. "
        "That is %.2f GB of the %.2f GB total before any fold slice is taken."
        % (format(n_cells, ","), n_cells * 14 * 8 / GB, 3 * n_cells * 14 * 8 / GB,
           total / GB))
    if fits is False:
        findings.append(
            "CALCULATED PEAK EXCEEDS 80 PERCENT OF AVAILABLE MEMORY. The pipeline as written "
            "would not be expected to complete at real scale on this machine. The fix is "
            "to build the design in float32 and residualise fold by fold without "
            "materialising a masked copy, which is an implementation change and must be "
            "re-qualified on the synthetic worlds before it is trusted.")
    elif fits is True:
        findings.append(
            "The calculated peak fits within 80 percent of currently available memory, but "
            "this is arithmetic on declared shapes, not a measured peak, and it ignores "
            "allocator fragmentation and whatever else is running. It is a feasibility "
            "indication, not a guarantee.")

    out = dict(
        schema="V64_STAGE4_REAL_SCALE_CAPACITY_V1", date="2026-10-01",
        raises="S97, from my own self-audit lane",
        method="arithmetic on the declared shapes of the real substrate. Shapes were "
               "read from the dictionaries and the availability header; no payload was "
               "materialised and no statistic was computed.",
        this_is_a_calculation_not_a_measured_peak=True,
        shapes=dict(metacells=n_mc, genes=n_g, intervals=n_iv, pairs=n_pairs,
                    donors=n_donors, donor_pair_cells=n_cells),
        allocations_gb={k: round(v / GB, 4) for k, v in items},
        sum_of_live_allocations_gb=round(total / GB, 3),
        plausible_peak_gb=round(worst / GB, 3),
        machine=dict(physical_total_gb=None if phys_total is None
                     else round(phys_total / GB, 3),
                     available_at_probe_gb=None if phys_avail is None
                     else round(phys_avail / GB, 3),
                     measured=phys_total is not None),
        calculated_peak_fits_in_80pct_of_available=fits,
        findings=findings,
        real_substrate_payload_read=False, computed_correspondence_values=0,
        producer_sha256=B.sha_file(os.path.abspath(__file__)))
    pth = "results/v64/phase_b_design/V64_STAGE4_REAL_SCALE_CAPACITY_V1.json"
    with open(pth, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    for f in findings:
        print("* " + f)
    print("")
    print("receipt sha256 " + B.sha_file(pth))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
