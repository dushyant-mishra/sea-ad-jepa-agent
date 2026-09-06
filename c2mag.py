import json, glob, os, sys
os.chdir(sys.argv[1])
FP16_MIN_SUBNORMAL = 5.96e-8
for f in sorted(glob.glob("C2_V3_D*.json")):
    d = json.load(open(f))
    u = d["updates"][0]
    e = u["mandatory_gradients_post_unscale"]["entries"]
    lr = u["live_reference_gradients_post_unscale"]["entries"]
    live = [v["norm"] for v in e.values() if v["status"] == "LIVE"]
    out = [v["norm"] for v in lr.values() if v["status"] == "LIVE"]
    print("%-24s dead=%2d/48  scaler=%s" % (
        d["label"], u["mandatory_gradients_post_unscale"]["dead_count"],
        d["factors"]["gradscaler_enabled"]))
    if live:
        print("      mandatory LIVE norms: min=%.3e max=%.3e" % (min(live), max(live)))
        print("      x65536 headroom vs fp16 min subnormal: min=%.3e" % (
            min(live) * 65536.0 / FP16_MIN_SUBNORMAL))
    if out:
        print("      attention.output norms: min=%.3e max=%.3e" % (min(out), max(out)))
