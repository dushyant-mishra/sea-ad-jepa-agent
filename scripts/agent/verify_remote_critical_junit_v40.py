#!/usr/bin/env python3
"""V40 experimental read-only GitHub-hosted JUnit provenance verifier.

Separately fetch run/job/artifact and exact source bytes from GitHub's API.
This is NOT the production critical-test authority, and same-workflow
attestation is not an independent governance approval. No protected data.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile

REPO = "dushyant-mishra/sea-ad-jepa-agent"
API = "https://api.github.com/repos/" + REPO
SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_XML_BYTES = 2 * 1024 * 1024
EXPECTED_WORKFLOW = ".github/workflows/v40-remote-critical-provenance.yml"
EXPECTED_JOB = "produce-seven-exact-tests"
EXPECTED_SOURCE = "tests/test_v39_critical_evidence_physical_provenance.py"
EXPECTED_ARTIFACT = "v40-critical-junit"
REQUIRED_NAMES = frozenset({
    "test_phantom_typed_critical_test_claim_is_locally_accepted",
    "test_caller_selects_required_test_vocabulary_without_independent_manifest",
    "test_source_sha_is_accepted_without_reading_any_original_source",
    "test_closure_digest_helper_accepts_duck_typed_unverified_critical_object",
    "test_nonpassing_status_still_fails_as_intended",
    "test_missing_test_status_still_fails_as_intended",
    "test_malformed_source_hash_still_fails_as_intended",
})


class RemoteEvidenceError(ValueError):
    pass


def fail(message: str) -> None:
    raise RemoteEvidenceError("STOP_V40_REMOTE_EVIDENCE: " + message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class _SignedArchiveRedirect(urllib.request.HTTPRedirectHandler):
    """Follow a GitHub artifact 302 without leaking its API bearer token.

    GitHub's archive API returns a short-lived signed Azure archive URL.
    Forwarding the GitHub Authorization header to Azure produces HTTP 401
    and is a credential-leak hazard. Never redirect to arbitrary domains.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        hostname = (target.hostname or "").lower()
        trusted_host = (
            hostname.endswith(".blob.core.windows.net")
            or hostname.endswith(".actions.githubusercontent.com")
            or hostname.endswith(".githubusercontent.com")
        )
        if target.scheme != "https" or not trusted_host:
            fail("GitHub artifact redirected to an untrusted archive host")
        safe_headers = {
            key: value for key, value in req.header_items()
            if key.lower() not in ("authorization", "cookie", "proxy-authorization")
        }
        return urllib.request.Request(newurl, headers=safe_headers, method=req.get_method())


class GithubTransport:
    def __init__(self, token: str | None):
        self.token = token

    def read(self, url: str, *, binary: bool = False):
        if not url.startswith(API + "/"):
            fail("non-allowlisted GitHub API request")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "jepa-v40-readonly-provenance",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        opener = (urllib.request.build_opener(_SignedArchiveRedirect()) if binary
                  else urllib.request.build_opener())
        with opener.open(urllib.request.Request(url, headers=headers), timeout=30) as response:
            # Only GitHub's documented artifact-archive endpoint may redirect
            # to the signed archive host. It must never supply API JSON.
            final = response.url
            if binary:
                if not (final.startswith("https://") and urlsplit(final).hostname and
                        urlsplit(final).hostname.endswith((".blob.core.windows.net", ".actions.githubusercontent.com", ".githubusercontent.com"))):
                    fail("artifact did not resolve to trusted signed archive host")
                if "/actions/artifacts/" not in url or not url.endswith("/zip"):
                    fail("binary request must use GitHub artifact archive endpoint")
                value = response.read(MAX_ARTIFACT_BYTES + 1)
                if len(value) > MAX_ARTIFACT_BYTES:
                    fail("artifact zip exceeds byte limit")
                return value
            if not final.startswith(API + "/"):
                fail("API JSON unexpectedly redirected off GitHub")
            value = response.read(2 * 1024 * 1024 + 1)
            if len(value) > 2 * 1024 * 1024:
                fail("API JSON exceeds byte limit")
            return json.loads(value)


