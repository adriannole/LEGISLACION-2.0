from flask import Flask, render_template, request, send_from_directory
import os
import requests
from docx import Document
import json
import markdown
from utils.extract_pdf import extraer_caso_estudio_md
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULTADOS_FOLDER = 'resultados/generados'
CACHE_FOLDER = 'cache'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTADOS_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

GEMINI_API_KEY = 'AIzaSyD5sdmxBouRcNPmDFU90Z2zDNYu6u2axfE'
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

def guardar_en_docx(texto, ruta):
    try:
        doc = Document()
        for parrafo in texto.split("\n\n"):
            if parrafo.strip():
                doc.add_paragraph(parrafo.strip())
        doc.save(ruta)
        return True
    except Exception as e:
        print(f"Error al guardar DOCX: {e}")
        return False

def evaluar_caso_con_ia(caso_texto):
    prompt_evaluador = (
        "Eres un auditor experto con 20 años de experiencia en calidad bajo la norma ISO 37001. "
        "Evalúa del 1 al 10 los siguientes criterios del siguiente caso de estudio:\n\n"
        "1. Claridad\n2. Aplicación de ISO 9001\n3. Profundidad técnica\n4. Viabilidad práctica\n\n"
        f"Texto a evaluar:\n\n{caso_texto}\n\n"
        "Devuélvelo en formato JSON así:\n"
        '{"claridad": 4, "iso": 6, "profundidad": 2, "viabilidad": 5}'
    )

    try:
        payload = {"contents": [{"parts": [{"text": prompt_evaluador}]}]}
        response = requests.post(GEMINI_API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            respuesta = data['candidates'][0]['content']['parts'][0]['text']
            # Limpieza de la respuesta
            respuesta = respuesta.replace("```json", "").replace("```", "").strip()
            evaluacion = json.loads(respuesta)
            return evaluacion
    except Exception as e:
        print(f"Error en evaluación IA: {e}")
    
    return {"claridad": 7, "iso": 7, "profundidad": 7, "viabilidad": 7}

def generar_comparacion_tabla_dinamica(eval_usuario, eval_ia):
    def mejor(valor1, valor2):
        if valor1 > valor2: return "🔵 Usuario"
        elif valor1 < valor2: return "🔴 IA"
        else: return "⚪ Empate"

    return f"""
    <table border="1" style="width:100%; border-collapse: collapse; margin-top: 20px;">
      <tr><th>Aspecto</th><th>Usuario</th><th>IA</th><th>Mejor Evaluado</th></tr>
      <tr><td>Claridad</td><td>{eval_usuario.get('claridad', 0)}</td><td>{eval_ia.get('claridad', 0)}</td><td>{mejor(eval_usuario.get('claridad', 0), eval_ia.get('claridad', 0))}</td></tr>
      <tr><td>Aplicación ISO</td><td>{eval_usuario.get('iso', 0)}</td><td>{eval_ia.get('iso', 0)}</td><td>{mejor(eval_usuario.get('iso', 0), eval_ia.get('iso', 0))}</td></tr>
      <tr><td>Profundidad Técnica</td><td>{eval_usuario.get('profundidad', 0)}</td><td>{eval_ia.get('profundidad', 0)}</td><td>{mejor(eval_usuario.get('profundidad', 0), eval_ia.get('profundidad', 0))}</td></tr>
      <tr><td>Viabilidad</td><td>{eval_usuario.get('viabilidad', 0)}</td><td>{eval_ia.get('viabilidad', 0)}</td><td>{mejor(eval_usuario.get('viabilidad', 0), eval_ia.get('viabilidad', 0))}</td></tr>
    </table>
    """

def generar_conclusion_automatica(eval_usuario, eval_ia):
    try:
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
    except Exception as e:
        print(f"Error en conclusión automática: {e}")
        return "<p>No se pudo generar la conclusión automática.</p>"

def generar_comparacion_detallada(texto_usuario, texto_ia):
    try:
        prompt_comparacion = (
            "Eres un experto en ISO 9000. Compara estos dos casos de estudio y genera un análisis detallado:\n\n"
            "CASO DEL USUARIO:\n\n" + texto_usuario + "\n\n"
            "CASO DE LA IA:\n\n" + texto_ia + "\n\n"
            "Proporciona un análisis comparativo no hagas cuadro solo texto detallado que incluya:\n"
            "1. Fortalezas y debilidades de cada versión\n"
            "2. Cumplimiento con ISO 9001\n"
            "3. Sugerencias de mejora\n\n"
            "Formato de respuesta: texto estructurado en Markdown"
        )
        
        payload = {"contents": [{"parts": [{"text": prompt_comparacion}]}]}
        response = requests.post(GEMINI_API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error en comparación detallada: {e}")
    
    return "No se pudo generar la comparación detallada."

def guardar_textos_cache(texto_usuario, texto_ia):
    try:
        with open(os.path.join(CACHE_FOLDER, 'caso_usuario.txt'), 'w', encoding='utf-8') as f:
            f.write(texto_usuario)
        
        with open(os.path.join(CACHE_FOLDER, 'caso_ia.txt'), 'w', encoding='utf-8') as f:
            f.write(texto_ia)
        return True
    except Exception as e:
        print(f"Error al guardar en caché: {e}")
        return False

def cargar_textos_cache():
    try:
        with open(os.path.join(CACHE_FOLDER, 'caso_usuario.txt'), 'r', encoding='utf-8') as f:
            texto_usuario = f.read()
        
        with open(os.path.join(CACHE_FOLDER, 'caso_ia.txt'), 'r', encoding='utf-8') as f:
            texto_ia = f.read()
        
        return texto_usuario, texto_ia
    except Exception as e:
        print(f"Error al cargar caché: {e}")
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cargar', methods=['GET', 'POST'])
def cargar():
    if request.method == 'POST':
        if 'pdf' not in request.files:
            return render_template('cargar_pdf.html', error="No se ha seleccionado archivo")
            
        archivo = request.files['pdf']
        grupo_resultado = request.form.get('grupo', '')

        if archivo.filename == '':
            return render_template('cargar_pdf.html', error="Nombre de archivo inválido")

        try:
            ruta_pdf = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
            archivo.save(ruta_pdf)

            # Extraer texto del PDF
            caso_usuario_md = extraer_caso_estudio_md(ruta_pdf)
            caso_usuario = markdown.markdown(caso_usuario_md)

            # Generar versión IA
            prompt_ia = (
                "Eres un experto en ISO 9001. Reescribe este caso de estudio "
                "aplicando principios de calidad, mejora continua, enfoque al cliente y gestión de riesgos:\n\n"
                f"{caso_usuario_md}"
            )
            payload = {"contents": [{"parts": [{"text": prompt_ia}]}]}
            response = requests.post(GEMINI_API_URL, json=payload, timeout=60)
            
            if response.status_code != 200:
                raise Exception("Error al conectar con la API de Gemini")
                
            caso_ia_md = response.json()['candidates'][0]['content']['parts'][0]['text']
            caso_ia = markdown.markdown(caso_ia_md)

            # Guardar en cache
            guardar_textos_cache(caso_usuario_md, caso_ia_md)

            # Evaluaciones
            evaluacion_usuario = evaluar_caso_con_ia(caso_usuario_md)
            evaluacion_ia = evaluar_caso_con_ia(caso_ia_md)

            # Comparación detallada
            comparacion_detallada = generar_comparacion_detallada(caso_usuario_md, caso_ia_md)
            comparacion_detallada_html = markdown.markdown(comparacion_detallada)

            # Guardar DOCX
            guardar_en_docx(caso_usuario_md, os.path.join(RESULTADOS_FOLDER, 'caso_usuario.docx'))
            guardar_en_docx(caso_ia_md, os.path.join(RESULTADOS_FOLDER, 'caso_ia.docx'))

            return render_template('comparativa.html',
                caso_usuario=caso_usuario,
                caso_ia=caso_ia,
                grupo=grupo_resultado,
                evaluacion_usuario=evaluacion_usuario,
                evaluacion_ia=evaluacion_ia,
                comparacion_tabla=generar_comparacion_tabla_dinamica(evaluacion_usuario, evaluacion_ia),
                conclusion=generar_conclusion_automatica(evaluacion_usuario, evaluacion_ia),
                comparacion_detallada=comparacion_detallada_html
            )

        except Exception as e:
            print(f"Error en procesamiento: {e}")
            return render_template('cargar_pdf.html', error=f"Error al procesar el archivo: {str(e)}")

    return render_template('cargar_pdf.html')

@app.route('/descargar/<archivo>')
def descargar(archivo):
    try:
        return send_from_directory(RESULTADOS_FOLDER, archivo, as_attachment=True)
    except Exception as e:
        return str(e), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)