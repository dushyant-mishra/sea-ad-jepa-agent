import sys, hashlib, csv, io, collections
sys.path.insert(0, r"D:/jepa_task2_review_2c391137")
import scripts.v5.td_unified.manifest_v1 as M
from scripts.v5.td_unified.canonical_v1 import canonical_sha256 as csha
def t(label, f, expect_raise):
    try: r=f(); ok = not expect_raise; print(("OK  " if ok else "BAD ")+label, "->", str(r)[:90])
    except Exception as e: ok = expect_raise; print(("OK  " if ok else "BAD ")+label, "-> RAISES", type(e).__name__, str(e)[:90])
raw = open(r"D:/Jepa project/exports/foundation_calibration_bundle_20260824/splits/reader_donor_split.csv","rb").read()
print("split sha256:", hashlib.sha256(raw).hexdigest(), "== frozen:", hashlib.sha256(raw).hexdigest()==M.FROZEN_READER_SPLIT_SHA256)
real = M.build_current_td_access_policy_from_reader_split(reader_split_raw=raw)
print("real policy built; fit donors:", len(real.assignment_basis["fit_donors"]))
# P1 forged policy: 104 fake donors, frozen strings, arbitrary folds
fake = sorted(f"FAKE_{i:03d}" for i in range(104))
basis = {"fit_donors": fake, "fold_count":5, "assignment_law": M.CURRENT_TD_ASSIGNMENT_LAW, "reader_split_raw_sha256": M.FROZEN_READER_SPLIT_SHA256, "population_registry_sha256": M.FROZEN_POPULATION_REGISTRY_SHA256}
folds = tuple(M.CrossFitFold(k, tuple(d for d in fake if d not in fake[k::5]), tuple(fake[k::5])) for k in range(5))
forged = M.PopulationAccessPolicy("ACCESS_POLICY","POPULATION_ACCESS_POLICY_V1","AUTHENTICATED_READER_SPLIT", M.FROZEN_READER_SPLIT_SHA256, M.FROZEN_POPULATION_REGISTRY_SHA256, basis, csha(basis), 5, folds, ("reader_fit",), ("reader_validation","reader_oracle"))
t("P1 forged 104 FAKE donors pass require_current_td_population_authority (should refuse)", lambda: M.require_current_td_population_authority(forged), True)
# P2 real donors but folds not per law
rd = real.assignment_basis["fit_donors"]
folds2 = tuple(M.CrossFitFold(k, tuple(d for d in rd if d not in rd[k::5]), tuple(rd[k::5])) for k in range(5))
b2 = dict(real.assignment_basis)
p2 = M.PopulationAccessPolicy("ACCESS_POLICY","POPULATION_ACCESS_POLICY_V1","AUTHENTICATED_READER_SPLIT", M.FROZEN_READER_SPLIT_SHA256, M.FROZEN_POPULATION_REGISTRY_SHA256, b2, csha(b2), 5, folds2, ("reader_fit",), ("reader_validation","reader_oracle"))
same = [f.held_out_donors for f in real.crossfit_folds] == [tuple(sorted(f.held_out_donors, key=lambda d:(hashlib.sha256(d.encode()).hexdigest(),d))) for f in folds2]
print("P2 alternative folds differ from law:", not same)
t("P2 real donors, folds NOT per DONOR_SHA256_ORDER law pass authority (should refuse)", lambda: M.require_current_td_population_authority(p2), True)
# P3 fabricated ledger without session
events = (M.ObservedAccess("reader_fit","BIOLOGICAL_VALUES",0,"EVAL", real.crossfit_folds[0].held_out_donors[:1]),)
pol_sha = real.canonical_sha256()
ledger = {"object_role":"OBSERVED_ACCESS_LEDGER","ledger_schema":"OBSERVED_ACCESS_LEDGER_V1","producer_id":"evil","access_policy_sha":pol_sha,"observed_access":[e.to_payload() for e in events]}
rcpt = M.ProducerAccessReceipt("evil", pol_sha, csha(ledger), events)
t("P3 hand-fabricated ledger (no session) accepted by validate_producer_access (should refuse)", lambda: M.validate_producer_access(real, rcpt, ledger_resolver={csha(ledger): ledger}.get), True)
# P4/P5 manifest with vacuous / contradictory sub-policies and unresolved population registry bytes
store = {}
def put(o):
    s = csha(o); store[s] = o; return s
code = b"controller = 1\n"; cs = hashlib.sha1(f"blob {len(code)}\0".encode()+code).hexdigest(); store[cs] = code
acc = put(real.to_payload())
psr = put({"object_role":"POPULATION_SPLIT_REGISTRY","reader_split_raw_sha256":M.FROZEN_READER_SPLIT_SHA256,"population_registry_sha256":M.FROZEN_POPULATION_REGISTRY_SHA256})
fields = {}
for f, role in M._MANIFEST_ROLE_BY_FIELD.items():
    if f == "access_policy_sha": fields[f] = acc
    elif f == "population_split_registry_sha": fields[f] = psr
    elif f == "protected_partition_policy_sha": fields[f] = put({"object_role":role,"reader_validation":"BIOLOGICAL_VALUES_ALLOWED","reader_oracle":"BIOLOGICAL_VALUES_ALLOWED"})
    elif f == "crossfit_policy_sha": fields[f] = put({"object_role":role,"folds":"LEAVE_SOURCE_OUT_CHOSEN_LATER"})
    elif f == "reader_validation_policy_sha": fields[f] = put({"object_role":role,"use":"RESCUE_ESTIMABILITY"})
    else: fields[f] = put({"object_role":role,"x":f})
man = {"schema":"TD_EXECUTION_MANIFEST_V1","controller_code_sha":cs, **fields}
t("P4 manifest with protected policy ALLOWING values + vacuous crossfit + validation RESCUE policy validates (should refuse)", lambda: M.validate_manifest(man, store.get).schema, True)
print("P5 population registry 50b29d7e bytes resolved during validate_manifest?:", M.FROZEN_POPULATION_REGISTRY_SHA256 in store, "(store never contained it; manifest still validated if P4 printed BAD)")
# P6 metadata replay: fold source composition under the law
src = {}
dpath = None
import subprocess
donors_csv = subprocess.check_output(["git","-C",r"D:/Jepa project","show","ccc3a089:results/target_discovery/real_qualification_macha_20261014/population/DONOR.csv"]).decode()
for row in csv.DictReader(io.StringIO(donors_csv)): src[row["donor_id"]] = row["source"]
for f in real.crossfit_folds:
    c = collections.Counter(src[d] for d in f.held_out_donors)
    print(f"  fold {f.fold_index}: held-out {len(f.held_out_donors)} donors, by source {dict(sorted(c.items()))}")
