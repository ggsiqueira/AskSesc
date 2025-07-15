import os
import json
from extraction.extrair_paginas import extrair_paginas
from extraction.extrair_eventos import extrair_eventos, filtrar_eventos


if __name__ == "__main__":
    pdf_path = "data/Maio2025.pdf"
    
    paginas = extrair_paginas(pdf_path)
    with open('./output/parsed/paginas.json', 'w') as fp:
        json.dump(paginas, fp, indent=2, ensure_ascii=False)
    
    eventos = extrair_eventos(paginas)
    eventos_validos = filtrar_eventos(eventos)
    eventos_dict =  [e.to_dict() for e in eventos_validos]
    with open('./output/parsed/eventos.json', 'w') as fp:
        json.dump(eventos_dict, fp, indent=2, ensure_ascii=False)
    