def checked_payload(transport, *, run_id: int, expected_sha: str,
                    downloaded_junit: bytes | None = None):
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id < 1:
        fail("invalid run ID")
    if not isinstance(expected_sha, str) or not SHA.fullmatch(expected_sha):
        fail("expected commit must be an exact 40-char SHA")
    run = transport.read(f"{API}/actions/runs/{run_id}")
    if run.get("id") != run_id:
        fail("run ID mismatch")
    if run.get("head_repository", {}).get("full_name") != REPO:
        fail("run head repository mismatch")
    if run.get("head_sha") != expected_sha:
        fail("run head SHA mismatch")
    if run.get("event") not in {"pull_request", "push", "workflow_dispatch"}:
        fail("unexpected run trigger")
    if run.get("workflow_id") is None:
        fail("workflow id missing")
    workflow = transport.read(f"{API}/actions/workflows/{run['workflow_id']}")
    if workflow.get("path", "").split("@")[0] != EXPECTED_WORKFLOW:
        fail("workflow path mismatch")

    jobs = transport.read(f"{API}/actions/runs/{run_id}/jobs?per_page=100")
    if jobs.get("total_count", 0) > 100 or len(jobs.get("jobs", [])) != jobs.get("total_count"):
        fail("jobs pagination not exhausted")
    matches = [job for job in jobs["jobs"] if job.get("name") == EXPECTED_JOB]
    if len(matches) != 1 or matches[0].get("conclusion") != "success":
        fail("expected one successful producing job")
    job = matches[0]
    if job.get("run_id") != run_id or job.get("head_sha") not in (None, expected_sha):
        fail("producing job belongs to another run")
    if job.get("status") != "completed" or not job.get("steps"):
        fail("producing job execution steps unavailable")
    # Positive job status is necessary but never enough: inspect original
    # JUnit bytes rather than trusting status strings or log summary counts.
    artifacts = transport.read(f"{API}/actions/runs/{run_id}/artifacts?per_page=100")
    if artifacts.get("total_count", 0) > 100 or len(artifacts.get("artifacts", [])) != artifacts.get("total_count"):
        fail("artifact pagination not exhausted")
    matches = [artifact for artifact in artifacts["artifacts"]
               if artifact.get("name") == EXPECTED_ARTIFACT]
    if len(matches) != 1 or matches[0].get("expired") is not False:
        fail("missing, ambiguous, or expired JUnit artifact")
    artifact = matches[0]
    if artifact.get("workflow_run", {}).get("id") != run_id:
        fail("artifact belongs to a different workflow run")
    artifact_id = artifact.get("id")
    if isinstance(artifact_id, bool) or not isinstance(artifact_id, int) or artifact_id < 1:
        fail("invalid artifact ID")
    digest = artifact.get("digest")
    if digest is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        fail("GitHub artifact digest malformed")
    if downloaded_junit is None:
        # Preferred path: independently download the exact GitHub API artifact.
        archive = transport.read(f"{API}/actions/artifacts/{artifact_id}/zip", binary=True)
        if digest is None or digest != "sha256:" + sha256(archive):
            fail("remotely downloaded ZIP does not match GitHub artifact SHA-256")
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            names = z.namelist()
            if names != ["v40-junit.xml"]:
                fail("JUnit archive must have exactly one expected member")
            info = z.getinfo(names[0])
            if info.file_size > MAX_XML_BYTES or info.is_dir() or info.external_attr >> 16 & 0o170000 == 0o120000:
                fail("oversize or unsafe JUnit archive member")
            xml_bytes = z.read(info)
            if len(xml_bytes) > MAX_XML_BYTES:
                fail("decompressed JUnit exceeded limit")
        delivery = "GH_API_SIGNED_ARCHIVE_DIRECT"
    else:
        # Experimental fallback for hosted CI only: official GitHub download
        # action fetched this run's named artifact before this script. This
        # check does NOT cryptographically verify its zip against REST digest.
        if not isinstance(downloaded_junit, bytes) or len(downloaded_junit) > MAX_XML_BYTES:
            fail("externally downloaded JUnit invalid or oversize")
        xml_bytes = downloaded_junit
        delivery = "OFFICIAL_ACTION_DOWNLOAD_EXPERIMENTAL_NO_ZIP_DIGEST_REPLAY"
    try:
        document = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        fail("malformed JUnit XML")
    if document.tag == "testsuites":
        suites = document.findall("testsuite")
        if len(suites) != 1:
            fail("must contain exactly one JUnit testsuite")
        suite = suites[0]
    elif document.tag == "testsuite":
        suite = document
    else:
        fail("unknown JUnit XML root")
    cases = list(suite.iter("testcase"))
    ids = [c.get("name") for c in cases]
    if len(cases) != len(REQUIRED_NAMES) or len(ids) != len(set(ids)) or set(ids) != REQUIRED_NAMES:
        fail("missing, duplicated, or substituted test identities")
    for field, wanted in (("tests", len(REQUIRED_NAMES)), ("errors", 0), ("failures", 0), ("skipped", 0)):
        if int(suite.get(field, -1)) != wanted:
            fail("JUnit count mismatch for " + field)
    if any(c.find("failure") is not None or c.find("error") is not None or
           c.find("skipped") is not None for c in cases):
        fail("JUnit child reports unsuccessful execution")
    if any(not c.get("classname", "").endswith("test_v39_critical_evidence_physical_provenance")
           for c in cases):
        fail("unexpected test module")
    # Verify source bytes at the pinned run head from a SEPARATE GitHub API
    # endpoint, including Git blob identity. This is better than a caller's
    # invented SHA field, but not a frozen independent suite-approval contract.
    src = transport.read(f"{API}/contents/{EXPECTED_SOURCE}?ref={expected_sha}")
    if src.get("path") != EXPECTED_SOURCE or src.get("encoding") != "base64":
        fail("missing GitHub pinned source content")
    source_bytes = base64.b64decode(src.get("content", ""), validate=False)
    if src.get("sha") != git_blob_sha(source_bytes):
        fail("GitHub content bytes disagree with returned Git blob identity")
    if len(source_bytes) < 100:
        fail("source file unexpectedly short")
    return {
        "schema": "JEPA_V40_REMOTE_CRITICAL_JUNIT_PROOF_NONAUTHORIZING",
        "repo": REPO, "run_id": run_id, "head_sha": expected_sha,
        "workflow_path": EXPECTED_WORKFLOW, "producing_job_id": job.get("id"),
        "junit_artifact_id": artifact_id, "junit_xml_sha256": sha256(xml_bytes),
        "test_source_sha256": sha256(source_bytes),
        "test_source_git_blob_sha1": src["sha"],
        "exact_test_ids": sorted(REQUIRED_NAMES), "tests": len(REQUIRED_NAMES),
        "remote_run_job_artifact_metadata_and_source_verified": True,
        "junit_delivery": delivery,
        "remote_archive_byte_digest_replayed": downloaded_junit is None,
        "training_authorized": False,
        "production_critical_test_root_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--receipt-out", type=Path)
    parser.add_argument("--downloaded-junit", type=Path,
                        help="experimental official GitHub download-artifact action path")
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    downloaded = None
    if args.downloaded_junit:
        if os.environ.get("GITHUB_ACTIONS") != "true":
            fail("external artifact fallback is only permitted in hosted GitHub Actions")
        downloaded = args.downloaded_junit.read_bytes()
    report = checked_payload(GithubTransport(token), run_id=args.run_id,
                             expected_sha=args.expected_sha, downloaded_junit=downloaded)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.receipt_out:
        args.receipt_out.write_text(output, encoding="utf-8")
    print(output, end="")
    print("V40_REMOTE_GITHUB_RUN_JOB_JUNIT_SOURCE_VERIFIED__NO_B2")


if __name__ == "__main__":
    main()
