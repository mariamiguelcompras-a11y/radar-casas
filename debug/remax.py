import json, urllib.request, re
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36", "Accept": "application/json", "Origin": "https://remax.pt"}
def req(url, body=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=30) as x: return x.status, x.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: return e.code, ""
base = [{"field":"businessTypeID","operationType":"int","operator":"=","value":"1"},
        {"field":"listingClassID","operationType":"int","operator":"=","value":"1"},
        {"field":"listingTypeID","operationType":"multiple","operator":"=","value":"1"},
        {"field":"Region2ID","operationType":"string","operator":"=","value":"541"}]
st, t = req("https://remax.pt/api/Listing/PaginatedMultiMatchSearch", {"filters": base, "pageNumber": 1, "pageSize": 100, "sort": ["-PublishDate"], "searchValue": ""})
d = json.loads(t); r0 = d["results"][0]
print("N", len(d["results"]))
for k, v in r0.items():
    if v not in (None, False, "", 0) : print("K", k, json.dumps(v, ensure_ascii=False)[:200])
st, t = req("https://remax.pt/api/Reference/Regions2?onlyCurrentCountry=true")
for x in json.loads(t):
    if re.search(r"oeiras|cascais|sintra|amadora|^lisboa", json.dumps(x, ensure_ascii=False).lower()): print("REG", json.dumps(x, ensure_ascii=False)[:200])
st, t = req("https://remax.pt/api/Reference/GetAll")
try:
    g = json.loads(t); print("GETALL keys", list(g.keys()))
    for k in g:
        if "type" in k.lower() or "typolog" in k.lower(): print("GA", k, json.dumps(g[k], ensure_ascii=False)[:500])
except Exception as e: print("GA err", st, e)
