#!/usr/bin/env python3
"""V41: independently obtain ORIGINAL V40 GitHub CI metadata + test artifact.

A separate GitHub-hosted reviewer job authenticates the exact source commit,
actual GitHub workflow job/steps, artifact identity+digest and ORIGINAL raw
JUnit bytes. This is evidence that the *synthetic V40 fixture* ran on GitHub,
NOT that current FULL104 critical tests ran, NOR B1/B2 authority.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
import os
import re
import urllib.request
from xml.etree import ElementTree as ET
from zipfile import ZipFile

REPO = "dushyant-mishra/sea-ad-jepa-agent"
RUN_ID = 36252237835
APPROVED_HEAD = "1510b52417704c710ee23b4e60238e65c3acba74"
ARTIFACT_ID = 10909547327
ARTIFACT_NAME = "v40-original-junit-run-evidence"
ARTIFACT_SHA256 = "a0b77345ef65e8b9196fb616488550f0b2cf57aea773dd9d25922a65879266ef"
WORKFLOW_PATH = ".github/workflows/v40-physical-critical-test-preflight.yml"
JOB_NAME = "strict-original-source-and-junit"
REQUIRED = {
    "test_exact_frozen_manifest_real_checkout_and_machine_junit_local_only",
    "test_original_suite_byte_tamper_fails",
    "test_original_runner_byte_tamper_fails",
    "test_forged_self_consistent_manifest_rejected_by_external_anchor",
    "test_replaced_checkout_head_fails_even_same_file_bytes",
    "test_junit_missing_required_test_fails",
    "test_junit_surplus_test_fails",
    "test_junit_duplicate_test_fails_even_when_count_matches",
    "test_junit_hidden_nonpass_fails_even_with_zero_summary[skipped]",
    "test_junit_hidden_nonpass_fails_even_with_zero_summary[failure]",
    "test_junit_hidden_nonpass_fails_even_with_zero_summary[error]",
    "test_junit_fake_summary_count_fails",
    "test_symlinked_suite_source_fails_even_same_bytes",
    "test_path_escape_manifest_rejected_before_source_read",
    "test_duplicate_frozen_required_ids_fail",
    "test_manifest_cannot_claim_training_true",
    "test_junit_doctype_rejected",
}
API_ROOT = f"https://api.github.com/repos/{REPO}"
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    raise SystemExit("STOP_V41_MISSING_AUTHENTICATED_GITHUB_TOKEN")


class RedirectWithoutToken(urllib.request.HTTPRedirectHandler):
    """Never forward the GitHub bearer token to external artifact storage."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        next_request = super().redirect_request(
            request, fp, code, msg, headers, newurl
        )
        if next_request is not None:
            next_request.remove_header("Authorization")
        return next_request


