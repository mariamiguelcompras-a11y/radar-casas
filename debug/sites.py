import sys, re, time
sys.path.insert(0, "scraper")
from scrape import get
SITES = ["https://www.century21.pt", "https://www.zome.pt", "https://www.kwportugal.pt", "https://www.iadportugal.pt",
 "https://www.decisoesesolucoes.com", "https://www.predimed.pt", "https://www.exp-portugal.pt", "https://www.castelhana.pt",
 "https://www.era.pt", "https://www.josebirra.pt", "https://www.casaideal.pt", "https://www.habisale.pt", "https://www.citylux.pt",
 "https://www.dommus.pt", "https://www.goldenagata.pt", "https://www.cascaisazul.pt", "https://www.imojoy.pt", "https://www.elitehomes.pt",
 "https://www.especialcasa.pt", "https://www.valordemercado.pt", "https://www.newloft.pt", "https://www.medimaio.pt", "https://www.uon.pt",
 "https://www.konsultti.pt", "https://www.veigas.pt", "https://www.rbrokers.pt", "https://www.isabelveigacabral.com", "https://www.fatimaemario.pt"]
FP = {"eGO": r"egorealestate|ego-real-estate|egorealestate\.com", "JanelaDigital": r"janeladigital|jd-imoveis", "Next": r"__NEXT_DATA__", "Nuxt": r"__NUXT__|_nuxt/",
      "WordPress": r"wp-content", "Wix": r"wixstatic|_wix", "Cloudflare-challenge": r"cf-chl|challenge-platform", "Casafari": r"casafari", "Infinity": r"infinityimob|imoinfinity", "Imopower": r"imopower", "Bitrix": r"bitrix", "React": r"id=\"root\"|data-reactroot"}
for s in SITES:
    try:
        st, h, fu = get(s, tentativas=1)
    except Exception as e:
        print(f"SITE {s} ERRO {e}"); continue
    h = h or ""
    fp = [k for k, r in FP.items() if re.search(r, h, re.I)]
    links = list(dict.fromkeys(re.findall(r'href="([^"]*(?:comprar|venda|imoveis|imóveis|properties|propriedades|search|pesquisa)[^"]*)"', h, re.I)))[:6]
    apis = list(dict.fromkeys(re.findall(r'["\'](/?api/[A-Za-z0-9/_-]+)', h)))[:6]
    print(f"SITE {s} {st} len={len(h)} -> {fu[:60]} {fp} LINKS {links} APIS {apis}")
    time.sleep(1)
