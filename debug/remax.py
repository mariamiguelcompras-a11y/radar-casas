import sys, collections; sys.path.insert(0, "scraper")
import outros
r = outros.remax()
print("TOTAL", len(r), collections.Counter((x["zona"], x["garagem"]) for x in r).most_common())
for x in r[:12]: print("EX", x["zona"], x["tipologia"], x["preco"], x["area"], x["wc"], x["garagem"], "|", (x["garagemFrase"] or "")[:80], "|", x["url"])
