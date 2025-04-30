import pdfplumber

def extraer_caso_estudio(ruta_pdf):
    texto_completo = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            contenido = pagina.extract_text()
            if contenido:
                texto_completo += contenido + "\n\n"
    return texto_completo.strip()
