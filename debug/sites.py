import sys, re, time, json
sys.path.insert(0, "scraper")
from scrape import get
def show(k, u, n=3, around=300):
    st, h, fu = get(u, tentativas=1); h = h or ""
    print(f"P {k} {st} {len(h)} {fu}")
    for m in list(re.finditer(r"€", h))[:n]:
        print("  E", re.sub(r"\s+", " ", h[max(0, m.start()-around): m.end()+80]))
    return h
h = show("habisale", "https://www.habisale.pt/comprar", 2, 900)
print("  HREF", list(dict.fromkeys(re.findall(r'href="(/[^"]*imovel[^"]*|/[^"]*\d{5,}[^"]*)"', h)))[:8])
print("  FORMS", re.findall(r'(?:action|data-url|data-href)="([^"]+)"', h)[:10])
h = show("ds-lisboa", "https://www.decisoesesolucoes.com/pt/imoveis/?pg=1&o=1&dd=11&cc=1110&or=30", 1, 600)
print("  SELECT", re.findall(r'<select[^>]*name="([^"]+)"', h)[:20])
print("  OPTS", re.findall(r'<option value="(\d+)"[^>]*>\s*(Oeiras|Cascais|Sintra|Lisboa|Amadora)\s*<', h)[:10])
h = show("iad", "https://www.iadportugal.pt/anuncios/lisboa/venda", 0)
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
print("  NUXTDATA", (m.group(1)[:1500] if m else "none"))
h = show("predimed", "https://www.predimed.pt/Imovel/34grmg", 2, 400)
for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)[:3]: print("  LD", s[:800])
