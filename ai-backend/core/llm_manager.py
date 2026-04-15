import os
from groq import AsyncGroq
import asyncio
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

load_dotenv()

class LLMManager:
    def __init__(self):
        # Configuración de Ollama (Local)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.local_model_name = os.getenv("LLM_MODEL", "llama3.1")
        self.local_model_name = os.getenv("LLM_MODEL", "llama3.2:1b")
        self.local_llm = OllamaLLM(base_url=self.ollama_base_url, model=self.local_model_name)
        
        # Configuración de Groq (Nube - Fallback)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        if self.groq_api_key and self.groq_api_key != "tu_api_key_de_groq_aqui":
            self.cloud_client = AsyncGroq(api_key=self.groq_api_key)
        else:
            self.cloud_client = None

    async def _call_local(self, prompt: str) -> str:
        """Llama a Ollama localmente."""
        # asyncio.to_thread es la forma moderna de ejecutar código bloqueante
        response = await asyncio.to_thread(self.local_llm.invoke, prompt)
        return response

    async def _call_cloud(self, system_prompt: str, user_message: str) -> str:
        """Llama a Groq como fallback (ultra-rápido y gratuito)."""
        if not self.cloud_client:
            raise Exception("No hay API Key de Groq configurada para el fallback.")

        print(f"[GROQ] Iniciando peticion a Groq (Fallback) con modelo {self.groq_model}...")
        response = await self.cloud_client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content

    async def generate_response(self, user_message: str, system_prompt: str) -> tuple[str, str]:
        """
        Intenta obtener respuesta del LLM local (Ollama), si falla o tarda más de 30s
        usa Groq como fallback en la nube (gratuito y muy veloz).
        Devuelve (Respuesta, Fuente).
        """
        combined_prompt = f"{system_prompt}\n\nPregunta de la usuaria: {user_message}\n\nRespuesta:"
        
        try:
            print(f"[LOCAL] Intentando generar respuesta con modelo: {self.local_model_name}...")
            # Un timeout generoso para permitir que cargue desde el disco duro
            local_reply = await asyncio.wait_for(self._call_local(combined_prompt), timeout=120.0)
            return local_reply.strip(), "local"
            
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] Modelo {self.local_model_name} tardo demasiado. Activando Fallback a Groq...")
        except Exception as e:
            print(f"[ERROR LOCAL] {e}. Activando Fallback a Groq...")

        # Proceder al Fallback con Groq
        try:
            cloud_reply = await self._call_cloud(system_prompt, user_message)
            return cloud_reply.strip(), "groq"
        except Exception as e:
            print(f"[FATAL] Error catastrofico en el fallback de Groq: {e}")
            raise e
