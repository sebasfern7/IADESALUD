import os
import argparse
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from faster_whisper import WhisperModel
import sys

# Agregar la ruta del backend al sys.path para poder importar módulos locales
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.rag_manager import RAGManager

def process_pdf(file_path: str, rag_manager: RAGManager):
    print(f"📄 Procesando PDF: {file_path}")
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()
    
    # Dividimos en chunks (pedazos manejables) para RAG. 
    # 1000 tokens con overlap de 200 es buena practica para mantener contexto.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    print(f"   -> Generados {len(splits)} fragmentos de texto. Guardando en ChromaDB...")
    rag_manager.vectorstore.add_documents(splits)
    print("✅ PDF guardado exitosamente.")

def process_audio_video(file_path: str, rag_manager: RAGManager):
    print(f"🎙️ Procesando Audio/Video con Whisper: {file_path}")
    # Usamos modelo 'small' o 'base' por defecto. Para mayor precision local, usar 'large-v3' si el PC lo soporta.
    model_size = "small" 
    
    # Run on CPU by default for maximum compatibility, change to "cuda" if GPU is available
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(file_path, beam_size=5, language="es")
    print(f"   -> Idioma detectado: {info.language} con probabilidad {info.language_probability}")
    
    full_text = ""
    for segment in segments:
        full_text += segment.text + " "
        
    print("   -> Transcripción terminada. Generando documento...")
    
    # Truco: Creamos un "Document" falso de Langchain
    from langchain.docstore.document import Document
    doc = Document(page_content=full_text.strip(), metadata={"source": file_path, "type": "audio/video"})
    
    # Lo dividimos y guardamos
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents([doc])
    
    print(f"   -> Generados {len(splits)} fragmentos. Guardando en ChromaDB...")
    rag_manager.vectorstore.add_documents(splits)
    print("✅ Audio/Video guardado exitosamente.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingesta de documentos o medios para IADESALUD.")
    parser.add_argument("filepath", type=str, help="Ruta al archivo (PDF, MP3, MP4)")
    args = parser.parse_args()
    
    if not os.path.exists(args.filepath):
        print(f"❌ Error: El archivo {args.filepath} no existe.")
        exit(1)
        
    rag = RAGManager()
    
    ext = args.filepath.lower().split('.')[-1]
    if ext == 'pdf':
        process_pdf(args.filepath, rag)
    elif ext in ['mp3', 'wav', 'mp4', 'mkv', 'm4a']:
        process_audio_video(args.filepath, rag)
    else:
        print(f"❌ Formato no soportado: .{ext}. Usa PDF, MP3, MP4, WAV.")
