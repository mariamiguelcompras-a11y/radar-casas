import sys, re, json
sys.path.insert(0, "scraper")
from scrape import get, next_data
st, h, fu = get("https://remax.pt/pt/comprar/imoveis/apartamento/lisboa/oeiras", tentativas=1)
nd = next_data(h)
def walk(o, path="", d=0):
    if d > 6: return
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, list) and v and isinstance(v[0], dict): print("LIST", path + "/" + k, len(v), list(v[0].keys())[:30])
            walk(v, path + "/" + k, d + 1)
walk(nd)
m = re.findall(r'href="(/pt/imoveis/[^"]+)"', h)[:5]; print("hrefs", m)
for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)[:2]: print("LD", s[:600])
st, h, fu = get("https://www.kwportugal.pt/pt/imoveis?business=sale&district=lisboa&county=oeiras", tentativas=1)
for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)[:2]: print("KWLD", s[:800])
print("KW hrefs", list(dict.fromkeys(re.findall(r'href="([^"]*imove[^"]*)"', h)))[:15])
