# Independent re-implementation from the 5ea1c2e6 module docstring ONLY. Does not import canonical_v1.
import hashlib, struct
JSON_D = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-V1\x00"
TEXT_D = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-TEXT-V1\x00"
REG_D = b"JEPA-PRODUCTION-SYNTHETIC-ORDERED-REGISTRY-V1\x00"
SET_D = b"JEPA-PRODUCTION-SYNTHETIC-ROW-SET-V1\x00"
BS = chr(92)
def eol(s): return s.replace("\r\n", "\n").replace("\r", "\n")
ESC = {'"': BS + '"', BS: BS + BS, "\n": BS + "n", "\t": BS + "t", "\x08": BS + "b", "\x0c": BS + "f"}
def s_(s):
    s = eol(s)
    return '"' + "".join(ESC[c] if c in ESC else (BS + "u%04x" % ord(c) if ord(c) < 0x20 else c) for c in s) + '"'
def enc(o):
    if o is None: return "null"
    if o is True: return "true"
    if o is False: return "false"
    if type(o) is int: return str(o)
    if type(o) is float:
        if o == 0.0: o = 0.0
        return repr(o)
    if type(o) is str: return s_(o)
    if type(o) is dict:
        d = {eol(k): v for k, v in o.items()}
        return "{" + ",".join(s_(k) + ":" + enc(d[k]) for k in sorted(d)) + "}"
    if type(o) in (list, tuple): return "[" + ",".join(enc(v) for v in o) + "]"
    raise TypeError
def cj(o): return enc(o).encode("utf-8")
def frame(b): return struct.pack(">Q", len(b)) + b
def H(b): return hashlib.sha256(b).hexdigest()
def sem(o): return H(JSON_D + cj(o))
def text(raw):
    t = raw.decode("utf-8")
    if t.startswith("﻿"): t = t[1:]
    return H(TEXT_D + eol(t).encode("utf-8"))
def ident(row, keys): return cj([row[k] for k in keys])
def header(keys, n): return cj({"identity_keys": keys, "n_rows": n})
def reg(rows, keys):
    keys = sorted(eol(k) for k in keys)
    body = hashlib.sha256(b"".join(frame(cj(r)) for r in rows)).digest()
    return H(REG_D + frame(header(keys, len(rows))) + body)
def rowset(rows, keys):
    keys = sorted(eol(k) for k in keys)
    ents = sorted((ident(r, keys), cj(r)) for r in rows)
    body = hashlib.sha256(b"".join(frame(i) + frame(b) for i, b in ents)).digest()
    return H(SET_D + frame(header(keys, len(rows))) + body)

kat_obj = {"s": "\x00\x1f\t\n\x7fé\U0001F600", "f": [1e16, 1e-5, 5e-324, 0.1, -0.0, 1.0]}
exp = (b'{"f":[1e+16,1e-05,5e-324,0.1,0.0,1.0],'
       b'"s":"\\u0000\\u001f\\t\\n\x7f\xc3\xa9\xf0\x9f\x98\x80"}')
print("canonical bytes KAT:", cj(kat_obj) == exp)
o = {"b": [1, 2.5, None, True], "a": {"z": 0, "y": 0.0}, "c": "x"}
print("semantic_sha256 KAT:", sem(o) == "9985d6352461c786289baa95b34c9523d607f6559dd0df4f02b8ab43ab321ecd")
print("semantic_text KAT  :", text(b"id\tv\r\nA\t1\r\n") == text(b"id\tv\nA\t1\n") == "383690d22cc9059e6132f0b6ad1ef3ef9f9e9c4e3caf183ec57a4667df61165b")
rows = [{"i": 0, "n": "A"}, {"i": 1, "n": "B"}, {"i": 2, "n": "C"}]
print("registry ['i'] KAT :", reg(rows, ["i"]) == "5d2356c29572e267f707a806e8ca28c7a8addd7c98b83d32395b4ab24e8c1387")
print("registry ['n','i'] :", reg(rows, ["n", "i"]) == "034242f85237cd803e081c91fa6adc709f68e8b7740026bf42655e6b6f2b8d39")
print("row-set ['i'] KAT  :", rowset(rows, ["i"]) == "7c65a8d0ddf15b5411458a2c91437c6001c701f0db51433d8eefcdbf8c3a5586")
