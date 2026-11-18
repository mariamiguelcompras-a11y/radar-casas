"""Outros portais além do Imovirtual: OLX, CustoJusto, Casa Sapo e RE/MAX.

Cada função devolve anúncios no mesmo formato de data/imoveis.json (sem os campos de controlo,
que o scrape.py acrescenta). Os sites que bloqueiam são saltados sem estragar o resto da pesquisa.
"""
import html as H
import json
import re
import time
from datetime import date, datetime, timedelta

import urllib.request

from scrape import (EXCLUIR_TITULO, PRECO_MAX, PRECO_MIN, classificar_garagem, get, next_data, pausa, zona_de)

HOJE = date.today().isoformat()

# Palavras da localização -> zona (a ordem importa: o mais específico primeiro)
ZONAS = [
    ("Alfragide", r"alfragide"),
    ("Linda-a-Velha", r"linda-a-velha|linda a velha"),
    ("Restelo", r"restelo"),
    ("Telheiras", r"telheiras"),
    ("Braço de Prata", r"bra[cç]o de prata"),
    ("Monsanto", r"monsanto"),
    ("Rio de Mouro", r"rio de mouro|rinchoa|serra das minas|albarraque"),
    ("São Marcos", r"s[aã]o marcos"),
    ("Algés", r"alg[eé]s|cruz quebrada|dafundo|miraflores"),
    ("Carcavelos", r"carcavelos|\bparede\b(?!s)"),
    ("Alcabideche", r"alcabideche|alvide|murches|malveira da serra|amoreira"),
    ("Cascais", r"cascais|estoril|s[aã]o domingos de rana|abóboda|aboboda|tires|trajouce|talaíde|talaide|caparide|matarraque"),
    ("Oeiras", r"oeiras|pa[cç]o de arcos|caxias|porto salvo|barcarena|carnaxide|queijas|tercena|leceia|outurela"),
    ("Sintra (perto)", r"massam[aá]|monte abra[aã]o|queluz|pend[aã]o|campinas"),
]
EXCLUIR_LOCAL = re.compile(r"belas|idanha|carregueira|reboleira|venteira|amadora(?!.*alfragide)|buraca", re.I)


def zona_texto(*partes):
    txt = " ".join(p for p in partes if p).lower()
    for zona, rx in ZONAS:
        if re.search(rx, txt):
            if zona == "Sintra (perto)" and re.search(r"belas|idanha|carregueira", txt) and "queluz" not in txt:
                return None
            return zona
    return None


PALAVRA_NUM = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tr[eê]s": 3, "quatro": 4}


