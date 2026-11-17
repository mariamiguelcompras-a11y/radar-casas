import json, urllib.request, ssl
def post(body):
    req = urllib.request.Request("https://remax.pt/api/Listing/PaginatedMultiMatchSearch", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36", "Accept": "application/json", "Origin": "https://remax.pt", "Referer": "https://remax.pt/pt/comprar/imoveis/apartamento/lisboa/oeiras"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, e.read()[:300]
base = [{"field":"businessTypeID","operationType":"int","operator":"=","value":"1"},
        {"field":"listingClassID","operationType":"int","operator":"=","value":"1"},
        {"field":"listingTypeID","operationType":"multiple","operator":"=","value":"1"},
        {"field":"Region2ID","operationType":"string","operator":"=","value":"541"}]
for sort in (["-PublishDate"], [], ["PublishDate"]):
    st, d = post({"filters": base, "pageNumber": 1, "pageSize": 24, "sort": sort, "searchValue": ""})
    print("SORT", sort, st, (d if st != 200 else {k: (v if not isinstance(v, list) else len(v)) for k, v in d.items()}))
    if st == 200 and d.get("results"):
        print("R0", json.dumps(d["results"][0], ensure_ascii=False)[:3000]); break
st, d = post({"filters": base + [{"field":"listingPrice","operationType":"double","operator":"<=","value":"360000"}], "pageNumber": 1, "pageSize": 24, "sort": ["-PublishDate"], "searchValue": ""})
print("PRICE", st, d.get("total") if st == 200 else d)
