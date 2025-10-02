from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from vosk import Model, KaldiRecognizer
import json
import os
import re
import spacy
import tempfile
import whisper

app = FastAPI(title="Microservicio de Transcripción")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tus dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar modelo de Whisper (solo una vez al iniciar)
model = whisper.load_model("base")

@app.get("/")
def read_root():
    return {"message": "Microservicio de transcripción funcionando"}

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": True}

'''
    Speech to Text
'''
@app.post("/transcribir")
async def transcribir_audio(audio: UploadFile = File(...)):
    #print(type(audio))
    with open(f"/tmp/{audio.filename}", "wb") as f:
        f.write(await audio.read())

    #print(f"/tmp/{audio.filename}")
    result = model.transcribe(f"/tmp/{audio.filename}")
    return {"texto": result["text"]}

'''
    Stream to Text
'''
@app.websocket("/stream")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    #rec = KaldiRecognizer(model, 16000)  # Vosk espera 16kHz

    try:
        model = Model("vosk-model-small-es-0.42")
        rec = KaldiRecognizer(model, 16000)  # 16kHz
        while True:
            # dentro de tu WebSocket:
            pcm_bytes = await ws.receive_bytes()

            if rec.AcceptWaveform(pcm_bytes):
                result = json.loads(rec.Result())
                await ws.send_text(result["text"])
            else:
                partial = json.loads(rec.PartialResult())
                await ws.send_text(partial["partial"])
                #await ws.send_text("[...] " + partial["partial"])
    except Exception as e:
        print(e)
        await ws.close()

'''
    Extracción de datos del texto de la denuncia
'''
@app.post("/get_datas")
async def get_datas(texto: str):
    nlp = spacy.load("es_core_news_sm")
    doc = nlp(texto)
    
    datos = {
        'full_name': '',
        'dni': '',
        'address': '',
        'phone': '',
        'email': ''
    }
    
    # Extraer nombres (ENTIDADES PER)
    for ent in doc.ents:
        if ent.label_ == "PER" and len(ent.text.split()) >= 2:
            datos['full_name'] = ent.text
            break
    
    # Extraer DNI/NIE (patrones regex)
    #dni_pattern = r'\b[0-9]{7,8}[A-Za-z]\b'
    #dnis = re.findall(dni_pattern, texto)
    #if dnis:
    #    datos['dni'] = dnis[0].upper()
    datos['dni'] = extract_dni(texto)
    
    # Extraer teléfonos
    #phone_pattern = r'(\+34|0034|34)?[ -]*(6|7)[ -]*([0-9][ -]*){8}'
    #phone_pattern = r'(\+\d{1,4})?[\s\-\.\(\)]*([\d\s\-\.\(\)]{8,15})'
    #phone_pattern = r'(?:\+?\d{1,4}[\s\-\.]?)?(?:\d[\s\-\.]?){8,}\d'
    #phone_pattern = r'[\+\d][\d\s\-\.\(\)]{8,20}'
    #phones = re.findall(phone_pattern, texto)
    #if phones:
    #    datos['telefono'] = phones[0][0] if phones[0][0] else phones[0][1] + ''.join(phones[0][2:])
    datos['phone'] = extract_phone(texto)
    
    # Extraer email
    #email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    #emails = re.findall(email_pattern, texto)
    #if emails:
    #    datos['email'] = emails[0]
    datos['email'] = extract_email(texto)
    
    print("Address")
    print(extract_address(texto))
    #datos['email'] = extract_email(texto)

    print("Texto")
    print(ia_text_deepseek(texto))
    return datos

def extract_dni(texto: str) -> List[str]:
    """
    Extrae todos los DNI/NIE de un texto, incluso con espacios
    """
    # Patrón regex que permite espacios opcionales
    patrones = [
        r'\b(\d(?:\s*\d){6,7}\s*[A-Za-z])\b',
        r'\b(\d{1,2}\s?\d{1,3}\s?\d{1,3}\s?[A-Za-z])\b',
        r'\b(\d{7,8})\s*[\-\—]\s*([A-Za-z])\b',
        r'\b([A-Z])\s*(\d{7})\s*([A-Z])\b'  # Para NIE: X 1234567 Z
    ]
    
    dnis_encontrados = []
    
    for patron in patrones:
        for match in re.finditer(patron, texto, re.IGNORECASE):
            # Unir grupos y eliminar espacios
            grupos = [g for g in match.groups() if g]
            dni_sin_espacios = ''.join(grupos).replace(' ', '').upper()
            
            # Validar formato básico
            if re.match(r'^([0-9]{7,8}[A-Z]|[A-Z][0-9]{7}[A-Z])$', dni_sin_espacios):
                dnis_encontrados.append(dni_sin_espacios)
    
    return dnis_encontrados[0] if len(dnis_encontrados) > 0 else ""