def analisar(titulo, desc, preco, area=None, ano=None, tipologia=None, quartos=None):
    """Aplica as mesmas regras do Imovirtual a um texto de anúncio."""
    tl, dl = (titulo or "").lower(), re.sub(r"<[^>]+>", " ", H.unescape(desc or "")).lower()
    texto = tl + " " + dl
    if quartos is None:
        m = re.search(r"\b[tv]\s?(\d)(?:\s?\+\s?(\d))?\b", tipologia.lower() if tipologia else tl) or re.search(r"\b[tv]\s?(\d)(?:\s?\+\s?(\d))?\b", dl)
        quartos = int(m.group(1)) if m else None
        extra = m.group(2) if m else None
    else:
        extra = None
    if re.search(r"\best[uú]dio\b", tl):
        quartos = 0
    wc = None
    m = re.search(r"(\d|um|uma|dois|duas|tr[eê]s|quatro)\s+(?:casas? de banho|wc|i\.?\s?s\.?\b|instala[cç][oõ]es sanit[aá]rias)", texto)
    if m:
        v = m.group(1)
        wc = int(v) if v.isdigit() else next((n for k, n in PALAVRA_NUM.items() if re.fullmatch(k, v)), None)
    elif re.search(r"su[ií]te", texto) and re.search(r"casa de banho (social|de servi[cç]o|completa)", texto):
        wc = 2
    garagem, frase = classificar_garagem([], tl, dl)
    elevador = "Não" if "sem elevador" in texto else ("Sim" if "elevador" in texto else "Não indicado")
    varanda = "Sim" if re.search(r"\b(varanda|terra[cç]o|jardim|logradouro)\b", texto) else "Não indicado"
    if re.search(r"para (remodelar|renovar|recuperar)|precisa de obras|necessita de obras", texto):
        estado = "Para remodelar"
    elif re.search(r"remodelad|renovad", texto):
        estado = "Renovado"
    elif re.search(r"a estrear|nova constru|novo\b", texto):
        estado = "Novo"
    else:
        estado = "Não indicado"
    construcao = "Nova" if re.search(r"a estrear|nova constru", texto) else ("Recente" if ano and ano >= 2015 else "Usada")
    em_planta = bool(re.search(r"em planta|em constru[cç][aã]o|entrega prevista|conclus[aã]o prevista|previs[aã]o de (entrega|conclus)", texto))
    m_arr = re.search(r"(vendid[oa] com inquilino|com inquilino|atualmente arrendad|actualmente arrendad|encontra-se arrendad|est[aá] arrendad|arrendad[oa] at[eé]|contrato de arrendamento (em vigor|at[eé]|v[aá]lido|ativo)|com rendimento)", texto)
    notas = []
    if re.search(r"\bsu[ií]te\b", texto):
        notas.append("Com suite.")
    if frase:
        notas.append(f"Garagem: \"{frase[:160]}\".")
    if m_arr:
        i = m_arr.start()
        notas.append(f"Arrendado? A descrição diz: \"…{texto[max(0, i - 40): i + 60].strip()}…\" — confirmar.")
    entrega = "Não se aplica"
    if em_planta or construcao == "Nova":
        m = re.search(r"(entrega|conclus[aã]o|previs[aã]o|trimestre)[^.]{0,60}?(20\d\d)", dl)
        entrega = m.group(0).strip().capitalize() if m else "Não indicado"
    pref = "Moradia " if re.search(r"\bmoradia|\bvivenda|\bcasa (t|v)\d", tl) else ""
    return {
        "quartos": quartos if quartos is not None else -1,
        "tipologia": f"{pref}T{quartos}" + (f"+{extra}" if extra else "") if quartos is not None else (tipologia or "?"),
        "titulo": titulo, "preco": preco, "area": area, "wc": wc, "garagem": garagem, "garagemFrase": frase,
        "varanda": varanda, "elevador": elevador, "construcao": construcao, "estado": estado, "ano": ano,
        "entrega": entrega, "arrendado": "Sim" if m_arr else "Não indicado", "emPlanta": em_planta,
        "notas": " ".join(notas),
    }


def valido(d):
    return (d.get("zona") and d.get("preco") and PRECO_MIN <= d["preco"] <= PRECO_MAX
            and d.get("quartos", -1) >= 2 and not EXCLUIR_TITULO.search(d.get("titulo") or ""))


# ---------------------------------------------------------------- OLX
OLX_LOCAIS = ["oeiras", "paco-de-arcos", "carnaxide", "linda-a-velha", "alges", "cascais", "estoril", "carcavelos",
              "parede", "sao-domingos-de-rana", "alcabideche", "alfragide", "massama", "monte-abraao", "queluz",
              "rio-de-mouro", "sao-marcos", "restelo", "telheiras", "monsanto", "braco-de-prata"]
OLX_CATS = ["apartamentos-venda", "moradias-venda"]


