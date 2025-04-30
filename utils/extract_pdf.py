import pdfplumber
import re

def extraer_caso_estudio(ruta_pdf):
    texto_completo = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            contenido = pagina.extract_text()
            if contenido:
                # Añadir doble salto para separar párrafos reales
                contenido = re.sub(r'(?<!\n)\n(?!\n)', ' ', contenido)  # Une líneas cortadas
                contenido = re.sub(r'\n{2,}', '\n\n', contenido)       # Asegura dobles saltos
                texto_completo += contenido + "\n\n"
    return texto_completo.strip()