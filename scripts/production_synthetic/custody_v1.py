r"""Freeze-before-use custody, withheld commitments and domain-separated RNG for
production synthetic V3.1.1 (implementation plan Task 2).

Controlling law: V3.1 sections 1.1 (freeze before use), 1.2 (seed commitment),
1.3 (single-realization attestation, withheld family) and 2.2 (class naming);
V3.1.1 errata E1 (post-exposure versions may not become easier) and E2 (the
withheld specification is secret until reveal); the plan's withheld-family
custody law and binding note N3 (no unique public withheld code path).

This module holds custody MECHANICS only. It never contains, generates or
persists a production secret and writes nothing to disk: the controller calls
it off-repo with its own nonce and withheld specification. Every hash and every
serialization comes from ``canonical_v1`` (imported as ``C``); no second
canonical form is defined here. ``CustodyError`` (a ``ValueError``) is raised
for every custody refusal. NO-ECHO RULE: a custody error never contains a
nonce, a secret, a matching path, a code-path identifier, a withheld-spec key
or any other caller-supplied key name (unknown keys are reported by count);
a ``C.CanonicalError`` underneath is replaced, not chained (``from None``),
because its text can quote supplied keys.

BYTE FORMAT. ``||`` is byte concatenation; frame(b) = len(b) as 8-byte
big-endian unsigned || b (the canonical_v1 framing). Inside a hash a 64-hex
digest enters as its 32 raw bytes, a tag as strict UTF-8, a count or index as
8-byte big-endian unsigned. H(domain; f1, f2, ...) = SHA-256(domain ||
frame(f1) || frame(f2) || ...). Domains (literal bytes, trailing NUL):
    COMMIT      b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-COMMIT-V1\x00"
    NONCE       b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-NONCE-COMMIT-V1\x00"
    SEALED-ROOT b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-SEALED-ROOT-V1\x00"
    ROOT-COMMIT b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-ROOT-COMMIT-V1\x00"
    REALIZATION b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-REALIZATION-ID-V1\x00"
    STREAM      b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-STREAM-V1\x00"

DECISIONS (each is the single authority for its quantity)

1. GENERATOR FREEZE (``freeze_generator_version(spec) -> GeneratorFreeze``).
   ``spec`` is a mapping with EXACTLY these top-level components (V3.1 s1.1);
   a missing or unknown key is refused:
     generator_source, transitive_dependencies   {name: 64-hex digest}, non-empty
     registries                                  {name: 64-hex digest}, non-empty
       (address/support and modality-namespace registries are bound by their
       ``C.ordered_registry_digest``, never inlined)
     parameter_distributions, mechanism_mixture,
       observation_calibration_distributions, applicability_control_matrix,
       serialization_contract                    non-empty mappings (bound as given)
     stress_regimes      non-empty {regime_name: definition}
     difficulty_grid     non-empty {dimension: {"level": number,
                         "harder_direction": "increasing" | "decreasing"}}
     challenge_families  {category: [unique names]} with categories exactly the
                         E1 list: adverse_regimes, control_families,
                         support_challenges, population_imbalance_challenges,
                         novelty_regimes, measurement_challenges
     realization_budgets {class_tag: positive int}; class tags only SYNTH_DEBUG
                         and SYNTH_QUALIFICATION (SYNTH_QUALIFICATION required);
                         any tag containing DEV or SEALED is refused (s2.2)
     withheld_family_commitment  64-hex E2 commitment (decision 2)
   generator_semantic_hash = C.semantic_sha256(spec). ``GeneratorFreeze`` is a
   frozen dataclass that stores the canonical spec bytes and re-derives and
   checks every field in ``__post_init__``, so an inconsistent freeze cannot be
   constructed; ``spec()`` returns a fresh deep copy.
   Withheld-plaintext tripwire (runs FIRST, before any key check, so nothing
   it would catch can be echoed): every mapping key and string value anywhere
   in the spec is lowercased with "-", " ", "." mapped to "_" and refused if it
   contains withheld_spec, withheld_family, withheld_mechanism, withheld_param,
   withheld_applicab, withheld_scor, withheld_budget, withheld_composition,
   withheld_variant, withheld_regime, withheld_class, nonce or preimage. The
   only exemption is the top-level key ``withheld_family_commitment``. This
   also refuses an unsalted hash of the withheld spec stored under such a key
   (it would admit dictionary attacks on a small spec space): the only public
   withheld artifact is the nonce-salted commitment. Evidence-rights state
   names such as WITHHELD_BY_EVIDENCE_RIGHTS do not match and stay legal. This
   is a tripwire, not a proof; the proof obligation is ``scan_secret_absence``
   (decision 8).

2. COMMITMENTS.
   commit_secret(nonce, payload_hash, tag) = hex H(COMMIT; nonce, payload_hash,
   tag); nonce is ``bytes`` of length >= 32 (str/int/bytearray/memoryview are
   refused), payload_hash 64 lowercase hex, tag a non-empty str.
   ``verify_reveal`` recomputes and raises CustodyError on any mismatch.
   nonce_commitment(nonce) = hex H(NONCE; nonce)  (the published H(nonce)).
   sealed_root(nonce, generator_semantic_hash, class_tag, budget) = raw 32-byte
   H(SEALED-ROOT; nonce, generator_semantic_hash, class_tag, budget)  (s1.2).
   root_commitment(root) = hex H(ROOT-COMMIT; root).
   E2 mapping. E2's controller_nonce IS the SYNTH_QUALIFICATION sealed nonce of
   the same generator version (read literally; a debug nonce can never open
   the withheld commitment). withheld_spec_sha256 =
   C.semantic_sha256(withheld_spec); payload_hash = C.semantic_sha256(
   {"withheld_spec_sha256": ..., "generator_precommitment_semantic_hash":
   ...}); commitment = commit_secret(qualification_nonce, payload_hash,
   withheld_class_tag). Hashing the spec first preserves E2's binding: SHA-256
   collision resistance makes withheld_spec_sha256 bind the spec exactly as the
   raw bytes would, so the commitment binds (spec, nonce, generator, tag);
   hiding comes from the >= 256-bit nonce, which is why the intermediate spec
   hash and payload hash are controller-only and never published.
   HASH-CYCLE RESOLUTION (documented deviation). Read literally, E2 puts
   generator_semantic_hash inside the commitment while decision 1 puts the
   commitment inside the spec that generator_semantic_hash hashes, which is
   unsatisfiable (it would need a SHA-256 fixed point). The commitment
   therefore binds the PRE-COMMITMENT identity
       precommitment_semantic_hash = C.semantic_sha256(
           {"generator_precommitment_v1": spec minus withheld_family_commitment})
   (``generator_precommitment_semantic_hash``), and generator_semantic_hash,
   which binds the commitment, is the identity everything else uses, including
   sealed_root. This is the only non-circular reading; both identities are
   carried by ``GeneratorFreeze``. Controller sequence: draw the qualification
   nonce, compute the precommitment hash, compute the commitment, freeze.

3. LEDGER (``CustodyLedger``). An append-only, hash-chained, in-memory ledger.
   Entry = {"index", "kind", "payload", "prev_entry_hash", "entry_hash"};
   entry_hash = C.semantic_sha256({"format":
   "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-ENTRY-V1", "index", "kind",
   "payload", "prev_entry_hash"}); the genesis prev hash is 64 zeros. Kinds:
   GENERATOR_FROZEN, NONCE_COMMITTED, WITHHELD_COMMITTED,
   REALIZATION_SET_ATTESTED, REQUALIFICATION_PREREQUISITES_RECORDED,
   EXPOSURE_RECORDED, FIT_OUTPUT_FROZEN, REVEALED, SUCCESSOR_RECORDED.
   (FIT_OUTPUT_FROZEN is an addition to the originally listed kinds: without
   it the s1.2/E2 rule "reveal only after the fit-side output is irrevocably
   frozen" could not be enforced.) There is no public append, delete or mutate
   method; only the custody functions below write, and each write runs that
   kind's precondition validator first. Serialization is
   C.canonical_json_bytes({"format": "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-
   LEDGER-V1", "entries": [...]}). ``from_bytes`` REPLAYS every entry through
   the same validators, so a ledger whose hash chain is valid but whose custody
   order is not (for example an exposure before the commitments) is refused.
   Limitation and obligation: anyone can recompute a chain, so a consistently
   re-chained prefix (tail truncation or entry deletion) is caught only against
   an anchored head (``expected_head``). The ledger head must therefore be
   published externally after EVERY entry; a head that was never published
   anchors nothing. This module cannot enforce publication; the packaging and
   finalizer tasks must.

4. RANDOM STREAMS (``derive_stream(root, *identity_parts)``). root must be
   exactly 32 ``bytes`` (ints, strings and bytearrays are refused, which blocks
   integer seeds). identity_parts are (key, value) pairs; keys come from the
   fixed vocabulary world_id, component_id, donor_id, cell_id, modality_id,
   address_id, purpose_tag, draw_index_tag; world_id and purpose_tag are
   required (the same cell in two worlds must never share a stream); values
   must be non-empty ``str`` with no control characters (bare ints, numpy ints,
   bools and floats are refused: integer offsets are prohibited, s1.2);
   duplicate keys are refused; key order is irrelevant (the identity is
   canonicalized as a JSON object). seed digest = H(STREAM; root,
   C.canonical_json_bytes({key: value})) (``stream_seed_digest``); stream =
   np.random.Generator(np.random.PCG64(np.random.SeedSequence(
   int.from_bytes(digest, "big")))). A stream depends only on (root, scientific
   identity), never on processing order. Numeric-looking string identities
   ("3") are lawful: they are hashed, not added to a seed.
   Secret-shape tripwire (PROSPECTIVE_CONVENTION): a nonce or root with fewer
   than 16 distinct byte values is refused. For 32 uniformly random bytes the
   false-refusal probability is <= C(256,15) * (15/256)**32 < 3e-16; the rule
   catches integer-derived secrets such as (42).to_bytes(32, "big") and
   constant fills. It cannot detect arithmetic on a random root, which is why
   the only sanctioned roots are ``sealed_root`` outputs whose commitment is
   verified at reveal (decision 7).

5. EXPOSURE (``record_exposure(freeze, exposure, ledger, *,
   expected_ledger_head=None) -> ExposureState``). exposure = exactly
   {"exposure_id", "method_id", "realization_class"}. Refused unless the
   version is the live lineage head (decision 6) and the ledger already holds,
   for it, GENERATOR_FROZEN, NONCE_COMMITTED for SYNTH_QUALIFICATION and for
   the exposed class, WITHHELD_COMMITTED, REALIZATION_SET_ATTESTED for the
   exposed class (no downstream method touches a realization outside an
   attested complete set, s1.3) and, for a POST_EXPOSURE_VERSION or
   NEW_SCIENTIFIC_TESTBED version, REQUALIFICATION_PREREQUISITES_RECORDED.
   Exposure ids are unique per version; a SYNTH_QUALIFICATION exposure after
   the qualification nonce or the withheld family has been revealed is
   refused. When ``expected_ledger_head`` is supplied it must equal the head
   before the append (a stale controller view is refused). Appends
   EXPOSURE_RECORDED; the returned ``ExposureState`` (derived from the ledger by
   ``exposure_state``) is then exposed.
   METHOD IDENTITY. ``method_id`` must be a 64-hex content digest of the frozen
   method identity (its code plus configuration); free-text labels are refused,
   because a label can be renamed while the method stays the same. The digest
   binds what was exposed; it does not prove that two digests are different
   methods (a trivial edit yields a new digest), which is why draws are also
   counted per lineage below.
   DRAW ACCOUNTING (Q2), A BINDING OBLIGATION. ``qualification_draws_for_method(
   ledger, method_id)`` returns, in ledger order, every SYNTH_QUALIFICATION
   exposure of that method digest across all versions of the lineage
   (generator hash, class tag, method_id, attested realization-set binding,
   exposure entry hash, ledger index). ``qualification_draws_in_lineage(ledger,
   generator_semantic_hash)`` returns the same fields for every
   SYNTH_QUALIFICATION exposure of ANY method across the version's whole
   lineage (all ancestors and descendants; debug exposures excluded). Every
   qualification claim (Tasks 11 and 12) MUST report BOTH lists and MUST
   account for multiplicity across ALL lineage draws regardless of method
   label: a changed method digest does not reset the count. Reroll refusal
   (W2) blocks only exact copies; near-copies (negligibly harder moves,
   boilerplate defect records, relabelled methods) are not refused but are
   made visible by these counts, which is how repeated sealed draws are
   prevented from being reported as a single clean qualification. A ledger
   holds exactly one lineage; draws recorded in any OTHER ledger the
   controller keeps for the same testbed are invisible here, so the
   qualification task must also account for every such ledger.

6. SUCCESSORS (``validate_successor_version(parent, child, *,
   parent_exposure_state, ledger, defect_record=None) -> VersionDisposition``;
   ``ledger`` is an added required keyword so the decision can be recorded).
   Lineage is STRICTLY LINEAR: the parent must be the lineage head (the most
   recently frozen version) with no successor recorded yet (a second successor
   of one parent is refused), every non-root GENERATOR_FROZEN needs a prior
   SUCCESSOR_RECORDED naming it, and each child is validated once. Once a
   successor is recorded the parent is SUPERSEDED: it can no longer receive a
   nonce or withheld commitment, a realization attestation, requalification
   prerequisites or an exposure (its fit freeze and reveals stay possible so
   its custody can close). Recording a successor commits the lineage to that
   child. parent_exposure_state must equal the ledger's own state for the
   parent, including ``ledger_head`` (forged or stale states are refused).
   E1 profile of a version: its difficulty_grid, its challenge-family names,
   and the semantic hash of each of the ten other frozen components
   (E1_FROZEN_COMPONENTS: generator_source, transitive_dependencies,
   parameter_distributions, mechanism_mixture,
   observation_calibration_distributions, stress_regimes,
   applicability_control_matrix, registries, serialization_contract,
   realization_budgets). withheld_family_commitment is excluded: it binds the
   precommitment hash and so changes in every version by construction.
   Against the reference version: "easier dimensions" are difficulty
   dimensions removed, moved in their easier direction or with
   harder_direction changed, and challenge-family names removed (identifiers
   "difficulty_grid/<dim>", "challenge_families/<category>/<name>");
   "changed components" are E1_FROZEN_COMPONENTS whose semantic hash differs.
   Because a distribution, mixture weight, control matrix or budget has no
   frozen ordering, ANY change to one of them after exposure is treated as a
   potential relaxation; a difficulty dimension may only stay or move harder,
   challenge-family names may only be added.
   Floor (blocks laundering): walking back from the parent, the floor is the
   first version that is exposed or was itself recorded as
   POST_EXPOSURE_VERSION / NEW_SCIENTIFIC_TESTBED; the reference is the floor,
   not merely the parent, so an unexposed intermediate cannot make a version
   easier than an exposed ancestor and a defect-corrected version cannot be
   relaxed further without a new record. Rolling back never-exposed hardening
   above the floor stays lawful.
   Dispositions: no floor -> PRE_EXPOSURE_REVISION (any change allowed);
   floor, no easier dimension, no changed component, no defect record ->
   SUCCESSOR_NOT_EASIER; floor and any easier dimension or changed component
   without a defect record -> CustodyError; with a defect record ->
   POST_EXPOSURE_VERSION, or NEW_SCIENTIFIC_TESTBED when it declares
   ``incomparable: True``. defect_record = exactly {parent_generator_semantic_
   hash, child_generator_semantic_hash (both exact), defect_description
   (non-empty), affected_dimensions (unique list, a superset of the easier
   dimensions), affected_components (unique list of E1_FROZEN_COMPONENTS
   names plus "withheld_family", a superset of the changed components; the two
   lists are not both empty), generator_side_evidence_sha256 (64-hex),
   justification_source (must
   equal "GENERATOR_DEFECT_AGAINST_FROZEN_SPEC"; anything else, including any
   downstream/method-performance justification, is refused because E1 forbids
   deleting a regime merely because a method failed on it), incomparable
   (bool)}. The ledger checks the FORM of a defect record, not its truth: the
   description and justification are an attested declaration by the
   controller and every defect record requires reviewer audit. Every
   disposition has inherits_qualification False, requires_realism_rerun True
   and requires_withheld_check True. A POST_EXPOSURE_VERSION or
   NEW_SCIENTIFIC_TESTBED version cannot be exposed until
   ``record_requalification_prerequisites`` binds a realism-rerun receipt hash
   and a withheld-check-plan hash (64-hex each) for it. Appends
   SUCCESSOR_RECORDED.
   REROLLS (W2). Once the lineage is exposed (a floor exists), a successor
   whose E1 profile equals that of its parent or of any exposed ancestor, and
   whose defect record (if any) does not list "withheld_family", is a reroll:
   it would only redraw the sealed realizations of a generator that methods
   have already seen, so it is refused ("reroll/seed-shopping prohibited").
   Comparing with exposed ancestors as well as the parent closes the detour
   through an unexposed intermediate (harden, then roll back exactly). Before
   any exposure an identical revision stays a PRE_EXPOSURE_REVISION. Fresh
   sealed draws for a new downstream method need a separately named
   qualification class whose budget was declared in the original freeze;
   classes cannot be added afterwards because realization_budgets is a frozen
   component.
   WITHHELD FAMILY FROZEN PER LINEAGE (W1). withheld_family_commitment is
   excluded from the E1 profile (it changes in every version), so the family
   itself is governed separately. Every successor's WITHHELD_COMMITTED declares
   withheld_family_change "UNCHANGED" or "CHANGED_BY_DEFECT" (the lineage root
   declares none). CHANGED_BY_DEFECT requires the successor's defect record to
   list "withheld_family" in affected_components (so after exposure it is a
   POST_EXPOSURE_VERSION or NEW_SCIENTIFIC_TESTBED); UNCHANGED is refused when
   the defect record lists it. The rule applies before exposure too. Nothing
   about the withheld spec is published before reveal (the declaration is a
   flag; no unsalted hash). The declaration is checked at the successor's
   withheld reveal against its REFERENCE, the nearest ancestor that committed a
   withheld family: the reference's family must already be revealed; UNCHANGED
   requires the same withheld-spec semantic hash and CHANGED_BY_DEFECT a
   different one (otherwise it is a disguised reroll); any mismatch is a hard
   custody failure that voids the version's qualification.
   WITHHELD-CHECK ELIGIBILITY (fail closed). A version's FAMILY GROUP is every
   version carrying the same family through unbroken UNCHANGED declarations,
   in both directions. A family is DISCLOSED by its withheld reveal or by the
   SYNTH_QUALIFICATION class-nonce reveal of any group member (that nonce opens
   the member's commitment, so a small spec space becomes enumerable).
   WITHHELD_COMMITTED records withheld_check_secret: false when the version
   declares UNCHANGED and the reused family has already been disclosed by an
   ancestor in its group, and true otherwise; replay recomputes it. Each
   withheld reveal records family_previously_public: true when the revealed
   family equals a family revealed earlier by any version OUTSIDE its group
   (Q3: a "change" back to an already-public family); replay recomputes it.
   Equality with the immediate reference under CHANGED_BY_DEFECT remains a
   hard failure; equality with any other earlier-revealed family is fail
   closed (ineligible), not a hard failure. ``withheld_check_eligible(ledger,
   generator_semantic_hash)`` returns True only when the family was committed
   while secret, no other group member disclosed it before this version's
   SYNTH_QUALIFICATION fit output froze, and its own reveal (if any) is not
   family_previously_public; it returns False for any version without a
   committed withheld family. It reflects the ledger as it stands and is final
   only after the version's own withheld reveal, so the qualification task
   must evaluate it after that reveal. A version with withheld_check_secret
   false can never satisfy the E2 withheld-family qualification check. Issuing
   a fresh withheld family after a reveal is an open design question for the
   deciding lane and is NOT implemented here: CHANGED_BY_DEFECT remains the
   only change path.

7. REALIZATION SET (``attest_realization_set(root, class_tag, budget, emitted,
   ledger, *, freeze) -> RealizationAttestation``; ``freeze`` is an added
   required keyword binding the generator version). The version must be the
   live head, budget must equal the frozen budget for the class and the class
   nonce must already be committed. Authorized ids: realization_id(i) = hex
   H(REALIZATION; root, class_tag, i) for i in range(budget)
   (``authorized_realization_ids``). ``emitted`` is a list of exactly
   {"realization_id", "content_sha256"}; the emitted id set must equal the
   authorized set: a missing id (discard), an extra or foreign id (seed
   shopping/replacement), a duplicate id or a duplicate content hash (a failed
   world replaced by a copy) is refused. The attestation binds
   root_commitment(root) (never the root itself), the authorized-id set digest
   and emitted_set_sha256 = C.semantic_row_set_sha256(emitted,
   ["realization_id"]). One attestation per (version, class) and one use per
   root: no re-emission. The producer-side check cannot see the nonce, so a
   set drawn from an uncommitted nonce is caught at reveal, which recomputes
   sealed_root from the revealed nonce and checks the root commitment and the
   authorized ids. DOWNSTREAM OBLIGATION: regenerating each realization's
   content from the revealed root and checking its content_sha256 is not done
   here; the packaging and qualification tasks must do it.
   Implication for later tasks: withheld-family worlds are emitted INSIDE the
   SYNTH_QUALIFICATION budget, so the public attestation binds them before
   scoring without revealing which realizations they are.

   FIT FREEZE AND REVEAL. ``record_fit_output_frozen`` requires an attested set
   and a recorded exposure for the class (once per class). ``reveal_class_nonce``
   requires the class fit output frozen, checks H(nonce) against
   NONCE_COMMITTED and the recomputed root and authorized ids against the
   attestation. ``reveal_withheld_family`` requires the SYNTH_QUALIFICATION fit
   output frozen, requires H(nonce) to equal the committed qualification nonce
   and verifies the commitment (decision 2). Either path discloses the
   qualification nonce, and both are refused before the qualification fit
   output is frozen. Each reveal happens once; any mismatch, early reveal or
   alternative withheld draw is a hard custody failure (E2).
   Two enabling rules keep W1 satisfiable without weakening E2. (a) A
   superseded version that never had a SYNTH_QUALIFICATION exposure can never
   freeze a qualification fit, so as a reference it could never be revealed and
   would deadlock its descendants; its withheld family may therefore be
   revealed once a descendant's qualification fit is frozen (it has no sealed
   run of its own to protect). (b) No withheld reveal is allowed while any
   SYNTH_QUALIFICATION run in the ledger is open (exposed, fit not frozen),
   because a shared (UNCHANGED) withheld family would be disclosed before that
   run's fit is frozen. Then the W1 reference checks of decision 6 run.
   (c) Q1: a SYNTH_QUALIFICATION class-nonce reveal of a version with a
   withheld commitment is refused while any member of its family group has an
   open qualification run, because that nonce opens the shared commitment.

8. SECRET SCAN (``scan_secret_absence(repo_tree, secret_bytes) -> dict``).
   repo_tree is a directory; every regular file and symlink under it is
   scanned, and every relative path name too; any ``.git`` entry is skipped.
   secret_bytes is ``bytes`` of >= 16 bytes (PROSPECTIVE_CONVENTION
   MIN_SCAN_SECRET_BYTES = 16, i.e. 128 bits: below this a secret is too short
   to be a meaningful secret (brute-forceable) and its needles are short enough
   to match unrelated bytes by coincidence, so an absence attestation would
   prove little and a presence finding would be unreliable; at 128 bits the
   chance that one fixed needle occurs by accident in a file of L bytes is about
   L / 2**128). Each file is streamed in 1 MiB chunks with overlap through
   three views:
     raw view       the bytes as stored: the secret itself, and the inner text
                    of Python ``repr(secret)`` (bytes-literal form);
     compact view   the bytes with ASCII whitespace removed (so MIME 76-column,
                    PEM 64-column and indented wrapping disappear): standard
                    and urlsafe base64 at all three byte alignments (only the
                    characters fixed by the secret alone, so padded, unpadded
                    and embedded encodings all match), the big-endian decimal
                    integer of the secret (only when it has >= 20 digits, so a
                    secret with many leading zero bytes cannot match every
                    number), the comma-joined decimal byte values (a JSON or
                    Python list of the secret's bytes, with or without spaces
                    or line wrapping), and the secret with its own whitespace
                    removed (catches pretty-printed copies of canonical JSON);
     hex view       the compact view lowercased with ':' and ',' separators and
                    '0x' prefixes removed: lowercase hex of the secret (covers
                    upper/mixed case, colon-separated, C-array and 0x forms).
   Any entry or directory that cannot be read refuses the scan (``os.walk``
   would otherwise skip it silently, which would read as absence). Returns
   ONLY {"secret_absent": bool, "tree_identity": C.ordered_registry_digest of
   rows {"path", "entry_type", "raw_sha256"} sorted by relative POSIX path,
   "files_scanned": int}: never the secret and never a matching path. An empty
   tree is refused (an attestation over nothing proves nothing).
   ``require_secret_absence`` raises a non-echoing CustodyError when the
   secret is present. RESIDUAL LIMITATIONS (not detected): a secret split
   across files or across non-adjacent places in one file; partial copies;
   arbitrary custom encodings (compressed, encrypted, XOR-ed, reversed,
   UTF-16, other separators or escapes); fully ``\x``-escaped strings (C, JS
   or a Python str of escapes; only the bytes-literal repr form is covered);
   the little-endian decimal integer of the secret; a withheld spec
   re-serialized differently from its canonical bytes (another key order,
   number format, string escaping or whitespace inside strings, or a subset of
   its fields); anything under ``.git`` (history must be
   covered by scanning an export of every published commit's tree);
   symlink targets (links are not followed, only the link text is scanned);
   anything outside the given tree. The controller must scan a full export of
   the exact committed tree (e.g. ``git archive``), never a sparse or dirty
   working copy, and scan once per secret (the qualification nonce and the
   canonical withheld spec bytes at least).

9. UNIQUE WITHHELD CODE PATHS (``attest_no_unique_withheld_code_path(
   withheld_exercised_paths, development_exercised_paths, public_code_paths)
   -> dict``). Each argument is a non-empty collection of non-empty str
   code-path identifiers (a bare string is refused);
   development_exercised_paths is the union over every non-withheld
   development and fixture world. CustodyError if any path in
   (withheld & public) is absent from development_exercised (N3); the error
   gives a count only. Returns ONLY {"no_unique_withheld_public_path": True,
   "public_paths_digest", "development_paths_digest"} (each digest is
   C.semantic_row_set_sha256 over rows {"code_path"}); nothing about the
   withheld paths, not even their count, is returned, and a digest failure
   never echoes an identifier. Identifiers should be the finest granularity
   available (branch or arc coverage): a file- or function-level check cannot
   see a withheld-only branch inside a shared function. Withheld-only code kept
   off-repo is not listed in the public generator_source; the controller binds
   it by putting its hash inside the withheld spec, so the commitment (and
   through it generator_semantic_hash) binds that code without publishing it.
   ``record_withheld_commitment`` requires attestations from decisions 8 and 9
   (all scans absent, one tree identity) before WITHHELD_COMMITTED is appended.

ORDER ENFORCED BY THE LEDGER (per version, live head only).
GENERATOR_FROZEN -> NONCE_COMMITTED (SYNTH_QUALIFICATION; SYNTH_DEBUG when
used; no nonce commitment after the version's first exposure; a nonce
commitment is never reused anywhere in the ledger) -> WITHHELD_COMMITTED
(carries H(qualification nonce) and must equal the SYNTH_QUALIFICATION
NONCE_COMMITTED entry; a successor declares withheld_family_change) ->
REALIZATION_SET_ATTESTED ->
[REQUALIFICATION_PREREQUISITES_RECORDED for POST_EXPOSURE_VERSION /
NEW_SCIENTIFIC_TESTBED] -> EXPOSURE_RECORDED -> FIT_OUTPUT_FROZEN -> REVEALED.
SUCCESSOR_RECORDED precedes the child's GENERATOR_FROZEN and supersedes the
parent. Prospective specification of the withheld family precedes seed
commitment (s1.3) because its commitment is part of the frozen spec.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import math
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np

import scripts.production_synthetic.canonical_v1 as C

__all__ = [
    "CustodyError",
    "SYNTH_DEBUG",
    "SYNTH_QUALIFICATION",
    "E1_FROZEN_COMPONENTS",
    "GeneratorFreeze",
    "ExposureState",
    "VersionDisposition",
    "RealizationAttestation",
    "CustodyLedger",
    "freeze_generator_version",
    "generator_precommitment_semantic_hash",
    "commit_secret",
    "verify_reveal",
    "nonce_commitment",
    "sealed_root",
    "root_commitment",
    "withheld_commitment_payload_hash",
    "withheld_family_commitment",
    "verify_withheld_reveal",
    "authorized_realization_ids",
    "stream_seed_digest",
    "derive_stream",
    "record_generator_freeze",
    "record_nonce_commitment",
    "record_withheld_commitment",
    "attest_realization_set",
    "record_requalification_prerequisites",
    "record_exposure",
    "exposure_state",
    "record_fit_output_frozen",
    "reveal_class_nonce",
    "reveal_withheld_family",
    "validate_successor_version",
    "scan_secret_absence",
    "require_secret_absence",
    "attest_no_unique_withheld_code_path",
    "withheld_check_eligible",
    "qualification_draws_for_method",
    "qualification_draws_in_lineage",
]

SYNTH_DEBUG = "SYNTH_DEBUG"
SYNTH_QUALIFICATION = "SYNTH_QUALIFICATION"
REALIZATION_CLASS_TAGS = (SYNTH_DEBUG, SYNTH_QUALIFICATION)

MIN_NONCE_BYTES = 32
ROOT_BYTES = 32
MIN_SCAN_SECRET_BYTES = 16  # PROSPECTIVE_CONVENTION, decision 8 (128 bits)
MIN_DISTINCT_SECRET_BYTES = 16  # PROSPECTIVE_CONVENTION tripwire, decision 4
MIN_DECIMAL_NEEDLE_DIGITS = 20  # PROSPECTIVE_CONVENTION, decision 8 (about 66 bits)
_SCAN_CHUNK = 1 << 20

_DOMAIN_COMMIT = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-COMMIT-V1\x00"
_DOMAIN_NONCE = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-NONCE-COMMIT-V1\x00"
_DOMAIN_SEALED_ROOT = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-SEALED-ROOT-V1\x00"
_DOMAIN_ROOT_COMMIT = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-ROOT-COMMIT-V1\x00"
_DOMAIN_REALIZATION = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-REALIZATION-ID-V1\x00"
_DOMAIN_STREAM = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-STREAM-V1\x00"
_LEDGER_FORMAT = "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-V1"
_ENTRY_FORMAT = "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-ENTRY-V1"
_GENESIS = "0" * 64

SPEC_COMPONENTS = (
    "generator_source",
    "transitive_dependencies",
    "parameter_distributions",
    "mechanism_mixture",
    "observation_calibration_distributions",
    "difficulty_grid",
    "stress_regimes",
    "challenge_families",
    "applicability_control_matrix",
    "registries",
    "serialization_contract",
    "realization_budgets",
    "withheld_family_commitment",
)
E1_FROZEN_COMPONENTS = tuple(
    c for c in SPEC_COMPONENTS if c not in ("difficulty_grid", "challenge_families", "withheld_family_commitment")
)
_DIGEST_MAP_COMPONENTS = ("generator_source", "transitive_dependencies", "registries")
_MAPPING_COMPONENTS = (
    "parameter_distributions",
    "mechanism_mixture",
    "observation_calibration_distributions",
    "applicability_control_matrix",
    "serialization_contract",
)
CHALLENGE_FAMILY_CATEGORIES = (
    "adverse_regimes",
    "control_families",
    "support_challenges",
    "population_imbalance_challenges",
    "novelty_regimes",
    "measurement_challenges",
)
HARDER_DIRECTIONS = ("increasing", "decreasing")
STREAM_IDENTITY_KEYS = (
    "world_id",
    "component_id",
    "donor_id",
    "cell_id",
    "modality_id",
    "address_id",
    "purpose_tag",
    "draw_index_tag",
)
_REQUIRED_STREAM_KEYS = ("world_id", "purpose_tag")
_WITHHELD_PLAINTEXT_MARKERS = (
    "withheld_spec",
    "withheld_family",
    "withheld_mechanism",
    "withheld_param",
    "withheld_applicab",
    "withheld_scor",
    "withheld_budget",
    "withheld_composition",
    "withheld_variant",
    "withheld_regime",
    "withheld_class",
    "nonce",
    "preimage",
)

WITHHELD_FAMILY_COMPONENT = "withheld_family"  # affected_components entry for a withheld-family change
_AFFECTABLE_COMPONENTS = E1_FROZEN_COMPONENTS + (WITHHELD_FAMILY_COMPONENT,)
WITHHELD_UNCHANGED = "UNCHANGED"
WITHHELD_CHANGED_BY_DEFECT = "CHANGED_BY_DEFECT"
_WITHHELD_CHANGE_VALUES = (WITHHELD_UNCHANGED, WITHHELD_CHANGED_BY_DEFECT)

PRE_EXPOSURE_REVISION = "PRE_EXPOSURE_REVISION"
SUCCESSOR_NOT_EASIER = "SUCCESSOR_NOT_EASIER"
POST_EXPOSURE_VERSION = "POST_EXPOSURE_VERSION"
NEW_SCIENTIFIC_TESTBED = "NEW_SCIENTIFIC_TESTBED"
_FLOOR_DISPOSITIONS = (POST_EXPOSURE_VERSION, NEW_SCIENTIFIC_TESTBED)
DEFECT_JUSTIFICATION = "GENERATOR_DEFECT_AGAINST_FROZEN_SPEC"
_DEFECT_KEYS = frozenset({
    "parent_generator_semantic_hash",
    "child_generator_semantic_hash",
    "defect_description",
    "affected_dimensions",
    "affected_components",
    "generator_side_evidence_sha256",
    "justification_source",
    "incomparable",
})

_REVEAL_CLASS_NONCE = "CLASS_NONCE"
_REVEAL_WITHHELD = "WITHHELD_FAMILY"

_HEX = frozenset("0123456789abcdef")
_CLASS_TAG_RE = re.compile(r"SYNTH_[A-Z0-9_]+")
_WHITESPACE = b" \t\r\n\v\f"


class CustodyError(ValueError):
    """Raised for every custody refusal."""


# --------------------------------------------------------------- primitives

def _frame(b: bytes) -> bytes:
    return len(b).to_bytes(8, "big") + b


def _digest(domain: bytes, *fields: bytes) -> bytes:
    h = hashlib.sha256(domain)
    for f in fields:
        h.update(_frame(f))
    return h.digest()


def _is_hex64(x: Any) -> bool:
    return isinstance(x, str) and len(x) == 64 and set(x) <= _HEX


def _hex64(x: Any, what: str) -> bytes:
    if not _is_hex64(x):
        raise CustodyError(f"{what} must be a 64-character lowercase hex SHA-256")
    return bytes.fromhex(x)


def _secret_shape(b: bytes, what: str) -> None:
    if len(set(b)) < MIN_DISTINCT_SECRET_BYTES:
        raise CustodyError(
            f"{what} has fewer than {MIN_DISTINCT_SECRET_BYTES} distinct byte values; "
            "it looks integer-derived or constant, not a >= 256-bit random secret"
        )


def _nonce(x: Any) -> bytes:
    if not isinstance(x, bytes):
        raise CustodyError(f"nonce must be bytes, got {type(x).__name__}")
    if len(x) < MIN_NONCE_BYTES:
        raise CustodyError(f"nonce must carry at least 256 bits ({MIN_NONCE_BYTES} bytes)")
    _secret_shape(x, "nonce")
    return x


def _root(x: Any) -> bytes:
    if not isinstance(x, bytes):
        raise CustodyError(f"stream root must be bytes (integer seeds are prohibited), got {type(x).__name__}")
    if len(x) != ROOT_BYTES:
        raise CustodyError(f"stream root must be exactly {ROOT_BYTES} bytes")
    _secret_shape(x, "stream root")
    return x


def _tag(tag: Any, what: str) -> bytes:
    if not isinstance(tag, str) or not tag:
        raise CustodyError(f"{what} must be a non-empty str")
    try:
        return tag.encode("utf-8")
    except UnicodeEncodeError:
        raise CustodyError(f"{what} is not valid Unicode text") from None


def _class_tag(tag: Any, what: str = "class tag") -> bytes:
    raw = _tag(tag, what)
    if "DEV" in tag.upper() or "SEALED" in tag.upper():
        raise CustodyError(
            f"{what} may not contain DEV or SEALED (V3.1 s2.2: use SYNTH_DEBUG / SYNTH_QUALIFICATION)"
        )
    if not _CLASS_TAG_RE.fullmatch(tag):
        raise CustodyError(f"{what} must match SYNTH_[A-Z0-9_]+")
    return raw


def _u64(n: Any, what: str, minimum: int) -> bytes:
    if isinstance(n, bool) or not isinstance(n, int):
        raise CustodyError(f"{what} must be an int, got {type(n).__name__}")
    if n < minimum or n >= 2**63:
        raise CustodyError(f"{what} must be in [{minimum}, 2**63)")
    return n.to_bytes(8, "big")


def _semantic(obj: Any, what: str) -> str:
    try:
        return C.semantic_sha256(obj)
    except C.CanonicalError:
        raise CustodyError(f"{what} is not canonically serializable") from None  # no-echo rule


def _canonical_copy(obj: Any, what: str) -> Any:
    try:
        return C.load_canonical_json(C.canonical_json_bytes(obj))
    except C.CanonicalError:
        raise CustodyError(f"{what} is not canonically serializable") from None  # no-echo rule


def _exact_keys(obj: Any, keys: Iterable[str], what: str) -> None:
    if not isinstance(obj, Mapping):
        raise CustodyError(f"{what} must be a mapping")
    keys = set(keys)
    got = set(obj)
    if got != keys:
        missing = sorted(keys - got)  # schema names only
        raise CustodyError(
            f"{what} must have exactly the required keys (missing {missing}; {len(got - keys)} unknown key(s))"
        )


def _nonempty_str(x: Any, what: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise CustodyError(f"{what} must be a non-empty str")
    return x


def _unique_str_list(x: Any, what: str) -> list:
    if isinstance(x, (str, bytes)) or not isinstance(x, (list, tuple)):
        raise CustodyError(f"{what} must be a list")
    for item in x:
        _nonempty_str(item, f"entry of {what}")
    if len(set(x)) != len(x):
        raise CustodyError(f"{what} has duplicates")
    return list(x)


# --------------------------------------------------------- commitments (2)

def commit_secret(nonce: bytes, payload_hash: str, tag: str) -> str:
    """Hiding, binding commitment H(COMMIT; nonce, payload_hash, tag) as hex."""
    return _digest(_DOMAIN_COMMIT, _nonce(nonce), _hex64(payload_hash, "payload_hash"),
                   _tag(tag, "commitment tag")).hex()


def verify_reveal(commitment: str, nonce: bytes, payload_hash: str, tag: str) -> None:
    """Raise CustodyError unless (nonce, payload_hash, tag) opens ``commitment``."""
    _hex64(commitment, "commitment")
    if not hmac.compare_digest(commit_secret(nonce, payload_hash, tag), commitment):
        raise CustodyError("commit/reveal mismatch: hard custody failure")


def nonce_commitment(nonce: bytes) -> str:
    """The published H(nonce) of V3.1 s1.2."""
    return _digest(_DOMAIN_NONCE, _nonce(nonce)).hex()


def sealed_root(nonce: bytes, generator_semantic_hash: str, class_tag: str, realization_budget: int) -> bytes:
    """sealed_root = H(nonce || generator_semantic_hash || class_tag || realization_budget), 32 raw bytes."""
    return _digest(
        _DOMAIN_SEALED_ROOT,
        _nonce(nonce),
        _hex64(generator_semantic_hash, "generator_semantic_hash"),
        _class_tag(class_tag),
        _u64(realization_budget, "realization_budget", 1),
    )


def root_commitment(root: bytes) -> str:
    """Public commitment to a sealed root; the root itself is never published before reveal."""
    return _digest(_DOMAIN_ROOT_COMMIT, _root(root)).hex()


def withheld_commitment_payload_hash(withheld_spec_sha256: str, precommitment_hash: str) -> str:
    """Controller-only payload hash bound by the E2 withheld-family commitment."""
    _hex64(withheld_spec_sha256, "withheld_spec_sha256")
    _hex64(precommitment_hash, "generator_precommitment_semantic_hash")
    return C.semantic_sha256({
        "withheld_spec_sha256": withheld_spec_sha256,
        "generator_precommitment_semantic_hash": precommitment_hash,
    })


def _withheld_spec_sha256(withheld_spec: Any) -> str:
    if not isinstance(withheld_spec, Mapping) or not withheld_spec:
        raise CustodyError("withheld_spec must be a non-empty mapping")
    return _semantic(withheld_spec, "withheld_spec")


def withheld_family_commitment(nonce: bytes, withheld_spec: Mapping, precommitment_hash: str,
                               withheld_class_tag: str) -> str:
    """E2 commitment to the controller-held withheld spec; ``nonce`` is the SYNTH_QUALIFICATION nonce."""
    _class_tag(withheld_class_tag, "withheld class tag")
    payload = withheld_commitment_payload_hash(_withheld_spec_sha256(withheld_spec), precommitment_hash)
    return commit_secret(nonce, payload, withheld_class_tag)


def verify_withheld_reveal(commitment: str, nonce: bytes, withheld_spec: Mapping, precommitment_hash: str,
                           withheld_class_tag: str) -> None:
    """Raise CustodyError unless the revealed withheld family opens ``commitment``."""
    _hex64(commitment, "withheld_family_commitment")
    if not hmac.compare_digest(
        withheld_family_commitment(nonce, withheld_spec, precommitment_hash, withheld_class_tag), commitment
    ):
        raise CustodyError("withheld-family reveal does not open the prior commitment: hard custody failure")


def authorized_realization_ids(root: bytes, class_tag: str, budget: int) -> list:
    """The exact authorized realization ids for (root, class, budget), in index order."""
    r = _root(root)
    t = _class_tag(class_tag)
    _u64(budget, "budget", 1)
    return [_digest(_DOMAIN_REALIZATION, r, t, i.to_bytes(8, "big")).hex() for i in range(budget)]


# ----------------------------------------------------------- streams (4)

def _canonical_identity(identity_parts: tuple) -> bytes:
    ident = {}
    for part in identity_parts:
        if not isinstance(part, (tuple, list)) or len(part) != 2:
            raise CustodyError("each identity part must be a (key, value) pair")
        key, value = part
        if not isinstance(key, str) or key not in STREAM_IDENTITY_KEYS:
            raise CustodyError(f"identity key must be one of {STREAM_IDENTITY_KEYS}")
        if not isinstance(value, str):
            raise CustodyError(
                f"identity value for {key} must be str (integer seed offsets are prohibited), "
                f"got {type(value).__name__}"
            )
        if not value or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
            raise CustodyError(f"identity value for {key} must be non-empty with no control characters")
        if key in ident:
            raise CustodyError(f"duplicate identity key {key}")
        ident[key] = value
    for key in _REQUIRED_STREAM_KEYS:
        if key not in ident:
            raise CustodyError(
                f"{key} is required for every random stream (the same cell in two worlds must never share one)"
            )
    try:
        return C.canonical_json_bytes(ident)
    except C.CanonicalError:
        raise CustodyError("stream identity is not canonically serializable") from None


def stream_seed_digest(root: bytes, *identity_parts) -> bytes:
    """H(STREAM; root, canonical identity): the 32-byte seed of a scientific-identity stream."""
    return _digest(_DOMAIN_STREAM, _root(root), _canonical_identity(identity_parts))


def derive_stream(root: bytes, *identity_parts) -> np.random.Generator:
    """Domain-separated generator for one scientific identity (order-invariant, no integer offsets)."""
    seed = int.from_bytes(stream_seed_digest(root, *identity_parts), "big")
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))


# ------------------------------------------------------ generator freeze (1)

def _norm_marker(text: str) -> str:
    out = text.lower()
    for ch in "- .":
        out = out.replace(ch, "_")
    return out


def _has_marker(text: str) -> bool:
    norm = _norm_marker(text)
    return any(m in norm for m in _WITHHELD_PLAINTEXT_MARKERS)


_PLAINTEXT_REFUSAL = ("public generator spec contains withheld-family plaintext or secret material "
                      "(E2: only the nonce-salted commitment may be public)")


def _reject_withheld_plaintext(spec: Mapping) -> None:
    stack = [(spec, True)]
    seen = set()
    while stack:
        obj, top = stack.pop()
        if isinstance(obj, (Mapping, list, tuple)):
            if id(obj) in seen:
                continue  # cyclic structures are refused later by canonical serialization
            seen.add(id(obj))
        if isinstance(obj, Mapping):
            for k, v in obj.items():
                if not (top and k == "withheld_family_commitment"):
                    if isinstance(k, str) and _has_marker(k):
                        raise CustodyError(_PLAINTEXT_REFUSAL)
                    stack.append((v, False))
        elif isinstance(obj, (list, tuple)):
            stack.extend((v, False) for v in obj)
        elif isinstance(obj, str) and _has_marker(obj):
            raise CustodyError(_PLAINTEXT_REFUSAL)


def _check_number(x: Any, what: str) -> None:
    if isinstance(x, (bool, np.bool_)) or not isinstance(x, (int, float, np.integer, np.floating)):
        raise CustodyError(f"{what} must be a number")
    if isinstance(x, (float, np.floating)) and not math.isfinite(float(x)):
        raise CustodyError(f"{what} must be finite")


def _validate_difficulty_grid(grid: Any) -> None:
    if not isinstance(grid, Mapping) or not grid:
        raise CustodyError("difficulty_grid must be a non-empty mapping")
    for dim, spec in grid.items():
        _nonempty_str(dim, "difficulty dimension name")
        _exact_keys(spec, ("level", "harder_direction"), "a difficulty dimension")
        _check_number(spec["level"], "a difficulty level")
        if spec["harder_direction"] not in HARDER_DIRECTIONS:
            raise CustodyError("harder_direction must be 'increasing' or 'decreasing'")


def _validate_challenge_families(fams: Any) -> None:
    _exact_keys(fams, CHALLENGE_FAMILY_CATEGORIES, "challenge_families")
    for cat in CHALLENGE_FAMILY_CATEGORIES:
        _unique_str_list(fams[cat], f"challenge family {cat}")


def _validate_budgets(budgets: Any) -> None:
    if not isinstance(budgets, Mapping) or not budgets:
        raise CustodyError("realization_budgets must be a non-empty mapping")
    for tag, n in budgets.items():
        if not isinstance(tag, str):
            raise CustodyError("realization budget class tags must be str")
        if "DEV" in tag.upper() or "SEALED" in tag.upper():
            raise CustodyError("realization classes may not be named DEV or SEALED (V3.1 s2.2)")
        if tag not in REALIZATION_CLASS_TAGS:
            raise CustodyError(f"realization budget class tag must be one of {REALIZATION_CLASS_TAGS}")
        _u64(n, f"realization budget for {tag}", 1)
    if SYNTH_QUALIFICATION not in budgets:
        raise CustodyError("realization_budgets must freeze a SYNTH_QUALIFICATION budget")


def _validate_spec(spec: Any) -> None:
    if not isinstance(spec, Mapping):
        raise CustodyError("generator spec must be a mapping")
    _reject_withheld_plaintext(spec)  # first, so no later message can echo withheld material
    _exact_keys(spec, SPEC_COMPONENTS, "generator spec")
    for k in _DIGEST_MAP_COMPONENTS:
        comp = spec[k]
        if not isinstance(comp, Mapping) or not comp:
            raise CustodyError(f"{k} must be a non-empty mapping of name -> 64-hex digest")
        for name, digest in comp.items():
            _nonempty_str(name, f"{k} entry name")
            _hex64(digest, f"{k} digest")
    for k in _MAPPING_COMPONENTS:
        if not isinstance(spec[k], Mapping) or not spec[k]:
            raise CustodyError(f"{k} must be a non-empty mapping")
    stress = spec["stress_regimes"]
    if not isinstance(stress, Mapping) or not stress:
        raise CustodyError("stress_regimes must be a non-empty mapping of regime name -> definition")
    for name, definition in stress.items():
        _nonempty_str(name, "stress regime name")
        if definition is None:
            raise CustodyError("a stress regime has no definition")
    _validate_difficulty_grid(spec["difficulty_grid"])
    _validate_challenge_families(spec["challenge_families"])
    _validate_budgets(spec["realization_budgets"])
    _hex64(spec["withheld_family_commitment"], "withheld_family_commitment")


def _precommitment_hash(spec: Mapping) -> str:
    return _semantic(
        {"generator_precommitment_v1": {k: v for k, v in spec.items() if k != "withheld_family_commitment"}},
        "generator spec",
    )


def _e1_profile(spec: Mapping) -> dict:
    return {
        "difficulty_grid": {d: {"level": v["level"], "harder_direction": v["harder_direction"]}
                            for d, v in spec["difficulty_grid"].items()},
        "challenge_families": {c: sorted(spec["challenge_families"][c]) for c in CHALLENGE_FAMILY_CATEGORIES},
        "component_hashes": {c: _semantic(spec[c], "generator component") for c in E1_FROZEN_COMPONENTS},
    }


@dataclass(frozen=True)
class GeneratorFreeze:
    """Immutable frozen generator identity (V3.1 s1.1); every field is re-derived and checked."""

    generator_semantic_hash: str
    precommitment_semantic_hash: str
    withheld_family_commitment: str
    canonical_spec: bytes = field(repr=False)

    def __post_init__(self):
        if not isinstance(self.canonical_spec, bytes):
            raise CustodyError("canonical_spec must be bytes")
        try:
            obj = C.load_canonical_json(self.canonical_spec)
            recanon = C.canonical_json_bytes(obj)
        except C.CanonicalError:
            raise CustodyError("canonical_spec is not a canonical JSON spec") from None
        if recanon != self.canonical_spec:
            raise CustodyError("canonical_spec is not in canonical form")
        _validate_spec(obj)
        if self.generator_semantic_hash != C.semantic_sha256(obj):
            raise CustodyError("generator_semantic_hash does not match the frozen spec")
        if self.precommitment_semantic_hash != _precommitment_hash(obj):
            raise CustodyError("precommitment_semantic_hash does not match the frozen spec")
        if self.withheld_family_commitment != obj["withheld_family_commitment"]:
            raise CustodyError("withheld_family_commitment does not match the frozen spec")

    def spec(self) -> dict:
        """A fresh deep copy of the frozen spec."""
        return C.load_canonical_json(self.canonical_spec)

    def realization_budgets(self) -> dict:
        return dict(self.spec()["realization_budgets"])

    def realization_budget(self, class_tag: str) -> int:
        budgets = self.realization_budgets()
        if class_tag not in budgets:
            raise CustodyError("class tag has no frozen realization budget in this generator version")
        return budgets[class_tag]

    def e1_profile(self) -> dict:
        return _e1_profile(self.spec())


def freeze_generator_version(spec: Mapping) -> GeneratorFreeze:
    """Validate and freeze a production generator version (decision 1)."""
    _validate_spec(spec)
    try:
        canon = C.canonical_json_bytes(spec)
        obj = C.load_canonical_json(canon)
    except C.CanonicalError:
        raise CustodyError("generator spec is not canonically serializable") from None
    return GeneratorFreeze(
        generator_semantic_hash=C.semantic_sha256(obj),
        precommitment_semantic_hash=_precommitment_hash(obj),
        withheld_family_commitment=obj["withheld_family_commitment"],
        canonical_spec=canon,
    )


def generator_precommitment_semantic_hash(spec_without_commitment: Mapping) -> str:
    """Identity the E2 commitment binds: the spec before its withheld commitment exists."""
    if not isinstance(spec_without_commitment, Mapping):
        raise CustodyError("generator spec must be a mapping")
    if "withheld_family_commitment" in spec_without_commitment:
        raise CustodyError("pass the spec WITHOUT withheld_family_commitment; it is computed from this hash")
    _validate_spec(dict(spec_without_commitment, withheld_family_commitment=_GENESIS))
    return _precommitment_hash(spec_without_commitment)


# ------------------------------------------------------------- ledger (3)

_ENTRY_KEYS = frozenset({"index", "kind", "payload", "prev_entry_hash", "entry_hash"})


class CustodyLedger:
    """Append-only, hash-chained custody ledger; every write is precondition-checked."""

    def __init__(self):
        self._entries = []

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def head(self) -> str:
        return self._entries[-1]["entry_hash"] if self._entries else _GENESIS

    def entries(self) -> list:
        """Deep copies of the entries; mutating them cannot change the ledger."""
        return _canonical_copy(self._entries, "ledger")

    def to_bytes(self) -> bytes:
        try:
            return C.canonical_json_bytes({"format": _LEDGER_FORMAT, "entries": self._entries})
        except C.CanonicalError:
            raise CustodyError("ledger is not canonically serializable") from None

    @classmethod
    def from_bytes(cls, raw: bytes, *, expected_head: str | None = None) -> "CustodyLedger":
        """Parse, re-chain and REPLAY every entry through the custody validators."""
        if not isinstance(raw, bytes):
            raise CustodyError("ledger bytes required")
        try:
            obj = C.load_canonical_json(raw)
        except C.CanonicalError:
            raise CustodyError("ledger is not valid canonical JSON") from None
        _exact_keys(obj, ("format", "entries"), "ledger")
        if obj["format"] != _LEDGER_FORMAT or not isinstance(obj["entries"], list):
            raise CustodyError("unrecognized ledger format")
        led = cls()
        for i, e in enumerate(obj["entries"]):
            if not isinstance(e, dict) or set(e) != _ENTRY_KEYS:
                raise CustodyError(f"ledger entry {i} is malformed")
            if type(e["index"]) is not int or e["index"] != i:
                raise CustodyError(f"ledger entry {i} has a wrong index")
            if e["prev_entry_hash"] != led.head:
                raise CustodyError(f"ledger entry {i} breaks the hash chain")
            try:
                led._append(e["kind"], e["payload"])
            except CustodyError as exc:
                raise CustodyError(f"ledger entry {i} fails custody replay: {exc}") from exc
            if led.head != e["entry_hash"]:
                raise CustodyError(f"ledger entry {i} hash mismatch (tampered)")
        if expected_head is not None:
            _hex64(expected_head, "expected_head")
            if led.head != expected_head:
                raise CustodyError("ledger head does not match the anchored head (truncated, re-chained or forged)")
        return led

    def verify(self, *, expected_head: str | None = None) -> str:
        """Replay this ledger from its own bytes; return the verified head."""
        return CustodyLedger.from_bytes(self.to_bytes(), expected_head=expected_head).head

    def _append(self, kind: str, payload: Any) -> str:
        if not isinstance(kind, str) or kind not in _VALIDATORS:
            raise CustodyError("unknown ledger entry kind")
        payload = _canonical_copy(payload, "ledger payload")
        _VALIDATORS[kind](self, payload)
        index = len(self._entries)
        prev = self.head
        entry_hash = C.semantic_sha256(
            {"format": _ENTRY_FORMAT, "index": index, "kind": kind, "payload": payload, "prev_entry_hash": prev}
        )
        self._entries.append(
            {"index": index, "kind": kind, "payload": payload, "prev_entry_hash": prev, "entry_hash": entry_hash}
        )
        return entry_hash


def _require_ledger(ledger: Any) -> CustodyLedger:
    if not isinstance(ledger, CustodyLedger):
        raise CustodyError("a CustodyLedger is required")
    return ledger


def _require_freeze_obj(freeze: Any) -> GeneratorFreeze:
    if not isinstance(freeze, GeneratorFreeze):
        raise CustodyError("a GeneratorFreeze is required")
    return freeze


def _payloads(led: CustodyLedger, kind: str, **match) -> list:
    return [e["payload"] for e in led._entries
            if e["kind"] == kind and all(e["payload"].get(k) == v for k, v in match.items())]


def _frozen_freeze(led: CustodyLedger, gsh: Any) -> GeneratorFreeze:
    found = _payloads(led, "GENERATOR_FROZEN", generator_semantic_hash=gsh)
    if not found:
        raise CustodyError("generator version is not frozen in this ledger")
    return freeze_generator_version(found[0]["spec"])


def _require_live_version(led: CustodyLedger, gsh: str) -> None:
    """Strictly linear lineage: only the latest frozen version without a recorded successor is usable."""
    frozen = _payloads(led, "GENERATOR_FROZEN")
    if (not frozen or frozen[-1]["generator_semantic_hash"] != gsh
            or _payloads(led, "SUCCESSOR_RECORDED", parent_generator_semantic_hash=gsh)):
        raise CustodyError(
            "generator version is superseded or is not the lineage head; only the live head may be committed, "
            "attested or exposed (strictly linear lineage)"
        )


def _exposed(led: CustodyLedger, gsh: str) -> bool:
    return bool(_payloads(led, "EXPOSURE_RECORDED", generator_semantic_hash=gsh))


def _revealed_qualification(led: CustodyLedger, gsh: str) -> bool:
    return bool(
        _payloads(led, "REVEALED", reveal_type=_REVEAL_CLASS_NONCE, generator_semantic_hash=gsh,
                  class_tag=SYNTH_QUALIFICATION)
        or _payloads(led, "REVEALED", reveal_type=_REVEAL_WITHHELD, generator_semantic_hash=gsh)
    )


def _successor_records(led: CustodyLedger) -> dict:
    return {p["child_generator_semantic_hash"]: p for p in _payloads(led, "SUCCESSOR_RECORDED")}


def _needs_requalification(led: CustodyLedger, gsh: str) -> bool:
    rec = _successor_records(led).get(gsh)
    return rec is not None and rec["disposition"] in _FLOOR_DISPOSITIONS


def _superseded(led: CustodyLedger, gsh: str) -> bool:
    return bool(_payloads(led, "SUCCESSOR_RECORDED", parent_generator_semantic_hash=gsh))


def _lineage_chain(led: CustodyLedger, gsh: str) -> list:
    """``gsh`` followed by its ancestors back to the lineage root (the lineage is linear)."""
    succ = _successor_records(led)
    out = []
    g = gsh
    while g is not None:
        out.append(g)
        rec = succ.get(g)
        g = rec["parent_generator_semantic_hash"] if rec is not None else None
    return out


def _descendants(led: CustodyLedger, gsh: str) -> list:
    frozen = [f["generator_semantic_hash"] for f in _payloads(led, "GENERATOR_FROZEN")]
    return frozen[frozen.index(gsh) + 1:] if gsh in frozen else []


def _withheld_reference(led: CustodyLedger, gsh: str):
    """Nearest ancestor that committed a withheld family: the lineage's frozen family for ``gsh``."""
    for g in _lineage_chain(led, gsh)[1:]:
        if _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=g):
            return g
    return None