def olx():
    vistos, out = set(), []
    for cat in OLX_CATS:
        for q in OLX_LOCAIS:
            for pagina in range(1, 8):
                url = (f"https://www.olx.pt/imoveis/apartamento-casa-a-venda/{cat}/q-{q}/"
                       f"?search%5Bfilter_float_price:to%5D={PRECO_MAX}&page={pagina}")
                st, html, _ = get(url)
                pausa()
                m = re.search(r'window\.__PRERENDERED_STATE__\s*=\s*"(.*?)";\s*\n', html or "", re.S)
                if st != 200 or not m:
                    print(f"  OLX falhou ({st}) {q}")
                    break
                L = json.loads(json.loads('"' + m.group(1) + '"'))["listing"]["listing"]
                ads = L.get("ads") or []
                for a in ads:
                    if a["url"] in vistos:
                        continue
                    vistos.add(a["url"])
                    params = {p.get("key"): p for p in a.get("params") or []}
                    preco = ((a.get("price") or {}).get("regularPrice") or {}).get("value")
                    area = None
                    if "area_util" in params:
                        try:
                            area = float(params["area_util"].get("normalizedValue"))
                        except (TypeError, ValueError):
                            pass
                    tip = (params.get("tipologia") or {}).get("value")
                    loc = (a.get("location") or {})
                    if (loc.get("regionName") or "").lower() != "lisboa":
                        continue
                    d = analisar(a.get("title"), a.get("description"), float(preco) if preco else None, area, None, tip)
                    d.update({
                        "zona": zona_texto(loc.get("cityName"), loc.get("pathName")) if not EXCLUIR_LOCAL.search(loc.get("pathName") or "") else None,
                        "localizacao": loc.get("cityName") or "",
                        "noMercadoDesde": (a.get("createdTime") or "")[:10] or None,
                        "atualizado": (a.get("lastRefreshTime") or "")[:10] or None,
                        "url": a["url"], "fonte": "OLX",
                        "agencia": "Profissional (OLX)" if a.get("isBusiness") else "Particular",
                        "chave": "OLX-" + str(a.get("id")),
                    })
                    if valido(d):
                        out.append(d)
                if pagina >= (L.get("totalPages") or 1) or not ads:
                    break
    print(f"OLX: {len(out)} anúncios válidos")
    return out


# ---------------------------------------------------------------- CustoJusto
CJ_CONCELHOS = ["oeiras", "cascais", "sintra", "amadora", "lisboa"]
CJ_CATS = ["apartamentos-venda", "moradias-venda"]


def custojusto():
    vistos, out = set(), []
    for conc in CJ_CONCELHOS:
        for cat in CJ_CATS:
            for pagina in range(1, 11):
                url = f"https://www.custojusto.pt/lisboa/{conc}/imobiliario/{cat}" + (f"?o={pagina}" if pagina > 1 else "")
                st, html, _ = get(url)
                pausa()
                nd = next_data(html) if st == 200 else None
                li = (((nd or {}).get("props") or {}).get("pageProps") or {}).get("listItems") or []
                novos = [x for x in li if x.get("url") not in vistos]
                if not novos:
                    break
                for x in novos:
                    vistos.add(x.get("url"))
                    preco = x.get("price") or 0
                    if not (PRECO_MIN <= preco <= PRECO_MAX):
                        continue
                    ln = x.get("locationNames") or {}
                    zona = zona_texto(ln.get("parish"), ln.get("county"), x.get("title"))
                    if not zona or EXCLUIR_LOCAL.search((ln.get("parish") or "") + " " + (x.get("title") or "")):
                        continue
                    u = "https://www.custojusto.pt" + x["url"]
                    st2, h2, f2 = get(u)
                    pausa()
                    ad = (((next_data(h2) or {}).get("props") or {}).get("pageProps") or {}).get("adData") if st2 == 200 else None
                    if not ad:
                        continue
                    p = ad.get("params") or {}
                    try:
                        area = float(p.get("size")) if p.get("size") else None
                    except ValueError:
                        area = None
                    try:
                        ano = int(p.get("construction_year")) if p.get("construction_year") else None
                    except ValueError:
                        ano = None
                    tip = ((p.get("rooms") or {}).get("name")) if isinstance(p.get("rooms"), dict) else p.get("rooms")
                    d = analisar(ad.get("title"), ad.get("body"), float(preco), area, ano, tip)
                    d.update({
                        "zona": zona, "localizacao": ln.get("parish") or conc.capitalize(),
                        "noMercadoDesde": (ad.get("listTime") or x.get("listTime") or "")[:10] or None,
                        "atualizado": None, "url": u, "fonte": "CustoJusto",
                        "agencia": (ad.get("name") or "Profissional") if ad.get("companyAd") else "Particular",
                        "chave": "CJ-" + str(ad.get("listID") or x.get("listID")),
                    })
                    if valido(d):
                        out.append(d)
    print(f"CustoJusto: {len(out)} anúncios válidos")
    return out


