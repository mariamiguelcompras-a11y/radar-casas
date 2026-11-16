"""Exploração pontual: estados dos empreendimentos e dados das frações (debug/)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from scrape import get, next_data, pausa
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug")
os.makedirs(OUT, exist_ok=True)
res = []
primeira_unidade = None
for loc in ["lisboa/oeiras", "lisboa/cascais", "lisboa/sintra", "lisboa/amadora"]:
    st, html, _ = get(f"https://www.imovirtual.com/pt/resultados/comprar/empreendimento/{loc}?limit=72")
    items = (((next_data(html) or {}).get("props", {}).get("pageProps", {}).get("data") or {}).get("searchAds") or {}).get("items") or []
    for it in items:
        st2, h2, _ = get(f"https://www.imovirtual.com/pt/empreendimento/{it['slug']}")
        pausa()
        ad = ((next_data(h2) or {}).get("props", {}).get("pageProps", {}) or {}).get("ad") or {}
        units = (ad.get("paginatedUnits") or {}).get("items") or []
        pag = {k: v for k, v in (ad.get("paginatedUnits") or {}).items() if k != "items"}
        d = {"loc": loc, "slug": it["slug"], "title": ad.get("title"), "attrs": ad.get("attributes"),
             "locs": ((ad.get("location") or {}).get("reverseGeocoding") or {}).get("locations"),
             "n_units": len(units), "pag": pag,
             "units": [{"slug": u.get("slug"), "chars": {c.get("key"): c.get("value") for c in (u.get("characteristics") or [])}} for u in units[:40]],
             "desc_entrega": [s for s in (ad.get("description") or "").replace("<", " <").split(".") if any(w in s.lower() for w in ("entrega", "conclus", "previs", "trimestre", "202"))][:4]}
        if units and primeira_unidade is None:
            primeira_unidade = units[0]
        res.append(d)
with open(os.path.join(OUT, "empreendimentos.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "unidade_exemplo.json"), "w", encoding="utf-8") as f:
    json.dump(primeira_unidade, f, ensure_ascii=False, indent=1)
print(len(res))
