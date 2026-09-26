"""V40 offline adversaries: injected transport is TEST-ONLY, not remote trust."""
from __future__ import annotations

import base64
import hashlib
import io
import zipfile
import urllib.request
from xml.etree import ElementTree as ET

import pytest

from scripts.agent.verify_remote_critical_junit_v40 import (
    API, EXPECTED_ARTIFACT, EXPECTED_JOB, EXPECTED_SOURCE, EXPECTED_WORKFLOW,
    REQUIRED_NAMES, RemoteEvidenceError, checked_payload, git_blob_sha,
    _SignedArchiveRedirect,
)

RUN = 123456
HEAD = "a" * 40
SOURCE_BYTES = b"# unit fixture source; not independently reviewed\\n" * 6


def make_archive(xml: bytes) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("v40-junit.xml", xml)
    return output.getvalue()


def junit(*, names=sorted(REQUIRED_NAMES), skipped=0):
    suite = ET.Element("testsuite", tests=str(len(names)), errors="0", failures="0",
                       skipped=str(skipped))
    for name in names:
        ET.SubElement(suite, "testcase",
                      classname="test_v39_critical_evidence_physical_provenance",
                      name=name)
    return ET.tostring(ET.Element("testsuites", **{}) ) if False else (
        ET.tostring(suite))


class StubGithub:
    def __init__(self):
        self.archive = make_archive(junit())
        self.run = {"id": RUN, "head_repository": {"full_name": "dushyant-mishra/sea-ad-jepa-agent"},
                    "head_sha": HEAD, "event": "pull_request", "workflow_id": 741}
        self.workflow = {"path": EXPECTED_WORKFLOW}
        self.jobs = {"total_count": 1, "jobs": [{
            "id": 333, "name": EXPECTED_JOB, "conclusion": "success", "status": "completed",
            "run_id": RUN, "head_sha": HEAD, "steps": [{"name": "Run tests",
                                                       "conclusion": "success"}],
        }]}
        self.artifacts = {"total_count": 1, "artifacts": [{
            "id": 444, "name": EXPECTED_ARTIFACT, "expired": False,
            "digest": "sha256:" + hashlib.sha256(self.archive).hexdigest(),
            "workflow_run": {"id": RUN},
        }]}
        self.source = {"path": EXPECTED_SOURCE, "sha": git_blob_sha(SOURCE_BYTES),
                       "encoding": "base64", "content": base64.b64encode(SOURCE_BYTES).decode()}

    def read(self, url, *, binary=False):
        if binary:
            assert url == f"{API}/actions/artifacts/444/zip"
            return self.archive
        if url == f"{API}/actions/runs/{RUN}":
            return self.run
        if url == f"{API}/actions/workflows/741":
            return self.workflow
        if url == f"{API}/actions/runs/{RUN}/jobs?per_page=100":
            return self.jobs
        if url == f"{API}/actions/runs/{RUN}/artifacts?per_page=100":
            return self.artifacts
        if url == f"{API}/contents/{EXPECTED_SOURCE}?ref={HEAD}":
            return self.source
        raise AssertionError(f"unknown URL {url}")


def verify(fake):
    return checked_payload(fake, run_id=RUN, expected_sha=HEAD)


def test_valid_test_only_fake_transport_exercises_complete_parser():
    report = verify(StubGithub())
    assert report["tests"] == 7 and report["training_authorized"] is False
    assert report["remote_run_job_artifact_metadata_and_source_verified"] is True  # test transport only!
    assert report["remote_archive_byte_digest_replayed"] is True


def test_run_sha_substitution_fails():
    fake = StubGithub()
    fake.run["head_sha"] = "b" * 40
    with pytest.raises(RemoteEvidenceError, match="head SHA mismatch"):
        verify(fake)


def test_wrong_workflow_fails():
    fake = StubGithub()
    fake.workflow["path"] = ".github/workflows/untrusted.yml"
    with pytest.raises(RemoteEvidenceError, match="workflow path"):
        verify(fake)


def test_nonpassing_job_fails():
    fake = StubGithub()
    fake.jobs["jobs"][0]["conclusion"] = "failure"
    with pytest.raises(RemoteEvidenceError, match="successful producing job"):
        verify(fake)


