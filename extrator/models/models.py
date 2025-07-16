from typing import List
from pydantic import BaseModel

class EventoHolder(BaseModel):
    titulo: str = ""
    categoria: str = ""
    subcategoria: str = ""
    unidade: str = ""
    descricao: str = ""
    rodape: str = ""