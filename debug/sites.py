import sys, re, json
sys.path.insert(0, "scraper")
from scrape import get
exec(open("debug/devalue.py").read())
st, h, fu = get("https://www.iadportugal.pt/anuncios/oeiras-1110/venda", tentativas=1)
hrefs = list(dict.fromkeys(re.findall(r'href="([^"]+)"', h)))
print("HREFS", [x for x in hrefs if re.search(r"\d{6,}|/r\d", x)][:10])
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
q = devalue(json.loads(m.group(1)))["data"]["vue-query-state"]["queries"][0]["state"]["data"]
it = q["items"][0]; ref = it["propertyListingRef"]; slug = it["slugs"]["pt"]
print("ITEM", ref, slug, it["location"], it["price"]["main"])
for u in [f"/anuncio/{slug}/r{ref}", f"/anuncio/{slug}-{ref}", f"/anuncio/{ref}", f"/imovel/{slug}/r{ref}", f"/anuncio/r{ref}"]:
    st, h2, fu2 = get("https://www.iadportugal.pt" + u, tentativas=1)
    print("TRY", u, st, fu2[:120], len(h2 or ""))
    if st == 200 and str(ref) in (h2 or ""):
        m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h2, re.S)
        d = devalue(json.loads(m.group(1)))
        for qq in d["data"]["vue-query-state"]["queries"]:
            s = json.dumps(qq["state"]["data"], ensure_ascii=False, default=str)
            if ref in s: print("DETQ", qq.get("queryKey"), s[:3500]); break
        break
