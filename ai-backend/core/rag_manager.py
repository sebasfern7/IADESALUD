import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv

load_dotenv()

class RAGManager:
    def __init__(self):
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Usamos nomic-embed-text localmente a traves de Ollama
        self.embeddings = OllamaEmbeddings(
            base_url=self.ollama_base_url,
            model=self.embedding_model_name
        )
        
        self._init_db()

    def _init_db(self):
        """Inicializa (o carga) la base de datos vectorial local"""
        # Si la carpeta no existe, Chroma la creara cuando ingresemos documentos
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="salud_db"
        )
        
    def search(self, query: str, top_k: int = 3):
        """
        Busca en la base de datos local los fragmentos mas relevantes a la pregunta de la mami.
        Retorna una lista de documentos.
        """
        try:
            # Retriever base, buscara usando similitud de coseno
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": top_k})
            docs = retriever.invoke(query)
            return docs
        except Exception as e:
            print(f"Error o base de datos vacía en RAG: {e}")
            return []
