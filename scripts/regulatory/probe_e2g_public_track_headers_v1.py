#!/usr/bin/env python3
"""HEAD-only availability check for a fixed small panel of E2G public tracks.

No GET, prediction parsing, Google Cloud requester-pays tokens, billing project,
or target comparison. Hard allowlist protects against untrusted URL redirection.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

API="https://e2g.stanford.edu/graphql"
QUERY="""query TrackAvailability {
 getDataTracks { cellTypeId cellType study modelType e2gPredictionsUrl }
}"""
PANEL={
    "inflammatory_macrophage_ENCSR593WXK": "inflammatory_macrophage_unstimulated_candidate",
    "inflammatory_macrophage_ENCSR643ZGR": "inflammatory_macrophage_lps_1h",
    "inflammatory_macrophage_ENCSR226JLK": "inflammatory_macrophage_lps_4h",
    "Macrophage": "scE2G_macrophages3",
    "Immune_monocyte_1": "scE2G_macrophages1",
    "brain_ENCSR344FLH": "rE2G_bulk_brain_context",
    "Stitziel_hCA_Myeloid": "scE2G_coronary_myeloid",
}
CAP=7_000_000


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl):
            raise ValueError("Unsafe redirect blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def allowed(url):
    p=urllib.parse.urlsplit(url)
    return (
        p.scheme=="https" and p.hostname=="storage.googleapis.com" and
        p.port is None and p.username is None and p.password is None and
        bool(p.path) and not p.query and not p.fragment
    )


def source_rows(timeout=12):
    req=urllib.request.Request(API, method="POST",
        data=json.dumps({"query":QUERY}).encode(),
        headers={"Content-Type":"application/json","User-Agent":"JEPA-E2G-Source-Probe/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        b=resp.read(CAP+1)
    if len(b)>CAP: raise RuntimeError("Metadata too large")
    x=json.loads(b)
    if x.get("errors") or not isinstance(x.get("data"),dict):
        raise RuntimeError("Bad GraphQL response")
    return x["data"]["getDataTracks"]


def head_only(url,timeout=12):
    if not allowed(url): return {"status":"SKIP_UNSAFE_URL"}
    p=urllib.parse.urlsplit(url)
    opener=urllib.request.build_opener(SafeRedirect)
    req=urllib.request.Request(url,method="HEAD",
        headers={"User-Agent":"JEPA-E2G-Source-Probe/1.0"})
    try:
        with opener.open(req,timeout=timeout) as resp:
            return {
                "status":"HTTP_"+str(resp.status),
                "content_type":resp.headers.get("Content-Type"),
                "content_length":resp.headers.get("Content-Length"),
                "accept_ranges":resp.headers.get("Accept-Ranges"),
                "host":p.hostname,
            }
    except urllib.error.HTTPError as exc:
        return {"status":"HTTP_"+str(exc.code),"host":p.hostname}
    except (OSError,TimeoutError,ValueError) as exc:
        return {"status":"TRANSPORT_ERROR_"+type(exc).__name__,"host":p.hostname}


def run():
    matches={}
    for r in source_rows():
        rid=r.get("cellTypeId")
        if rid in PANEL:
            if rid in matches: raise RuntimeError("Duplicate source ID: "+rid)
            matches[rid]=r
    if set(matches)!=set(PANEL):
        raise RuntimeError("Selected public sources missing: "+str(set(PANEL)-set(matches)))
    outcomes=[]
    for rid,role in PANEL.items():
        row=matches[rid]
        url=row.get("e2gPredictionsUrl") or ""
        result=head_only(url)
        outcomes.append({
            "source_id":rid,"role":role,
            "published_cell_type":row.get("cellType"),
            "published_study":row.get("study"),
            "model_family":row.get("modelType"),
            "url_basename":urllib.parse.urlsplit(url).path.rsplit("/",1)[-1],
            "probe":result,
            "biology_status":"NOT_EVALUATED",
        })
    return {
        "schema":"JEPA_E2G_SELECTED_PUBLIC_TRACK_HEAD_V1",
        "endpoint":API,"operation":"HEAD_ONLY__NO_DATA_TRANSFER",
        "sources":outcomes,
        "microglia_direct_validation":False,
        "target_winner":None,"real_training":False,
    }


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
