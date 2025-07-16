import logging
from extrator.extrair_paginas import extrair_paginas
from extrator.extrair_eventos import extrair_eventos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    pdf_path = "data/Maio2025.pdf"
    
    logger.info("📂 Processando PDF...")
    paginas = extrair_paginas(pdf_path, save_path='./output/parsed/paginas.json')

    logger.info("💃 Extraindo informação de eventos...")
    eventos = extrair_eventos(paginas, save_path='./output/parsed/eventos.json')