def _shared_family_versions(led: CustodyLedger, gsh: str, change: Any) -> list:
    """Ancestors that, by UNCHANGED declarations, carry the same withheld family as ``gsh``."""
    out = []
    g, declared = gsh, change
    while declared == WITHHELD_UNCHANGED:
        ref = _withheld_reference(led, g)
        if ref is None:
            break
        out.append(ref)
        committed = _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=ref)
        g, declared = ref, committed[0]["withheld_family_change"]
    return out


def _withheld_revealed(led: CustodyLedger, gsh: str) -> bool:
    return bool(_payloads(led, "REVEALED", reveal_type=_REVEAL_WITHHELD, generator_semantic_hash=gsh))


def _family_disclosed(led: CustodyLedger, gsh: str) -> bool:
    """The family is disclosed by its withheld reveal or by the qualification nonce that opens its commitment."""
    return _withheld_revealed(led, gsh) or bool(_payloads(
        led, "REVEALED", reveal_type=_REVEAL_CLASS_NONCE, generator_semantic_hash=gsh, class_tag=SYNTH_QUALIFICATION))


def _family_group(led: CustodyLedger, gsh: str) -> set:
    """Every version carrying the same withheld family as ``gsh`` through UNCHANGED declarations, both directions."""
    committed = _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=gsh)
    if not committed:
        return {gsh}
    group = {gsh} | set(_shared_family_versions(led, gsh, committed[0]["withheld_family_change"]))
    for p in _payloads(led, "WITHHELD_COMMITTED"):
        if gsh in _shared_family_versions(led, p["generator_semantic_hash"], p["withheld_family_change"]):
            group.add(p["generator_semantic_hash"])
    return group


