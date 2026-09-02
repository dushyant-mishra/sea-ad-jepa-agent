# F1 canonical serialization and randomization contract v3

Strings are Unicode NFC then UTF-8, with no case conversion. `FRAME(tag,payload)=uint8(tag)||uint64_be(len(payload))||payload`. Integers are unsigned big-endian and range-checked. SHA fields designated raw32 are decoded bytes, never hex text. CSV is UTF-8, comma-delimited, RFC-4180 quoted, LF-terminated; CSV is reporting-only wherever an exact integer or digest has a dedicated canonical binary grammar. JSON authority hashes use UTF-8 canonical JSON with sorted keys and separators `,` and `:`.

The public 32-byte OS-CSPRNG key is frozen in `F1_QUERY_RANDOMIZATION_AUTHORITY.json`. `ROOT_KEY=HMAC-SHA256(key, FRAME(1,"F1_DESIGN_SAMPLED_QUERY_V3_HMAC")||FRAME(2,raw32(repair manifest SHA)))`. Each draw block is HMAC-SHA256 over the typed `DRAWMSG` implemented in the hash-bound generator. The draw message excludes candidate address. Rejection sampling uses `L=floor(2^256/M)M`; the first unsigned-big-endian block `z<L` yields `t=z mod M`. Ascending address cumulative integer mass selects the query.

Probability claim: over the one-time uniform key-generation experiment, under the standard keyed-PRF/random-oracle idealization, the blocks for distinct typed assignment/counter messages are independent uniform 256-bit values. The claim is not made over a fixed public identifier hash.
