"""Exploração pontual: guarda amostras dos dados de empreendimentos do Imovirtual em debug/."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from scrape import get, next_data

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug")
os.makedirs(OUT, exist_ok=True)
urls = {
    "emp_oeiras": "https://www.imovirtual.com/pt/resultados/comprar/empreendimento/lisboa/oeiras",
    "emp_cascais": "https://www.imovirtual.com/pt/resultados/comprar/empreendimento/lisboa/cascais",
    "emp_sintra": "https://www.imovirtual.com/pt/resultados/comprar/empreendimento/lisboa/sintra",
    "apt_primary": "https://www.imovirtual.com/pt/resultados/comprar/apartamento/lisboa/oeiras?market=PRIMARY",
}
resumo = {}
def corta(o, n=0):
    if n > 4: return "…"
    if isinstance(o, dict): return {k: corta(v, n+1) for k, v in list(o.items())[:60]}
    if isinstance(o, list): return [corta(x, n+1) for x in o[:3]]
    if isinstance(o, str): return o[:200]
    return o
for nome, u in urls.items():
    st, html, final = get(u)
    nd = next_data(html) if st == 200 else None
    pp = (nd or {}).get("props", {}).get("pageProps", {})
    data = pp.get("data") or {}
    sa = data.get("searchAds") or {}
    items = sa.get("items") or []
    resumo[nome] = {"status": st, "final": final, "pageProps_keys": list(pp.keys())[:40], "data_keys": list(data.keys())[:40],
                    "n_items": len(items), "total": (sa.get("pagination") or {}).get("totalItems")}
    with open(os.path.join(OUT, nome + ".json"), "w", encoding="utf-8") as f:
        json.dump({"items": corta(items[:3]), "data_other": corta({k: v for k, v in data.items() if k != "searchAds"})}, f, ensure_ascii=False, indent=1)
    # abrir o primeiro empreendimento / anúncio
    if items:
        it = items[0]
        href = it.get("href") or ""
        slug = it.get("slug") or ""
        alvo = ("https://www.imovirtual.com" + href.replace("[lang]", "pt").replace("ad/", "anuncio/")) if href.startswith("/") else f"https://www.imovirtual.com/pt/anuncio/{slug}"
        st2, h2, f2 = get(alvo)
        nd2 = next_data(h2) if st2 == 200 else None
        pp2 = (nd2 or {}).get("props", {}).get("pageProps", {})
        resumo[nome]["primeiro"] = {"alvo": alvo, "status": st2, "final": f2, "keys": list(pp2.keys())[:40]}
        with open(os.path.join(OUT, nome + "_ficha.json"), "w", encoding="utf-8") as f:
            json.dump(corta(pp2), f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "resumo.json"), "w", encoding="utf-8") as f:
    json.dump(resumo, f, ensure_ascii=False, indent=1)
print(json.dumps(resumo, ensure_ascii=False, indent=1))