def _previously_public(led: CustodyLedger, gsh: str, withheld_spec: Any) -> bool:
    """True if a family revealed earlier by a version outside this version's family group is identical (Q3)."""
    this = _semantic(withheld_spec, "withheld_spec")
    group = _family_group(led, gsh)
    return any(_semantic(r["withheld_spec"], "withheld_spec") == this
               for r in _payloads(led, "REVEALED", reveal_type=_REVEAL_WITHHELD)
               if r["generator_semantic_hash"] not in group)


def _open_qualification_runs(led: CustodyLedger) -> set:
    exposed = {p["generator_semantic_hash"] for p in _payloads(led, "EXPOSURE_RECORDED",
                                                               realization_class=SYNTH_QUALIFICATION)}
    frozen = {p["generator_semantic_hash"] for p in _payloads(led, "FIT_OUTPUT_FROZEN",
                                                              class_tag=SYNTH_QUALIFICATION)}
    return exposed - frozen


# ---------------------------------------------------------- E1 comparison

def _validate_e1_profile(profile: Any) -> None:
    _exact_keys(profile, ("difficulty_grid", "challenge_families", "component_hashes"), "E1 profile")
    _validate_difficulty_grid(profile["difficulty_grid"])
    _validate_challenge_families(profile["challenge_families"])
    hashes = profile["component_hashes"]
    _exact_keys(hashes, E1_FROZEN_COMPONENTS, "E1 component hashes")
    for c in E1_FROZEN_COMPONENTS:
        _hex64(hashes[c], "E1 component hash")


