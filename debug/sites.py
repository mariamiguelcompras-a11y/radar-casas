import sys, re, time, json
sys.path.insert(0, "scraper")
from scrape import get
exec(open("debug/devalue.py").read())
st, h, fu = get("https://www.iadportugal.pt/anuncios/oeiras-1110/venda?page=2", tentativas=1)
print("LIST", st, fu)
links = list(dict.fromkeys(re.findall(r'href="(/anuncio[^"]+)"', h)))[:5]
print("LINKS", links)
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
d = devalue(json.loads(m.group(1)))
q = d["data"]["vue-query-state"]["queries"][0]["state"]["data"]
print("TOTAL", q["totalItems"], [ (x["propertyListingRef"], x["location"], x["price"]["main"]) for x in q["items"][:5]])
if links:
    st, h2, fu2 = get("https://www.iadportugal.pt" + links[0], tentativas=1)
    print("DET", st, fu2)
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h2, re.S)
    d2 = devalue(json.loads(m.group(1)))
    for qq in d2["data"]["vue-query-state"]["queries"]:
        print("QKEY", qq.get("queryKey"))
        print("QDATA", json.dumps(qq["state"]["data"], ensure_ascii=False, default=str)[:4000])
