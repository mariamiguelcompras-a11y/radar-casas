import json, urllib.request, re
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36", "Accept": "application/json,text/html", "Origin": "https://remax.pt"}
def req(url, body=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=30) as x: return x.status, x.geturl(), x.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: return e.code, url, ""
st, u, t = req("https://remax.pt/api/Reference/GetAll"); g = json.loads(t)
print("TYPES", [(x["id"], x["displayText"]) for x in g["listingTypes"]])
print("ATTR", [(x["id"], x["displayText"]) for x in g["listingAttributesTypes"]])
st, u, t = req("https://remax.pt/api/Reference/Regions2?onlyCurrentCountry=true")
print("LX", [x for x in json.loads(t) if x.get("regionSearch") == "lisboa"])
st, u, t = req("https://remax.pt/api/Listing/GetListingByTitle?listingPublicId=123751650-27")
print("DET", st)
if st == 200:
    d = json.loads(t)
    for k, v in d.items():
        if v not in (None, False, "", 0, []) and k not in ("listingPictures",): print("D", k, json.dumps(v, ensure_ascii=False)[:300])
for cand in ["https://remax.pt/pt/imoveis/venda-apartamento-t2-oeiras-alges-linda-a-velha-e-cruz-quebrada-dafundo/123751650-27",
             "https://remax.pt/pt/imoveis/123751650-27", "https://remax.pt/imoveis/venda-apartamento-t2-oeiras-alges-linda-a-velha-e-cruz-quebrada-dafundo/123751650-27"]:
    st, u, t = req(cand); print("URL", st, u, len(t), "350" in t)
