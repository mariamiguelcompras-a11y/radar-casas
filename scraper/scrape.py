"""Radar de casas: recolhe anúncios do Imovirtual e atualiza data/imoveis.json.

Corre no GitHub Actions de 2 em 2 dias. Só usa a biblioteca padrão do Python.

O que faz em cada execução:
1. Percorre as páginas de resultados do Imovirtual por zona e tipologia
   (T2 a T5+, apartamentos e moradias, até PRECO_MAX).
2. Abre a ficha de cada anúncio e lê os dados estruturados (preço, área,
   casas de banho, extras, ano, estado, data de entrada no mercado, agência).
3. Volta a abrir os anúncios já guardados que não apareceram nas pesquisas:
   se a ficha já não existir (404/410 ou sem anúncio), marca-os "Removido".
4. Guarda o histórico de preços e nunca grava um link que não abra a ficha.
"""
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "imoveis.json")
LOG_FILE = os.path.join(ROOT, "data", "ultima-execucao.json")

PRECO_MAX = 360000          # teto (até 10 000 € acima de 350 000 € entra como "acima do teto")
PRECO_MIN = 50000           # abaixo disto é quase sempre um arrendamento mal classificado
BASE = "https://www.imovirtual.com"

# Zonas pesquisadas no Imovirtual (caminho da pesquisa)
LOCAIS = [
    "lisboa/oeiras",
    "lisboa/cascais",
    "lisboa/amadora/alfragide",
    "lisboa/sintra/massama-e-monte-abraao",
    "lisboa/sintra/queluz-e-belas",
]
TIPOS = ["apartamento", "moradia"]
TIPOLOGIAS = ["t2", "t3", "t4", "t5"]

