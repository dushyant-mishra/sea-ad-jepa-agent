import sys, time
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014/tests/production_synthetic")
import pathlib, tempfile
import custody_fixtures_v1 as T
import scripts.production_synthetic.custody_v1 as CU
tmp = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_quality_scratch"))
tree = T.make_tree(tmp)

def scenario(n_versions, exps_per_version, big_spec=False):
    led = CU.CustodyLedger()
    prev = None
    t0 = time.perf_counter()
    for v in range(n_versions):
        def edit(s, v=v):
            s["difficulty_grid"]["confounding_strength"]["level"] = 2 + v
            if big_spec:
                s["parameter_distributions"]["bulk"] = {f"p{i}": {"mu": i * 0.5, "sigma": 1.0} for i in range(5000)}
        fr, qn = T.make_world(edit=edit)
        if prev is not None:
            CU.validate_successor_version(prev, fr, parent_exposure_state=CU.exposure_state(prev, led), ledger=led)
        CU.record_generator_freeze(fr, led)
        nonces = {T.DEBUG: T.dummy_nonce(), T.QUAL: qn}
        for tag in (T.DEBUG, T.QUAL):
            CU.record_nonce_commitment(fr, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(nonces[tag]))
        CU.record_withheld_commitment(fr, led, withheld_class_tag=T.WTAG, nonce_commitment=CU.nonce_commitment(qn),
            secret_absence_attestations=[{"secret_absent": True, "tree_identity": T._h("t"), "files_scanned": 2, "nonce_commitment": CU.nonce_commitment(qn)}],
            code_path_attestation=T.code_path_attestation(),
            withheld_family_change=None if prev is None else "UNCHANGED")
        for tag in (T.DEBUG, T.QUAL):
            b = fr.realization_budget(tag)
            root = CU.sealed_root(nonces[tag], fr.generator_semantic_hash, tag, b)
            CU.attest_realization_set(fr, led, root=root, class_tag=tag, emitted=T.emit(root, tag, b))
        for j in range(exps_per_version):
            T.expose(fr, led, T.QUAL if j % 2 else T.DEBUG, f"e{v}-{j}")
        prev = fr
    build = time.perf_counter() - t0
    t = time.perf_counter(); raw = led.to_bytes(); tb = time.perf_counter() - t
    t = time.perf_counter(); led.verify(expected_head=led.head); tv = time.perf_counter() - t
    t = time.perf_counter(); d1 = CU.qualification_draws_for_method(led, T.METHOD); tq1 = time.perf_counter() - t
    t = time.perf_counter(); d2 = CU.qualification_draws_in_lineage(led, prev.generator_semantic_hash); tq2 = time.perf_counter() - t
    t = time.perf_counter(); el = CU.withheld_check_eligible(led, prev.generator_semantic_hash); te = time.perf_counter() - t
    t = time.perf_counter(); led.entries(); ten = time.perf_counter() - t
    print(f"versions={n_versions} entries={len(led)} bytes={len(raw)/1e6:.2f}MB big_spec={big_spec} build={build:.2f}s "
          f"to_bytes={tb:.3f}s verify/replay={tv:.2f}s draws_method={tq1:.3f}s ({len(d1)}) draws_lineage={tq2:.3f}s "
          f"eligible={te:.3f}s entries()={ten:.3f}s")

scenario(1, 1000)
scenario(20, 45)
scenario(1, 2000)
scenario(5, 40, big_spec=True)
scenario(5, 200, big_spec=True)