def api(path: str):
    request = urllib.request.Request(
        API_ROOT + path,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.load(response)


def archive(url: str) -> bytes:
    if url != API_ROOT + f"/actions/artifacts/{ARTIFACT_ID}/zip":
        raise ValueError("artifact URL was not exact approved GitHub API location")
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    opener = urllib.request.build_opener(RedirectWithoutToken)
    with opener.open(request, timeout=60) as response:
        return response.read()


def require(condition: bool, message: str):
    if not condition:
        raise ValueError("STOP_V41_" + message)


def main():
    run = api(f"/actions/runs/{RUN_ID}")
    require(run["id"] == RUN_ID, "RUN_ID")
    require(run["head_sha"] == APPROVED_HEAD, "HEAD_SHA")
    require(run["event"] == "pull_request", "EVENT")
    require(run["status"] == "completed" and run["conclusion"] == "success", "RUN_NOT_SUCCESS")
    require(run["run_attempt"] == 1, "UNREVIEWED_RERUN")
    require(run["path"] == WORKFLOW_PATH, "WORKFLOW_PATH")
    require(run["head_repository"]["full_name"] == REPO, "HEAD_REPOSITORY")

    jobs = api(f"/actions/runs/{RUN_ID}/jobs?per_page=100")
    require(jobs["total_count"] == 1 and len(jobs["jobs"]) == 1, "JOB_CARDINALITY")
    job = jobs["jobs"][0]
    require(job["name"] == JOB_NAME, "JOB_IDENTITY")
    require(job["conclusion"] == "success" and job["status"] == "completed", "JOB_NOT_SUCCESS")
    steps = {s["name"]: s for s in job["steps"]}
    for name in (
        "Run V40 preflight and adversaries with exact JUnit outcomes",
        "Preserve original test evidence for separate CI-provider audit",
    ):
        require(name in steps and steps[name]["conclusion"] == "success",
                "REQUIRED_STEP_DID_NOT_RUN")

    arts = api(f"/actions/runs/{RUN_ID}/artifacts?per_page=100")
    require(arts["total_count"] == 1 and len(arts["artifacts"]) == 1,
            "ARTIFACT_CARDINALITY")
    art = arts["artifacts"][0]
    require(art["id"] == ARTIFACT_ID and art["name"] == ARTIFACT_NAME, "ARTIFACT_IDENTITY")
    require(art["expired"] is False and art["size_in_bytes"] > 0, "ARTIFACT_MISSING")
    require(art["workflow_run"]["head_sha"] == APPROVED_HEAD, "ARTIFACT_HEAD")
    require(art["workflow_run"]["id"] == RUN_ID, "ARTIFACT_RUN_ID")
    require(art["digest"] == "sha256:" + ARTIFACT_SHA256, "ARTIFACT_PROVIDER_DIGEST")

    original_zip = archive(art["archive_download_url"])
    require(hashlib.sha256(original_zip).hexdigest() == ARTIFACT_SHA256,
            "DOWNLOADED_ARCHIVE_SHA256")
    with ZipFile(BytesIO(original_zip)) as bundle:
        names = bundle.namelist()
        require(len(names) == 2 and set(names) == {"v40.xml", "v40.log"},
                "ARTIFACT_CONTENT_PATHS")
        require(all(not n.startswith("/") and ".." not in n.split("/")
                    for n in names), "UNSAFE_ARTIFACT_PATH")
        require(bundle.testzip() is None, "ARTIFACT_ZIP_CRC")
        raw_xml = bundle.read("v40.xml")
        raw_log = bundle.read("v40.log").decode("utf-8", errors="strict")
    require(b"<!DOCTYPE" not in raw_xml.upper() and b"<!ENTITY" not in raw_xml.upper(),
            "JUNIT_EXTERNAL_ENTITIES")
    root = ET.fromstring(raw_xml)
    if root.tag == "testsuites":
        require(len(root) == 1, "MULTIPLE_JUNIT_SUITES")
        root = root[0]
    require(root.tag == "testsuite", "JUNIT_ROOT")
    cases = root.findall("testcase")
    require(len(cases) == len(REQUIRED), "JUNIT_TEST_COUNT")
    counts = {key: int(root.attrib.get(key, "-1"))
              for key in ("tests", "errors", "failures", "skipped")}
    require(counts == {"tests": 17, "errors": 0, "failures": 0, "skipped": 0},
            "JUNIT_NONPASS_OR_FALSE_COUNT")
    actual = [case.attrib.get("name") for case in cases]
    require(len(set(actual)) == 17 and set(actual) == REQUIRED,
            "JUNIT_TEST_IDENTITY")
    # Pytest's original JUnit names modules with the package prefix
    # "tests.". Reject any OTHER class path; the first V41 run physically
    # confirmed the too-narrow unqualified equality was a false reject.
    allowed_classes = {
        "tests.test_v40_critical_test_physical_preflight_research",
        "test_v40_critical_test_physical_preflight_research",
    }
    require(
        all(
            not list(case) and
            case.attrib.get("classname") in allowed_classes
            for case in cases
        ),
        "JUNIT_HIDDEN_NONPASS_OR_CLASS:" +
        ",".join(sorted({str(case.attrib.get("classname")) for case in cases})),
    )
    require("V40_PHYSICAL_LOCAL_PARITY_PASS_EXTERNAL_CI_AUTHORITY_FALSE" in raw_log,
            "POSITIVE_LOCAL_NEGATIVE_EXTERNAL_MARKER")
    require(re.search(r"\b17 passed in [0-9.]+s\b", raw_log) is not None,
            "ACTUAL_TEST_RUNNER_PASS_COUNT")

    print(json.dumps({
        "scope": "V40_SYNTHETIC_ONLY_ORIGINAL_GITHUB_CI_PROVIDER_REPLAY",
        "run_id": RUN_ID, "approved_head_sha": APPROVED_HEAD,
        "original_git_provider_job_id": job["id"],
        "original_artifact_id": ARTIFACT_ID,
        "original_artifact_sha256": ARTIFACT_SHA256,
        "original_junit_sha256": hashlib.sha256(raw_xml).hexdigest(),
        "original_junit_exact_pass": len(REQUIRED),
        "github_run_and_artifact_authenticated_for_this_synthetic_scope": True,
        "actual_full_v5_critical_suite_qualified": False,
        "frozen_current_v5_test_policy_approved": False,
        "full104_training_authorized": False,
        "protected_confirmation_accessed": False,
    }, sort_keys=True, indent=2))
    print("V41_ORIGINAL_PROVIDER_RUN_AND_17_EXACT_JUNIT_ARTIFACTS_VERIFIED__NOT_B2")


if __name__ == "__main__":
    main()