def _easier(old: Mapping, new: Mapping) -> dict:
    out = {}
    og, ng = old["difficulty_grid"], new["difficulty_grid"]
    for dim in sorted(og):
        key = f"difficulty_grid/{dim}"
        if dim not in ng:
            out[key] = "removed"
            continue
        o, n = og[dim], ng[dim]
        if o["harder_direction"] != n["harder_direction"]:
            out[key] = "harder_direction_changed"
        elif o["harder_direction"] == "increasing" and n["level"] < o["level"]:
            out[key] = "relaxed"
        elif o["harder_direction"] == "decreasing" and n["level"] > o["level"]:
            out[key] = "relaxed"
    for cat in CHALLENGE_FAMILY_CATEGORIES:
        for name in sorted(set(old["challenge_families"][cat]) - set(new["challenge_families"][cat])):
            out[f"challenge_families/{cat}/{name}"] = "removed"
    return out


def _changed_components(old: Mapping, new: Mapping) -> list:
    return [c for c in E1_FROZEN_COMPONENTS if old["component_hashes"][c] != new["component_hashes"][c]]


def _validate_defect_record(rec: Any, parent: str, child: str) -> dict:
    _exact_keys(rec, _DEFECT_KEYS, "defect_record")
    if rec["justification_source"] != DEFECT_JUSTIFICATION:
        raise CustodyError(
            f"defect_record.justification_source must be {DEFECT_JUSTIFICATION}: E1 forbids relaxing or "
            "deleting a regime because a downstream method failed on it"
        )
    if rec["parent_generator_semantic_hash"] != parent or rec["child_generator_semantic_hash"] != child:
        raise CustodyError("defect_record must name the exact parent and child generator hashes")
    _nonempty_str(rec["defect_description"], "defect_record.defect_description")
    _hex64(rec["generator_side_evidence_sha256"], "defect_record.generator_side_evidence_sha256")
    dims = _unique_str_list(rec["affected_dimensions"], "defect_record.affected_dimensions")
    comps = _unique_str_list(rec["affected_components"], "defect_record.affected_components")
    if any(c not in _AFFECTABLE_COMPONENTS for c in comps):
        raise CustodyError(f"defect_record.affected_components may name only {_AFFECTABLE_COMPONENTS}")
    if not dims and not comps:
        raise CustodyError("defect_record must name at least one affected dimension or component")
    if not isinstance(rec["incomparable"], bool):
        raise CustodyError("defect_record.incomparable must be a bool")
    return rec


