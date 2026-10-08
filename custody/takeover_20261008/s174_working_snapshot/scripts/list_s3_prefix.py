from __future__ import annotations

import argparse
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
BUCKET_ALIASES = {
    "single-cell": "sea-ad-single-cell-profiling",
    "neuropathology": "sea-ad-quantitative-neuropathology",
    "spatial": "sea-ad-spatial-transcriptomics",
}


def list_page(bucket: str, prefix: str, max_keys: int, token: str | None) -> tuple[list[dict[str, str]], str | None]:
    params = {
        "list-type": "2",
        "prefix": prefix,
        "max-keys": str(max_keys),
    }
    if token:
        params["continuation-token"] = token

    url = f"https://{bucket}.s3.amazonaws.com/?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        xml = response.read()

    root = ET.fromstring(xml)
    rows = []
    for item in root.findall("s3:Contents", S3_NS):
        rows.append(
            {
                "key": item.findtext("s3:Key", default="", namespaces=S3_NS),
                "last_modified": item.findtext("s3:LastModified", default="", namespaces=S3_NS),
                "size": item.findtext("s3:Size", default="0", namespaces=S3_NS),
            }
        )

    next_token = root.findtext("s3:NextContinuationToken", default=None, namespaces=S3_NS)
    return rows, next_token


def human_size(size: int) -> str:
    value = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def main() -> None:
    parser = argparse.ArgumentParser(description="List public SEA-AD S3 objects with prefix and regex filtering.")
    parser.add_argument("--bucket", default="single-cell", help="Bucket alias or full bucket name.")
    parser.add_argument("--prefix", default="", help="S3 key prefix.")
    parser.add_argument("--pattern", default="", help="Optional regex applied to object key.")
    parser.add_argument("--max-keys", type=int, default=100, help="Objects to request per S3 page.")
    parser.add_argument("--max-pages", type=int, default=1, help="Maximum pages to request.")
    args = parser.parse_args()

    bucket = BUCKET_ALIASES.get(args.bucket, args.bucket)
    regex = re.compile(args.pattern) if args.pattern else None
    token = None
    matched = 0

    for _ in range(args.max_pages):
        rows, token = list_page(bucket=bucket, prefix=args.prefix, max_keys=args.max_keys, token=token)
        for row in rows:
            key = row["key"]
            if regex and not regex.search(key):
                continue
            size = int(row["size"])
            print(f"{human_size(size):>10}  {row['last_modified']}  s3://{bucket}/{key}")
            matched += 1
        if not token:
            break

    print(f"\nMatched objects: {matched}")


if __name__ == "__main__":
    main()