#def extract_phone(texto: str) -> List[Dict]:
def extract_phone(texto: str):
    """Combina regex con spaCy para mejor precisión"""

    # Cargar modelo de spaCy
    try:
        nlp = spacy.load("es_core_news_sm")
        doc = nlp(texto)
    except:
        doc = None

    # Patrón flexible
    patron = r'[\+\d][\d\s\-\.\(\)]{8,20}'
    resultados = []
    for match in re.finditer(patron, texto):
        candidato = match.group()
        digitos = re.findall(r'\d', candidato)
        
        if len(digitos) >= 9:  # Mínimo 9 dígitos reales
            telefono_limpio = ''.join(digitos)
            if candidato.startswith('+'):
                telefono_limpio = '+' + telefono_limpio
            
            # Usar spaCy para contexto si está disponible
            contexto = {}
            if doc:
                contexto = _obtener_contexto_spacy(doc, match.start(), match.end())
            
            resultados.append({
                'original': candidato,
                'limpio': telefono_limpio,
                'digitos': len(digitos),
                'contexto': contexto
            })
    
    return resultados[0]["limpio"]

def _obtener_contexto_spacy(doc, start_pos: int, end_pos: int) -> Dict:
    """Obtiene contexto usando spaCy"""
    for sent in doc.sents:
        if sent.start_char <= start_pos and end_pos <= sent.end_char:
            return {
                'oracion': sent.text,
                'entidades': [ent.text for ent in sent.ents],
                'es_contacto': any(palabra in sent.text.lower() 
                                 for palabra in ['teléfono', 'contacto', 'llamar'])
            }
    return {}

def extract_email(texto: str) -> Dict:
    from email_extractor import EmailExtractor
    """Procesa texto y extrae emails con información contextual"""

    extractor = EmailExtractor()
    emails = extractor.extraer_emails(texto)

    # Enriquecer con información adicional
    for email in emails:
        email['longitud'] = len(email['email_limpio'])
        partes = email['email_limpio'].split('@')
        if len(partes) == 2:
            email['usuario'] = partes[0]
            email['dominio'] = partes[1]
        else:
            email['usuario'] = ''
            email['dominio'] = ''

    return emails[0]["email_limpio"]
    #return {
    #    'total_emails': len(emails),
    #    'emails': emails,
    #    'texto_original': texto
    #}

def extract_address(texto: str) -> List[Dict]:
    from address_extractor import ComponentesConSpacyExtractor
    """Extrae direcciones con información de entidades de spaCy"""

    extractor = ComponentesConSpacyExtractor()
    
    resultado = extractor.extraer_con_contexto(texto)
    
    for campo in ['calle', 'numero', 'piso', 'puerta', 'codigo_postal', 'localidad', 'provincia', 'pais']:
        if resultado[campo]:
            print(f"   {campo.upper():<15}: {resultado[campo]}")
    
        #print(f"   CONTEXTO_VALIDO: {resultado['contexto_valido']}")
    print(f"   CONFIANZA: {resultado['confianza']:.2f}")

def analisis_gramatical_detallado(texto: str):
    """
    Análisis gramatical detallado usando spaCy
    """
    nlp = spacy.load("es_core_news_md")
    doc = nlp(texto)
    
    analisis = {
        'sustantivos': [],
        'verbos': [],
        'adjetivos': [],
        'adverbios': [],
        'errores_potenciales': [],
        'estructura_oraciones': []
    }
    
    # Análisis de cada token
    for token in doc:
        if token.pos_ == 'NOUN':
            analisis['sustantivos'].append(token.text)
        elif token.pos_ == 'VERB':
            analisis['verbos'].append(token.text)
        elif token.pos_ == 'ADJ':
            analisis['adjetivos'].append(token.text)
        elif token.pos_ == 'ADV':
            analisis['adverbios'].append(token.text)
        
        # Detectar errores potenciales
        if token.dep_ == 'nsubj' and token.head.pos_ != 'VERB':
            analisis['errores_potenciales'].append(f"Posible error de concordancia: {token.text}")
    
    # Análisis de estructura
    for sent in doc.sents:
        analisis['estructura_oraciones'].append({
            'texto': sent.text,
            'longitud': len(sent),
            'raiz': sent.root.text
        })
    
    return analisis


