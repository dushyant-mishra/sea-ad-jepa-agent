"""Macha independent review of consolidated main e4925cff (2026-11-02), tests only.

Scope: the repaired standalone V2C verifier and D1 producer as they sit on main,
and the deployment/student_v2c Docker fixture. Synthetic canaries only; no
protected expression, no source rights, no issuer identity, no training.

Naming (a passing run confers NO authority of any kind):
  test_red_*    defects found on main e4925cff; expected to FAIL there.
  test_limit_*  characterizations of limitations that remain; PASS means the
                limitation still holds (they are not acceptance evidence).
  other tests   guards on properties this review demonstrated.

The byte-identical #516/#518 suites carry the original hostile V2C/D1 cases.
This file adds what those suites cannot see on main: the legacy modules are
gone from the tree, a plain same-user launch is still no process boundary,
and the container's protections are launch-time flags, not image properties.

Docker tests need a Linux engine. Without one they skip, unless
MACHA_REQUIRE_DOCKER=1 (CI) turns the skip into a failure.
"""
from __future__ import annotations

import atexit
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

import pytest

from scripts.v5.td_unified import observation_d1_base_only_student_v2c_fixture_v1 as P
from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C

REPO = Path(__file__).resolve().parents[3]
TD = "scripts/v5/td_unified/"
V2C_FILE = REPO / TD / "observation_v2c_standalone_student_gate_v1.py"
DEPLOY = REPO / "deployment" / "student_v2c"
LEGACY = ("observation_normalization_view_v2_bound_content_v1.py",
          "observation_v2b_public_student_gate_v1.py",
          "observation_normalization_view_v2_fixture.py",
          "observation_v2_private_pair_coherence_v1.py",
          "observation_d1_base_only_student_fixture_v1.py")

IMAGE = "jepa-student-v2c-macha-main-review:test"
REFUSAL = b'{"authority_effect":"NONE","status":"REFUSED_STUDENT_V2C_FIXTURE"}\n'
# The README's documented launch, exactly as the author's container tests pass it.
MANDATED = ("--read-only", "--network", "none", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "1",
            "--memory", "256m", "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=8m")
VERIFIER_FILES = ("/opt/student/student_v2c.py", "/opt/student/entrypoint.py",
                  "/opt/student/manifest.json")


def _without(flags, *names):
    out, skip = [], False
    for i, f in enumerate(flags):
        if skip:
            skip = False
            continue
        if f in names:
            skip = i + 1 < len(flags) and not flags[i + 1].startswith("--")
            continue
        out.append(f)
    return out


def _policy():
    return {
        "query_address_id": "MAIN_Q",
        "base_evidence_rights": ["BASE"],
        "address_rights": {"MAIN_A": "BASE", "MAIN_B": "BASE", "MAIN_Q": "QUERY"},
        "operator_states": {"MAIN_OP": {"MAIN_A": C._MS, "MAIN_B": C._SU, "MAIN_Q": C._MS}},
        "cell_roster": [
            {"cell_id": "MAIN_C0", "donor_id": "MAIN_D0", "source_id": "MAIN_S0", "operator_id": "MAIN_OP"},
            {"cell_id": "MAIN_C1", "donor_id": "MAIN_D1", "source_id": "MAIN_S0", "operator_id": "MAIN_OP"},
        ],
    }


def _request():
    view = P.produce_d1_base_only_student_v2c_fixture(
        base_observations=[{"cell_id": "MAIN_C0", "base_counts": {"MAIN_A": 5}},
                           {"cell_id": "MAIN_C1", "base_counts": {"MAIN_A": 3}}],
        expected_policy=_policy())
    return {"student_view": view, "expected_policy": _policy()}


