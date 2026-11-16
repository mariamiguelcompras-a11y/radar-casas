"""Outros portais além do Imovirtual: OLX, CustoJusto e Casa Sapo.

Cada função devolve anúncios no mesmo formato de data/imoveis.json (sem os campos de controlo,
que o scrape.py acrescenta). Os sites que bloqueiam são saltados sem estragar o resto da pesquisa.
"""
import html as H
import json
import re
import time
from datetime import date, datetime, timedelta

from scrape import (EXCLUIR_TITULO, PRECO_MAX, PRECO_MIN, classificar_garagem, get, next_data, pausa)

HOJE = date.today().isoformat()

# Palavras da localização -> zona (a ordem importa: o mais específico primeiro)
ZONAS = [
    ("Alfragide", r"alfragide"),
    ("Oeiras", r"linda-a-velha|linda a velha"),
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
              "parede", "sao-domingos-de-rana", "alcabideche", "alfragide", "massama", "monte-abraao", "queluz"]
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
CJ_CONCELHOS = ["oeiras", "cascais", "sintra", "amadora"]
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


def recolher():
    todos = []
    for fn in (olx, custojusto, casasapo):
        try:
            todos += fn()
        except Exception as e:  # um portal com problemas não pode estragar a pesquisa
            print(f"Aviso: {fn.__name__} falhou: {e}")
    return todos
