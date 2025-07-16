import json
from tqdm import tqdm
from enum import Enum, auto
from typing import List, Dict
from models.models import EventoHolder
from .extrair_paginas import extrair_paginas


class ParserState(Enum):
    EXPECT_TITLE = auto(),
    COLECT_TITLE = auto() ,
    COLECT_BODY = auto() ,
    COLECT_FOOTER = auto() ,


def extrair_eventos(paginas: List[Dict], save_path : str = "") -> List[EventoHolder]:
    eventos = []
    evento_atual = None
    estado = ParserState.EXPECT_TITLE
    unidade_atual = ""
    categoria = []
    for pagina in tqdm(paginas):
        # Determina categoria da página

        if categoria:
            cat_ant = categoria
            categoria = [pagina[f"header_{i}"]["text"] if pagina[f"header_{i}"] else None for i in [1, 2]]
            for c1 in cat_ant:
                for c2 in categoria:
                    if c1 and c2 and (c1 != c2):
                        unidade_atual = ""
                        if evento_atual:
                            eventos.append(evento_atual)
                            evento_atual = None
        else:
            categoria = [pagina[f"header_{i}"]["text"] if pagina[f"header_{i}"] else None for i in [1, 2]]
            
        blocos_ordenados = pagina["blocos"]
        
        for bloco in blocos_ordenados:
            p = bloco["page"]
            
            if bloco.get("type") == "location":
                estado = ParserState.EXPECT_TITLE
                if evento_atual:
                    eventos.append(evento_atual)
                    evento_atual = None

                unidade_atual = "\n".join(linha["text"] for linha in bloco["linhas"])
                continue
            
            elif bloco.get("type") != "event":
                continue
            
            for linha in bloco["linhas"]:
                if linha["type"] == "title":
                    if estado == ParserState.COLECT_TITLE and evento_atual:
                        evento_atual.titulo += f" {linha['text']}"
                    elif estado == ParserState.COLECT_FOOTER or estado == ParserState.COLECT_BODY:
                        if evento_atual:
                            eventos.append(evento_atual)
                        evento_atual = None
                        estado = ParserState.COLECT_TITLE
                    
                    if not evento_atual:
                        evento_atual = EventoHolder()
                        evento_atual.unidade = unidade_atual
                        evento_atual.categoria = categoria[p] if categoria[p] else categoria[p-1]
                        evento_atual.titulo += f" {linha['text']}"
                        estado = ParserState.COLECT_TITLE

                elif linha["type"] == "category" and evento_atual:
                    evento_atual.subcategoria = evento_atual.categoria
                    evento_atual.categoria = linha["text"]
                    estado = ParserState.COLECT_BODY

                elif linha["type"] == "body" and evento_atual:
                    evento_atual.descricao += f" {linha['text']}"
                    estado = ParserState.COLECT_BODY

                elif linha["type"] == "footer" and evento_atual:
                    evento_atual.rodape += f" {linha['text']}"
                    estado = ParserState.COLECT_FOOTER
                
                    
    # Adiciona o último evento se existir
    if evento_atual:
        eventos.append(evento_atual)
    
    eventos = filtrar_eventos(eventos)
    if save_path:
        eventos_dict = [e.dict() for e in eventos]
        with open(save_path, 'w') as fp:
            json.dump(eventos_dict, fp, indent=2, ensure_ascii=False)

    return eventos

def filtrar_eventos(eventos):
    evento_valido = lambda e : e.titulo and e.descricao and e.rodape and e.categoria 
    return list(filter(evento_valido, eventos))

def processar_eventos(pdf_path: str) -> List[Dict]:
    paginas = extrair_paginas(pdf_path)
    eventos = extrair_eventos(paginas)
    eventos_validos = filtrar_eventos(eventos)
    eventos_dict =  [e.to_dict() for e in eventos_validos]
    with open('eventos.json', 'w') as fp:
        json.dump(eventos_dict, fp, indent=2, ensure_ascii=False)
    return eventos_dict

if __name__ == "__main__":
    processar_eventos("./content/Maio2025.pdf")