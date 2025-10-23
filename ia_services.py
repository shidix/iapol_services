from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pyannote.audio import Pipeline
from pydub import AudioSegment

import os
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

# Pipeline para diarización
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1"
)

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
    tmp_path = f"/tmp/{audio.filename}"
    tmp_wav = "/tmp/normalized.wav"
    #with open(f"/tmp/{audio.filename}", "wb") as f:
    with open(tmp_path, "wb") as f:
        f.write(await audio.read())

    #print(f"/tmp/{audio.filename}")
    #result = model.transcribe(f"/tmp/{audio.filename}")

    res = ""

    #audio2 = AudioSegment.from_wav(tmp_path)
    audio2 = AudioSegment.from_file(tmp_path)
    audio2 = audio2.set_frame_rate(16000).set_channels(1)
    audio2.export(tmp_wav, format="wav")

    #print("Procesando diarización...")
    diarization = diarization_pipeline(tmp_wav)

    #print("\nResultados:")
    #for segment, _, speaker in diarization.itertracks(yield_label=True):
    for segment, speaker in diarization.speaker_diarization:
        # Convertir tiempos a milisegundos (pydub usa ms)
        start_ms = int(segment.start * 1000)
        end_ms = int(segment.end * 1000)

        # Recortar segmento de audio
        segment_audio = audio2[start_ms:end_ms]
        segment_audio.export("temp_segment.wav", format="wav")

        # Transcribir con Whisper
        result = model.transcribe("temp_segment.wav", language="es")  # Cambia "es" al idioma necesario
        text = result["text"].strip()

        res += f"{speaker}: {text} (de {segment.start:.1f}s a {segment.end:.1f}s)\n"

    # Limpieza
    os.remove("temp_segment.wav")
    #os.remove(tmp_path)
    os.remove(tmp_wav)

    return {"texto": res}
    #return {"texto": result["text"]}

'''
    Main
'''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

