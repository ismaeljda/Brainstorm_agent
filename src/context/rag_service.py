"""
Service RAG (Retrieval Augmented Generation) avec Pinecone.
"""

import os
from typing import List, Dict, Any, Optional

# Import Pinecone optionnel (désactivé pour utiliser Qdrant uniquement)
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    Pinecone = None
    ServerlessSpec = None

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader
)
import uuid


class RAGService:
    """Service de gestion RAG avec Pinecone."""

    def __init__(self,
                 pinecone_api_key: Optional[str] = None,
                 index_name: str = "debatehub-context"):
        """
        Initialise le service RAG.

        Args:
            pinecone_api_key: Clé API Pinecone
            index_name: Nom de l'index Pinecone
        """
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = index_name

        # Initialiser Pinecone
        if self.pinecone_api_key:
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            self._ensure_index()
        else:
            self.pc = None
            print("⚠️ PINECONE_API_KEY non définie - RAG désactivé")

        # Initialiser OpenAI Embeddings
        # Utilise text-embedding-3-small (5x moins cher et plus rapide)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=1536  # Compatible avec l'index Pinecone
        )

        # Text splitter pour découper les documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def _ensure_index(self) -> None:
        """Crée l'index Pinecone s'il n'existe pas."""
        if not self.pc:
            return

        existing_indexes = [index.name for index in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI embeddings dimension
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )

    def load_document(self, file_path: str) -> str:
        """
        Charge un document depuis un fichier.

        Args:
            file_path: Chemin du fichier

        Returns:
            Contenu du document
        """
        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == '.txt':
                loader = TextLoader(file_path)
            elif file_extension in ['.doc', '.docx']:
                loader = UnstructuredWordDocumentLoader(file_path)
            elif file_extension in ['.xls', '.xlsx']:
                loader = UnstructuredExcelLoader(file_path)
            else:
                # Fallback : essayer de lire comme texte
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            documents = loader.load()
            return "\n\n".join([doc.page_content for doc in documents])

        except Exception as e:
            raise Exception(f"Erreur lors du chargement du document : {str(e)}")

    def index_document(self,
                      doc_id: str,
                      content: str,
                      metadata: Dict[str, Any] = None) -> List[str]:
        """
        Indexe un document dans Pinecone.

        Args:
            doc_id: Identifiant unique du document
            content: Contenu du document
            metadata: Métadonnées du document

        Returns:
            Liste des IDs des chunks indexés
        """
        if not self.pc:
            return []

        # Découper le document en chunks
        chunks = self.text_splitter.split_text(content)

        # Créer les embeddings
        embeddings_list = self.embeddings.embed_documents(chunks)

        # Préparer les vecteurs pour Pinecone
        index = self.pc.Index(self.index_name)
        vectors = []
        chunk_ids = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)

            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    **(metadata or {}),
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "text": chunk
                }
            })

        # Indexer dans Pinecone
        index.upsert(vectors=vectors)

        return chunk_ids

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche des documents pertinents.

        Args:
            query: Requête de recherche
            top_k: Nombre de résultats à retourner

        Returns:
            Liste des résultats avec score et contenu
        """
        if not self.pc:
            return []

        # Créer l'embedding de la requête
        query_embedding = self.embeddings.embed_query(query)

        # Rechercher dans Pinecone
        index = self.pc.Index(self.index_name)
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        # Formater les résultats
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "doc_id": match.metadata.get("doc_id", ""),
                "metadata": match.metadata
            })

        return formatted_results

    def delete_document(self, doc_id: str) -> None:
        """
        Supprime un document de l'index.

        Args:
            doc_id: Identifiant du document
        """
        if not self.pc:
            return

        index = self.pc.Index(self.index_name)

        # Rechercher tous les chunks du document
        # Note: Pinecone ne permet pas de filtrer par metadata lors de la suppression
        # On doit d'abord récupérer les IDs puis les supprimer

        # Pour simplifier, on suppose que les chunk IDs suivent le pattern: {doc_id}_chunk_{i}
        # On pourrait améliorer en stockant les chunk IDs lors de l'indexation
        try:
            # Supprimer par filtre de metadata (si supporté par votre plan Pinecone)
            index.delete(filter={"doc_id": doc_id})
        except:
            # Fallback : supprimer les chunks un par un
            # Cela nécessiterait de stocker les chunk IDs
            pass

    def get_relevant_context(self, query: str, max_chars: int = 3000) -> str:
        """
        Récupère le contexte pertinent pour une requête.

        Args:
            query: Requête
            max_chars: Nombre maximum de caractères à retourner

        Returns:
            Contexte pertinent formaté
        """
        results = self.search(query, top_k=5)

        if not results:
            return ""

        context_parts = ["=== DOCUMENTS DE RÉFÉRENCE PERTINENTS ===\n"]
        total_chars = 0

        for i, result in enumerate(results, 1):
            text = result['text']
            score = result['score']

            # Limiter la longueur totale
            if total_chars + len(text) > max_chars:
                remaining_chars = max_chars - total_chars
                text = text[:remaining_chars] + "..."

            context_parts.append(f"[Document {i} - Score: {score:.2f}]")
            context_parts.append(text)
            context_parts.append("")

            total_chars += len(text)

            if total_chars >= max_chars:
                break

        return "\n".join(context_parts)


# Instance globale
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Récupère l'instance globale du service RAG."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
