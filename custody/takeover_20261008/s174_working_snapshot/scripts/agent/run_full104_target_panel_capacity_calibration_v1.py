#!/usr/bin/env python3
"""Tombstone for the superseded direct-stream target-panel calibration driver.

The direct implementation would rescan all 8,915 FULL104 Level-4 blocks for
every calibration target/fold.  It is intentionally disabled before any
terminal or control outcome was opened.  Use the authenticated calibration-only
cache builder followed by the offline evaluator instead.
"""

raise SystemExit(
    "SUPERSEDED_FAIL_CLOSED: direct-stream target-panel calibration is disabled. "
    "Use scripts/agent/build_full104_control_calibration_cache_v1.py and then "
    "scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py. "
    "The cache is CONTROL_CALIBRATION_ONLY and is forbidden for terminal masking qualification."
)
