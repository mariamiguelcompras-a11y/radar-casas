"""Teste pontual: guarda páginas de exemplo (pesquisa + 1 anúncio) dos portais em debug/amostras/."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from scrape import get
OUT = "debug/amostras"; os.makedirs(OUT, exist_ok=True)
SITES = {
 "casasapo": ("https://casa.sapo.pt/comprar-apartamentos/t2/oeiras/", r'href="(https://casa\.sapo\.pt/comprar-apartamento[^"]+\.html[^"]*)"'),
 "olx": ("https://www.olx.pt/imoveis/apartamento-casa-a-venda/apartamentos-venda/oeiras/?search%5Bfilter_enum_tipologia%5D%5B0%5D=t2", r'href="(/d/anuncio/[^"]+\.html)"'),
 "custojusto": ("https://www.custojusto.pt/lisboa/oeiras/imobiliario/apartamentos-casas-venda", r'href="(https://www\.custojusto\.pt/lisboa/[^"]+/\d+)"'),
}
for nome, (url, rx) in SITES.items():
    st, html, final = get(url, tentativas=2)
    open(f"{OUT}/{nome}_pesquisa.html", "w", encoding="utf-8").write(html)
    links = re.findall(rx, html)
    print(nome, st, final, len(html), "links", len(links), links[:3])
    if links:
        u = links[0] if links[0].startswith("http") else "https://www.olx.pt" + links[0]
        st2, h2, f2 = get(u, tentativas=2)
        open(f"{OUT}/{nome}_anuncio.html", "w", encoding="utf-8").write(h2)
        print("  anuncio", st2, f2, len(h2))
