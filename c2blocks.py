import json, glob, os, sys
os.chdir(sys.argv[1])
for f in ["C2_V3_D1_AUTOCAST_OFF.json", "C2_V3_D0_BASELINE_FP16.json",
          "C2_V3_D5_MICROBATCH_1.json"]:
    if not os.path.exists(f):
        continue
    d = json.load(open(f))
    u = d["updates"][0]
    e = u["mandatory_gradients_post_unscale"]["entries"]
    statuses = {}
    per_block = {}
    for n, v in e.items():
        statuses[v["status"]] = statuses.get(v["status"], 0) + 1
        blk = n.split(".")[1]
        per_block.setdefault(blk, []).append((n, v["norm"], v["status"]))
    print("==", d["label"], "statuses:", statuses)
    for blk in sorted(per_block):
        norms = [x[1] for x in per_block[blk] if x[1] is not None]
        sts = {x[2] for x in per_block[blk]}
        if norms:
            print("   block %s  n=%d  min=%.3e  max=%.3e  %s"
                  % (blk, len(per_block[blk]), min(norms), max(norms), sorted(sts)))
        else:
            print("   block %s  n=%d  all-None  %s" % (blk, len(per_block[blk]), sorted(sts)))
