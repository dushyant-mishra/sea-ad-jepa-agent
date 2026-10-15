import sys, hashlib, hmac
sys.path.insert(0, r"D:/jepa_task2_recheck_c7dfff1c")
import scripts.v5.td_unified.manifest_v1 as M
from scripts.v5.td_unified.canonical_v1 import canonical_sha256 as csha

results = []
def t(label, f, expect_raise):
    try:
        r = f(); ok = not expect_raise; msg = str(r)[:90]
    except Exception as e:
        ok = expect_raise; msg = f"RAISES {type(e).__name__}: {str(e)[:90]}"
    results.append(ok); print(("OK  " if ok else "BAD ") + label, "->", msg)

raw = open(r"D:/Jepa project/exports/foundation_calibration_bundle_20260824/splits/reader_donor_split.csv", "rb").read()
RAW = {M.FROZEN_READER_SPLIT_SHA256: raw}
real = M.build_current_td_access_policy_from_reader_split(reader_split_raw=raw)
fit = real.assignment_basis["fit_donors"]

print("== attack 1/2: forged population, non-law folds")
fake = sorted(f"FAKE_{i:03d}" for i in range(104))
def policy(donors, folds):
    basis = {"fit_donors": donors, "fold_count": 5, "assignment_law": M.CURRENT_TD_ASSIGNMENT_LAW,
             "reader_split_raw_sha256": M.FROZEN_READER_SPLIT_SHA256, "population_registry_sha256": M.FROZEN_POPULATION_REGISTRY_SHA256}
    return M.PopulationAccessPolicy("ACCESS_POLICY", "POPULATION_ACCESS_POLICY_V1", "AUTHENTICATED_READER_SPLIT",
        M.FROZEN_READER_SPLIT_SHA256, M.FROZEN_POPULATION_REGISTRY_SHA256, basis, csha(basis), 5, folds,
        ("reader_fit",), ("reader_validation", "reader_oracle"))
def naive_folds(d):
    return tuple(M.CrossFitFold(k, tuple(x for x in d if x not in d[k::5]), tuple(d[k::5])) for k in range(5))
forged = policy(fake, naive_folds(fake))
nonlaw = policy(fit, naive_folds(fit))
t("A1 forged FAKE donors with raw resolver refused", lambda: M.require_current_td_population_authority(forged, raw_resolver=RAW.get), True)
t("A1 forged FAKE donors without raw resolver refused", lambda: M.require_current_td_population_authority(forged), True)
t("A2 lawful donors, non-law folds refused", lambda: M.require_current_td_population_authority(nonlaw, raw_resolver=RAW.get), True)
t("A2 payload validation of non-law folds refused", lambda: M.validate_population_access_policy_payload(nonlaw.to_payload(), raw_resolver=RAW.get), True)
t("positive: real policy accepted with raw resolver", lambda: M.require_current_td_population_authority(real, raw_resolver=RAW.get), False)

print("== attack 3: session issuance / access validation without raw resolver or with altered bytes")
key = b"harness-key-0123456789abcdef"
reg = M.HarnessAccessRegistry(attestation_key=key)
vals = {d: f"v_{d}" for d in fit}
altered = {M.FROZEN_READER_SPLIT_SHA256: raw.replace(b"reader_fit", b"reader_fiT", 1)}
t("A3 issue_session without raw resolver refused", lambda: reg.issue_session(policy=real, producer_id="p", reader_fit_values=vals), True)
t("A3 issue_session with altered split bytes refused", lambda: reg.issue_session(policy=real, producer_id="p", reader_fit_values=vals, raw_resolver=altered.get), True)
t("A3 issue_session for forged policy refused", lambda: reg.issue_session(policy=forged, producer_id="p", reader_fit_values={d: 0 for d in fake}, raw_resolver=RAW.get), True)
s = reg.issue_session(policy=real, producer_id="p", reader_fit_values=vals, raw_resolver=RAW.get)
f0 = real.crossfit_folds[0]
s.read_fit(0, "EVAL", f0.held_out_donors[:2], "BIOLOGICAL_VALUES")
rcpt, ledger = s.finalize()
t("positive: harness-attested receipt validates", lambda: M.validate_producer_access(real, rcpt, session_registry=reg, raw_resolver=RAW.get), False)
t("A3 validate_producer_access without raw resolver refused", lambda: M.validate_producer_access(real, rcpt, session_registry=reg), True)
t("A3 validate_producer_access with altered bytes refused", lambda: M.validate_producer_access(real, rcpt, session_registry=reg, raw_resolver=altered.get), True)

