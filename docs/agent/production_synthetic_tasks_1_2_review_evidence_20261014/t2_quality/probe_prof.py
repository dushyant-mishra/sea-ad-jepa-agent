import sys, time, cProfile, pstats
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014/tests/production_synthetic")
exec(open("D:/jepa_ps_t2_quality_scratch/probe_perf.py").read().split("scenario(1, 1000)")[0])
import scripts.production_synthetic.canonical_v1 as C
fr, qn = T.make_world(edit=lambda s: s["parameter_distributions"].update(bulk={f"p{i}": {"mu": i*0.5, "sigma": 1.0} for i in range(5000)}))
print("spec bytes", len(fr.canonical_spec))
t=time.perf_counter(); CU.freeze_generator_version(fr.spec()); print("one freeze", time.perf_counter()-t)
led = CU.CustodyLedger(); CU.record_generator_freeze(fr, led)
nonces = {T.DEBUG: T.dummy_nonce(), T.QUAL: qn}
for tag in (T.DEBUG, T.QUAL):
    CU.record_nonce_commitment(fr, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(nonces[tag]))
CU.record_withheld_commitment(fr, led, withheld_class_tag=T.WTAG, nonce_commitment=CU.nonce_commitment(qn),
    secret_absence_attestations=[{"secret_absent": True, "tree_identity": T._h("t"), "files_scanned": 2}],
    code_path_attestation=T.code_path_attestation())
for tag in (T.DEBUG, T.QUAL):
    b = fr.realization_budget(tag); root = CU.sealed_root(nonces[tag], fr.generator_semantic_hash, tag, b)
    CU.attest_realization_set(root, tag, b, T.emit(root, tag, b), led, freeze=fr)
pr = cProfile.Profile(); pr.enable()
for j in range(10): T.expose(fr, led, T.DEBUG, f"x{j}")
pr.disable()
pstats.Stats(pr).sort_stats("cumulative").print_stats(12)
