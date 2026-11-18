"""Pesquisa rápida só dos links que a utilizadora acrescentou no radar (corre em 1–3 minutos).

Lê data/imoveis.json, analisa os links de data/links-manuais.json e grava o resultado,
sem esperar pela pesquisa completa da manhã.
"""
import json

import manuais
from scrape import DATA_FILE


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        guardados = {x["chave"]: x for x in json.load(f)}
    novos = manuais.processar(guardados)
    lista = sorted(guardados.values(), key=lambda x: (x.get("noMercadoDesde") or ""), reverse=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=1)
    print(f"Links manuais analisados; {novos} novos no radar.")


if __name__ == "__main__":
    main()
