"""Anúncios que a utilizadora acrescentou à mão no radar (secção "Adicionar anúncio por link").

data/links-manuais.json é uma lista de {id, url, preco, tipologia, zona, garagem, notas, criado},
copiada da base de dados do radar pela tarefa diária. Cada link é lido e analisado com as mesmas
regras dos outros anúncios; quando o site não deixa ler (Idealista, SuperCasa...), usam-se os dados
que ela escreveu no formulário. Estes anúncios ficam sempre no radar (não são tirados por falta de
garagem ou por estarem fora das zonas): foi ela que os escolheu.
"""
import html as H
import json
import os
import re
from datetime import date
from urllib.parse import urlparse

from scrape import (BASE, ficha, get, next_data, pausa, chave as chave_imovirtual)
import outros

HOJE = date.today().isoformat()
FICHEIRO = os.path.join(os.path.dirname(__file__), "..", "data", "links-manuais.json")


def numero(v):
    if v in (None, ""):
        return None
    try:
        return float(re.sub(r"[^\d,.]", "", str(v)).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def quartos_de(tip):
    m = re.search(r"T\s?(\d)", tip or "", re.I)
    return int(m.group(1)) if m else None


def nome_site(url):
    h = urlparse(url).hostname or ""
    h = h.replace("www.", "")
    return {"idealista.pt": "Idealista", "supercasa.pt": "SuperCasa", "imovirtual.com": "Imovirtual", "olx.pt": "OLX",
            "custojusto.pt": "CustoJusto", "casa.sapo.pt": "Casa Sapo", "remax.pt": "RE/MAX", "iadportugal.pt": "iad",
            "century21.pt": "Century 21", "era.pt": "ERA", "zome.pt": "Zome", "kwportugal.pt": "KW"}.get(h, h or "Link")


def generico(url):
    """Lê uma página qualquer: título, descrição e o primeiro preço. Devolve None se o site não deixar."""
    st, html, final = get(url)
    pausa()
    if st != 200 or not html:
        return None
    def meta(nome):
        m = re.search(r'<meta[^>]+(?:property|name)="%s"[^>]+content="([^"]*)"' % nome, html, re.I)
        return H.unescape(m.group(1)) if m else ""
    titulo = meta("og:title") or (re.search(r"<title>(.*?)</title>", html, re.S | re.I) or [None, ""])[1]
    corpo = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    corpo = H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", corpo)))
    texto = (meta("og:description") + " " + corpo)[:20000]
    m = re.search(r"(\d{2,3}(?:[ . ]\d{3}))\s?€|€\s?(\d{2,3}(?:[ . ]\d{3}))", texto)
    preco = numero(m.group(1) or m.group(2)) if m else None
    m = re.search(r"(\d{2,3}(?:[.,]\d+)?)\s?m²", texto)
    area = numero(m.group(1)) if m else None
    a = outros.analisar(titulo.strip(), texto, preco, area)
    a.update({"zona": outros.zona_texto(titulo, texto[:3000]), "localizacao": "", "noMercadoDesde": None, "atualizado": None})
    return a


def imovirtual(url, e):
    slug = url.split("/pt/anuncio/")[1].split("?")[0]
    st, d = ficha(slug, f"t{quartos_de(e.get('tipologia')) or 2}", "moradia" if re.search(r"moradia|vivenda", slug) else "apartamento")
    if st != 200 or not d:
        return None, st
    d.pop("reservado", None)
    d["chave"] = chave_imovirtual(url)
    return d, 200


def remax(url):
    titulo = url.rstrip("/").split("/")[-1]
    det = outros.remax_api("Listing/GetListingByTitle?listingPublicId=" + titulo)
    pausa()
    if not det:
        return None
    locs = ["Lisboa", det.get("regionName2") or "", det.get("regionName3") or "", det.get("localZone") or ""]
    a = outros.remax_montar(det, det, det.get("regionName2") or "", locs, det.get("listingPrice") or 0, det.get("numberOfBedrooms"))
    a["chave"] = "REMAX-" + titulo
    return a


def iad(url):
    m = re.search(r"/r(\d+)", url)
    st, html, _ = get(url)
    pausa()
    if st != 200 or not m:
        return None
    ref = m.group(1)
    det = next((q for q in outros.iad_dados(html) if isinstance(q, dict) and str(q.get("propertyListingRef")) == ref), None)
    if not det:
        return None
    desc = det.get("description") or ""
    if isinstance(desc, dict):
        desc = desc.get("pt") or next(iter(desc.values()), "")
    preco = numero((det.get("prices") or {}).get("formattedMain"))
    quartos = det.get("bedroomsCount")
    titulo = det.get("title") or f"T{quartos}"
    a = outros.analisar(titulo, desc, preco, det.get("mainSurface"), None, f"T{quartos}" if quartos else None, quartos)
    place = ((det.get("location") or {}).get("place")) or ""
    a.update({"zona": outros.zona_texto(place, titulo, desc), "localizacao": place,
              "noMercadoDesde": det.get("firstPublishDate"), "atualizado": None, "chave": "IAD-" + ref})
    return a


def custojusto(url):
    st, html, _ = get(url)
    pausa()
    ad = (((next_data(html) or {}).get("props") or {}).get("pageProps") or {}).get("adData") if st == 200 else None
    if not ad:
        return None
    p = ad.get("params") or {}
    tip = ((p.get("rooms") or {}).get("name")) if isinstance(p.get("rooms"), dict) else p.get("rooms")
    a = outros.analisar(ad.get("title"), ad.get("body"), numero(ad.get("price")), numero(p.get("size")),
                        int(p["construction_year"]) if str(p.get("construction_year") or "").isdigit() else None, tip)
    a.update({"zona": outros.zona_texto(ad.get("title"), ad.get("body")), "localizacao": "",
              "noMercadoDesde": (ad.get("listTime") or "")[:10] or None, "atualizado": None,
              "chave": "CJ-" + str(ad.get("listID"))})
    return a


def analisar_link(e):
    """Devolve (chave, anúncio) para um link manual."""
    url = (e.get("url") or "").strip()
    host = urlparse(url).hostname or ""
    a, st = None, None
    try:
        if "imovirtual.com" in host and "/pt/anuncio/" in url:
            a, st = imovirtual(url, e)
        elif "remax.pt" in host:
            a = remax(url)
        elif "iadportugal.pt" in host:
            a = iad(url)
        elif "custojusto.pt" in host:
            a = custojusto(url)
        elif not re.search(r"idealista\.|supercasa\.", host):   # estes dois bloqueiam sempre: nem se tenta
            a = generico(url)
    except Exception as ex:
        print(f"  Aviso: link manual {url} não foi lido: {ex}")
        a = None
    lido = a is not None
    a = a or {"titulo": "", "preco": None, "area": None, "wc": None, "garagem": "Não indicado", "garagemFrase": "",
              "varanda": "Não indicado", "elevador": "Não indicado", "construcao": "Não indicado", "estado": "Não indicado",
              "ano": None, "entrega": "Não se aplica", "arrendado": "Não indicado", "emPlanta": False, "notas": "",
              "zona": None, "localizacao": "", "noMercadoDesde": None, "atualizado": None, "tipologia": "?", "quartos": -1}
    # O que ela escreveu no formulário completa o que o anúncio não diz
    if not a.get("preco") and numero(e.get("preco")):
        a["preco"] = numero(e.get("preco"))
    if e.get("tipologia") and (not a.get("tipologia") or a["tipologia"] == "?" or (a.get("quartos") or -1) < 0):
        a["tipologia"] = e["tipologia"]
    if e.get("zona") and e["zona"] != "Outra":
        a["zona"] = a.get("zona") or e["zona"]
    a["zona"] = a.get("zona") or (e.get("zona") if e.get("zona") and e["zona"] != "Outra" else "Outra zona")
    # restantes campos do formulário (úteis sobretudo no Idealista e no SuperCasa, que não deixam ler o anúncio)
    if numero(e.get("area")) and not a.get("area"):
        a["area"] = numero(e.get("area"))
    if numero(e.get("wc")) and not a.get("wc"):
        a["wc"] = int(numero(e.get("wc")))
    if numero(e.get("ano")) and not a.get("ano"):
        a["ano"] = int(numero(e.get("ano")))
        a["construcao"] = "Recente" if a["ano"] >= 2015 else "Usada"
    for campo in ("varanda", "elevador", "estado", "arrendado"):
        if e.get(campo) and a.get(campo) in (None, "", "Não indicado"):
            a[campo] = e[campo]
    if e.get("titulo") and not lido:
        a["titulo"] = e["titulo"]
    if e.get("garagem") == "Não" and a.get("garagem") in (None, "", "Não indicado"):
        a["garagem"], a["garagemFrase"] = "Não", "Indicado por si ao adicionar o anúncio"
    if e.get("garagem") in ("Sim", "À parte (opcional)") and a.get("garagem") in (None, "", "Não indicado"):
        a["garagem"], a["garagemFrase"] = e["garagem"], "Indicado por si ao adicionar o anúncio"
    if not a.get("titulo"):
        a["titulo"] = f"{a.get('tipologia') or ''} em {a['zona']} ({nome_site(url)})".strip()
    a.pop("quartos", None)
    a.pop("reservado", None)
    k = a.pop("chave", None) or ("MAN-" + str(e.get("id")))
    nota_lida = "" if lido else f" Não foi possível ler o anúncio no {nome_site(url)}: os dados são os que indicou."
    a.update({"url": url, "fonte": a.get("fonte") or nome_site(url), "agencia": a.get("agencia") or nome_site(url),
              "manual": True, "linkManualId": e.get("id"), "analisado": lido,
              "notas": ((a.get("notas") or "") + nota_lida + (f" As suas notas: {e['notas']}" if e.get("notas") else "")).strip(),
              "noMercadoDesde": a.get("noMercadoDesde") or (e.get("criado") or HOJE)[:10]})
    return k, a


def processar(guardados):
    """Junta os links manuais a guardados (dicionário chave -> anúncio). Devolve quantos são novos."""
    try:
        with open(FICHEIRO, encoding="utf-8") as f:
            entradas = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0
    novos = 0
    ids_ativos = {str(e.get("id")) for e in entradas if e.get("url")}
    # links que ela retirou da lista deixam de ser manuais
    for k, x in list(guardados.items()):
        if x.get("manual") and str(x.get("linkManualId")) not in ids_ativos:
            # só entrou no radar por ter sido adicionada à mão (primeira vez = análise do link): sai
            if k.startswith("MAN-") or x.get("soManual"):
                del guardados[k]
                continue
            x.pop("manual", None)
            x.pop("linkManualId", None)
    for e in entradas:
        if not (e.get("url") or "").startswith("http"):
            continue
        k, a = analisar_link(e)
        # se a mesma casa já estiver no radar (pelo link), atualiza essa
        existente = next((kk for kk, x in guardados.items() if x.get("url") == a["url"] or a["url"] in (x.get("outrosLinks") or [])), None)
        k = existente or k
        antigo = guardados.get(k)
        if antigo:
            hist = antigo.get("historicoPrecos", [])
            if antigo.get("preco") and a.get("preco") and a["preco"] != antigo["preco"]:
                hist.append({"data": HOJE, "de": antigo["preco"], "para": a["preco"]})
            if existente and antigo.get("url") != a["url"]:
                antigo.update({"manual": True, "linkManualId": e.get("id")})
            else:
                antigo.update({kk: vv for kk, vv in a.items() if vv not in (None, "")})
            antigo.update({"historicoPrecos": hist, "ultimaVerificacao": HOJE})
            antigo.setdefault("disponibilidade", "Ativo")
        else:
            a.update({"chave": k, "primeiraVez": HOJE, "ultimaVerificacao": HOJE, "disponibilidade": "Ativo", "historicoPrecos": [], "soManual": True})
            guardados[k] = a
            novos += 1
    print(f"Links adicionados à mão: {len(entradas)} ({novos} novos)")
    return novos