def _git_tree_names():
    try:
        done = subprocess.run(["git", "-C", str(REPO), "ls-tree", "--name-only", "HEAD", TD],
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode:
        return None
    return {Path(p).name for p in done.stdout.split()}


# --------------------------------------------------------------------------
# Main source tree, no Docker
# --------------------------------------------------------------------------

def test_main_tree_excludes_the_legacy_teacher_aware_modules():
    """Checked against the committed tree, so a sparse checkout cannot make it vacuous."""
    names = _git_tree_names()
    if names is None:
        pytest.skip("not a git checkout; the tree check needs git")
    assert "observation_v2c_standalone_student_gate_v1.py" in names  # positive control
    present = sorted(set(LEGACY) & names)
    assert not present, f"legacy teacher-aware modules are back on this tree: {present}"


_LAUNCH = r'''
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("student_only_v2c", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with open(sys.argv[2], encoding="utf8") as handle:
    private = json.load(handle)
print(json.dumps({"verifier_callable": callable(module.validate_student_v2c),
                  "private_query_count_read": private["hidden_q"]}))
'''


def test_limit_a_same_user_launch_of_main_v2c_still_reads_a_teacher_private_file():
    """Without the container there is no OS boundary: removing #502 from the tree removed
    the legacy import side door, not the same-user file-read side door."""
    token = secrets.token_hex(8)
    with tempfile.TemporaryDirectory() as student, tempfile.TemporaryDirectory() as teacher:
        copy = Path(student) / "student_v2c.py"
        copy.write_bytes(V2C_FILE.read_bytes())
        private = Path(teacher) / "teacher_private_hidden_q.json"
        private.write_text(json.dumps({"hidden_q": token}), encoding="utf8")
        done = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", _LAUNCH, str(copy), str(private)],
                              capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr[-800:]
    out = json.loads(done.stdout)
    assert out == {"verifier_callable": True, "private_query_count_read": token}


# --------------------------------------------------------------------------
# deployment/student_v2c on a Linux Docker engine
# --------------------------------------------------------------------------

def _linux_engine():
    if shutil.which("docker") is None:
        return "docker CLI absent"
    try:
        done = subprocess.run(["docker", "info", "--format", "{{.OSType}}"],
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"docker info failed: {type(exc).__name__}"
    if done.returncode or done.stdout.strip() != "linux":
        return f"no Linux engine ({done.stdout.strip() or done.stderr.strip()[:120]})"
    return None


def _docker(*args, timeout=120, **kw):
    return subprocess.run(["docker", *args], capture_output=True, timeout=timeout, **kw)


@pytest.fixture(scope="module")
def image(tmp_path_factory):
    why = _linux_engine()
    if why:
        if os.environ.get("MACHA_REQUIRE_DOCKER") == "1":
            pytest.fail(f"MACHA_REQUIRE_DOCKER=1 but {why}", pytrace=False)
        pytest.skip(why)
    from deployment.student_v2c.build_context_v1 import produce_context
    ctx = tmp_path_factory.mktemp("macha-v2c") / "ctx"
    manifest = produce_context(ctx)
    built = _docker("build", "--progress=plain", "--tag", IMAGE, str(ctx), timeout=900, text=True)
    if built.returncode:
        pytest.fail("docker build failed: " + (built.stdout + built.stderr)[-3000:], pytrace=False)
    log = built.stdout + built.stderr
    base = sorted({w for w in log.split() if w.startswith("docker.io/library/python:3.11-slim-bookworm@sha256:")})
    inspect = json.loads(_docker("image", "inspect", IMAGE, text=True).stdout)[0]
    info = _docker("info", "--format", "{{json .}}", text=True)
    engine = json.loads(info.stdout) if info.returncode == 0 else {}
    evidence = {
        "image_id": inspect["Id"], "base_resolved": base, "config_user": inspect["Config"]["User"],
        "entrypoint": inspect["Config"]["Entrypoint"], "manifest": manifest,
        "engine": {k: engine.get(k) for k in ("ServerVersion", "OperatingSystem", "KernelVersion",
                                              "SecurityOptions", "CgroupVersion", "CgroupDriver",
                                              "DefaultRuntime")},
    }
    out_dir = os.environ.get("MACHA_EVIDENCE_DIR")
    if out_dir:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        Path(out_dir, "macha_student_v2c_image_identity.json").write_text(
            json.dumps(evidence, indent=1, sort_keys=True), encoding="utf8")
    return {"ctx": ctx, "manifest": manifest, "inspect": inspect, "history_log": log, "evidence": evidence}


def _run(flags, data=b"", code=None, args=(), timeout=90):
    cmd = ["docker", "run", "--rm", "-i", *flags]
    if code is None:
        cmd.append(IMAGE)
    else:
        cmd += ["--entrypoint", "python", IMAGE, "-I", "-S", "-B", "-c", code, *args]
    return subprocess.run(cmd, input=data, capture_output=True, timeout=timeout)


_INSIDE = r'''
import importlib.util, json, os, sys
r = {"uid": os.getuid(), "gid": os.getgid(), "groups": os.getgroups()}
status = {}
for line in open("/proc/self/status"):
    k, _, v = line.partition(":")
    status[k] = v.strip()
r["caps"] = {k: status.get(k) for k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")}
r["no_new_privs"], r["seccomp"] = status.get("NoNewPrivs"), status.get("Seccomp")
mounts = []
for line in open("/proc/self/mountinfo"):
    f = line.split(); s = f.index("-")
    mounts.append([f[4], f[5], f[s + 1]])
r["mounts"] = mounts
r["ifaces"] = sorted(os.listdir("/sys/class/net"))
r["routes"] = len(open("/proc/net/route").read().splitlines()) - 1
r["pids"] = sorted(int(p) for p in os.listdir("/proc") if p.isdigit())
try:
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0); r["fork"] = "ALLOWED"
except OSError:
    r["fork"] = "DENIED"
writable = []
for root, dirs, files in os.walk("/"):
    dirs[:] = [d for d in dirs if os.path.join(root, d) not in ("/proc", "/sys")]
    probe = os.path.join(root, ".macha-write-probe")
    try:
        fd = os.open(probe, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except OSError:
        continue
    os.close(fd); os.unlink(probe); writable.append(root)
r["writable_dirs"] = writable
files = []
for p in ("/opt/student/student_v2c.py", "/opt/student/entrypoint.py", "/opt/student/manifest.json"):
    st = os.stat(p)
    try:
        fd = os.open(p, os.O_WRONLY | os.O_APPEND); os.close(fd); w = True
    except OSError:
        w = False
    files.append([p, st.st_uid, st.st_mode & 0o777, w])
r["verifier_files"] = files
hits = []
pat = ("observation_", "teacher", "jepa", ".git", "id_rsa", "credential", ".pem", ".key", "secret", "student_v2c")
for root, dirs, names in os.walk("/"):
    dirs[:] = [d for d in dirs if os.path.join(root, d) not in ("/proc", "/sys")]
    hits += [os.path.join(root, n) for n in names + dirs if any(x in n.lower() for x in pat)]
r["name_hits"] = sorted(hits)
r["sys_path"] = sys.path
r["find_spec"] = {m: importlib.util.find_spec(m) is not None for m in ("scripts", "pip", "deployment")}
print(json.dumps(r))
'''


def _inside(flags):
    done = _run(list(flags), code=_INSIDE)
    if done.returncode:
        pytest.fail("in-container probe failed: " + done.stderr.decode(errors="replace")[-1500:], pytrace=False)
    return json.loads(done.stdout)


_PUBLIC_NAME_HITS_ALLOWED = ("/etc/ssl/certs/", "/usr/share/ca-certificates/", "/usr/lib/ssl/cert.pem",
                             "/usr/local/lib/python3.11/secrets.py",
                             "/usr/local/lib/python3.11/site-packages/pip/_vendor/certifi/cacert.pem",
                             "/opt/student/student_v2c.py")


def test_build_context_and_image_hold_only_the_declared_verifier_package(image):
    ctx, manifest, inspect = image["ctx"], image["manifest"], image["inspect"]
    assert {p.name for p in ctx.iterdir()} == {"student_v2c.py", "entrypoint.py", "Dockerfile", "manifest.json"}
    raw = (ctx / "student_v2c.py").read_bytes()
    assert hashlib.sha1(b"blob %d\x00" % len(raw) + raw).hexdigest() == manifest["source_blob_sha1"]
    assert raw == V2C_FILE.read_bytes()
    assert (ctx / "entrypoint.py").read_bytes() == (DEPLOY / "entrypoint_v1.py").read_bytes()
    assert (ctx / "Dockerfile").read_bytes() == (DEPLOY / "Dockerfile.v1").read_bytes()
    assert manifest["authority_effect"] == "NONE" and manifest["real_training_authorized"] is False
    assert manifest["production_source_rights_issuer_authenticated"] is False
    assert inspect["Config"]["User"] == "65534:65534"
    assert inspect["Config"]["Entrypoint"] == ["python", "-I", "-S", "-B", "/opt/student/entrypoint.py"]
    env_keys = {e.split("=", 1)[0] for e in inspect["Config"]["Env"]}
    assert env_keys == {"PATH", "LANG", "GPG_KEY", "PYTHON_VERSION", "PYTHON_SHA256",
                        "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE"}, env_keys
    hist = _docker("history", "--no-trunc", "--format", "{{.CreatedBy}}", IMAGE, text=True).stdout.splitlines()
    # Newest first; the base image ends with its CMD, and Dockerfile.v1 declares none.
    ours = hist[:next(i for i, h in enumerate(hist) if h.startswith("CMD"))]
    assert ours and not [h for h in ours if h.split()[0] in ("RUN", "ADD", "ARG") or "secret" in h], ours
    hits = _inside(MANDATED)["name_hits"]
    assert "/opt/student/student_v2c.py" in hits  # positive control for the scan
    unexpected = [h for h in hits if not h.startswith(_PUBLIC_NAME_HITS_ALLOWED)]
    assert not unexpected, f"teacher/legacy/credential-like files inside the image: {unexpected}"


def test_mandated_launch_enforces_the_documented_restrictions(image):
    r = _inside(MANDATED)
    assert (r["uid"], r["gid"]) == (65534, 65534) and set(r["groups"]) <= {65534}
    assert set(r["caps"].values()) == {"0000000000000000"}, r["caps"]
    assert r["no_new_privs"] == "1" and r["seccomp"] == "2"
    assert r["ifaces"] == ["lo"] and r["routes"] == 0
    assert r["pids"] == [1] and r["fork"] == "DENIED"
    root = [m for m in r["mounts"] if m[0] == "/"]
    assert root and root[0][1].split(",")[0] == "ro", root
    assert "/tmp" in r["writable_dirs"]  # positive control for the write scan
    assert set(r["writable_dirs"]) <= {"/tmp", "/dev/shm", "/dev/mqueue"}, r["writable_dirs"]
    assert all(p.startswith("/usr/local/lib/python") for p in r["sys_path"]), r["sys_path"]
    assert r["find_spec"] == {"scripts": False, "pip": False, "deployment": False}
    assert not any(m[0].startswith(("/mnt", "/opt", "/home", "/data", "/run/secrets")) for m in r["mounts"])


def test_limit_a_sandboxed_receipt_equals_the_host_receipt_and_attests_no_runtime(image):
    """Fixture equivalence holds, which is also the limitation: nothing in the bytes says
    the receipt was computed inside the sandbox rather than by anyone on the host."""
    req = _request()
    done = _run(MANDATED, json.dumps(req).encode())
    assert done.returncode == 0, done.stdout[-500:] + done.stderr[-800:]
    got = json.loads(done.stdout)
    assert got == C.validate_student_v2c(student_view=req["student_view"], expected_policy=req["expected_policy"])
    assert not [k for k in got if any(w in k for w in ("runtime", "container", "isolation", "image", "signature"))]


def test_mandated_launch_refuses_teacher_role_and_d2_depth_uniformly(image):
    req = _request()
    teacher = json.loads(json.dumps(req))
    teacher["student_view"]["view_kind"] = "TEACHER_RICHER_RIGHTS"
    d2 = json.loads(json.dumps(req))
    d2["student_view"]["rows"][0]["base_rights_normalization_depth"] += 1
    for bad in (teacher, d2):
        done = _run(MANDATED, json.dumps(bad).encode())
        assert (done.returncode, done.stdout) == (2, REFUSAL)


def test_red_the_runtime_user_owns_and_can_rewrite_its_own_verifier(image):
    """Expected: the code the sandbox runs is root-owned and not writable by uid 65534,
    so an omitted --read-only cannot let the runtime user replace its verifier.
    Observed on main: Dockerfile.v1 COPY --chown=65534:65534 makes uid 65534 the owner."""
    r = _inside(_without(MANDATED, "--read-only"))
    bad = [f for f in r["verifier_files"] if f[1] != 0 or f[2] & 0o022 or f[3]]
    if bad:
        pytest.fail("runtime user can modify the packaged verifier ([path, uid, mode, writable]): "
                    + json.dumps(bad), pytrace=False)


def _teacher_mount_dir():
    d = Path(tempfile.mkdtemp(prefix="macha-teacher-canary-"))
    atexit.register(shutil.rmtree, d, True)
    d.chmod(0o755)
    f = d / "teacher_private_hidden_q.json"
    f.write_text(json.dumps({"hidden_q": secrets.token_hex(8)}), encoding="utf8")
    f.chmod(0o644)
    return d


_WEAKENED = {
    "no_flags_at_all": lambda: [],
    "writable_root": lambda: _without(MANDATED, "--read-only"),
    "default_bridge_network": lambda: _without(MANDATED, "--network"),
    "capabilities_kept": lambda: _without(MANDATED, "--cap-drop"),
    "new_privileges_allowed": lambda: _without(MANDATED, "--security-opt"),
    "host_tmpfs_bound_under_dev": lambda: list(MANDATED) + ["-v", "/dev/shm:/dev/macha-host-shm:ro"],
    "pids_unlimited": lambda: _without(MANDATED, "--pids-limit"),
    "memory_unlimited": lambda: _without(MANDATED, "--memory"),
    "root_user": lambda: _without(MANDATED, "--user") + ["--user", "0:0"],
    "host_pid_namespace": lambda: list(MANDATED) + ["--pid", "host"],
    "teacher_bind_mount": lambda: list(MANDATED) + ["-v", f"{_teacher_mount_dir()}:/mnt/teacher:ro"],
}


@pytest.mark.parametrize("weakening", sorted(_WEAKENED))
def test_red_default_entrypoint_serves_receipts_when_a_mandated_restriction_is_weakened(image, weakening):
    """Expected: the shipped entrypoint refuses (constant refusal) unless the documented
    restrictions are observable from inside. Observed on main: it serves a receipt under any
    launch, so the boundary exists only if every launcher remembers every flag.

    seccomp=unconfined is deliberately absent: Docker Desktop wraps containers in an outer
    filter, so /proc/self/status reports Seccomp 2 either way and no in-container check
    could satisfy that case (verified locally, 2026-11-02)."""
    flags = _WEAKENED[weakening]()
    done = _run(flags, json.dumps(_request()).encode())
    if (done.returncode, done.stdout) != (2, REFUSAL):
        pytest.fail(f"{weakening}: served rc={done.returncode} stdout={done.stdout[:160]!r}", pytrace=False)


def test_limit_a_launcher_bind_mount_exposes_teacher_files_inside_the_mandated_sandbox(image):
    """Teacher files are absent because no one mounted them (code excluded / not mounted),
    not because the environment forbids it: one extra -v reads the canary under every flag."""
    d = _teacher_mount_dir()
    want = json.loads((d / "teacher_private_hidden_q.json").read_text(encoding="utf8"))["hidden_q"]
    code = "import json;print(json.load(open('/mnt/teacher/teacher_private_hidden_q.json'))['hidden_q'])"
    done = _run(list(MANDATED) + ["-v", f"{d}:/mnt/teacher:ro"], code=code)
    assert done.returncode == 0, done.stderr[-800:]
    assert done.stdout.decode().strip() == want


def test_limit_every_restriction_is_a_launch_flag_not_an_image_property(image):
    """An entrypoint override with no flags: network, writable root and process creation all return."""
    r = _inside([])
    assert "eth0" in r["ifaces"] and r["routes"] > 0
    assert r["fork"] == "ALLOWED" and r["no_new_privs"] == "0"
    assert [m for m in r["mounts"] if m[0] == "/"][0][1].split(",")[0] == "rw"


def test_limit_cpu_bound_code_outlives_a_killed_client_under_the_mandated_flags(image):
    """No CPU quota or engine-side deadline: killing the docker client (as a subprocess timeout
    does) leaves the container running until someone removes it."""
    name = "macha-orphan-" + secrets.token_hex(4)
    cmd = ["docker", "run", "--rm", "-i", "--name", name, *MANDATED, "--entrypoint", "python", IMAGE,
           "-I", "-S", "-B", "-c", "while True: pass"]
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.time() + 60
        while time.time() < deadline:
            ps = _docker("ps", "--filter", f"name={name}", "--format", "{{.Names}}", text=True).stdout.split()
            if name in ps:
                break
            time.sleep(0.5)
        proc.kill()
        proc.wait(timeout=30)
        time.sleep(3)
        ps = _docker("ps", "--filter", f"name={name}", "--format", "{{.Names}}", text=True).stdout.split()
        assert name in ps, "container stopped with its client; the orphan limitation no longer holds"
    finally:
        _docker("rm", "-f", name)