'''
    IA Texts
'''
def ia_text_deepseek(texto: str):
    from rewrite_deepseek import CorrectorDeepSeek
    corrector = CorrectorDeepSeek(api_key="sk-ce8146e704414c10ba2ed30e8f39abf6")

    correccion = corrector.corregir_texto(texto, tipo_correccion="datos")
    print(f"Original: {texto}")
    print(f"Corregido: {correccion}")
    print("-" * 50)
    return correccion

def ia_text_spacy(texto: str):
    from rewrite_text import MejoradorRedaccionSpacy

    # Inicializar el mejorador
    mejorador = MejoradorRedaccionSpacy()

    # Mejorar el texto
    resultado = mejorador.mejorar_redaccion(texto)

    print("📝 TEXTO ORIGINAL:")
    print(resultado['texto_original'])

    print("\n✨ TEXTO MEJORADO:")
    print(resultado['texto_mejorado'])

    #print("\n📊 ANÁLISIS:")
    #for key, value in resultado['analisis'].items():
    #    if isinstance(value, float):
    #        print(f"{key}: {value:.2f}")
    #    else:
    #        print(f"{key}: {value}")

    #print("\n💡 RECOMENDACIONES:")
    #for rec in resultado['recomendaciones']:
    #    print(f"• {rec}")
    return resultado['texto_mejorado']

def ia_text_tokenizer(texto: str):
    from transformers import GPT2LMHeadModel, AutoModelForCausalLM, AutoTokenizer
    import torch

    model_name = "DeepESP/gpt2-spanish"

    #model_name = "PlanTL-GOB-ES/gpt2-base-bne"
    #revision = "a7c1e72b198fb1dee4b085a2f288f2d8f8e1c8e3"

    #model_name = "MMG/Llama-3-8B-Spanish"

    # Load model and tokenizer
    #model = GPT2LMHeadModel.from_pretrained(
    #    model_name,
    #    force_download=True,  # Force fresh download
    #    resume_download=False  # Don't resume incomplete downloads
    #)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Set padding token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Example text generation
    text = texto
    inputs = tokenizer(text, return_tensors="pt")

    # Generate text
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            #max_new_tokens=50,
            #do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode and print result
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated_text

def ia_text_pipeline(texto: str):
    print("--0--")
    from transformers import pipeline

    print("--a--")
    #prompt = f"corregir y completar el siguiente texto en español: {texto}"

    generador = pipeline(
        "text-generation",
        model="milyiyo/paraphraser-spanish-t5-small"
        #model="google/mt5-base"
        #model="planTL-GOB-ES/mt5-small"
        #model="PlanTL-GOB-ES/gpt2-base-bne",
        #temperature=0.8,
        #max_new_tokens=50,
        #max_length=900
    )

    print("--b--")
    #text_result = generador(prompt)[0]['generated_text']
    #print(text_result)

    versiones = mejorar_y_expandir_texto(texto, generador, num_versiones=2)

    # Mostrar resultados
    for i, v in enumerate(versiones, start=1):
        text_result = v
        print(f"Versión {i}:\n{v}\n{'-'*60}\n")

    return text_result


def mejorar_y_expandir_texto(texto, generador, num_versiones=2):
    """
    Recibe un texto en español y devuelve varias versiones mejoradas,
    corregidas y ampliadas con ejemplos o detalles adicionales.
    """
    # Prompt que indica corrección y expansión
    prompt = f"Corrige la ortografía y mejora este texto, expandiéndolo con ejemplos y detalles: {texto}"

    # Generar varias versiones
    resultados = generador(
        prompt,
        #max_new_tokens=250,
        #max_length=900,          # longitud mayor para expandir
        #truncation=True,
        num_return_sequences=num_versiones,
        do_sample=True,          # permite creatividad
        top_k=50,
        top_p=0.95
    )

    # Extraer solo el texto generado
    versiones = [r['generated_text'] for r in resultados]
    return versiones

'''
    Main
'''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

