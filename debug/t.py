import sys, json; sys.path.insert(0, "scraper")
import manuais
for e in [{"id":"t1","url":"https://www.imovirtual.com/pt/anuncio/apartamento-t2-para-venda-ID1jeai","tipologia":"T2"},
          {"id":"t2","url":"https://remax.pt/pt/imoveis/venda-apartamento-t3-cascais-alcabideche/126361026-10"},
          {"id":"t3","url":"https://www.iadportugal.pt/anuncio/apartamento-venda-2-quartos-queluz-80m2/r1034540"},
          {"id":"t4","url":"https://www.idealista.pt/imovel/12345678/","preco":"310000","tipologia":"T3","zona":"Cascais","garagem":"Sim"},
          {"id":"t5","url":"https://www.predimed.pt/Imovel/34grmg"}]:
    k, a = manuais.analisar_link(e)
    print("R", k, a.get("fonte"), a.get("tipologia"), a.get("preco"), a.get("zona"), a.get("garagem"), a.get("analisado"), "|", (a.get("titulo") or "")[:60])
g = {}
open("data/links-manuais.json","w").write(json.dumps([{"id":"t4","url":"https://www.idealista.pt/imovel/12345678/","preco":"310000","tipologia":"T3","zona":"Cascais","garagem":"Sim"}]))
print("NOVOS", manuais.processar(g), list(g))
