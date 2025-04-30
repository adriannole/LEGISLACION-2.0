import pdfplumber
import re

def extraer_caso_estudio_md(ruta_pdf):
    md_texto = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            contenido = pagina.extract_text()
            if not contenido:
                continue

            # Une líneas partidas sin dobles saltos y conserva párrafos
            contenido = re.sub(r'(?<!\n)\n(?!\n)', ' ', contenido)
            bloques = re.split(r'\n{2,}', contenido)

            for bloque in bloques:
                bloque = bloque.strip()
                if not bloque:
                    continue
                if bloque.isupper() and len(bloque.split()) <= 8:
                    md_texto += f"## {bloque.title()}\n\n"
                else:
                    md_texto += f"{bloque}\n\n"
    return md_texto.strip()