# Sub-zonas de Sintra que ficam longe de Oeiras/Cascais: não entram
SINTRA_EXCLUIR = ["belas", "idanha", "carregueira", "tala", "venda seca", "a-da-beja", "serra da silveira"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

HOJE = date.today().isoformat()


def get(url, tentativas=3):
    """Devolve (status, texto, url_final). Status 0 = falha de rede."""
    for n in range(tentativas):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace"), r.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return e.code, "", url
            if e.code in (403, 429, 500, 502, 503) and n < tentativas - 1:
                time.sleep(5 * (n + 1))
                continue
            return e.code, "", url
        except Exception:
            if n < tentativas - 1:
                time.sleep(5 * (n + 1))
                continue
            return 0, "", url
    return 0, "", url


def pausa():
    time.sleep(1.0 + random.random())


def next_data(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def pesquisa(tipo, tipologia, local):
    """Devolve a lista de slugs dos anúncios de uma pesquisa (todas as páginas)."""
    slugs = []
    for pagina in range(1, 15):
        url = f"{BASE}/pt/resultados/comprar/{tipo},{tipologia}/{local}?priceMax={PRECO_MAX}&limit=72&page={pagina}"
        status, html, _ = get(url)
        pausa()
        if status != 200:
            print(f"  ! pesquisa falhou ({status}): {url}")
            break
        nd = next_data(html)
        try:
            dados = nd["props"]["pageProps"]["data"]["searchAds"]
        except (TypeError, KeyError):
            print(f"  ! pesquisa sem dados: {url}")
            break
        items = dados.get("items") or []
        for it in items:
            if it.get("slug"):
                slugs.append(it["slug"])
        total_paginas = (dados.get("pagination") or {}).get("totalPages") or 1
        if pagina >= total_paginas or not items:
            break
    return slugs


def zona_de(locs):
    """locs = nomes da localização, do distrito para a rua. Devolve a zona ou None (fora)."""
    nomes = [n.lower() for n in locs]
    txt = " > ".join(nomes)
    if "oeiras" in nomes:
        if "algés, linda-a-velha e cruz quebrada-dafundo" in nomes:
            return "Oeiras" if "linda-a-velha" in nomes else "Algés"
        return "Oeiras"
    if "cascais" in nomes:
        if "carcavelos e parede" in nomes:
            return "Carcavelos"
        if "alcabideche" in nomes:
            return "Alcabideche"
        return "Cascais"
    if "amadora" in nomes:
        return "Alfragide" if "alfragide" in nomes else None
    if "sintra" in nomes:
        if not ("massamá e monte abraão" in nomes or "queluz e belas" in nomes):
            return None
        sub = nomes[-1] if nomes else ""
        if any(x in sub for x in SINTRA_EXCLUIR) and "queluz" not in sub:
            return None
        return "Sintra (perto)"
    return None


def num(v):
    if isinstance(v, list):
        v = v[0] if v else None
    if v is None:
        return None
    m = re.search(r"\d+(?:[.,]\d+)?", str(v))
    return float(m.group(0).replace(",", ".")) if m else None


def ficha(slug, tipologia_pesquisa, tipo):
    """Lê a ficha de um anúncio. Devolve (status, dados ou None)."""
    url = f"{BASE}/pt/anuncio/{slug}"
    status, html, final = get(url)
    pausa()
    if status != 200:
        return status, None
    if "/pt/anuncio/" not in final:
        return 404, None
    nd = next_data(html)
    ad = (((nd or {}).get("props") or {}).get("pageProps") or {}).get("ad")
    if not ad:
        return 404, None
    t = ad.get("target") or {}
    desc = re.sub(r"<[^>]+>", " ", ad.get("description") or "")
    dl = desc.lower()
    titulo = ad.get("title") or ""
    tl = titulo.lower()
    extras = [str(x).lower() for x in (t.get("Extras_types") or [])]
    locs = [l.get("name", "") for l in ((ad.get("location") or {}).get("reverseGeocoding") or {}).get("locations") or []]
    rua = (((ad.get("location") or {}).get("address") or {}).get("street") or {}).get("name") or ""

    preco = num(t.get("Price"))
    area = num(t.get("Area"))
    wc_raw = t.get("Bathrooms_num")
    wc = None
    if wc_raw:
        w = wc_raw[0] if isinstance(wc_raw, list) else wc_raw
        wc = 4 if "more" in str(w) else (int(num(w)) if num(w) is not None else None)
    ano = num(t.get("Build_year"))
    ano = int(ano) if ano and 1800 < ano < 2100 else None
    cs = ",".join(t.get("Construction_status") or [])
    nova = (t.get("MarketType") == "primary") or bool(re.search(r"\b(a estrear|nova constru|em constru)", tl + " " + dl))

    if "garage" in extras or re.search(r"\b(garagem|box)\b", tl):
        garagem = "Sim"
    elif re.search(r"\b(garagem|box|parqueamento|lugar de estacionamento|estacionamento privativo)\b", dl):
        garagem = "Por confirmar"
    else:
        garagem = "Não indicado"
    if re.search(r"sem elevador", dl + " " + tl):
        elevador = "Não"
    elif "lift" in extras or "elevador" in dl:
        elevador = "Sim"
    else:
        elevador = "Não indicado"
    varanda = "Sim" if (any(x in extras for x in ("balcony", "terrace", "garden")) or re.search(r"\b(varanda|terraço|terraco|jardim)\b", dl + " " + tl)) else "Não indicado"

    if nova:
        estado = "Novo"
    elif re.search(r"remodelad|renovad", tl + " " + dl) and "para remodelar" not in dl and "a necessitar" not in dl:
        estado = "Renovado"
    elif "to_renovation" in cs or re.search(r"para (remodelar|renovar|recuperar)|precisa de obras", tl + " " + dl):
        estado = "Para remodelar"
    elif "ready_to_use" in cs:
        estado = "Bom"
    else:
        estado = "Não indicado"
    construcao = "Nova" if nova else ("Recente" if ano and ano >= 2015 else "Usada")

    entrega = "Não se aplica"
    if nova:
        m = re.search(r"(entrega|conclus[aã]o|conclu[ií]d[oa]|previs[aã]o)[^.]{0,60}?(20\d\d)", dl)
        entrega = (m.group(0).strip().capitalize() if m else "Não indicado")

    arrendado = "Não indicado"
    if re.search(r"(arrendad[oa] (atualmente|actualmente|até|com contrato)|com inquilino|vendid[oa] com inquilino|contrato de arrendamento (em vigor|até|ativo)|encontra-se arrendad|está arrendad|atualmente arrendad|inquilin)", dl):
        arrendado = "Sim"

    pref = "Moradia " if tipo == "moradia" else ""
    tip = pref + tipologia_pesquisa.upper()
    if re.search(r"\bt\s?\d\s?\+\s?\d", tl):
        m = re.search(r"\bt\s?(\d)\s?\+\s?(\d)", tl)
        tip = f"{pref}T{m.group(1)}+{m.group(2)}"

    notas = []
    if re.search(r"\bsu[ií]te\b", dl + " " + tl):
        notas.append("Com suite.")
    if garagem == "Por confirmar":
        notas.append("A descrição fala de estacionamento: confirmar se é privativo.")
    if arrendado == "Sim":
        notas.append("A descrição refere inquilino/arrendamento: confirmar.")
    piso = ",".join(t.get("Floor_no") or []).replace("floor_", "").replace("ground_floor", "r/c")
    if piso:
        notas.append(f"Andar: {piso}.")
    ce = ",".join(t.get("Energy_certificate") or []).upper()
    if ce:
        notas.append(f"Certificado energético {ce}.")

    return 200, {
        "id": ad.get("id"),
        "titulo": titulo,
        "localizacao": ", ".join([x for x in [locs[-1] if locs else "", rua] if x]) or titulo,
        "zona": zona_de(locs),
        "preco": preco,
        "area": area,
        "tipologia": tip,
        "wc": wc,
        "garagem": garagem,
        "varanda": varanda,
        "elevador": elevador,
        "construcao": construcao,
        "estado": estado,
        "ano": ano,
        "entrega": entrega,
        "arrendado": arrendado,
        "noMercadoDesde": (ad.get("createdAtFirst") or ad.get("createdAt") or "")[:10] or None,
        "atualizado": (ad.get("modifiedAt") or "")[:10] or None,
        "url": url,
        "fonte": "Imovirtual",
        "agencia": ((ad.get("agency") or {}).get("name") or (ad.get("owner") or {}).get("name") or "Particular"),
        "notas": " ".join(notas),
    }


def chave(url):
    m = re.search(r"-(ID[0-9A-Za-z]+)(?:\.html)?$", url)
    return m.group(1) if m else url


def main():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            guardados = {x["chave"]: x for x in json.load(f)}
    except FileNotFoundError:
        guardados = {}

    # 1. Pesquisas
    vistos = {}  # chave -> (slug, tipologia, tipo)
    falhas_pesquisa = 0
    for tipo in TIPOS:
        for tipologia in TIPOLOGIAS:
            for local in LOCAIS:
                print(f"Pesquisa: {tipo} {tipologia} {local}")
                slugs = pesquisa(tipo, tipologia, local)
                if not slugs:
                    falhas_pesquisa += 0  # pesquisa vazia é normal (ex. moradias T2 em Alfragide)
                for s in slugs:
                    k = chave(s)
                    vistos.setdefault(k, (s, tipologia, tipo))
    print(f"Anúncios encontrados nas pesquisas: {len(vistos)}")
    if not vistos:
        print("ERRO: nenhuma pesquisa devolveu anúncios. O Imovirtual pode ter bloqueado o pedido. Nada foi alterado.")
        sys.exit(1)

    # 2. Fichas dos anúncios encontrados
    novos = atualizados = removidos = 0
    for k, (slug, tipologia, tipo) in vistos.items():
        status, d = ficha(slug, tipologia, tipo)
        if status != 200 or not d:
            continue
        if d["zona"] is None or d["preco"] is None or not (PRECO_MIN <= d["preco"] <= PRECO_MAX):
            continue
        antigo = guardados.get(k)
        if antigo:
            hist = antigo.get("historicoPrecos", [])
            if antigo.get("preco") and d["preco"] != antigo["preco"]:
                hist.append({"data": HOJE, "de": antigo["preco"], "para": d["preco"]})
            antigo.update({kk: vv for kk, vv in d.items() if vv is not None})
            antigo.update({"historicoPrecos": hist, "ultimaVerificacao": HOJE, "disponibilidade": "Ativo"})
            atualizados += 1
        else:
            d.update({"chave": k, "primeiraVez": HOJE, "ultimaVerificacao": HOJE,
                      "disponibilidade": "Ativo", "historicoPrecos": []})
            guardados[k] = d
            novos += 1

    # 3. Anúncios guardados que não apareceram: confirmar se ainda existem
    for k, x in guardados.items():
        if k in vistos or x.get("disponibilidade") == "Removido":
            continue
        status, html, final = get(x["url"])
        pausa()
        ok = status == 200 and "/pt/anuncio/" in final and next_data(html) and (next_data(html).get("props", {}).get("pageProps", {}).get("ad"))
        if status in (404, 410) or (status == 200 and not ok):
            x["disponibilidade"] = "Removido"
            removidos += 1
        x["ultimaVerificacao"] = HOJE

    lista = sorted(guardados.values(), key=lambda x: (x.get("noMercadoDesde") or ""), reverse=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=1)
    resumo = {"data": HOJE, "encontrados": len(vistos), "novos": novos, "atualizados": atualizados,
              "removidos": removidos, "total": len(lista),
              "ativos": sum(1 for x in lista if x.get("disponibilidade") == "Ativo")}
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=1)
    print(json.dumps(resumo, ensure_ascii=False))


if __name__ == "__main__":
    main()
