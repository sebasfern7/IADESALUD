import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv

from core.rag_manager import RAGManager
from core.llm_manager import LLMManager
from core.prompts import build_system_prompt

load_dotenv()

app = FastAPI(title="IADESALUD API", version="1.1.0")

class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    reply: str
    source: str

class TranscribeResponse(BaseModel):
    text: str

rag_manager = RAGManager()
llm_manager = LLMManager()

# ─── Endpoint de Chat (Texto) ────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        user_message = request.message

        # 1. Recuperar contexto de la base de datos vectorial
        context_docs = rag_manager.search(user_message)
        context_text = "\n".join([doc.page_content for doc in context_docs])

        # 2. Ensamblar Prompt con el contexto RAG
        system_prompt = build_system_prompt(context_text)

        # 3. Llamar al LLM (Híbrido: Local -> Nube como fallback)
        reply, source = await llm_manager.generate_response(user_message, system_prompt)

        return ChatResponse(reply=reply, source=source)

    except Exception as e:
        print(f"Error procesando el chat: {e}")
        # Mensaje seguro y cariñoso ante fallos catastróficos
        safe_reply = "Mi sistema de memoria se cerró un momentito, ¿podrías repetirme la pregunta mi amor? ❤️"
        return ChatResponse(reply=safe_reply, source="error")


# ─── Endpoint de Transcripción de Audio (Notas de Voz) ───────────────────────

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Recibe un archivo de audio (OGG/MP3/WAV) y lo transcribe con Whisper local.
    Usado por el bot de WhatsApp para convertir notas de voz a texto.
    """
    try:
        from faster_whisper import WhisperModel

        # Guardamos el audio en un archivo temporal
        suffix = os.path.splitext(audio.filename or "audio.ogg")[1] or ".ogg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Cargamos el modelo Whisper (se carga una vez y se reutiliza en producción)
        whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, info = whisper_model.transcribe(tmp_path, beam_size=5, language="es")

        full_text = " ".join([segment.text for segment in segments]).strip()
        os.unlink(tmp_path)  # Limpiamos el temporal

        print(f"[AUDIO] Transcripcion completada: \"{full_text}\"")
        return TranscribeResponse(text=full_text)

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="faster-whisper no está instalado. Instala con: pip install faster-whisper"
        )
    except Exception as e:
        print(f"Error en transcripción de audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error transcribiendo audio: {str(e)}")


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "IADESALUD API", "version": "1.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
