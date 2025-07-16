import json
import pdfplumber
from collections import defaultdict
from .utils.unidades_sesc import unidades
from .utils.visualizacao import desenhar_layout

LINHAS_Y = [55, 615]

PAGE_1_COLS = [120 * i + 45 for i in range(4)]
PAGE_2_COLS = [120 * i + 495 for i in range(4)]


PAGE_1_COLS_EXP = [145 * i + 115 for i in range(3)]
PAGE_2_COLS_EXP = [145 * i + 490 for i in range(3)]


def agrupar_linhas_por_letras(chars, tolerancia_y=2, dx_word=1, max_dx=10):

    # 1. Agrupa caracteres por altura similar (com tolerância de Y)
    buckets = defaultdict(list)
    for ch in chars:
        y_key = round(ch["top"] / tolerancia_y)
        buckets[y_key].append(ch)

    linhas = []

    for y_key in sorted(buckets):
        bucket = buckets[y_key]
        
        unique_bucket = {tuple(sorted(b.items())) for b in bucket}
        bucket = [dict(t) for t in unique_bucket]
        linha_chars = sorted(bucket, key=lambda c: c["x0"])

        grupo_atual = [linha_chars[0]]
        for i in range(1, len(linha_chars)):
            anterior = linha_chars[i - 1]
            atual = linha_chars[i]
            dx = atual["x0"] - anterior["x1"]

            if dx <= dx_word:
                grupo_atual.append(atual)
            elif dx < max_dx:
                dummy = {
                    "text" : " ",
                    "x0": atual["x0"],
                    "top": atual["top"],
                    "x1": atual["x1"],
                    "bottom": atual["bottom"],
                    "fontname" : atual["fontname"]
                }
                grupo_atual.append(dummy)
                grupo_atual.append(atual)
            else:
                # Fecha linha atual
                if grupo_atual:
                    linha = construir_linha(grupo_atual)
                    linhas.append(linha)
                grupo_atual = [atual]

        if grupo_atual:
            linha = construir_linha(grupo_atual)
            linhas.append(linha)

    return linhas

def is_footer(linha):
    keywords = ["R$", "GRÁTIS", "DIAS", "LOCAL", "TEATRO", "ACESSIBILIDADE", "LIBRAS"]
    weekdays = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"]

    if "SEMIBOLD" not in linha["font"].upper():
        return False
    
    if round(linha["size"], 2) != 8.5:
        if linha["text"] in "AL A10 A12 A14 A16 A18":
            linha["type"] = "footer"
            return True
        else:
            return False

    for word in keywords + weekdays:
        if word in linha["text"].upper() :
            linha["type"] = "footer"
            return True
    
    return False
    
def is_body(linha):
    if "REGULAR" in linha["font"].upper() and linha["size"] ==8.5:
        linha["type"] = "body"
        return True

    return False

def is_title(linha):
    if linha["bold"] and linha["size"] == 10:
        linha["type"] = "title"
        return True
    return False

def is_type(linha):
    if linha["bold"] and linha["size"] == 7:
        linha["type"] = "category"
        return True
    return False
    

def is_event_line(linha):
    is_event = is_body(linha) or is_title(linha) or is_footer(linha) or is_type(linha)
    return is_event

def is_event_block(bloco):
    lines_event = sum(1 for x in bloco["linhas"] if is_event_line(x))
    event = lines_event >= (len(bloco["linhas"]) / 2)
    
    if event:
        for linha in bloco["linhas"]:
            if not linha.get("type"):
                if linha["bold"]:

                    linha["type"] = "footer"
                else:
                    linha["type"] = "body"

        bloco["type"] = "event"
        return True
    
    return False

def get_header(linhas):
    is_header_1 = lambda e : e["top"] <= LINHAS_Y[0] and e["x0"] <= PAGE_1_COLS[-1]
    is_header_2 = lambda e : e["top"] <= LINHAS_Y[0] and e["x0"] >= PAGE_2_COLS[0]
    
    header_1 = list(filter(is_header_1, linhas))
    header_2 = list(filter(is_header_2, linhas))

    header_1 = header_1[0] if header_1 else None
    header_2 = header_2[0] if header_2 else None

    return header_1, header_2

def agrupar_blocos_por_linhas(page, linhas, P1_COLS=PAGE_1_COLS, P2_COLS=PAGE_2_COLS, dyt=10):
    blocos = []

    lx1 = list(zip(P1_COLS, P1_COLS[1:]))
    lx2 = list(zip(P2_COLS, P2_COLS[1:]))
    imagens = page.images

    linhas_layout = list(filter(lambda seq : in_limits(seq, imagens), linhas))
    for c1, c2 in lx1 + lx2:
        linhas_layout = list(filter(lambda x : x["x0"] >= c1 and x["x1"] <= c2, linhas_layout))
        linhas_layout = list(filter(lambda x : x["x0"] >= c1 and x["x1"] <= c2, linhas_layout))
        linhas_layout = sorted(linhas_layout, key=lambda l : l["top"])
        
        if not linhas_layout:
            continue
        linha_ant = linhas_layout[0]
        bloco_atual = []
        for linha_att in linhas_layout[1:]:
            if not bloco_atual:
                bloco_atual.append(linha_ant)
            
            dy = abs(linha_ant["bottom"] - linha_att["top"])
            if dy < dyt:
                bloco_atual.append(linha_att)
            else:
                blocos.append(criar_bboxes_bloco(bloco_atual))
                bloco_atual = []
            
            linha_ant = linha_att
        
        if bloco_atual:
            blocos.append(criar_bboxes_bloco(bloco_atual))
    return blocos

