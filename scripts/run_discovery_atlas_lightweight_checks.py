from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


COMPILE_TARGETS = [
    "discovery_atlas/audit_discovery_atlas_final_state.py",
    "discovery_atlas/internal_robustness_stability_v1.py",
    "discovery_atlas/build_internal_evidence_scorecard_v1.py",
    "discovery_atlas/ablation_artifact_readiness_v1.py",
    "open_validation/align_to_graph_jepa.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run lightweight local checks for the Discovery Atlas."
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_atlas_lightweight_checks.md"),
    )
    return parser.parse_args()


def run_command(name: str, command: list[str]) -> dict[str, object]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    return {
        "name": name,
        "command": " ".join(command),
        "return_code": result.returncode,
        "status": "pass" if result.returncode == 0 else "fail",
        "stdout_tail": result.stdout[-2000:].strip(),
        "stderr_tail": result.stderr[-2000:].strip(),
    }


def main() -> None:
    args = parse_args()
    checks: list[dict[str, object]] = []
    for target in COMPILE_TARGETS:
        checks.append(
            run_command(
                f"compile::{target}",
                [sys.executable, "-m", "py_compile", target],
            )
        )

    checks.append(
        run_command(
            "final_state_audit",
            [
                sys.executable,
                "discovery_atlas/audit_discovery_atlas_final_state.py",
            ],
        )
    )
    discovery_test_code = (
        "import tests.test_discovery_atlas_logic as t; "
        "tests=[getattr(t,n) for n in sorted(dir(t)) "
        "if n.startswith('test_') and callable(getattr(t,n))]; "
        "[test() for test in tests]; "
        "print(f'{len(tests)} discovery logic tests passed')"
    )
    checks.append(
        run_command(
            "discovery_logic_direct_tests",
            [sys.executable, "-c", discovery_test_code],
        )
    )
    checks.append(
        run_command(
            "open_validation_alignment_direct_tests",
            [sys.executable, "tests/test_open_validation_alignment.py"],
        )
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    counts = {
        status: sum(check["status"] == status for check in checks)
        for status in ["pass", "fail"]
    }
    lines = [
        "# Discovery Atlas Lightweight Checks",
        "",
        "## Summary",
        "",
        f"- Pass: {counts['pass']}",
        f"- Fail: {counts['fail']}",
        "- Heavy model inference: not run",
        "- Baseline and manifold audit outputs: not regenerated",
        "- Discovery logic tests: imported and called by function name",
        "- Open-validation alignment tests: direct synthetic runner",
        "",
        "## Checks",
        "",
        "| check | status | return_code | command |",
        "| --- | --- | --- | --- |",
    ]
    for check in checks:
        lines.append(
            "| {name} | {status} | {return_code} | `{command}` |".format(
                **check
            )
        )
    lines.extend(["", "## Output tails", ""])
    for check in checks:
        lines.extend(
            [
                f"### {check['name']}",
                "",
                f"- Status: `{check['status']}`",
                f"- Return code: `{check['return_code']}`",
                "",
                "Stdout tail:",
                "",
                "```text",
                str(check["stdout_tail"]) or "(empty)",
                "```",
                "",
                "Stderr tail:",
                "",
                "```text",
                str(check["stderr_tail"]) or "(empty)",
                "```",
                "",
            ]
        )
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"pass={counts['pass']} fail={counts['fail']}")
    print(f"Wrote {args.report}")
    if counts["fail"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