def _compute_disposition(led, parent, child, child_profile, defect_record):
    """Return (disposition, easier dims dict, changed components list, floor hash or None) per decision 6."""
    if defect_record is not None:
        _validate_defect_record(defect_record, parent, child)
    succ = _successor_records(led)
    chain = _lineage_chain(led, parent)
    floor = None
    for g in chain:
        rec = succ.get(g)
        if _exposed(led, g) or (rec is not None and rec["disposition"] in _FLOOR_DISPOSITIONS):
            floor = g
            break
    if floor is not None:
        withheld_changes = (defect_record is not None
                            and WITHHELD_FAMILY_COMPONENT in defect_record["affected_components"])
        if not withheld_changes:
            references = [parent] + [g for g in chain if _exposed(led, g)]
            if any(_frozen_freeze(led, g).e1_profile() == child_profile for g in references):
                raise CustodyError(
                    "W2: reroll/seed-shopping prohibited: after exposure, a successor identical in every public "
                    "component to its parent or to an exposed ancestor, with the same withheld family, would only "
                    "redraw the sealed realizations"
                )
    reference = _frozen_freeze(led, floor if floor is not None else parent).e1_profile()
    easier = _easier(reference, child_profile)
    changed = _changed_components(reference, child_profile)
    if floor is None:
        return PRE_EXPOSURE_REVISION, easier, changed, None
    if defect_record is None:
        if easier or changed:
            raise CustodyError(
                f"E1: successor of an exposed lineage is easier than its floor in {len(easier)} dimension(s) and "
                f"changes frozen component(s) {changed}; this requires a documented generator-defect record"
            )
        return SUCCESSOR_NOT_EASIER, easier, changed, floor
    uncovered_dims = set(easier) - set(defect_record["affected_dimensions"])
    if uncovered_dims:
        raise CustodyError(
            f"defect_record.affected_dimensions does not cover {len(uncovered_dims)} easier dimension(s)"
        )
    uncovered_comps = [c for c in changed if c not in defect_record["affected_components"]]
    if uncovered_comps:
        raise CustodyError(f"defect_record.affected_components does not cover changed component(s) {uncovered_comps}")
    disposition = NEW_SCIENTIFIC_TESTBED if defect_record["incomparable"] else POST_EXPOSURE_VERSION
    return disposition, easier, changed, floor


# -------------------------------------------------------------- validators

def _check_code_path_attestation(cpa: Any) -> None:
    _exact_keys(cpa, ("no_unique_withheld_public_path", "public_paths_digest", "development_paths_digest"),
                "code_path_attestation")
    if cpa["no_unique_withheld_public_path"] is not True:
        raise CustodyError("code-path attestation does not attest the absence of a unique withheld public path")
    _hex64(cpa["public_paths_digest"], "public_paths_digest")
    _hex64(cpa["development_paths_digest"], "development_paths_digest")


def _v_generator_frozen(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("generator_semantic_hash", "spec"), "GENERATOR_FROZEN payload")
    fr = freeze_generator_version(p["spec"])
    gsh = fr.generator_semantic_hash
    if gsh != p["generator_semantic_hash"]:
        raise CustodyError("GENERATOR_FROZEN hash does not match its spec")
    frozen = _payloads(led, "GENERATOR_FROZEN")
    if any(f["generator_semantic_hash"] == gsh for f in frozen):
        raise CustodyError("generator version is already frozen in this ledger")
    if not frozen:
        return  # lineage root
    head = frozen[-1]["generator_semantic_hash"]
    rec = _successor_records(led).get(gsh)
    if rec is None or rec["parent_generator_semantic_hash"] != head:
        raise CustodyError(
            "a new version in an existing lineage must first pass validate_successor_version against the "
            "lineage head (E1)"
        )
    if rec["child_e1_profile"] != fr.e1_profile():
        raise CustodyError("frozen child differs from the profile validated in SUCCESSOR_RECORDED")


def _v_nonce_committed(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("generator_semantic_hash", "class_tag", "nonce_commitment"), "NONCE_COMMITTED payload")
    fr = _frozen_freeze(led, p["generator_semantic_hash"])
    gsh, tag = fr.generator_semantic_hash, p["class_tag"]
    _require_live_version(led, gsh)
    _class_tag(tag)
    fr.realization_budget(tag)
    _hex64(p["nonce_commitment"], "nonce_commitment")
    if _payloads(led, "NONCE_COMMITTED", generator_semantic_hash=gsh, class_tag=tag):
        raise CustodyError("a nonce is already committed for this class: seed replacement is prohibited")
    if _payloads(led, "NONCE_COMMITTED", nonce_commitment=p["nonce_commitment"]):
        raise CustodyError("nonce reuse across classes or versions is prohibited")
    if _exposed(led, gsh):
        raise CustodyError("s1.2: nonces must be committed before any downstream exposure of this version")


