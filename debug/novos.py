import sys; sys.path.insert(0, "scraper")
from scrape import *
vistos = {}
for local in LOCAIS:
    for tipo in TIPOS:
        for tip in TIPOLOGIAS:
            url = f"{BASE}/pt/resultados/comprar/{tipo},{tip}/{local}?priceMax={PRECO_MAX}&limit=72&by=LATEST&direction=DESC"
            st, html, _ = get(url); pausa()
            try: items = next_data(html)["props"]["pageProps"]["data"]["searchAds"]["items"]
            except Exception: continue
            for it in items:
                c = it.get("createdAtFirst") or it.get("dateCreatedFirst") or it.get("dateCreated") or ""
                if c[:10] >= "2026-11-12":
                    vistos[it["slug"]] = (tip, tipo, c[:10])
print("RECENTES", len(vistos))
for slug, (tip, tipo, c) in sorted(vistos.items(), key=lambda x: x[1][2], reverse=True):
    st, d = ficha(slug, tip, tipo)
    if not d: print("X", c, slug, st); continue
    print("N", c, d["zona"], d["tipologia"], d["preco"], d["garagem"], "|", (d.get("garagemFrase") or "")[:90], "|", slug)
