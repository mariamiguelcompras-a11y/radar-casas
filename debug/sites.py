import sys, re, time, json
sys.path.insert(0, "scraper")
from scrape import get
def devalue(arr):
    memo = {}
    def r(i):
        if not isinstance(i, int) or i < 0: return None
        if i in memo: return memo[i]
        v = arr[i]
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in ("ShallowReactive", "Reactive", "Ref", "ShallowRef"): out = r(v[1])
            elif v and isinstance(v[0], str) and v[0] in ("Set", "Map", "Date"): out = v[1:]
            else:
                out = []; memo[i] = out; out.extend(r(x) for x in v); return out
        elif isinstance(v, dict):
            out = {}; memo[i] = out
            for k, x in v.items(): out[k] = r(x)
            return out
        else: out = v
        memo[i] = out; return out
    return r(0)
st, h, fu = get("https://www.iadportugal.pt/anuncios/lisboa/venda", tentativas=1)
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
d = devalue(json.loads(m.group(1)))
q = d["data"]["vue-query-state"]["queries"][0]["state"]["data"]
print("IAD total", q["totalItems"], "per", q["itemsPerPage"])
print("IAD item", json.dumps(q["items"][0], ensure_ascii=False, default=str)[:2500])
print("IAD seo", json.dumps(q["seoLinks"], ensure_ascii=False, default=str)[:1500])
st, h, fu = get("https://www.decisoesesolucoes.com/pt/imoveis/?pg=1&o=1&or=30", tentativas=1)
print("DS links", [x for x in dict.fromkeys(re.findall(r'href="([^"]+)"', h)) if re.search(r"oeiras|cascais|sintra|lisboa", x, re.I)][:15])
print("DS card", re.sub(r"\s+", " ", h[h.find("_15597") - 1500: h.find("_15597") + 1500])[:3000])
st, h, fu = get("https://www.rbrokers.pt/imovel-venda-apartamento-t2-sintra-6224222", tentativas=1)
print("RB", st, len(h))
for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)[:2]: print("RBLD", s[:1500])
i = h.find("€"); print("RBE", re.sub(r"\s+", " ", h[i-800:i+200]))