print("== attack 4: hand-made ledgers never issued by the harness")
events = (M.ObservedAccess("reader_fit", "BIOLOGICAL_VALUES", 0, "EVAL", f0.held_out_donors[:1]),)
psha = real.canonical_sha256()
v1 = {"object_role": "OBSERVED_ACCESS_LEDGER", "ledger_schema": "OBSERVED_ACCESS_LEDGER_V1", "producer_id": "evil", "access_policy_sha": psha, "observed_access": [e.to_payload() for e in events]}
r1 = M.ProducerAccessReceipt("evil", psha, csha(v1), events)
t("A4 hand-made V1 ledger via ledger_resolver refused (authoritative)", lambda: M.validate_producer_access(real, r1, ledger_resolver={csha(v1): v1}.get, raw_resolver=RAW.get), True)
t("A4 hand-made V1 ledger with a registry refused", lambda: M.validate_producer_access(real, r1, session_registry=reg, raw_resolver=RAW.get), True)
unsigned = {"object_role": "OBSERVED_ACCESS_LEDGER", "ledger_schema": "OBSERVED_ACCESS_LEDGER_V2_HARNESS_ATTESTED", "session_id": "0" * 64, "producer_id": "evil", "access_policy_sha": psha, "observed_access": [e.to_payload() for e in events]}
v2 = {**unsigned, "harness_attestation": hmac.new(b"attacker-guess-key-000", csha(unsigned).encode(), hashlib.sha256).hexdigest()}
r2 = M.ProducerAccessReceipt("evil", psha, csha(v2), events)
t("A4 hand-made V2 ledger with forged HMAC refused", lambda: M.validate_producer_access(real, r2, session_registry=reg, raw_resolver=RAW.get), True)
t("A4 genuine ledger replayed under another registry refused", lambda: M.validate_producer_access(real, rcpt, session_registry=M.HarnessAccessRegistry(attestation_key=key), raw_resolver=RAW.get), True)
# disclosed in-process limitation: producer code reaching private attributes of the session
s2 = reg.issue_session(policy=real, producer_id="q", reader_fit_values=vals, raw_resolver=RAW.get)
clean = (M.ObservedAccess("reader_fit", "METADATA", 0, "TRAIN", f0.train_donors[:1]),)
def inprocess_bypass():
    r, l = s2._harness_registry._finalize_session(s2._session_id, "q", psha, clean, None)
    M.validate_producer_access(real, r, session_registry=reg, raw_resolver=RAW.get)
    return "in-process private-attribute finalize produced an attested ledger that validates"
print("LIMIT (expected under disclosed app-level instrumentation):", end=" ")
try: print(inprocess_bypass())
except Exception as e: print("refused:", type(e).__name__, str(e)[:80])
print("LIMIT session holds all fit values in producer memory:", len(s2._reader_fit_values))

print("== attack 5/6: manifest sub-policies and B4 identities")
store = {}
def put(o):
    h = csha(o); store[h] = o; return h
def code_obj(b):
    h = hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest(); store[h] = b; return h
def base_fields(overrides=None):
    o = overrides or {}
    f = {}
    f["access_policy_sha"] = put(real.to_payload())
    f["population_split_registry_sha"] = put({"object_role": "POPULATION_SPLIT_REGISTRY", "reader_split_raw_sha256": M.FROZEN_READER_SPLIT_SHA256, "population_registry_sha256": M.FROZEN_POPULATION_REGISTRY_SHA256})
    f["crossfit_policy_sha"] = put(o.get("crossfit", M.derive_crossfit_policy_payload(real)))
    f["protected_partition_policy_sha"] = put(o.get("protected", M.derive_protected_partition_policy_payload(real)))
    f["reader_fit_policy_sha"] = put(M.derive_reader_partition_policy_payload(real, "reader_fit"))
    f["reader_validation_policy_sha"] = put(o.get("validation", M.derive_reader_partition_policy_payload(real, "reader_validation")))
    f["reader_oracle_policy_sha"] = put(M.derive_reader_partition_policy_payload(real, "reader_oracle"))
    norm = put({"object_role": "NORMALIZATION_CONTRACT", "rule": "log1p(raw*1e4/library)"})
    lib = put({"object_role": "LIBRARY_CONTRACT", "rule": "full-source library"})
    f["normalization_library_contract_sha"] = put(o.get("normlib", {"object_role": "NORMALIZATION_LIBRARY_CONTRACT", "contract_schema": "NORMALIZATION_LIBRARY_CONTRACT_IDENTITY_V1", "normalization_contract_sha": norm, "library_contract_sha": lib}))
    tp = code_obj(b"def portfolio(): pass\n")
    f["target_portfolio_code_identity_sha"] = put({"object_role": "TARGET_PORTFOLIO_CODE_IDENTITY", "identity_schema": "GIT_BLOB_IDENTITY_V1", "git_blob_sha1": tp})
    f["target_portfolio_policy_sha"] = put({"object_role": "TARGET_PORTFOLIO_POLICY", "policy_schema": "TARGET_PORTFOLIO_POLICY_IDENTITY_V1", "policy_contract_sha": put({"object_role": "TARGET_PORTFOLIO_POLICY_CONTRACT", "c": 1})})
    pc = code_obj(b"def produce(): pass\n"); ec = code_obj(b"def execute(): pass\n")
    row = {"unit_id": "G8", "producer_code_sha1": pc, "executor_code_sha1": ec,
           "producer_policy_sha": put({"object_role": "PRODUCER_POLICY", "p": 1}), "executor_policy_sha": put({"object_role": "EXECUTOR_POLICY", "e": 1}),
           "schema_sha": put({"object_role": "UNIT_SCHEMA", "s": 1}), "metric_sha": put({"object_role": "METRIC_DEFINITION", "m": 1}),
           "reference_producer_sha": put({"object_role": "REFERENCE_PRODUCER", "r": 1}), "falsifier_sha": put({"object_role": "FALSIFIER_CONTROL", "f": 1})}
    row.update(o.get("row", {}))
    f["unit_execution_identity_table_sha"] = put(o.get("table", {"object_role": "UNIT_EXECUTION_IDENTITY_TABLE", "table_schema": "UNIT_EXECUTION_IDENTITY_TABLE_V1", "units": [row]}))
    for field, role in M._MANIFEST_ROLE_BY_FIELD.items():
        if field not in f:
            f[field] = put({"object_role": role, "x": field})
    return {"schema": "TD_EXECUTION_MANIFEST_V1", "controller_code_sha": code_obj(b"controller = 1\n"), **f}