def _v_withheld_committed(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("generator_semantic_hash", "withheld_class_tag", "withheld_family_commitment",
                    "nonce_commitment", "withheld_family_change", "withheld_check_secret", "secret_absence",
                    "code_path_attestation"), "WITHHELD_COMMITTED payload")
    fr = _frozen_freeze(led, p["generator_semantic_hash"])
    gsh = fr.generator_semantic_hash
    _require_live_version(led, gsh)
    _class_tag(p["withheld_class_tag"], "withheld class tag")
    change = p["withheld_family_change"]
    rec = _successor_records(led).get(gsh)
    if rec is None:
        if change is not None:
            raise CustodyError("the lineage root declares no withheld_family_change")
    else:
        if not isinstance(change, str) or change not in _WITHHELD_CHANGE_VALUES:
            raise CustodyError(f"a successor must declare withheld_family_change as one of {_WITHHELD_CHANGE_VALUES}")
        listed = (rec["defect_record"] is not None
                  and WITHHELD_FAMILY_COMPONENT in rec["defect_record"]["affected_components"])
        if change == WITHHELD_CHANGED_BY_DEFECT and not listed:
            raise CustodyError(
                "W1: CHANGED_BY_DEFECT requires the successor's defect record to list withheld_family in "
                "affected_components; the withheld family is otherwise frozen for the lineage"
            )
        if change == WITHHELD_UNCHANGED and listed:
            raise CustodyError("W1: the successor's defect record declares a withheld-family change, not UNCHANGED")
    secret = not any(_family_disclosed(led, g) for g in _shared_family_versions(led, gsh, change))
    if p["withheld_check_secret"] is not secret:
        raise CustodyError("withheld_check_secret does not match the ledger (whether the reused family is public)")
    if p["withheld_family_commitment"] != fr.withheld_family_commitment:
        raise CustodyError("WITHHELD_COMMITTED does not match the commitment bound by the frozen generator")
    _hex64(p["nonce_commitment"], "nonce_commitment")
    qual = _payloads(led, "NONCE_COMMITTED", generator_semantic_hash=gsh, class_tag=SYNTH_QUALIFICATION)
    if not qual:
        raise CustodyError(
            "E2: the withheld commitment's nonce is the SYNTH_QUALIFICATION sealed nonce; commit it first"
        )
    if not hmac.compare_digest(p["nonce_commitment"], qual[0]["nonce_commitment"]):
        raise CustodyError("E2: the withheld commitment must be bound to the SYNTH_QUALIFICATION sealed nonce")
    if _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=gsh):
        raise CustodyError("the withheld family is already committed for this generator version")
    if _exposed(led, gsh):
        raise CustodyError("E2: the withheld family must be committed before any downstream exposure")
    sa = p["secret_absence"]
    _exact_keys(sa, ("tree_identity", "secrets_scanned", "files_scanned"), "secret_absence record")
    _hex64(sa["tree_identity"], "tree_identity")
    _u64(sa["secrets_scanned"], "secrets_scanned", 1)
    _u64(sa["files_scanned"], "files_scanned", 1)
    _check_code_path_attestation(p["code_path_attestation"])


def _v_realization_set(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("generator_semantic_hash", "class_tag", "budget", "root_commitment", "authorized_ids_digest",
                    "emitted_set_sha256", "n_emitted"), "REALIZATION_SET_ATTESTED payload")
    fr = _frozen_freeze(led, p["generator_semantic_hash"])
    gsh, tag = fr.generator_semantic_hash, p["class_tag"]
    _require_live_version(led, gsh)
    _class_tag(tag)
    if type(p["budget"]) is not int or p["budget"] != fr.realization_budget(tag):
        raise CustodyError("attested budget must equal the frozen realization budget exactly")
    if type(p["n_emitted"]) is not int or p["n_emitted"] != p["budget"]:
        raise CustodyError("the attested set must contain exactly the budgeted number of realizations")
    for k in ("root_commitment", "authorized_ids_digest", "emitted_set_sha256"):
        _hex64(p[k], k)
    if not _payloads(led, "NONCE_COMMITTED", generator_semantic_hash=gsh, class_tag=tag):
        raise CustodyError("s1.2: the class nonce must be committed before its realizations are attested")
    if _payloads(led, "REALIZATION_SET_ATTESTED", generator_semantic_hash=gsh, class_tag=tag):
        raise CustodyError("s1.3: the realization set for this class is already attested; no re-emission")
    if _payloads(led, "REALIZATION_SET_ATTESTED", root_commitment=p["root_commitment"]):
        raise CustodyError("a sealed root may back only one attested realization set")


def _v_requalification(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("generator_semantic_hash", "realism_rerun_receipt_sha256", "withheld_check_plan_sha256"),
                "REQUALIFICATION_PREREQUISITES_RECORDED payload")
    fr = _frozen_freeze(led, p["generator_semantic_hash"])
    gsh = fr.generator_semantic_hash
    _require_live_version(led, gsh)
    _hex64(p["realism_rerun_receipt_sha256"], "realism_rerun_receipt_sha256")
    _hex64(p["withheld_check_plan_sha256"], "withheld_check_plan_sha256")
    if not _needs_requalification(led, gsh):
        raise CustodyError(
            "requalification prerequisites apply only to POST_EXPOSURE_VERSION / NEW_SCIENTIFIC_TESTBED versions"
        )
    if _payloads(led, "REQUALIFICATION_PREREQUISITES_RECORDED", generator_semantic_hash=gsh):
        raise CustodyError("requalification prerequisites are already recorded for this version")


def _v_exposure(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("generator_semantic_hash", "exposure_id", "method_id", "realization_class"),
                "EXPOSURE_RECORDED payload")
    fr = _frozen_freeze(led, p["generator_semantic_hash"])
    gsh, tag = fr.generator_semantic_hash, p["realization_class"]
    _require_live_version(led, gsh)
    _nonempty_str(p["exposure_id"], "exposure_id")
    _hex64(p["method_id"], "method_id (content digest of the frozen method code + configuration)")
    _class_tag(tag, "realization_class")
    fr.realization_budget(tag)
    if not _payloads(led, "NONCE_COMMITTED", generator_semantic_hash=gsh, class_tag=SYNTH_QUALIFICATION):
        raise CustodyError("s1.2: no downstream exposure before the qualification nonce commitment")
    if not _payloads(led, "NONCE_COMMITTED", generator_semantic_hash=gsh, class_tag=tag):
        raise CustodyError("s1.2: no downstream exposure before the exposed class's nonce commitment")
    if not _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=gsh):
        raise CustodyError("E2: no downstream exposure before the withheld-family commitment")
    if not _payloads(led, "REALIZATION_SET_ATTESTED", generator_semantic_hash=gsh, class_tag=tag):
        raise CustodyError("s1.3: no downstream exposure before the class realization set is attested")
    if _needs_requalification(led, gsh) and not _payloads(
            led, "REQUALIFICATION_PREREQUISITES_RECORDED", generator_semantic_hash=gsh):
        raise CustodyError(
            "E1: a POST_EXPOSURE_VERSION / NEW_SCIENTIFIC_TESTBED version needs recorded requalification "
            "prerequisites (realism rerun receipt and withheld-check plan) before any exposure"
        )
    if _payloads(led, "EXPOSURE_RECORDED", generator_semantic_hash=gsh, exposure_id=p["exposure_id"]):
        raise CustodyError("duplicate exposure_id for this generator version")
    if tag == SYNTH_QUALIFICATION and _revealed_qualification(led, gsh):
        raise CustodyError("the sealed qualification secrets are revealed; no further qualification exposure")


def _v_fit_output(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("generator_semantic_hash", "class_tag", "fit_output_sha256"), "FIT_OUTPUT_FROZEN payload")
    fr = _frozen_freeze(led, p["generator_semantic_hash"])
    gsh, tag = fr.generator_semantic_hash, p["class_tag"]
    _class_tag(tag)
    _hex64(p["fit_output_sha256"], "fit_output_sha256")
    if not _payloads(led, "REALIZATION_SET_ATTESTED", generator_semantic_hash=gsh, class_tag=tag):
        raise CustodyError("fit output cannot be frozen for an unattested realization set")
    if not _payloads(led, "EXPOSURE_RECORDED", generator_semantic_hash=gsh, realization_class=tag):
        raise CustodyError("fit output cannot be frozen before a recorded exposure of that class")
    if _payloads(led, "FIT_OUTPUT_FROZEN", generator_semantic_hash=gsh, class_tag=tag):
        raise CustodyError("fit output for this class is already irrevocably frozen")


def _nonce_from_hex(x: Any) -> bytes:
    if not isinstance(x, str) or len(x) % 2 or not set(x) <= _HEX:
        raise CustodyError("revealed nonce must be lowercase hex")
    return _nonce(bytes.fromhex(x))


def _v_revealed(led: CustodyLedger, p: dict) -> None:
    if not isinstance(p, Mapping):
        raise CustodyError("REVEALED payload must be a mapping")
    rt = p.get("reveal_type")
    if rt == _REVEAL_CLASS_NONCE:
        _exact_keys(p, ("reveal_type", "generator_semantic_hash", "class_tag", "nonce_hex"), "REVEALED payload")
        fr = _frozen_freeze(led, p["generator_semantic_hash"])
        gsh, tag = fr.generator_semantic_hash, p["class_tag"]
        _class_tag(tag)
        nonce = _nonce_from_hex(p["nonce_hex"])
        if not _payloads(led, "FIT_OUTPUT_FROZEN", generator_semantic_hash=gsh, class_tag=tag):
            raise CustodyError("s1.2: a nonce is revealed only after that class's fit output is irrevocably frozen")
        if _payloads(led, "REVEALED", reveal_type=rt, generator_semantic_hash=gsh, class_tag=tag):
            raise CustodyError("this class nonce is already revealed")
        if (tag == SYNTH_QUALIFICATION and _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=gsh)
                and _family_group(led, gsh) & _open_qualification_runs(led)):
            raise CustodyError(
                "Q1: the qualification nonce opens this version's withheld commitment; no reveal while a version "
                "sharing that withheld family has an open sealed qualification run"
            )
        committed = _payloads(led, "NONCE_COMMITTED", generator_semantic_hash=gsh, class_tag=tag)[0]
        if not hmac.compare_digest(nonce_commitment(nonce), committed["nonce_commitment"]):
            raise CustodyError("revealed nonce does not match the committed H(nonce): hard custody failure")
        att = _payloads(led, "REALIZATION_SET_ATTESTED", generator_semantic_hash=gsh, class_tag=tag)[0]
        root = sealed_root(nonce, gsh, tag, att["budget"])
        if not hmac.compare_digest(root_commitment(root), att["root_commitment"]):
            raise CustodyError(
                "attested realizations were not drawn from the committed nonce (seed replacement or shopping): "
                "hard custody failure"
            )
        ids = authorized_realization_ids(root, tag, att["budget"])
        ids_digest = C.semantic_row_set_sha256([{"realization_id": r} for r in ids], ["realization_id"])
        if ids_digest != att["authorized_ids_digest"]:
            raise CustodyError("attested authorized-id set does not match the revealed root: hard custody failure")
    elif rt == _REVEAL_WITHHELD:
        _exact_keys(p, ("reveal_type", "generator_semantic_hash", "withheld_class_tag", "nonce_hex",
                        "withheld_spec", "family_previously_public"), "REVEALED payload")
        fr = _frozen_freeze(led, p["generator_semantic_hash"])
        gsh = fr.generator_semantic_hash
        nonce = _nonce_from_hex(p["nonce_hex"])
        if not _payloads(led, "FIT_OUTPUT_FROZEN", generator_semantic_hash=gsh, class_tag=SYNTH_QUALIFICATION):
            early_reference_reveal = (
                _superseded(led, gsh)
                and not _payloads(led, "EXPOSURE_RECORDED", generator_semantic_hash=gsh,
                                  realization_class=SYNTH_QUALIFICATION)
                and any(_payloads(led, "FIT_OUTPUT_FROZEN", generator_semantic_hash=d, class_tag=SYNTH_QUALIFICATION)
                        for d in _descendants(led, gsh))
            )
            if not early_reference_reveal:
                raise CustodyError(
                    "E2: the withheld family is revealed only after the sealed fit output is frozen (a superseded "
                    "version with no sealed run of its own: only after a descendant's qualification fit is frozen)"
                )
        if _payloads(led, "REVEALED", reveal_type=rt, generator_semantic_hash=gsh):
            raise CustodyError("the withheld family is already revealed")
        committed = _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=gsh)[0]
        if p["withheld_class_tag"] != committed["withheld_class_tag"]:
            raise CustodyError("withheld class tag differs from the committed tag: hard custody failure")
        if not hmac.compare_digest(nonce_commitment(nonce), committed["nonce_commitment"]):
            raise CustodyError(
                "E2: the withheld family opens only with the SYNTH_QUALIFICATION sealed nonce: hard custody failure"
            )
        verify_withheld_reveal(fr.withheld_family_commitment, nonce, p["withheld_spec"],
                               fr.precommitment_semantic_hash, p["withheld_class_tag"])
        reference = _withheld_reference(led, gsh)
        prior = None
        if reference is not None:
            prior = _payloads(led, "REVEALED", reveal_type=rt, generator_semantic_hash=reference)
            if not prior:
                raise CustodyError("W1: the lineage's earlier withheld family must be revealed first")
        if _open_qualification_runs(led):  # includes this version's own run
            raise CustodyError(
                "no withheld reveal while a sealed qualification run in the lineage is still open (a shared "
                "withheld family would be disclosed before that fit is frozen)"
            )
        if reference is not None:
            same = _semantic(p["withheld_spec"], "withheld_spec") == _semantic(prior[0]["withheld_spec"],
                                                                               "withheld_spec")
            change = committed["withheld_family_change"]
            if change == WITHHELD_UNCHANGED and not same:
                raise CustodyError(
                    "W1: the revealed withheld family differs from the lineage's frozen withheld family although "
                    "declared UNCHANGED: hard custody failure; the qualification of this version is void"
                )
            if change == WITHHELD_CHANGED_BY_DEFECT and same:
                raise CustodyError(
                    "W1: the declared withheld-family change is not a change (a disguised reroll): hard custody "
                    "failure"
                )
        if p["family_previously_public"] is not _previously_public(led, gsh, p["withheld_spec"]):
            raise CustodyError("family_previously_public does not match the ledger's earlier reveals")
    else:
        raise CustodyError("unknown reveal_type")


