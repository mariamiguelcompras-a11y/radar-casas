"""Teste pontual: que sites conseguem ser lidos a partir do GitHub (estado, bloqueio, dados estruturados)."""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from scrape import get
SITES = {
 "idealista": "https://www.idealista.pt/comprar-casas/oeiras/com-t2/",
 "casasapo": "https://casa.sapo.pt/comprar-apartamentos/t2/oeiras/",
 "supercasa": "https://supercasa.pt/comprar-casas/oeiras/com-t2",
 "portalimobiliario": "https://portalimobiliario.com.pt/",
 "construcaonova": "https://construcaonova.pt/",
 "flatin": "https://flatin.pt/",
 "casayes": "https://www.casayes.pt/",
 "imoportugal": "https://imo-portugal.com/",
 "habitarportugal": "https://www.habitarportugal.pt/",
 "creditocasa": "https://www.creditocasa.pt/",
 "casaportugal": "https://www.casaportugal.pt/",
 "agentecasa": "https://agentecasa.pt/",
 "casatoo": "https://casatoo.pt/pt",
 "olx": "https://www.olx.pt/imoveis/apartamento-casa-a-venda/oeiras/",
 "custojusto": "https://www.custojusto.pt/lisboa/oeiras/imobiliario",
 "hatudo": "https://www.hatudo.pt/",
 "trovit": "https://casa.trovit.pt/index.php/cod.search_homes/type.1/what_d.oeiras%20t2/",
 "mitula": "https://casas.mitula.pt/casas/apartamento-t2-oeiras",
 "nestoria": "https://www.nestoria.pt/oeiras/apartamento/venda",
 "kyero": "https://www.kyero.com/pt/portugal",
 "greenacres": "https://www.green-acres.pt/",
 "properstar": "https://www.properstar.pt/",
 "remax": "https://www.remax.pt/",
 "era": "https://www.era.pt/",
 "century21": "https://www.century21.pt/",
 "zome": "https://www.zome.pt/",
 "kw": "https://www.kwportugal.pt/",
 "engelvoelkers": "https://www.engelvoelkers.com/pt/pt",
 "predimed": "https://www.predimed.pt/",
 "comprarcasa": "https://www.comprarcasa.pt/",
 "veigas": "https://www.veigas.eu/",
 "dils": "https://dils.com/pt/",
}
res = {}
for nome, url in SITES.items():
    t = time.time()
    st, html, final = get(url, tentativas=1)
    low = html.lower()
    res[nome] = {
        "status": st, "final": final[:120], "bytes": len(html), "s": round(time.time() - t, 1),
        "bloqueio": bool(re.search(r"captcha|cf-chl|just a moment|access denied|datadome|px-captcha|attention required", low)),
        "next_data": "__next_data__" in low, "ld_json": low.count("application/ld+json"),
        "precos_eur": len(re.findall(r"\d{3}[ .]\d{3}\s?€|€\s?\d{3}[ .]\d{3}", html)),
        "t2": len(re.findall(r"\bT2\b", html)),
    }
    print(nome, res[nome])
os.makedirs("debug", exist_ok=True)
json.dump(res, open("debug/sites.json", "w"), ensure_ascii=False, indent=1)