good = base_fields()
t("positive: full manifest validates", lambda: M.validate_manifest(good, store.get, raw_resolver=RAW.get).schema, False)
t("A5 manifest without raw resolver refused", lambda: M.validate_manifest(good, store.get), True)
t("A5 protected policy allowing biological values refused", lambda: M.validate_manifest(base_fields({"protected": {"object_role": "PROTECTED_PARTITION_POLICY", "policy_schema": "PROTECTED_PARTITION_POLICY_V1", "reader_validation_access_classes": ["BIOLOGICAL_VALUES"], "reader_oracle_access_classes": ["PARTITION_IDENTITY"]}}), store.get, raw_resolver=RAW.get), True)
t("A5 crossfit 'folds chosen later' refused", lambda: M.validate_manifest(base_fields({"crossfit": {"object_role": "CROSSFIT_POLICY", "folds": "LEAVE_SOURCE_OUT_CHOSEN_LATER"}}), store.get, raw_resolver=RAW.get), True)
t("A5 validation 'rescue estimability' refused", lambda: M.validate_manifest(base_fields({"validation": {"object_role": "READER_VALIDATION_POLICY", "use": "RESCUE_ESTIMABILITY"}}), store.get, raw_resolver=RAW.get), True)
omitted = dict(good); omitted.pop("unit_execution_identity_table_sha")
t("A6 omitted unit table refused", lambda: M.validate_manifest(omitted, store.get, raw_resolver=RAW.get), True)
t("A6 role-spoofed normalization object refused", lambda: M.validate_manifest(base_fields({"normlib": {"object_role": "TARGET_PORTFOLIO_POLICY", "contract_schema": "NORMALIZATION_LIBRARY_CONTRACT_IDENTITY_V1", "normalization_contract_sha": "0" * 64, "library_contract_sha": "1" * 64}}), store.get, raw_resolver=RAW.get), True)
lib_as_norm = put({"object_role": "LIBRARY_CONTRACT", "rule": "x"})
t("A6 nested spoof: library object in normalization slot refused", lambda: M.validate_manifest(base_fields({"normlib": {"object_role": "NORMALIZATION_LIBRARY_CONTRACT", "contract_schema": "NORMALIZATION_LIBRARY_CONTRACT_IDENTITY_V1", "normalization_contract_sha": lib_as_norm, "library_contract_sha": lib_as_norm}}), store.get, raw_resolver=RAW.get), True)
t("A6 nested spoof: metric slot holds falsifier object refused", lambda: M.validate_manifest(base_fields({"row": {"metric_sha": put({"object_role": "FALSIFIER_CONTROL", "f": 9})}}), store.get, raw_resolver=RAW.get), True)
t("A6 unit producer code sha with no bytes refused", lambda: M.validate_manifest(base_fields({"row": {"producer_code_sha1": "a" * 40}}), store.get, raw_resolver=RAW.get), True)
t("A6 unit row with extra key refused", lambda: M.validate_manifest(base_fields({"row": {"extra": "x"}}), store.get, raw_resolver=RAW.get), True)
t("A6 empty unit table refused", lambda: M.validate_manifest(base_fields({"table": {"object_role": "UNIT_EXECUTION_IDENTITY_TABLE", "table_schema": "UNIT_EXECUTION_IDENTITY_TABLE_V1", "units": []}}), store.get, raw_resolver=RAW.get), True)
print("NOTE vacuous role-tagged nested contract accepted (content not schema-checked):", end=" ")
try:
    M.validate_manifest(base_fields({"row": {"metric_sha": put({"object_role": "METRIC_DEFINITION"})}}), store.get, raw_resolver=RAW.get); print("accepted")
except Exception as e: print("refused", str(e)[:60])
print(f"\nSUMMARY: {sum(results)}/{len(results)} expected outcomes; BAD={len(results)-sum(results)}")
