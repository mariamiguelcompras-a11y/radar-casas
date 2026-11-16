"""Teste pontual: endereços de pesquisa e fichas de Casa Sapo, OLX e CustoJusto."""
import json, os, re, sys, html as H
sys.path.insert(0, os.path.dirname(__file__))
from scrape import get
OUT = "debug/amostras"; os.makedirs(OUT, exist_ok=True)
res = {}
# Casa Sapo: ficha
h = open(f"{OUT}/casasapo_pesquisa.html", encoding="utf-8").read() if os.path.exists(f"{OUT}/casasapo_pesquisa.html") else get("https://casa.sapo.pt/comprar-apartamentos/t2/oeiras/")[1]
reais = re.findall(r'l=(https://casa\.sapo\.pt/comprar-[^"#?]+\.html)', H.unescape(h))
if reais:
    st, d, f = get(reais[0]); open(f"{OUT}/casasapo_anuncio.html", "w", encoding="utf-8").write(d); res["sapo_ficha"] = [st, f, len(d)]
for nome, u in {"sapo_preco": "https://casa.sapo.pt/comprar-apartamentos/t2/oeiras/?lp=360000",
                "sapo_pag2": "https://casa.sapo.pt/comprar-apartamentos/t2/oeiras/?pn=2",
                "sapo_cascais": "https://casa.sapo.pt/comprar-apartamentos/t2/cascais/?lp=360000"}.items():
    st, d, f = get(u); res[nome] = [st, f, len(d), len(re.findall(r'class="property-info"', d)), re.findall(r'property-price-value">([^<]+)', d)[:6]]
# OLX variantes
for nome, u in {
  "olx_lisboa": "https://www.olx.pt/imoveis/apartamento-casa-a-venda/apartamentos-venda/lisboa/?search%5Bfilter_float_price:to%5D=360000&search%5Bfilter_enum_tipologia%5D%5B0%5D=t2",
  "olx_oeiras_q": "https://www.olx.pt/imoveis/apartamento-casa-a-venda/apartamentos-venda/q-oeiras/?search%5Bfilter_float_price:to%5D=360000",
  "olx_cat": "https://www.olx.pt/imoveis/apartamento-casa-a-venda/apartamentos-venda/?search%5Bfilter_float_price:to%5D=360000&search%5Bregion_id%5D=11",
}.items():
    st, d, f = get(u)
    m = re.search(r'window\.__PRERENDERED_STATE__\s*=\s*"(.*?)";\s*\n', d, re.S)
    info = [st, f[:150]]
    if m:
        L = json.loads(json.loads('"' + m.group(1) + '"'))["listing"]["listing"]
        ads = L.get("ads") or []
        info += [L.get("totalElements"), L.get("totalPages"), len(ads), [ (a["title"][:40], (a.get("price") or {}).get("displayValue"), a["location"]["cityName"][:40]) for a in ads[:5]]]
    res[nome] = info
# CustoJusto variantes + ficha
for nome, u in {
  "cj_venda1": "https://www.custojusto.pt/lisboa/oeiras/imobiliario/apartamentos/venda",
  "cj_venda2": "https://www.custojusto.pt/lisboa/oeiras/imobiliario/apartamentos?f=v",
  "cj_venda3": "https://www.custojusto.pt/lisboa/oeiras/imobiliario/apartamentos-venda",
  "cj_venda4": "https://www.custojusto.pt/lisboa/imobiliario/apartamentos?pe=360000&st=s",
}.items():
    st, d, f = get(u)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', d, re.S)
    info = [st, f[:150]]
    if m:
        pp = json.loads(m.group(1))["props"]["pageProps"]
        li = pp.get("listItems") or []
        info += [len(li), [(x["title"][:40], x.get("price"), x.get("url")) for x in li[:5]], [k for k in pp.keys()][:30]]
        if li and "cj_ficha" not in res:
            u2 = "https://www.custojusto.pt" + li[0]["url"]
            st2, d2, f2 = get(u2); open(f"{OUT}/custojusto_anuncio.html", "w", encoding="utf-8").write(d2); res["cj_ficha"] = [st2, f2, len(d2)]
    res[nome] = info
json.dump(res, open("debug/teste2.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