# ---------------------------------------------------------------- Casa Sapo (limita pedidos: ritmo lento)
SAPO_LOCAIS = ["oeiras", "cascais", "sintra", "amadora"]
SAPO_TIPOS = [("apartamentos", "t2"), ("apartamentos", "t3"), ("moradias", "t2"), ("moradias", "t3")]


def casasapo():
    out = []
    for loc in SAPO_LOCAIS:
        for tipo, tip in SAPO_TIPOS:
            url = f"https://casa.sapo.pt/comprar-{tipo}/{tip}/{loc}/"
            st, html, _ = get(url, tentativas=1)
            if st == 429:
                print("  Casa Sapo limitou os pedidos; fica para a próxima pesquisa.")
                print(f"Casa Sapo: {len(out)} anúncios válidos")
                return out
            time.sleep(20)
            if st != 200:
                continue
            for bloco in html.split('class="property-info-content"')[1:]:
                m = re.search(r'l=(https://casa\.sapo\.pt/comprar-[^"#?&]+\.html)', H.unescape(bloco))
                if not m:
                    continue
                txt = lambda cls: H.unescape(re.sub(r"<[^>]+>", " ", (re.search(rf'class="{cls}"[^>]*>(.*?)</div>', bloco, re.S) or [None, ""])[1])).strip()
                preco_txt = txt("property-price-value")
                try:
                    preco = float(re.sub(r"[^\d]", "", preco_txt)) if preco_txt else None
                except ValueError:
                    preco = None
                feats = txt("property-features-text")
                ma = re.search(r"(\d+(?:[.,]\d+)?)\s*m", feats)
                area = float(ma.group(1).replace(",", ".")) if ma else None
                local = txt("property-location")
                desc = txt("property-description")
                agencia = (re.search(r'title="Veja todos os im[^"]*anunciante ([^"]+)"', H.unescape(bloco)) or [None, "Não indicado"])[1]
                d = analisar(txt("property-type"), desc, preco, area, None, txt("property-type"))
                d.update({
                    "zona": zona_texto(local) if not EXCLUIR_LOCAL.search(local) else None,
                    "localizacao": local.split(",")[0], "noMercadoDesde": None, "atualizado": None,
                    "url": m.group(1), "fonte": "Casa Sapo", "agencia": agencia,
                    "chave": "SAPO-" + ((re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.html", m.group(1)) or [None, m.group(1)[-45:-5]])[1]),
                })
                d["notas"] = (d["notas"] + " Casa Sapo: dados do resumo do anúncio; confirmar casas de banho e garagem na ficha.").strip()
                if valido(d):
                    out.append(d)
    print(f"Casa Sapo: {len(out)} anúncios válidos")
    return out


# RE/MAX: o site carrega as casas da sua própria API (a mesma que a página usa no browser)
REMAX_REGIOES = {"Oeiras": 541, "Cascais": 536, "Sintra": 542, "Amadora": 532, "Lisboa": 537}
REMAX_TIPOS = "1,3,11"   # apartamento, duplex, moradia
REMAX_H = {"Content-Type": "application/json", "Accept": "application/json", "Origin": "https://remax.pt",
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def remax_api(caminho, corpo=None):
    for tentativa in range(3):
        try:
            req = urllib.request.Request("https://remax.pt/api/" + caminho, data=json.dumps(corpo).encode() if corpo else None, headers=REMAX_H)
            with urllib.request.urlopen(req, timeout=40) as x:
                return json.loads(x.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
        time.sleep(5 * (tentativa + 1))
    return None


def remax_montar(x, det, nome, locs, preco, quartos):
    """Monta o anúncio RE/MAX no formato do radar (x = linha da pesquisa, det = ficha)."""
    desc = next((y.get("description") for y in (det.get("descriptions") or []) if y.get("languageID") == 9 or y.get("languageCode") == "PT"), "") or ""
    tipo = {1: "Apartamento", 3: "Duplex", 11: "Moradia", 21: "Terreno", 13: "Quinta", 24: "Habitação"}.get(x.get("listingTypeID"), "")
    titulo = f"{tipo} T{quartos} em {x.get('localZone') or x.get('regionName3') or nome}".strip()
    area = x.get("livingArea") or x.get("totalArea")
    a = analisar(titulo, desc, float(preco), area, x.get("constructionYear"), f"T{quartos}", quartos)
    a["tipologia"] = ("Moradia " if x.get("listingTypeID") == 11 else "") + f"T{quartos}"
    if a["garagem"].startswith("À parte") or a["garagem"] == "Não":
        pass   # a descrição diz que a garagem se compra à parte (ou que não há): prevalece sobre a ficha
    elif x.get("garage") or (x.get("garageSpots") or 0) > 0:
        a["garagem"] = "Sim"
        a["garagemFrase"] = a.get("garagemFrase") or f"Garagem assinalada nas características do anúncio RE/MAX ({x.get('garageSpots') or 1} lugar(es))"
    elif x.get("parking") and a["garagem"] in ("Não indicado",):
        a["garagem"], a["garagemFrase"] = "Sim", "Estacionamento assinalado nas características do anúncio RE/MAX"
    if x.get("numberOfBathrooms"):
        a["wc"] = x["numberOfBathrooms"]
    if x.get("elevator"):
        a["elevador"] = "Sim"
    if set(x.get("listingAttributesIds") or []) & {5, 8, 9}:
        a["varanda"] = "Sim"
    a.update({
        "zona": zona_de([l for l in locs if l], titulo + " " + desc),
        "localizacao": ", ".join(v for v in (x.get("localZone"), x.get("regionName2")) if v),
        "noMercadoDesde": (x.get("publishDate") or x.get("contractDate") or "")[:10] or None,
        "atualizado": (x.get("modified") or "")[:10] or None,
        "url": f"https://remax.pt/pt/imoveis/{x.get('descriptionTags') or 'imovel'}/{x['listingTitle']}",
        "fonte": "RE/MAX", "agencia": x.get("officeName") or "RE/MAX",
        "chave": "REMAX-" + x["listingTitle"],
    })
    return a


def remax():
    out = []
    for nome, rid in REMAX_REGIOES.items():
        filtros = [{"field": "businessTypeID", "operationType": "int", "operator": "=", "value": "1"},
                   {"field": "listingClassID", "operationType": "int", "operator": "=", "value": "1"},
                   {"field": "listingTypeID", "operationType": "multiple", "operator": "=", "value": REMAX_TIPOS},
                   {"field": "Region2ID", "operationType": "string", "operator": "=", "value": str(rid)}]
        for pagina in range(1, 60):
            d = remax_api("Listing/PaginatedMultiMatchSearch", {"filters": filtros, "pageNumber": pagina, "pageSize": 100, "sort": ["-PublishDate"], "searchValue": ""})
            pausa()
            res = (d or {}).get("results") or []
            if not res:
                if d is None:
                    print(f"  RE/MAX falhou: {nome} página {pagina}")
                break
            for x in res:
                preco = x.get("listingPrice") or 0
                quartos = x.get("numberOfBedrooms")
                if not (PRECO_MIN <= preco <= PRECO_MAX) or (quartos or 0) < 2 or x.get("privatePrice"):
                    continue
                locs = ["Lisboa", x.get("regionName2") or nome, x.get("regionName3") or "", x.get("localZone") or ""]
                talvez = (x.get("regionName3") or "") in ("Belém", "Lumiar", "Carnide", "Marvila", "Parque das Nações", "Campolide",
                                                         "Benfica", "Alcântara", "Ajuda", "Cacém e São Marcos")
                if zona_de([l for l in locs if l]) is None and not talvez:
                    continue   # fora das zonas (sem gastar um pedido com a ficha)
                det = remax_api("Listing/GetListingByTitle?listingPublicId=" + x["listingTitle"]) or x
                pausa()
                a = remax_montar(x, det, nome, locs, preco, quartos)
                if valido(a):
                    out.append(a)
            if not (d or {}).get("hasNextPage"):
                break
    print(f"RE/MAX: {len(out)} anúncios válidos")
    return out


# iad Portugal: as páginas trazem os dados em __NUXT_DATA__ (formato "devalue" do Nuxt)
def devalue(arr):
    """Reconstrói o objeto a partir do formato achatado do Nuxt (lista em que os valores apontam para índices)."""
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


def iad_dados(html):
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html or "", re.S)
    if not m:
        return []
    d = devalue(json.loads(m.group(1)))
    return [q["state"]["data"] for q in ((d.get("data") or {}).get("vue-query-state") or {}).get("queries", []) if (q.get("state") or {}).get("data")]


IAD_CONCELHOS = {"oeiras-1110": "Oeiras", "cascais-1105": "Cascais", "sintra-1111": "Sintra", "amadora-1115": "Amadora", "lisboa-1106": "Lisboa"}


def iad():
    out = []
    for slug, conc in IAD_CONCELHOS.items():
        for pagina in range(1, 40):
            st, html, _ = get(f"https://www.iadportugal.pt/anuncios/{slug}/venda" + (f"?page={pagina}" if pagina > 1 else ""))
            pausa()
            lista = next((q for q in iad_dados(html) if isinstance(q, dict) and "items" in q), None) if st == 200 else None
            itens = (lista or {}).get("items") or []
            if not itens:
                break
            for x in itens:
                preco = ((x.get("price") or {}).get("main")) or 0
                quartos = next((r.get("value") for r in (x.get("rooms") or []) if r.get("type") == "bedrooms"), None)
                if not (PRECO_MIN <= preco <= PRECO_MAX) or (quartos or 0) < 2 or x.get("propertyType") not in ("apartment", "house"):
                    continue
                place = (x.get("location") or {}).get("place") or ""
                pre_zona = zona_texto(place, conc if conc != "Lisboa" else "", x.get("title"), x.get("description"))
                if not pre_zona:
                    continue
                ref = x["propertyListingRef"]
                url = f"https://www.iadportugal.pt/anuncio/{(x.get('slugs') or {}).get('pt') or 'imovel'}/r{ref}"
                st2, h2, _ = get(url)
                pausa()
                det = next((q for q in iad_dados(h2) if isinstance(q, dict) and str(q.get("propertyListingRef")) == str(ref)), None) if st2 == 200 else None
                det = det or x
                desc = det.get("description") or x.get("description") or ""
                if isinstance(desc, dict):
                    desc = desc.get("pt") or next(iter(desc.values()), "")
                extras = json.dumps(det.get("features") or det.get("characteristics") or [], ensure_ascii=False)
                area = det.get("mainSurface") or next((s_.get("value") for s_ in (x.get("surfaceList") or [])), None)
                tipo = "Moradia " if x.get("propertyType") == "house" else ""
                titulo = x.get("title") or f"{tipo}T{quartos} em {place}"
                a = analisar(titulo, desc, float(preco), area, None, f"T{quartos}", quartos)
                a["tipologia"] = f"{tipo}T{quartos}"
                if a["garagem"] == "Não indicado" and re.search(r"garag|parking|parqueamento|estacionamento", extras, re.I):
                    a["garagem"], a["garagemFrase"] = "Sim", "Garagem/estacionamento assinalado nas características do anúncio iad"
                a.update({
                    "zona": zona_texto(place, conc if conc != "Lisboa" else "", titulo, desc) or pre_zona,
                    "localizacao": ", ".join(v for v in (place, conc) if v),
                    "noMercadoDesde": det.get("firstPublishDate"), "atualizado": None, "url": url,
                    "fonte": "iad", "agencia": "iad Portugal" + (f" ({(x.get('agent') or {}).get('fullName')})" if (x.get("agent") or {}).get("fullName") else ""),
                    "chave": "IAD-" + str(ref),
                })
                if valido(a):
                    out.append(a)
            if pagina * int((lista or {}).get("itemsPerPage") or 30) >= int((lista or {}).get("totalItems") or 0):
                break
    print(f"iad: {len(out)} anúncios válidos")
    return out


def recolher():
    todos = []
    for fn in (olx, custojusto, casasapo, remax, iad):
        try:
            todos += fn()
        except Exception as e:  # um portal com problemas não pode estragar a pesquisa
            print(f"Aviso: {fn.__name__} falhou: {e}")
    return todos
