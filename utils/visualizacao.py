from PIL import ImageDraw
import os

os.makedirs("output/layout", exist_ok=True)
def desenhar_colunas(im, draw, scx, P1_COLS, P2_COLS):
    COLS = P1_COLS + P2_COLS
    for x in COLS:
        x_scaled = int(x * scx)
        if x_scaled < im.original.width:  # Make sure line is within image bounds
            draw.line([(x_scaled, 0), (x_scaled, im.original.height)], fill="blue", width=3)
            print(f"Drew column line at x={x_scaled}")

def desenhar_linhas(im, draw, scy, LINHAS_Y):
    y_scaled_1 = int(LINHAS_Y[0] * scy)
    y_scaled_2 = int(LINHAS_Y[1] * scy)
    
    draw.line([(0, y_scaled_1), (im.original.width, y_scaled_1)], fill="purple", width=3)
    draw.line([(0, y_scaled_2), (im.original.width, y_scaled_2)], fill="purple", width=3)


def desenhar_bloco(bloco, draw, scx, scy, color="green"):
    if not bloco:
        return
        
    # Scale coordinates to image space
    x0 = int(bloco["x0"] * scx)
    y0 = int(bloco["top"] * scy)  # top in PDF = top in image
    x1 = int(bloco["x1"] * scx)
    y1 = int(bloco["bottom"] * scy)  # bottom in PDF = bottom in image

    draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

def desenhas_blocos(blocos, draw, scx, scy, color="green"):
    for bloco in blocos:
        desenhar_bloco(bloco, draw, scx, scy, color)

def desenhar_imagens(page, draw, scx, scy):
    imagens = page.images
    for img in imagens:
        x0 = int(img["x0"] * scx)
        y0 = int(img["top"] * scy)  # top in PDF = top in image
        x1 = int(img["x1"] * scx)
        y1 = int(img["bottom"] * scy)  # bottom in PDF = bottom in image

        draw.rectangle([x0, y0, x1, y1], outline="orange", width=3)

def desenhar_layout(page, header_1, header_2, blocos, cols1, cols2, linhas, salvar_como):
    im = page.to_image(resolution=150)
    img = im.original.copy()  # copia a imagem para editar
    draw = ImageDraw.Draw(img)
    
    scale_x = im.original.width / page.width
    scale_y = im.original.height / page.height
    
    blocos_evento = list(filter(lambda b: b["type"] == "event", blocos))
    blocos_location = list(filter(lambda b: b["type"] == "location", blocos))
    
    desenhar_colunas(im, draw, scale_x, P1_COLS=cols1, P2_COLS=cols2)
    desenhar_linhas(im, draw, scale_y, linhas)
    desenhar_bloco(header_1, draw, scale_x, scale_y, color="pink")
    desenhar_bloco(header_2, draw, scale_x, scale_y, color="pink")
    desenhas_blocos(blocos_evento, draw, scale_x, scale_y)
    desenhas_blocos(blocos_location, draw, scale_x, scale_y, color="red")
    desenhar_imagens(page, draw, scale_x, scale_y)
    
    img.save(salvar_como)
    print(f"Imagem salva como: {salvar_como}")
