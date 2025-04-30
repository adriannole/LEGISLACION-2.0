from flask import Flask, render_template, request, send_from_directory
import os
import requests
from docx import Document
import json
import markdown
from utils.extract_pdf import extraer_caso_estudio_md

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

def evaluar_caso_con_ia(caso_texto):
    prompt_evaluador = (
        "Eres un auditor experto en calidad bajo la norma ISO 9001. "
        "Evalúa del 1 al 10 los siguientes criterios del siguiente caso de estudio:\n\n"
        "1. Claridad\n2. Aplicación de ISO 9001\n3. Profundidad técnica\n4. Viabilidad práctica\n\n"
        f"Texto a evaluar:\n\n{caso_texto}\n\n"
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

def generar_comparacion_tabla_dinamica(eval_usuario, eval_ia):
    def mejor(valor1, valor2):
        if valor1 > valor2: return "🔵 Usuario"
        elif valor1 < valor2: return "🔴 IA"
        else: return "⚪ Empate"

    return f"""
    <table border="1" style="width:100%; border-collapse: collapse; margin-top: 20px;">
      <tr><th>Aspecto</th><th>Usuario</th><th>IA</th><th>Mejor Evaluado</th></tr>
      <tr><td>Claridad</td><td>{eval_usuario['claridad']}</td><td>{eval_ia['claridad']}</td><td>{mejor(eval_usuario['claridad'], eval_ia['claridad'])}</td></tr>
      <tr><td>Aplicación ISO</td><td>{eval_usuario['iso']}</td><td>{eval_ia['iso']}</td><td>{mejor(eval_usuario['iso'], eval_ia['iso'])}</td></tr>
      <tr><td>Profundidad Técnica</td><td>{eval_usuario['profundidad']}</td><td>{eval_ia['profundidad']}</td><td>{mejor(eval_usuario['profundidad'], eval_ia['profundidad'])}</td></tr>
      <tr><td>Viabilidad</td><td>{eval_usuario['viabilidad']}</td><td>{eval_ia['viabilidad']}</td><td>{mejor(eval_usuario['viabilidad'], eval_ia['viabilidad'])}</td></tr>
    </table>
    """

def generar_conclusion_automatica(eval_usuario, eval_ia):
    score_usuario = sum(eval_usuario.values())
    score_ia = sum(eval_ia.values())

    if score_usuario > score_ia:
        ganador = "🔵 El caso del usuario presenta una mayor calidad general."
    elif score_usuario < score_ia:
        ganador = "🔴 La versión generada por IA es superior en términos técnicos y estructurales."
    else:
        ganador = "⚪ Ambos casos tienen un nivel equivalente de calidad."

    return (
        f"<p style='text-align: justify; margin-top: 15px;'>"
        f"{ganador} Se sugiere revisar los criterios más bajos para mejoras futuras. "
        f"Esta conclusión está basada en una evaluación IA bajo criterios de la norma ISO 9001.</p>"
    )

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

            # Texto original del usuario en Markdown (texto plano)
            caso_usuario_md = extraer_caso_estudio_md(ruta_pdf)
            # Para mostrarlo renderizado
            caso_usuario = markdown.markdown(caso_usuario_md)

            # Reescritura por IA (usa texto plano original del usuario, no el HTML)
            prompt_ia = (
                "Eres un experto en ISO 9001. Reescribe este caso de estudio "
                "aplicando principios de calidad, mejora continua, enfoque al cliente y gestión de riesgos:\n\n"
                f"{caso_usuario_md}"
            )
            payload = {"contents": [{"parts": [{"text": prompt_ia}]}]}
            response = requests.post(GEMINI_API_URL, json=payload)
            caso_ia_md = response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else "Error al generar respuesta."
            caso_ia = markdown.markdown(caso_ia_md)

            # Evaluación dinámica de ambos (usa los textos planos para evaluación, no el HTML)
            evaluacion_usuario = evaluar_caso_con_ia(caso_usuario_md)
            evaluacion_ia = evaluar_caso_con_ia(caso_ia_md)

            # Guardar ambos en DOCX
            guardar_en_docx(caso_usuario_md, os.path.join(RESULTADOS_FOLDER, 'caso_usuario.docx'))
            guardar_en_docx(caso_ia_md, os.path.join(RESULTADOS_FOLDER, 'caso_ia.docx'))

            return render_template('comparativa.html',
                caso_usuario=caso_usuario,
                caso_ia=caso_ia,
                grupo=grupo_resultado,
                evaluacion_usuario=evaluacion_usuario,
                evaluacion_ia=evaluacion_ia,
                comparacion_tabla=generar_comparacion_tabla_dinamica(evaluacion_usuario, evaluacion_ia),
                conclusion=generar_conclusion_automatica(evaluacion_usuario, evaluacion_ia)
            )

    return render_template('cargar_pdf.html')

@app.route('/descargar/<archivo>')
def descargar(archivo):
    return send_from_directory(RESULTADOS_FOLDER, archivo, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Usa el puerto definido por Railway o 5000 por defecto
    app.run(debug=True, host='0.0.0.0', port=port)