# V80 frozen original FIT and receipt ZIPs — GitHub custody

These **are the original ZIP bytes** from [GitHub Actions run 38504094639](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/38504094639), physically committed to this public Git branch by a SHA-256-gated [one-time archival workflow](../../../.github/workflows/jepa-v80-original-public-fit-archive-once.yml), [successful run 41900549918](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41900549918).

- **FIT:** `V80-original-fit-transport-artifact.zip`, 660,628 bytes, SHA-256 `4cec8966cff7bdddb3640903f4525328d23ed3482e2b232ead1bc440993fca71`; contains one `fit_transport.json` (8,935,002 bytes, SHA-256 `77f89e8336ec2a2d0184abbd81bfd7d6ff04f2dc57aa80891b6d8021869737b3`).
- **RECEIPT:** `V80-original-receipt-artifact.zip`, 1,274 bytes, SHA-256 `97e264cfe76709f5098b346e56130716640e6c8ce8562974d6ab126ac82a47fe`; contains `V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json` (1,922 bytes, SHA-256 `346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`).
- The exact Git tree stores the ZIPs as blobs `8b81742b66dfd7d2d40940933c7775a515e0610d` and `4ec0e2eed6eba099645638232f3962482ae2dc26`.

To verify after retrieving the two ZIP files, from this directory:

```bash
echo '4cec8966cff7bdddb3640903f4525328d23ed3482e2b232ead1bc440993fca71  V80-original-fit-transport-artifact.zip' | sha256sum -c -
echo '97e264cfe76709f5098b346e56130716640e6c8ce8562974d6ab126ac82a47fe  V80-original-receipt-artifact.zip' | sha256sum -c -
```

The SHA and source identities are also in [V80_ORIGINAL_PUBLIC_FIT_ASSET_MANIFEST_V1.json](V80_ORIGINAL_PUBLIC_FIT_ASSET_MANIFEST_V1.json). This archival step **does not run an estimator or alter the original benchmark**. PR #534's independent cross-host SHA mismatch remains a genuine failing diagnostic; never replace the original SHA with a new host's generated SHA.

## Sealed controller ZIP — NOT in this public repository

Original controller artifact ID `11866917064`, ZIP 6,844,053 bytes, SHA-256 `184d58c6988c81f8f23597510c2113542d1fc55af04409448c14adb8892d3f46`. The original sealed ZIP was separately downloaded and opaque-file-hashed into the owner conversation, but **its controller truth was never opened** and **its raw ZIP is not permitted anywhere in this public Git repository or its CI fit/test side**.

The controller role's safe persistence **is still OPEN**: owner must store this unchanged ZIP in a separate **private, controller-only GitHub repository or other access-controlled vault**, verify re-download and SHA, and record only its hash/locator under the allowed public manifest. No independent private escrow has been verified by Sol. Original GitHub Actions artifact expiry: 2026-11-13 03:01:58 UTC.

**Only reviewers:** Sol reviews Macha's code; Macha reviews Sol's. External custody security cannot be substituted by agent review. No TARGET, student, training or Stage4 authority from these files.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
