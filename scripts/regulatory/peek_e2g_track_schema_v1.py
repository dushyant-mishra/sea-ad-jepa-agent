#!/usr/bin/env python3
"""Bounded 32KiB HTTP range schema peek of two public E2G browser tracks."""
import json
import urllib.request
import urllib.parse
import zlib

ENDPOINT="https://e2g.stanford.edu/graphql"
Q="""query PublicTrackPeek { getDataTracks {
 cellTypeId cellType e2gPredictionsUrl modelType } }"""
PANEL=("inflammatory_macrophage_ENCSR593WXK","Macrophage")
CAP=32768

def main():
    post=urllib.request.Request(ENDPOINT,data=json.dumps({"query":Q}).encode(),
         method="POST",headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(post, timeout=15) as r:
        obj=json.loads(r.read(8_000_000))
    if obj.get("errors"): raise RuntimeError("GraphQL errors")
    rows=obj["data"]["getDataTracks"]
    out=[]
    for ident in PANEL:
        matches=[r for r in rows if r["cellTypeId"]==ident]
        if len(matches)!=1: raise ValueError("Wrong match count for "+ident)
        row=matches[0];url=row["e2gPredictionsUrl"]
        p=urllib.parse.urlsplit(url)
        if not(p.scheme=="https" and p.hostname=="storage.googleapis.com" and
               p.port is None and p.username is None and p.password is None and
               not p.query and not p.fragment):
            raise ValueError("Unsafe URL")
        get=urllib.request.Request(url,method="GET",
             headers={"Range":f"bytes=0-{CAP-1}","Accept-Encoding":"identity"})
        with urllib.request.urlopen(get,timeout=20) as resp:
            if resp.status!=206: raise RuntimeError("Server did not honor range")
            raw=resp.read(CAP+1)
            if len(raw)>CAP: raise RuntimeError("Too large")
        if url.endswith(".gz"):
            text=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(raw,MAX_LENGTH:=150000)
        else: text=raw
        lines=text.decode("utf-8",errors="replace").splitlines()[:4]
        out.append({"source_id":ident,"model":row["modelType"],
                    "bytes_received":len(raw),"compressed":url.endswith(".gz"),
                    "sample_lines": [s[:360] for s in lines],
                    "status":"SCHEMA_SAMPLE_ONLY_NO_TARGET_COMPARISON"})
    print(json.dumps({"schema":"E2G_RANGE_HEADER_PEEK_V1","sources":out,
                      "target_selection":False,"causal_validation":False},indent=2))

if __name__=="__main__":main()