def _v_successor(led: CustodyLedger, p: dict) -> None:
    _exact_keys(p, ("parent_generator_semantic_hash", "child_generator_semantic_hash", "child_e1_profile",
                    "defect_record", "disposition", "easier_dimensions", "changed_components",
                    "floor_generator_semantic_hash"), "SUCCESSOR_RECORDED payload")
    parent, child = p["parent_generator_semantic_hash"], p["child_generator_semantic_hash"]
    _hex64(parent, "parent generator hash")
    _hex64(child, "child generator hash")
    frozen = _payloads(led, "GENERATOR_FROZEN")
    if not frozen or frozen[-1]["generator_semantic_hash"] != parent:
        raise CustodyError("successor parent must be the lineage head frozen in this ledger")
    if _payloads(led, "SUCCESSOR_RECORDED", parent_generator_semantic_hash=parent):
        raise CustodyError("this version already has a recorded successor; the lineage is strictly linear")
    if child == parent:
        raise CustodyError("an identical generator version is not a successor")
    if any(f["generator_semantic_hash"] == child for f in frozen):
        raise CustodyError("child generator version is already frozen")
    if child in _successor_records(led):
        raise CustodyError("this child version was already validated; one successor record per version")
    _validate_e1_profile(p["child_e1_profile"])
    disposition, easier, changed, floor = _compute_disposition(led, parent, child, p["child_e1_profile"],
                                                               p["defect_record"])
    recomputed = (disposition, sorted(easier), changed, floor)
    if recomputed != (p["disposition"], p["easier_dimensions"], p["changed_components"],
                      p["floor_generator_semantic_hash"]):
        raise CustodyError("recorded successor disposition does not match its recomputation")


_VALIDATORS = {
    "GENERATOR_FROZEN": _v_generator_frozen,
    "NONCE_COMMITTED": _v_nonce_committed,
    "WITHHELD_COMMITTED": _v_withheld_committed,
    "REALIZATION_SET_ATTESTED": _v_realization_set,
    "REQUALIFICATION_PREREQUISITES_RECORDED": _v_requalification,
    "EXPOSURE_RECORDED": _v_exposure,
    "FIT_OUTPUT_FROZEN": _v_fit_output,
    "REVEALED": _v_revealed,
    "SUCCESSOR_RECORDED": _v_successor,
}
LEDGER_KINDS = tuple(_VALIDATORS)


# ------------------------------------------------------ custody operations

@dataclass(frozen=True)
class ExposureState:
    """Exposure of one generator version as recorded in a ledger at ``ledger_head``."""

    generator_semantic_hash: str
    exposed: bool
    exposure_count: int
    ledger_head: str


@dataclass(frozen=True)
class RealizationAttestation:
    """Receipt binding the complete emitted realization set before scoring (s1.3)."""

    generator_semantic_hash: str
    class_tag: str
    budget: int
    root_commitment: str
    authorized_ids_digest: str
    emitted_set_sha256: str
    n_emitted: int
    ledger_entry_hash: str


@dataclass(frozen=True)
class VersionDisposition:
    """E1 disposition of a successor generator version."""

    disposition: str
    parent_generator_semantic_hash: str
    child_generator_semantic_hash: str
    floor_generator_semantic_hash: str | None
    easier_dimensions: tuple
    easier_reasons: tuple
    changed_components: tuple
    defect_record_sha256: str | None
    inherits_qualification: bool
    requires_realism_rerun: bool
    requires_withheld_check: bool
    ledger_entry_hash: str


def record_generator_freeze(freeze: GeneratorFreeze, ledger: CustodyLedger) -> str:
    """Append GENERATOR_FROZEN (lineage root, or a child already validated as a successor)."""
    fr = _require_freeze_obj(freeze)
    return _require_ledger(ledger)._append(
        "GENERATOR_FROZEN", {"generator_semantic_hash": fr.generator_semantic_hash, "spec": fr.spec()}
    )


def record_nonce_commitment(freeze: GeneratorFreeze, ledger: CustodyLedger, *, class_tag: str,
                            nonce_commitment: str) -> str:
    """Append NONCE_COMMITTED with the published H(nonce); the nonce itself never enters."""
    fr = _require_freeze_obj(freeze)
    return _require_ledger(ledger)._append("NONCE_COMMITTED", {
        "generator_semantic_hash": fr.generator_semantic_hash,
        "class_tag": class_tag,
        "nonce_commitment": nonce_commitment,
    })


def record_withheld_commitment(freeze: GeneratorFreeze, ledger: CustodyLedger, *, withheld_class_tag: str,
                               nonce_commitment: str, secret_absence_attestations: Iterable[Mapping],
                               code_path_attestation: Mapping, withheld_family_change: str | None = None) -> str:
    """Append WITHHELD_COMMITTED, bound to the committed qualification nonce, once the private scans pass.

    ``withheld_family_change`` is None for the lineage root and "UNCHANGED" or "CHANGED_BY_DEFECT" for every
    successor (decision 6, W1).
    """
    fr = _require_freeze_obj(freeze)
    if isinstance(secret_absence_attestations, (str, bytes, Mapping)):
        raise CustodyError("secret_absence_attestations must be a list of scan attestations")
    scans = list(secret_absence_attestations)
    if not scans:
        raise CustodyError("at least one secret-absence scan attestation is required")
    for s in scans:
        _exact_keys(s, ("secret_absent", "tree_identity", "files_scanned"), "secret-absence attestation")
        if s["secret_absent"] is not True:
            raise CustodyError("a secret-absence scan found secret material; the commitment may not be published")
        _hex64(s["tree_identity"], "tree_identity")
    if len({s["tree_identity"] for s in scans}) != 1 or len({s["files_scanned"] for s in scans}) != 1:
        raise CustodyError("all secret-absence scans must cover one and the same tree")
    _check_code_path_attestation(code_path_attestation)
    led = _require_ledger(ledger)
    secret = not any(_family_disclosed(led, g)
                     for g in _shared_family_versions(led, fr.generator_semantic_hash, withheld_family_change))
    payload = {
        "generator_semantic_hash": fr.generator_semantic_hash,
        "withheld_class_tag": withheld_class_tag,
        "withheld_family_commitment": fr.withheld_family_commitment,
        "nonce_commitment": nonce_commitment,
        "withheld_family_change": withheld_family_change,
        "withheld_check_secret": secret,
        "secret_absence": {"tree_identity": scans[0]["tree_identity"], "secrets_scanned": len(scans),
                           "files_scanned": scans[0]["files_scanned"]},
        "code_path_attestation": dict(code_path_attestation),
    }
    return led._append("WITHHELD_COMMITTED", payload)


def withheld_check_eligible(ledger: CustodyLedger, generator_semantic_hash: str) -> bool:
    """True only if this version's withheld family was committed while secret, stayed secret until its
    qualification fit froze, and was not a family already made public by another version; False for any version
    without a committed withheld family (fail closed). Final only after the version's own withheld reveal."""
    led = _require_ledger(ledger)
    committed = _payloads(led, "WITHHELD_COMMITTED", generator_semantic_hash=generator_semantic_hash)
    if not committed or committed[0]["withheld_check_secret"] is not True:
        return False
    group = _family_group(led, generator_semantic_hash) - {generator_semantic_hash}
    fit_index = None
    for i, e in enumerate(led._entries):
        p = e["payload"]
        if (e["kind"] == "FIT_OUTPUT_FROZEN" and p["generator_semantic_hash"] == generator_semantic_hash
                and p["class_tag"] == SYNTH_QUALIFICATION):
            fit_index = i
    for i, e in enumerate(led._entries):
        p = e["payload"]
        if e["kind"] != "REVEALED" or p["generator_semantic_hash"] not in group:
            continue
        discloses = p["reveal_type"] == _REVEAL_WITHHELD or p.get("class_tag") == SYNTH_QUALIFICATION
        if discloses and (fit_index is None or i < fit_index):
            return False  # a sharing version's family or qualification nonce became public before this fit froze
    own = _payloads(led, "REVEALED", reveal_type=_REVEAL_WITHHELD, generator_semantic_hash=generator_semantic_hash)
    if own and own[0]["family_previously_public"] is True:
        return False  # Q3: the "new" family had already been made public by another version
    return True


def _qualification_draw(led: CustodyLedger, index: int, entry: dict) -> dict:
    p = entry["payload"]
    att = [a for a in led._entries if a["kind"] == "REALIZATION_SET_ATTESTED"
           and a["payload"]["generator_semantic_hash"] == p["generator_semantic_hash"]
           and a["payload"]["class_tag"] == SYNTH_QUALIFICATION][0]
    return {
        "ledger_index": index,
        "exposure_entry_hash": entry["entry_hash"],
        "exposure_id": p["exposure_id"],
        "method_id": p["method_id"],
        "generator_semantic_hash": p["generator_semantic_hash"],
        "class_tag": SYNTH_QUALIFICATION,
        "realization_set": {
            "attestation_entry_hash": att["entry_hash"],
            "emitted_set_sha256": att["payload"]["emitted_set_sha256"],
            "root_commitment": att["payload"]["root_commitment"],
            "authorized_ids_digest": att["payload"]["authorized_ids_digest"],
            "budget": att["payload"]["budget"],
        },
    }


def _qualification_exposures(led: CustodyLedger):
    for i, e in enumerate(led._entries):
        if e["kind"] == "EXPOSURE_RECORDED" and e["payload"]["realization_class"] == SYNTH_QUALIFICATION:
            yield i, e


def qualification_draws_for_method(ledger: CustodyLedger, method_id: str) -> list:
    """Every SYNTH_QUALIFICATION exposure of ``method_id`` in the ledger, across all versions, in ledger order.

    BINDING OBLIGATION (decision 5): every qualification claim must report this complete list together with
    ``qualification_draws_in_lineage`` and account for multiplicity across draws.
    """
    led = _require_ledger(ledger)
    _hex64(method_id, "method_id (content digest of the frozen method code + configuration)")
    return [_qualification_draw(led, i, e) for i, e in _qualification_exposures(led)
            if e["payload"]["method_id"] == method_id]


def qualification_draws_in_lineage(ledger: CustodyLedger, generator_semantic_hash: str) -> list:
    """Every SYNTH_QUALIFICATION exposure of ANY method across the version's whole lineage (all ancestors and
    descendants), in ledger order; a changed method digest does not reset this count (decision 5)."""
    led = _require_ledger(ledger)
    _frozen_freeze(led, generator_semantic_hash)  # a version outside this ledger's lineage is refused
    lineage = set(_lineage_chain(led, generator_semantic_hash)) | set(_descendants(led, generator_semantic_hash))
    return [_qualification_draw(led, i, e) for i, e in _qualification_exposures(led)
            if e["payload"]["generator_semantic_hash"] in lineage]


