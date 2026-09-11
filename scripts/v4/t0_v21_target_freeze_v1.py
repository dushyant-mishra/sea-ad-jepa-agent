#!/usr/bin/env python3
"""46-development-donor successor target freeze receipt schema; no refit occurs here."""
from __future__ import annotations
import hashlib,json
from typing import Any,Mapping,Sequence
STOP="STOP_T0_V21_TARGET_FREEZE_INVALID"; KIND="t0_v21_target_freeze_receipt_v1"; N=46
DIGEST_FIELDS=("role_ledger_digest","expression_root_digest","molecular_address_digest","cell_identity_digest","donor_order_digest","ridge_trace_digest","learned_parameter_digest","measurement_artifact_digest","crossfit_authority_digest","code_sha","contract_sha")
def _fail(m):raise RuntimeError(f"{STOP}: {m}")
def _hex(n,v):
 s=str(v)
 if len(s)!=64 or any(c not in '0123456789abcdef' for c in s):_fail(f"{n} must be lowercase SHA-256")
 return s
def _digest(v):return hashlib.sha256(b'T0_V21_TARGET_FREEZE_RECEIPT_V1\0'+json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def seal_target_freeze_receipt(*,development_donor_ids:Sequence[str],protected_donor_ids:Sequence[str],estimator_id:str,ridge_exponent:float,bindings:Mapping[str,str],qualification_receipt_digests:Sequence[str])->dict[str,Any]:
 dev=tuple(map(str,development_donor_ids)); prot=set(map(str,protected_donor_ids))
 if len(dev)!=N or len(set(dev))!=N:_fail("exactly 46 unique development donors required")
 if set(dev)&prot:_fail("protected donor appears in 46-donor development refit")
 missing=[k for k in DIGEST_FIELDS if k not in bindings]
 if missing:_fail(f"bindings missing {missing}")
 for k in DIGEST_FIELDS:_hex(k,bindings[k])
 q=tuple(map(str,qualification_receipt_digests))
 if len(q)<2:_fail("measurement and cross-fit qualification receipt digests are required")
 for i,x in enumerate(q):_hex(f"qualification_receipt_digests[{i}]",x)
 body={"kind":KIND,"development_donor_ids":list(dev),"n_development_donors":N,"estimator_id":str(estimator_id),"ridge_exponent":float(ridge_exponent),"bindings":dict(bindings),"qualification_receipt_digests":list(q)}
 body["package_root"]=_digest(body)
 return body
def validate_target_freeze_receipt(receipt:Mapping[str,Any],*,expected_role_ledger_digest:str,expected_expression_root_digest:str)->dict[str,Any]:
 if receipt.get("kind")!=KIND:_fail("V21 46-donor target freeze receipt required")
 root=receipt.get("package_root",""); body={k:receipt[k] for k in receipt if k!="package_root"}
 if root!=_digest(body):_fail("package root does not recompute")
 dev=receipt.get("development_donor_ids",[])
 if len(dev)!=N or len(set(dev))!=N:_fail("receipt is not a 46-donor successor authority")
 b=receipt.get("bindings",{})
 if b.get("role_ledger_digest")!=expected_role_ledger_digest:_fail("role ledger mismatch")
 if b.get("expression_root_digest")!=expected_expression_root_digest:_fail("expression root mismatch")
 for k in DIGEST_FIELDS:
  if k not in b:_fail(f"binding {k} missing")
  _hex(k,b[k])
 return {"verified":True,"package_root":root,"n_development_donors":N}
