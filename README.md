# 🏥 IADESALUD — Asistente Médico para WhatsApp

Asistente de salud y bienestar para WhatsApp, con IA local (Ollama + llama3.1) y fallback a la nube (OpenAI). Diseñado para ser empático, sencillo y resistente a fallos.

---

## 🗂️ Estructura del Proyecto

```
IADESALUD/
├── ai-backend/               # Motor Python (FastAPI + LangChain + ChromaDB)
│   ├── core/
│   │   ├── llm_manager.py    # Orquestación LLM: local (Ollama) → nube (OpenAI)
│   │   ├── rag_manager.py    # Búsqueda semántica en ChromaDB
│   │   └── prompts.py        # System prompt cálido y empático
│   ├── scripts/
│   │   └── ingest_data.py    # Ingesta de PDFs y audio/video en ChromaDB
│   ├── data/                 # Base de datos vectorial local (ChromaDB)
│   ├── main.py               # FastAPI: /api/chat, /api/transcribe, /api/health
│   ├── requirements.txt
│   └── .env                  # 🔑 TUS CLAVES (no subir a git)
│
└── whatsapp-bot/             # Bot Node.js (whatsapp-web.js)
    ├── index.js              # Lógica del bot (texto + notas de voz)
    ├── package.json
    └── .env                  # 📱 Número permitido + URLs del backend
```

---

## ✅ Requisitos Previos (Windows)

| Herramienta | Instalación |
|---|---|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) |
| **Node.js 18+** | [nodejs.org](https://nodejs.org/) |
| **Ollama** | [ollama.com](https://ollama.com/) |
| **ffmpeg** | [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) → añadir al PATH |
| **Google Chrome** | [google.com/chrome](https://www.google.com/chrome/) (para puppeteer) |

---

## 🚀 Guía de Instalación Paso a Paso (Windows)

### Paso 1 — Descargar los Modelos de IA Local

Abre una terminal (PowerShell o CMD) y ejecuta:

```powershell
# Descargar el LLM principal (es grande, ~4GB, ten paciencia)
ollama run llama3.1

# Descargar el modelo de embeddings semánticos
ollama pull nomic-embed-text
```

> **Nota:** Ollama debe estar ejecutándose en segundo plano. Puedes verificarlo con `ollama list`.

---

### Paso 2 — Configurar el Backend Python

```powershell
# Ir a la carpeta del backend
cd C:\Users\SEBASTIAN FERNANDEZ\Downloads\IADESALUD\ai-backend

# Crear entorno virtual (muy recomendado)
python -m venv venv

# Activar el entorno virtual en Windows
.\venv\Scripts\Activate.ps1

# Si da error de permisos, ejecuta primero:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Instalar dependencias
pip install -r requirements.txt
```

#### Configurar variables de entorno

Edita el archivo `ai-backend\.env` y pon tu clave real de OpenAI:

```env
OPENAI_API_KEY=sk-TU-CLAVE-REAL-DE-OPENAI-AQUI
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1
EMBEDDING_MODEL=nomic-embed-text
CHROMA_PERSIST_DIR=./data/chroma_db
```

#### Iniciar el Backend

```powershell
python main.py
```

El backend estará disponible en: **http://localhost:8000**
Puedes verificarlo en: http://localhost:8000/api/health

---

### Paso 3 — Configurar el Bot de WhatsApp

```powershell
# Ir a la carpeta del bot
cd C:\Users\SEBASTIAN FERNANDEZ\Downloads\IADESALUD\whatsapp-bot

# Instalar dependencias Node.js
npm install
```

#### Configurar el número autorizado

Edita `whatsapp-bot\.env`:

```env
# Número SIN el +. Ejemplo España: 34699112233 | México: 521234567890
ALLOW_PHONE_NUMBER=34600000000

API_BACKEND_URL=http://localhost:8000/api/chat
API_TRANSCRIBE_URL=http://localhost:8000/api/transcribe
```

#### Iniciar y vincular WhatsApp

```powershell
npm start
```

Aparecerá un **código QR** en la terminal. Escanéalo con el WhatsApp del número que usarás como bot:
1. Abre WhatsApp en el móvil del bot
2. Ve a **Configuración → Dispositivos vinculados → Vincular dispositivo**
3. Escanea el QR

Cuando veas `✅ Cliente de WhatsApp listo e integrado.` ¡está funcionando!

---

### Paso 4 — Alimentar el Conocimiento Médico (RAG)

Para que la IA responda con información médica real en lugar de generalidades:

```powershell
# Activar entorno virtual (si no está activo)
cd C:\Users\SEBASTIAN FERNANDEZ\Downloads\IADESALUD\ai-backend
.\venv\Scripts\Activate.ps1

# Ingestar un PDF médico
python scripts\ingest_data.py C:\ruta\a\tu\documento_medico.pdf

# Ingestar un audio o video médico
python scripts\ingest_data.py C:\ruta\a\tu\consulta_medica.mp3
```

Puedes ingestar varios documentos, todos se acumulan en la base de datos local.

---

## 🔧 Solución de Problemas Frecuentes en Windows

### Error: `execution of scripts is disabled`
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: `puppeteer/Chrome not found`
Instala Google Chrome y reinicia. Si el error persiste, edita `index.js` y descomenta la línea:
```js
executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
```

### Error: `ffmpeg not found` (al transcribir audio)
Descarga ffmpeg desde https://www.gyan.dev/ffmpeg/builds/ y añade la carpeta `bin/` al PATH de Windows.

### Ollama no responde / timeout
- Asegúrate de que Ollama esté corriendo (ícono en la bandeja del sistema)
- El sistema automáticamente usará OpenAI como respaldo
- Verifica con: `ollama list`

---

## 🏗️ Arquitectura del Sistema

```
[Tu madre - WhatsApp] 
       ↓ mensaje (texto o voz)
[whatsapp-bot/index.js]
       ↓ HTTP POST
[ai-backend/main.py - FastAPI]
       ↓ busca contexto
[ChromaDB - vectores locales]
       ↓ prompt ensamblado
[Ollama - llama3.1 (LOCAL)]  →→ falla/timeout →→  [OpenAI - gpt-3.5-turbo (NUBE)]
       ↓ respuesta
[Tu madre - WhatsApp] ❤️
```

---

## ⚠️ Importante: Seguridad

- **Nunca subas el archivo `.env` a GitHub** — contiene tu clave de OpenAI
- El bot tiene whitelist estricta: solo responde al número configurado
- Los datos médicos se almacenan **solo en tu computadora**, sin subir a ningún servidor externo

---

*IADESALUD v1.1.0 — Con ❤️ para que tu madre tenga siempre una respuesta cariñosa y bien informada.*