def attest_realization_set(root: bytes, class_tag: str, budget: int, emitted: Iterable[Mapping],
                           ledger: CustodyLedger, *, freeze: GeneratorFreeze) -> RealizationAttestation:
    """Attest that exactly the authorized realizations were emitted (decision 7)."""
    fr = _require_freeze_obj(freeze)
    led = _require_ledger(ledger)
    _root(root)
    _class_tag(class_tag)
    _u64(budget, "budget", 1)
    if budget != fr.realization_budget(class_tag):
        raise CustodyError("budget must equal the frozen realization budget for this class exactly")
    if isinstance(emitted, (str, bytes, Mapping)) or not isinstance(emitted, (list, tuple)):
        raise CustodyError("emitted must be a list of {realization_id, content_sha256} rows")
    rows = []
    for r in emitted:
        _exact_keys(r, ("realization_id", "content_sha256"), "emitted realization row")
        if not isinstance(r["realization_id"], str):
            raise CustodyError("realization_id must be str")
        _hex64(r["content_sha256"], "content_sha256")
        rows.append({"realization_id": r["realization_id"], "content_sha256": r["content_sha256"]})
    ids = [r["realization_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise CustodyError("duplicate realization id: re-emission or replacement is prohibited")
    if len({r["content_sha256"] for r in rows}) != len(rows):
        raise CustodyError("duplicate realization content: a realization was replaced by a copy")
    authorized = authorized_realization_ids(root, class_tag, budget)
    missing = set(authorized) - set(ids)
    extra = set(ids) - set(authorized)
    if missing:
        raise CustodyError(f"{len(missing)} authorized realization(s) missing: discard is prohibited")
    if extra:
        raise CustodyError(f"{len(extra)} unauthorized realization id(s): seed shopping or replacement")
    payload = {
        "generator_semantic_hash": fr.generator_semantic_hash,
        "class_tag": class_tag,
        "budget": budget,
        "root_commitment": root_commitment(root),
        "authorized_ids_digest": C.semantic_row_set_sha256([{"realization_id": r} for r in authorized],
                                                           ["realization_id"]),
        "emitted_set_sha256": C.semantic_row_set_sha256(rows, ["realization_id"]),
        "n_emitted": len(rows),
    }
    h = led._append("REALIZATION_SET_ATTESTED", payload)
    return RealizationAttestation(ledger_entry_hash=h, **payload)


def record_requalification_prerequisites(freeze: GeneratorFreeze, ledger: CustodyLedger, *,
                                         realism_rerun_receipt_sha256: str,
                                         withheld_check_plan_sha256: str) -> str:
    """Bind the realism-rerun receipt and withheld-check plan a defect-corrected version needs before exposure."""
    fr = _require_freeze_obj(freeze)
    return _require_ledger(ledger)._append("REQUALIFICATION_PREREQUISITES_RECORDED", {
        "generator_semantic_hash": fr.generator_semantic_hash,
        "realism_rerun_receipt_sha256": realism_rerun_receipt_sha256,
        "withheld_check_plan_sha256": withheld_check_plan_sha256,
    })


def exposure_state(freeze: GeneratorFreeze, ledger: CustodyLedger) -> ExposureState:
    """The ledger's own record of whether this frozen version has been exposed."""
    fr = _require_freeze_obj(freeze)
    led = _require_ledger(ledger)
    _frozen_freeze(led, fr.generator_semantic_hash)
    n = len(_payloads(led, "EXPOSURE_RECORDED", generator_semantic_hash=fr.generator_semantic_hash))
    return ExposureState(generator_semantic_hash=fr.generator_semantic_hash, exposed=n > 0, exposure_count=n,
                         ledger_head=led.head)


def record_exposure(freeze: GeneratorFreeze, exposure: Mapping, ledger: CustodyLedger, *,
                    expected_ledger_head: str | None = None) -> ExposureState:
    """Record a downstream exposure; refused unless every commitment precedes it (decision 5)."""
    fr = _require_freeze_obj(freeze)
    led = _require_ledger(ledger)
    if expected_ledger_head is not None:
        _hex64(expected_ledger_head, "expected_ledger_head")
        if expected_ledger_head != led.head:
            raise CustodyError("the ledger has advanced past the expected head (stale controller view)")
    _exact_keys(exposure, ("exposure_id", "method_id", "realization_class"), "exposure")
    led._append("EXPOSURE_RECORDED", {"generator_semantic_hash": fr.generator_semantic_hash, **exposure})
    return exposure_state(fr, led)


def record_fit_output_frozen(freeze: GeneratorFreeze, ledger: CustodyLedger, *, class_tag: str,
                             fit_output_sha256: str) -> str:
    """Irrevocably freeze the fit-side output identity for a class; reveal is possible only after this."""
    fr = _require_freeze_obj(freeze)
    return _require_ledger(ledger)._append("FIT_OUTPUT_FROZEN", {
        "generator_semantic_hash": fr.generator_semantic_hash,
        "class_tag": class_tag,
        "fit_output_sha256": fit_output_sha256,
    })


def reveal_class_nonce(freeze: GeneratorFreeze, ledger: CustodyLedger, *, class_tag: str, nonce: bytes) -> str:
    """Reveal a class nonce after its fit output is frozen; verifies H(nonce) and the sealed root."""
    fr = _require_freeze_obj(freeze)
    return _require_ledger(ledger)._append("REVEALED", {
        "reveal_type": _REVEAL_CLASS_NONCE,
        "generator_semantic_hash": fr.generator_semantic_hash,
        "class_tag": class_tag,
        "nonce_hex": _nonce(nonce).hex(),
    })


def reveal_withheld_family(freeze: GeneratorFreeze, ledger: CustodyLedger, *, withheld_spec: Mapping,
                           nonce: bytes, withheld_class_tag: str) -> str:
    """Reveal the withheld family after the sealed fit output is frozen; ``nonce`` is the qualification nonce."""
    fr = _require_freeze_obj(freeze)
    led = _require_ledger(ledger)
    spec = _canonical_copy(withheld_spec, "withheld_spec")
    return led._append("REVEALED", {
        "reveal_type": _REVEAL_WITHHELD,
        "generator_semantic_hash": fr.generator_semantic_hash,
        "withheld_class_tag": withheld_class_tag,
        "nonce_hex": _nonce(nonce).hex(),
        "withheld_spec": spec,
        "family_previously_public": _previously_public(led, fr.generator_semantic_hash, spec),
    })


def validate_successor_version(parent: GeneratorFreeze, child: GeneratorFreeze, *,
                               parent_exposure_state: ExposureState, ledger: CustodyLedger,
                               defect_record: Mapping | None = None) -> VersionDisposition:
    """Classify and record a successor generator version under E1 (decision 6)."""
    pa = _require_freeze_obj(parent)
    ch = _require_freeze_obj(child)
    led = _require_ledger(ledger)
    if not isinstance(parent_exposure_state, ExposureState):
        raise CustodyError("parent_exposure_state must be an ExposureState")
    if parent_exposure_state.generator_semantic_hash != pa.generator_semantic_hash:
        raise CustodyError("parent_exposure_state belongs to a different generator version")
    actual = exposure_state(pa, led)
    if (parent_exposure_state.exposed, parent_exposure_state.exposure_count) != (actual.exposed,
                                                                                actual.exposure_count):
        raise CustodyError("parent_exposure_state disagrees with the ledger (forged or stale)")
    if parent_exposure_state.ledger_head != led.head:
        raise CustodyError("parent_exposure_state is stale: the ledger has advanced since it was read")
    rec = None if defect_record is None else _canonical_copy(defect_record, "defect_record")
    profile = ch.e1_profile()
    disposition, easier, changed, floor = _compute_disposition(
        led, pa.generator_semantic_hash, ch.generator_semantic_hash, profile, rec)
    h = led._append("SUCCESSOR_RECORDED", {
        "parent_generator_semantic_hash": pa.generator_semantic_hash,
        "child_generator_semantic_hash": ch.generator_semantic_hash,
        "child_e1_profile": profile,
        "defect_record": rec,
        "disposition": disposition,
        "easier_dimensions": sorted(easier),
        "changed_components": changed,
        "floor_generator_semantic_hash": floor,
    })
    return VersionDisposition(
        disposition=disposition,
        parent_generator_semantic_hash=pa.generator_semantic_hash,
        child_generator_semantic_hash=ch.generator_semantic_hash,
        floor_generator_semantic_hash=floor,
        easier_dimensions=tuple(sorted(easier)),
        easier_reasons=tuple((k, easier[k]) for k in sorted(easier)),
        changed_components=tuple(changed),
        defect_record_sha256=None if rec is None else C.semantic_sha256(rec),
        inherits_qualification=False,
        requires_realism_rerun=True,
        requires_withheld_check=True,
        ledger_entry_hash=h,
    )


# ------------------------------------------------------------ secret scan (8)

def _b64_cores(secret: bytes) -> list:
    """Base64 substrings fixed by the secret alone, for each of the three byte alignments."""
    out = []
    n = len(secret)
    for k in range(3):
        start = -(-8 * k // 6)  # ceil(8k / 6): first char whose 6 bits lie inside the secret
        end = (8 * (k + n) - 6) // 6  # last char whose 6 bits lie inside the secret
        for enc in (base64.b64encode, base64.urlsafe_b64encode):
            text = enc(b"\x00" * k + secret).rstrip(b"=")
            out.append(text[start:end + 1])
    return out


def _scan_needles(secret: bytes):
    """(raw-view, compact-view, hex-view) needles for one secret (decision 8)."""
    raw = {secret, repr(secret)[2:-1].encode("ascii")}
    compact = set(_b64_cores(secret))
    decimal = str(int.from_bytes(secret, "big")).encode("ascii")
    if len(decimal) >= MIN_DECIMAL_NEEDLE_DIGITS:
        compact.add(decimal)
    squeezed = secret.translate(None, _WHITESPACE)
    if len(squeezed) >= MIN_SCAN_SECRET_BYTES:
        compact.add(squeezed)
    compact.add(",".join(str(b) for b in secret).encode("ascii"))  # JSON/Python list of byte values
    hexes = {secret.hex().encode("ascii")}
    return tuple(sorted(raw)), tuple(sorted(compact)), tuple(sorted(hexes))


class _Matcher:
    """Streaming search of one byte stream through the raw, compact and hex views."""

    def __init__(self, needles):
        self._raw, self._compact, self._hex = needles
        self._keep = max(len(n) for group in needles for n in group) - 1
        self._raw_tail = self._compact_tail = self._hex_tail = self._hex_carry = b""
        self.hit = False

    def feed(self, chunk: bytes) -> None:
        if self.hit:
            return
        raw = self._raw_tail + chunk
        piece = chunk.translate(None, _WHITESPACE)
        compact = self._compact_tail + piece
        h = self._hex_carry + piece.lower().replace(b":", b"").replace(b",", b"")
        if h.endswith(b"0"):  # hold a trailing "0" back: the next chunk may start with "x"
            self._hex_carry, h = b"0", h[:-1]
        else:
            self._hex_carry = b""
        hexbuf = self._hex_tail + h.replace(b"0x", b"")
        self.hit = (any(n in raw for n in self._raw) or any(n in compact for n in self._compact)
                    or any(n in hexbuf for n in self._hex))
        k = self._keep
        self._raw_tail, self._compact_tail, self._hex_tail = raw[-k:], compact[-k:], hexbuf[-k:]

    def finish(self) -> bool:
        if not self.hit and self._hex_carry:
            hexbuf = self._hex_tail + self._hex_carry
            self.hit = any(n in hexbuf for n in self._hex)
        self._hex_carry = b""
        return self.hit


def _scan_file(path: str, needles):
    h = hashlib.sha256()
    m = _Matcher(needles)
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(_SCAN_CHUNK)
            if not chunk:
                break
            h.update(chunk)
            m.feed(chunk)
    return h.hexdigest(), m.finish()


def _bytes_hit(data: bytes, needles) -> bool:
    m = _Matcher(needles)
    m.feed(data)
    return m.finish()


def scan_secret_absence(repo_tree, secret_bytes: bytes) -> dict:
    """Attest whether ``secret_bytes`` is absent from every file and path name under ``repo_tree``."""
    if not isinstance(secret_bytes, bytes):
        raise CustodyError("secret must be bytes")
    if len(secret_bytes) < MIN_SCAN_SECRET_BYTES:
        raise CustodyError(f"secret must be at least {MIN_SCAN_SECRET_BYTES} bytes to be scanned meaningfully")
    try:
        root = os.fspath(repo_tree)
    except TypeError:
        raise CustodyError("repo_tree must be a path") from None
    if not isinstance(root, str) or not os.path.isdir(root):
        raise CustodyError("repo_tree must be an existing directory")
    needles = _scan_needles(secret_bytes)
    rows = []
    found = False

    def visit(full: str, entry_type: str, data_hash: str, hit: bool) -> None:
        nonlocal found
        rel = os.path.relpath(full, root).replace(os.sep, "/")
        try:
            rel_bytes = rel.encode("utf-8")
        except UnicodeEncodeError:
            raise CustodyError("tree contains a path name that is not valid Unicode") from None
        found = found or hit or _bytes_hit(rel_bytes, needles)
        rows.append({"path": rel, "entry_type": entry_type, "raw_sha256": data_hash})

    def link(full: str) -> None:
        target = os.fsencode(os.readlink(full))
        visit(full, "symlink", C.raw_sha256(target), _bytes_hit(target, needles))

    def unreadable(exc: OSError) -> None:
        # os.walk skips unlistable directories by default; a skipped directory must never read as "absent"
        raise CustodyError("part of the tree could not be listed; refusing to attest") from None

    try:
        for dirpath, dirnames, filenames in os.walk(root, onerror=unreadable, followlinks=False):
            keep = []
            for d in sorted(dirnames):
                if d == ".git":
                    continue
                full = os.path.join(dirpath, d)
                if os.path.islink(full):
                    link(full)
                else:
                    keep.append(d)
            dirnames[:] = keep
            for f in sorted(filenames):
                if f == ".git":
                    continue
                full = os.path.join(dirpath, f)
                mode = os.lstat(full).st_mode
                if stat.S_ISLNK(mode):
                    link(full)
                elif stat.S_ISREG(mode):
                    visit(full, "file", *_scan_file(full, needles))
    except OSError:
        raise CustodyError("a tree entry could not be read; refusing to attest") from None
    if not rows:
        raise CustodyError("scan covered no files; an empty tree attests nothing")
    rows.sort(key=lambda r: r["path"])
    try:
        tree_identity = C.ordered_registry_digest(rows, ["path"])
    except C.CanonicalError:
        raise CustodyError("tree identity could not be computed (colliding or invalid path names)") from None
    return {"secret_absent": not found, "tree_identity": tree_identity, "files_scanned": len(rows)}


def require_secret_absence(repo_tree, secret_bytes: bytes) -> dict:
    """``scan_secret_absence`` that raises (without echoing secret or path) when the secret is present."""
    att = scan_secret_absence(repo_tree, secret_bytes)
    if not att["secret_absent"]:
        raise CustodyError("secret material is present in the scanned tree; refusing to attest absence")
    return att


# -------------------------------------------- unique withheld code paths (9)

def _path_set(paths: Any, what: str) -> set:
    if isinstance(paths, (str, bytes, Mapping)):
        raise CustodyError(f"{what} must be a collection of code-path identifiers, not a single value")
    try:
        items = list(paths)
    except TypeError:
        raise CustodyError(f"{what} must be a collection of code-path identifiers") from None
    for p in items:
        if not isinstance(p, str) or not p:
            raise CustodyError(f"{what} must contain only non-empty str identifiers")
    out = set(items)
    if not out:
        raise CustodyError(f"{what} is empty; an attestation over nothing proves nothing")
    return out


def _paths_digest(paths: set, what: str) -> str:
    try:
        return C.semantic_row_set_sha256([{"code_path": p} for p in sorted(paths)], ["code_path"])
    except C.CanonicalError:
        # canonical errors quote the colliding identifier; never echo a code path
        raise CustodyError(
            f"{what} could not be digested (identifiers collide after line-ending normalization or are not "
            "valid text)"
        ) from None


def attest_no_unique_withheld_code_path(withheld_exercised_paths: Iterable[str],
                                        development_exercised_paths: Iterable[str],
                                        public_code_paths: Iterable[str]) -> dict:
    """N3: every public path the withheld family exercises must also be exercised by non-withheld worlds."""
    withheld = _path_set(withheld_exercised_paths, "withheld_exercised_paths")
    development = _path_set(development_exercised_paths, "development_exercised_paths")
    public = _path_set(public_code_paths, "public_code_paths")
    unique_public = (withheld & public) - development
    if unique_public:
        raise CustodyError(
            f"{len(unique_public)} public code path(s) are exercised only by the withheld family; they must stay "
            "controller-side/off-repo until reveal (N3): custody failure"
        )
    _paths_digest(withheld, "withheld_exercised_paths")  # validated, never returned
    return {
        "no_unique_withheld_public_path": True,
        "public_paths_digest": _paths_digest(public, "public_code_paths"),
        "development_paths_digest": _paths_digest(development, "development_exercised_paths"),
    }
