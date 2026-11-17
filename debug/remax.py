import sys, json; sys.path.insert(0, "scraper")
import outros
d = outros.remax_api("Listing/GetListingByTitle?listingPublicId=123751650-27")
print("DESCS", json.dumps(d.get("descriptions"), ensure_ascii=False)[:3000])
def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items(): walk(v, p + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o[:3]): walk(v, f"{p}[{i}]")
    elif isinstance(o, str) and len(o) > 150: print("LONG", p, o[:200].replace("\n", " "))
walk(d)
from scrape import get
st, h, f = get("https://remax.pt/pt/imoveis/venda-apartamento-t2-oeiras-alges-linda-a-velha-e-cruz-quebrada-dafundo/123751650-27")
import re
for m in re.finditer(r"garage|parque|estaciona", h, re.I):
    print("PAGE", h[max(0, m.start()-120): m.end()+120].replace("\n", " ")[:260]); 