def criar_bboxes_bloco(bloco):
    x0 = min(l["x0"] for l in bloco)
    top = min(l["top"] for l in bloco)
    x1 = max(l["x1"] for l in bloco)
    bottom = max(l["bottom"] for l in bloco)

    return {
        "linhas": bloco,
        "x0": x0,
        "top": top,
        "x1": x1,
        "bottom": bottom,
    }
        

def construir_linha(chars):
    return {
        "text": "".join(c["text"] for c in chars),
        "font" : chars[0].get("fontname", ""),
        "size" : round(chars[0].get("size", ""), 2),
        "bold": all(is_bold(c) for c in chars),
        "x0": min(c["x0"] for c in chars),
        "x1": max(c["x1"] for c in chars),
        "top": min(c["top"] for c in chars),
        "bottom": max(c["bottom"] for c in chars),
    }

def is_location(bloco):
    titulo = " ".join([linha["text"] for linha in bloco["linhas"]])
    for unidade in unidades:
        if unidade in titulo:
            bloco["type"] = "location"
            return True
    return False


def is_bold(token):
    font = token.get("fontname", "").lower()
    return "bold" in font 

def in_limits(elem, zone_elems):
    if (elem["x0"] <= PAGE_1_COLS[0] or 
       (elem["x1"] >= PAGE_1_COLS[-1] and elem["x0"] < PAGE_2_COLS[0]) or
       (elem["x1"] >= PAGE_2_COLS[-1])):
        return False
    
    if elem["top"] <= LINHAS_Y[0] or elem["bottom"] >= LINHAS_Y[1]:
        return False
    
    for ze in zone_elems:
        if (elem["x0"] >= ze["x0"] and
            elem["x1"] <= ze["x1"] and
            elem["top"] >= ze["top"] and
            elem["bottom"] <= ze["bottom"]):
                return False
    
    return True


def ordernar_blocos(blocos, del1, del2):
    in_col = lambda x, c1, c2 : x["x0"] >= c1 and x["x1"]  <= c2
    lx1 = list(zip(del1, del1[1:]))
    lx2 = list(zip(del2, del2[1:]))
    
    pages = [lx1, lx2]
    blocos_ord = []
    
    for page, limits in enumerate(pages):
        for c1, c2 in limits:
            blocos_in_col = list(filter(lambda b : in_col(b, c1, c2), blocos))
            for bloco in blocos_in_col: bloco["page"] = page
            blocos_in_col = sorted(blocos_in_col, key=lambda c: c["top"])
            blocos_ord.extend(blocos_in_col)

    return blocos_ord


def extrair_pagina(page):
    chars = page.extract_words(extra_attrs=["x0", "x1", "top", "bottom", "fontname", "size"])
    
    linhas = agrupar_linhas_por_letras(chars)
    header_1, header_2 = get_header(linhas)
    
    if (header_1 and "EXPOSIÇÕES" in header_1["text"]) or (header_2 and "EXPOSIÇÕES" in header_2["text"]):
        cols1, cols2 = PAGE_1_COLS_EXP, PAGE_2_COLS_EXP
        blocos = agrupar_blocos_por_linhas(page, linhas, P1_COLS=cols1, P2_COLS=cols2)    
    else:            
        cols1, cols2 = PAGE_1_COLS, PAGE_2_COLS
        blocos = agrupar_blocos_por_linhas(page, linhas)
    
    blocos_evento = list(filter(is_event_block, blocos))
    blocos_location = list(filter(is_location, blocos))
    
    
    blocos = blocos_evento + blocos_location
    blocos = ordernar_blocos(blocos, cols1, cols2)
    
    return blocos, header_1, header_2, cols1, cols2

def is_information_line(linha):
    """
    Returns True if the line is INFORMATION: size 8.5 and font family is either Bold or Medium.
    """
    font = linha["font"].upper()
    return (
        linha["size"] == 8.5 and (
            "BOLD" in font or "MEDIUM" in font
        )
    )


def is_title_line(linha):
    """
    Returns True if the line is a TITLE: BOLD and font size 10.
    """
    font = linha["font"].upper()
    return "BOLD" in font and linha["size"] == 10


def is_normal_text_line(linha):
    """
    Returns True if the line is NORMAL TEXT: size 8.5 and font is regular (not bold, not medium).
    """
    font = linha["font"].upper()
    return linha["size"] == 8.5 and ("REGULAR" in font or ("BOLD" not in font and "MEDIUM" not in font))

def extrair_paginas(path_pdf : str, skip : int=2, draw : bool = False, save_path=""):
    pages = []
    with pdfplumber.open(path_pdf) as pdf:
        for i, page in enumerate(pdf.pages[skip:]):
           blocos, header_1, header_2, del1, del2 = extrair_pagina(page)
           pages.append({
                "header_1" : header_1,
                "header_2" : header_2,
                "blocos" : blocos,
                "del1" : del1,
                "del2" : del2

           })
           
           if draw: desenhar_layout(page, header_1, header_2, blocos, del1, del2, LINHAS_Y, salvar_como=f"./output/layout/preview_{(i+skip):02d}.png")
    
    if save_path:
        with open(save_path, 'w') as fp:
            json.dump(pages, fp, indent=2, ensure_ascii=False)

    return pages

if __name__ == "__main__":
    path_pdf = "./content/Maio2025.pdf"
    pages = extrair_paginas(path_pdf)