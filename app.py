from flask import Flask, render_template, request, send_from_directory
import os
import requests
from utils.extract_pdf import extraer_caso_estudio
from docx import Document
import json
import markdown  # nuevo

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULTADOS_FOLDER = 'resultados/generados'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTADOS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

GEMINI_API_KEY = 'AIzaSyD5sdmxBouRcNPmDFU90Z2zDNYu6u2axfE'
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
def guardar_en_docx(texto, ruta):
    doc = Document()
    for parrafo in texto.split("\n\n"):
        doc.add_paragraph(parrafo.strip())
    doc.save(ruta)

def evaluar_caso_con_ia(caso_ia):
    prompt_evaluador = (
        "Eres un auditor experto en calidad bajo la norma ISO 9001. "
        "Evalúa del 1 al 10 los siguientes criterios del siguiente caso de estudio:\n\n"
        "1. Claridad\n2. Aplicación de ISO 9001\n3. Profundidad técnica\n4. Viabilidad práctica\n\n"
        f"Texto a evaluar:\n\n{caso_ia}\n\n"
        "Devuélvelo en formato JSON así:\n"
        '{"claridad": 8, "iso": 9, "profundidad": 7, "viabilidad": 8}'
    )

    payload = {"contents": [{"parts": [{"text": prompt_evaluador}]}]}
    response = requests.post(GEMINI_API_URL, json=payload)
    if response.status_code == 200:
        try:
            data = response.json()
            respuesta = data['candidates'][0]['content']['parts'][0]['text']
            evaluacion = json.loads(respuesta)
            return evaluacion
        except:
            return {"claridad": 7, "iso": 7, "profundidad": 7, "viabilidad": 7}
    return {"claridad": 5, "iso": 5, "profundidad": 5, "viabilidad": 5}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cargar', methods=['GET', 'POST'])
def cargar():
    if request.method == 'POST':
        archivo = request.files['pdf']
        grupo_resultado = request.form['grupo']

        if archivo:
            ruta_pdf = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
            archivo.save(ruta_pdf)

            caso_usuario = extraer_caso_estudio(ruta_pdf)
            caso_usuario = caso_usuario.replace('<br>', '\n')  # limpia saltos de línea planos

            prompt_ia = (
                "Eres un experto en ISO 9001. Reescribe este caso de estudio "
                "aplicando principios de calidad, mejora continua, enfoque al cliente y gestión de riesgos:\n\n"
                f"{caso_usuario}"
            )

            payload = {"contents": [{"parts": [{"text": prompt_ia}]}]}
            response = requests.post(GEMINI_API_URL, json=payload)
            caso_ia_md = response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else "Error al generar respuesta."
            caso_ia = markdown.markdown(caso_ia_md)

            evaluacion = evaluar_caso_con_ia(caso_ia_md)

            # Guardar documentos en Word
            guardar_en_docx(caso_usuario, os.path.join(RESULTADOS_FOLDER, 'caso_usuario.docx'))
            guardar_en_docx(caso_ia_md, os.path.join(RESULTADOS_FOLDER, 'caso_ia.docx'))

            return render_template('comparativa.html',
                                   caso_usuario=caso_usuario,
                                   caso_ia=caso_ia,
                                   grupo=grupo_resultado,
                                   evaluacion=evaluacion)

    return render_template('cargar_pdf.html')

@app.route('/descargar/<archivo>')
def descargar(archivo):
    return send_from_directory(RESULTADOS_FOLDER, archivo, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)