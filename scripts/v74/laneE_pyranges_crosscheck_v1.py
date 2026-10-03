# Independent cross-check: reproduce the attrition with the SAME library call
# pycisTopic uses -- pyranges .overlap(invert=True) -- rather than with my own
# interval code. Agreement across two implementations is evidence; agreement of a
# producer with itself is not.
import json, hashlib
import pyranges as pr
import pandas as pd

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as fh:
        for b in iter(lambda: fh.read(8<<20), b''): h.update(b)
    return h.hexdigest()

REG='/out/blacklist/ROUTE_A_UNIVERSE_COPY.bed'
BL='/out/blacklist/ENCFF356LFX.bed'

reg = pd.read_csv(REG, sep='\t', header=None,
                  names=['Chromosome','Start','End','Name'])
regions = pr.PyRanges(reg)
blacklist = pr.read_bed(BL)
kept = regions.overlap(blacklist, invert=True)
kdf = kept.df

out = {
  "implementation": "pyranges .overlap(invert=True) -- the identical call pycisTopic makes at iterative_peak_calling.py:145 and cistopic_class.py:579",
  "pyranges_version": pr.__version__,
  "region_bed_sha256": sha(REG),
  "blacklist_bed_sha256": sha(BL),
  "n_regions_in": int(len(reg)),
  "n_regions_kept": int(len(kdf)),
  "n_regions_dropped": int(len(reg)-len(kdf)),
  "bp_in": int((reg.End-reg.Start).sum()),
  "bp_kept": int((kdf.End-kdf.Start).sum()),
  "bp_dropped": int((reg.End-reg.Start).sum()-(kdf.End-kdf.Start).sum()),
}
with open('/out/receipts/V74_LANEE_PYRANGES_CROSSCHECK_V1.json','w') as fh:
    json.dump(out, fh, indent=2); fh.write('\n')
print(json.dumps(out, indent=2))
