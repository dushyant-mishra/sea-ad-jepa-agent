import sys
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import scripts.production_synthetic.canonical_v1 as C
BS = chr(92)
raw = ('{"a' + BS + 'r' + BS + 'n":1,"a' + BS + 'n":2}').encode()
print(raw)
try: print("loader:", ascii(C.load_canonical_json(raw)))
except C.CanonicalError as e: print("loader CE:", e)
try: print("semantic:", C.semantic_sha256(C.load_canonical_json(raw)))
except C.CanonicalError as e: print("semantic CE:", e)
print(ascii(C.load_canonical_json(('"' + BS + 'ud83d' + BS + 'ude00"').encode())))
