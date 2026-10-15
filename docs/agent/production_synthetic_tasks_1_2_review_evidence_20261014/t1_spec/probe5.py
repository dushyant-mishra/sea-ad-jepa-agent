import sys, random
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import scripts.production_synthetic.canonical_v1 as C
L = C.load_canonical_json
BS = chr(92)
def t(label, b):
    try: print(f"{label}: OK -> {ascii(L(b))}")
    except C.CanonicalError as e: print(f"{label}: CE {str(e)[:80]}")
    except Exception as e: print(f"{label}: OTHER {type(e).__name__}")
cases = {
 "1E-400": b"1E-400", "0.0e-0": b"0.0e-0", "00.1": b"00.1", "-00.1": b"-00.1",
 "-0.0000000e-9999": b"-0.0000000e-9999",
 "1+400z e-800 (~1e-400, true underflow)": b"1" + b"0"*400 + b"e-800",
 "1+400z e-500 (=1e-100, legit)": b"1" + b"0"*400 + b"e-500",
 "1+400z e-722 (=1e-322 subnormal, legit)": b"1" + b"0"*400 + b"e-722",
 "0.000..1 e-300 (=1e-310 subnormal)": b"0." + b"0"*9 + b"1e-300",
 "2.5e-324 (rounds up to min subnormal)": b"2.5e-324",
 "2.4703282292062328e-324 (just above half)": b"2.4703282292062328e-324",
 "2.4703282292062327e-324 (just below half)": b"2.4703282292062327e-324",
 "4.9e-324": b"4.9e-324", "1e-323": b"1e-323",
 "0.0e999": b"0.0e999", "0e+5": b"0E+5", "-0e-0": b"-0e-0",
 "1e999 nested": b'{"a":[1e999]}', "1e-400 in obj": b'{"a":{"b":[1,1e-400]}}',
 "1.0": b"1.0", "1e308": b"1e308", "1.8e308": b"1.8e308",
 "big mantissa 1+5000 zeros .0": b"1" + b"0"*5000 + b".0",
}
for k, v in cases.items(): t(k, v)
q = lambda s: s.replace("\\", BS).encode()
t("lone hi surrogate value", ('"' + BS + 'ud800"').encode())
t("lone lo surrogate in key nested", ('{"x":[{"' + BS + 'udc00":1}]}').encode())
t("reversed pair", ('"' + BS + 'ude00' + BS + 'ud83d"').encode())
t("valid pair", ('"' + BS + 'ud83d' + BS + 'ude00"').encode())
t("nested CR vs LF keys in array", ('[{"a' + BS + 'r":1,"a' + BS + 'n":2}]').encode())
t("CRLF vs CR keys", ('{"a' + BS + 'r' + BS + 'n":1,"a' + BS + 'r":2}').encode())
t("distinct keys a vs a\n", ('{"a":1,"a' + BS + 'n":2}').encode())
t("same key in sibling objects ok", b'[{"a":1},{"a":2}]')
t("dup via escape", ('{"a":1,"' + BS + 'u0061":2}').encode())
# exhaustive-ish: random decimal literals: rule must reject iff float==0 and value truly nonzero
rng = random.Random(1); wrong = 0
for _ in range(20000):
    mant = rng.choice(["0", "1", "9", "0.0", "0.5", "2.4703282292062327", "2.4703282292062328", "123", "0.00007"])
    e = rng.randrange(-700, 0)
    s = f"{rng.choice(['', '-'])}{mant}e{e}"
    truly_zero = all(c in "0.-" for c in s.split("e")[0])
    try: v = L(s.encode()); acc = True
    except C.CanonicalError: acc = False
    f = float(s)
    if acc and f == 0.0 and not truly_zero: wrong += 1
    if (not acc) and (f != 0.0 or truly_zero): wrong += 1
print("random literal rule violations:", wrong)