def test_artifact_replay_from_other_run_fails():
    fake = StubGithub()
    fake.artifacts["artifacts"][0]["workflow_run"]["id"] = 1
    with pytest.raises(RemoteEvidenceError, match="different workflow run"):
        verify(fake)


def test_missing_or_duplicated_test_id_fails():
    fake = StubGithub()
    ids = sorted(REQUIRED_NAMES)
    ids[-1] = ids[0]
    fake.archive = make_archive(junit(names=ids))
    fake.artifacts["artifacts"][0]["digest"] = "sha256:" + hashlib.sha256(fake.archive).hexdigest()
    with pytest.raises(RemoteEvidenceError, match="test identities"):
        verify(fake)


def test_xml_claiming_skips_fails():
    fake = StubGithub()
    fake.archive = make_archive(junit(skipped=1))
    fake.artifacts["artifacts"][0]["digest"] = "sha256:" + hashlib.sha256(fake.archive).hexdigest()
    with pytest.raises(RemoteEvidenceError, match="JUnit count mismatch"):
        verify(fake)


def test_source_bytes_differ_from_git_blob_fails():
    fake = StubGithub()
    fake.source["sha"] = "0" * 40
    with pytest.raises(RemoteEvidenceError, match="Git blob identity"):
        verify(fake)


def test_job_pagination_truncation_fails():
    fake = StubGithub()
    fake.jobs["total_count"] = 120
    with pytest.raises(RemoteEvidenceError, match="pagination"):
        verify(fake)


def test_xml_extra_member_archive_fails():
    fake = StubGithub()
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w") as z:
        z.writestr("v40-junit.xml", junit())
        z.writestr("attacker.xml", junit())
    fake.archive = buff.getvalue()
    fake.artifacts["artifacts"][0]["digest"] = "sha256:" + hashlib.sha256(fake.archive).hexdigest()
    with pytest.raises(RemoteEvidenceError, match="exactly one"):
        verify(fake)

def test_signed_archive_redirect_strips_github_bearer():
    url = "https://productionresults01.blob.core.windows.net/short-lived?sig=fake"
    initial = urllib.request.Request(
        f"{API}/actions/artifacts/444/zip",
        headers={"Authorization": "Bearer SECRET", "User-Agent": "audit"},
    )
    redirected = _SignedArchiveRedirect().redirect_request(
        initial, None, 302, "redirect", {}, url
    )
    assert redirected.full_url == url
    assert all(key.lower() != "authorization" for key, _ in redirected.header_items())


def test_arbitrary_archive_redirect_host_is_rejected():
    initial = urllib.request.Request(
        f"{API}/actions/artifacts/444/zip", headers={"Authorization": "Bearer SECRET"}
    )
    with pytest.raises(RemoteEvidenceError, match="untrusted archive host"):
        _SignedArchiveRedirect().redirect_request(
            initial, None, 302, "redirect", {},
            "https://attacker.example/download?token=stolen",
        )

def test_externally_downloaded_junit_keeps_archive_replay_explicitly_false():
    fake = StubGithub()
    fake.artifacts["artifacts"][0]["digest"] = "sha256:" + "b" * 64
    report = checked_payload(
        fake, run_id=RUN, expected_sha=HEAD,
        downloaded_junit=junit(),
    )
    assert report["remote_archive_byte_digest_replayed"] is False
    assert "EXPERIMENTAL" in report["junit_delivery"]


def test_invalid_rest_artifact_digest_fails_even_with_downloaded_junit():
    fake = StubGithub()
    fake.artifacts["artifacts"][0]["digest"] = "unverified"
    with pytest.raises(RemoteEvidenceError, match="digest malformed"):
        checked_payload(fake, run_id=RUN, expected_sha=HEAD,
                        downloaded_junit=junit())

def test_remote_zip_bytes_not_accepted_without_matching_github_digest():
    fake = StubGithub()
    fake.artifacts["artifacts"][0]["digest"] = "sha256:" + "0" * 64
    with pytest.raises(RemoteEvidenceError, match="ZIP does not match"):
        verify(fake)
