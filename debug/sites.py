import sys, re, time
sys.path.insert(0, "scraper")
from scrape import get
URLS = {
 "remax": "https://www.remax.pt/pt/comprar/imoveis/apartamento/lisboa/oeiras",
 "remax-api": "https://www.remax.pt/api/Listing/PaginatedMultiMatchSearch?page=1&pageSize=24",
 "era": "https://www.era.pt/comprar?tp=1&dt=11&ct=1110",
 "century21": "https://www.century21.pt/comprar/apartamento/oeiras/",
 "kw": "https://www.kwportugal.pt/pt/imoveis?business=sale&district=lisboa&county=oeiras",
 "zome": "https://www.zome.pt/pt/imoveis/comprar/apartamento/lisboa/oeiras",
 "predimed": "https://www.predimed.pt/comprar/apartamentos/lisboa/oeiras",
 "iad": "https://www.iadportugal.pt/imoveis/venda/oeiras",
 "decisoes": "https://www.decisoesesolucoes.com/imoveis/comprar/apartamento/lisboa/oeiras",
 "supercasa": "https://supercasa.pt/comprar-casas/oeiras",
 "idealista": "https://www.idealista.pt/comprar-casas/oeiras/",
 "casayes": "https://casayes.pt/pt/comprar/casas/lisboa/oeiras",
 "imoveis-coldwell": "https://www.coldwellbanker.pt/pt/comprar/apartamento/lisboa/oeiras",
 "realtyone": "https://www.realtyone.pt/comprar/apartamento/lisboa/oeiras",
 "sapo": "https://casa.sapo.pt/comprar-apartamentos/oeiras/",
 "bpi-imoveis": "https://www.bpiexpressoimobiliario.pt/comprar/apartamento/oeiras",
 "imovendo": "https://www.imovendo.pt/comprar/lisboa/oeiras",
}
for k, u in URLS.items():
    try:
        st, html, fu = get(u, tentativas=1)
    except Exception as e:
        print(k, "ERRO", e); continue
    h = html or ""
    flags = [f for f in ("__NEXT_DATA__", "__NUXT__", "window.__INITIAL", "application/ld+json", "captcha", "datadome", "cloudflare") if f.lower() in h.lower()]
    n = len(re.findall(r"€", h))
    print(f"{k:16} {st} len={len(h)} euros={n} {flags} -> {fu[:90]}")
    time.sleep(2)
