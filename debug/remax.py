import sys, re, json, urllib.request
sys.path.insert(0, "scraper")
from scrape import get, next_data
st, h, fu = get("https://remax.pt/pt/comprar/imoveis/apartamento/lisboa/oeiras", tentativas=1)
nd = next_data(h)
pp = nd["props"]["pageProps"]
print("PP keys", list(pp.keys()))
for k in pp:
    v = json.dumps(pp[k], ensure_ascii=False)
    if k not in ("mainFilters","advancedFilters","listingTypeOptions"): print("PP", k, v[:500])
print("buildId", nd.get("buildId"), "page", nd.get("page"), "query", nd.get("query"))
srcs = list(dict.fromkeys(re.findall(r'src="(/_next/static/[^"]+\.js)"', h)))
print(len(srcs))
for s in srcs:
    st2, js, _ = get("https://remax.pt" + s, tentativas=1)
    for m in re.finditer(r"(api/[A-Za-z]+/[A-Za-z]+)", js or ""):
        print("API", s.split('/')[-1][:30], js[max(0,m.start()-200):m.end()+300].replace("\n"," "))
