import sys, json, re, time, collections
sys.path.insert(0, "scraper")
from scrape import get, next_data, BASE
CAND = ["lisboa/lisboa/belem","lisboa/lisboa/lumiar","lisboa/lisboa/carnide","lisboa/lisboa/marvila",
 "lisboa/lisboa/parque-das-nacoes","lisboa/lisboa/campolide","lisboa/lisboa/ajuda","lisboa/lisboa/alcantara",
 "lisboa/lisboa/benfica","lisboa/sintra/rio-de-mouro","lisboa/sintra/cacem-e-sao-marcos",
 "lisboa/sintra/agualva-e-mira-sintra","lisboa/sintra/algueirao-mem-martins"]
for loc in CAND:
    st, html, fu = get(f"{BASE}/pt/resultados/comprar/apartamento,t2/{loc}?priceMax=360000&limit=72")
    nd = next_data(html) if st == 200 else None
    items = []
    try:
        s = nd["props"]["pageProps"]["data"]["searchAds"]
        items = s["items"]; tot = s.get("pagination", {}).get("totalItems")
    except Exception as e:
        tot = f"? {e}"
    print("##", loc, st, fu, "total", tot)
    c = collections.Counter()
    for it in items[:72]:
        loc_ = it.get("location", {})
        rg = loc_.get("reverseGeocoding", {}).get("locations", [])
        c[" > ".join(x.get("fullName", x.get("name", "")) if isinstance(x, dict) else str(x) for x in rg)] += 1
    for k, v in c.most_common(8): print("   ", v, k)
    if items: print("   keys:", list(items[0].get("location", {}).keys()), json.dumps(items[0].get("location"), ensure_ascii=False)[:400])
    time.sleep(2)
