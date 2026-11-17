import sys, re, time, json
sys.path.insert(0, "scraper")
from scrape import get
P = {
 "c21": "https://century21.pt/comprar/imoveis/distrito-lisboa/concelho-oeiras",
 "zome": "https://www.zome.pt/pt/pesquisar/comprar-casa/apartamento/t2/l1-lisboa/l2-oeiras",
 "iad": "https://www.iadportugal.pt/anuncios/lisboa/venda",
 "ds": "https://www.decisoesesolucoes.com/pt/imoveis/?pg=1&o=1&or=30",
 "era": "https://www.era.pt/comprar?ob=1&tp=1,2&ord=3&page=1",
 "predimed": "https://www.predimed.pt/imoveis",
 "habisale": "https://www.habisale.pt/comprar",
 "citylux": "https://www.citylux.pt/comprar",
 "imojoy": "https://www.imojoy.pt/imoveis/venda",
 "konsultti": "https://www.konsultti.pt/imoveis",
 "rbrokers": "https://www.rbrokers.pt/imoveis?imovel=2&natureza=8&pesquisa=false",
 "elite": "https://www.elitehomes.pt/lista-propriedades",
}
for k, u in P.items():
    st, h, fu = get(u, tentativas=1); h = h or ""
    euros = len(re.findall(r"\d[\d.\s ]{3,}\s?€|€\s?\d", h))
    hrefs = list(dict.fromkeys(re.findall(r'href="([^"#]{12,160})"', h)))
    det = [x for x in hrefs if re.search(r"\d{4,}|/imovel/|/anuncio|/propriedade|/detalhe|ref", x, re.I)][:6]
    js = [m for m in ("__NEXT_DATA__", "__NUXT__", "window.__NUXT__", "application/ld+json", "dataLayer", "listings", "properties") if m in h]
    print(f"P {k} {st} len={len(h)} euros={euros} {js} -> {fu[:80]}\n   DET {det}")
    m = re.search(r"€", h)
    time.sleep(1)
