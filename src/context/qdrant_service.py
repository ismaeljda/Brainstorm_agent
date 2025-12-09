"""
Service RAG Production-Grade avec Qdrant.
Inspiré de : https://github.com/techwithtim/ProductionGradeRAGPythonApp
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader
)


class QdrantRAGService:
    """
    Service RAG avec Qdrant - Production Grade.

    Avantages vs Pinecone :
    - ✅ Open-source et gratuit
    - ✅ Peut tourner en local (pas besoin de cloud)
    - ✅ Plus rapide pour les petits datasets
    - ✅ Pas de limite de vecteurs
    """

    def __init__(self,
                 url: str = None,
                 collection_name: str = "debatehub-context",
                 embedding_dim: int = 1536):
        """
        Initialise le service RAG avec Qdrant.

        Args:
            url: URL Qdrant (default: local en mémoire)
            collection_name: Nom de la collection
            embedding_dim: Dimension des embeddings (1536 pour text-embedding-3-small)
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        # Initialiser Qdrant
        # Si pas d'URL, utiliser en mémoire (parfait pour dev/test)
        if url:
            self.client = QdrantClient(url=url, timeout=30)
            print(f"✅ Qdrant connecté à : {url}")
        else:
            # Mode en mémoire (pas besoin de serveur Qdrant!)
            self.client = QdrantClient(":memory:")
            print("✅ Qdrant initialisé en mémoire (mode dev)")

        # Créer la collection si elle n'existe pas
        self._ensure_collection()

        # Initialiser OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=self.embedding_dim
        )

        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def _ensure_collection(self) -> None:
        """Crée la collection Qdrant si elle n'existe pas."""
        try:
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    ),
                )
                print(f"✅ Collection '{self.collection_name}' créée")
            else:
                print(f"ℹ️  Collection '{self.collection_name}' existe déjà")
        except Exception as e:
            print(f"⚠️ Erreur création collection : {e}")

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
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_extension in ['.doc', '.docx']:
                loader = UnstructuredWordDocumentLoader(file_path)
            elif file_extension in ['.xls', '.xlsx']:
                loader = UnstructuredExcelLoader(file_path)
            else:
                # Fallback
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            documents = loader.load()
            return "\n\n".join([doc.page_content for doc in documents])

        except Exception as e:
            raise Exception(f"Erreur chargement document : {str(e)}")

    def index_document(self,
                      doc_id: str,
                      content: str,
                      metadata: Dict[str, Any] = None) -> List[str]:
        """
        Indexe un document dans Qdrant.

        Args:
            doc_id: ID unique du document
            content: Contenu du document
            metadata: Métadonnées

        Returns:
            Liste des IDs des chunks indexés
        """
        # Découper en chunks
        chunks = self.text_splitter.split_text(content)

        # Créer les embeddings
        embeddings_list = self.embeddings.embed_documents(chunks)

        # Préparer les points Qdrant
        points = []
        chunk_ids = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
            # ID unique basé sur le doc_id + index
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{i}"))
            chunk_ids.append(chunk_id)

            # Payload avec métadonnées
            payload = {
                **(metadata or {}),
                "doc_id": doc_id,
                "chunk_index": i,
                "text": chunk
            }

            points.append(
                PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload=payload
                )
            )

        # Upsert dans Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        print(f"✅ {len(chunks)} chunks indexés pour le document '{doc_id}'")

        return chunk_ids

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche sémantique dans Qdrant.

        Args:
            query: Requête de recherche
            top_k: Nombre de résultats

        Returns:
            Liste des résultats avec score et contenu
        """
        # Créer l'embedding de la requête
        query_embedding = self.embeddings.embed_query(query)

        # Rechercher dans Qdrant (nouvelle API)
        try:
            # API moderne (Qdrant >= 1.7.0)
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                with_payload=True,
                limit=top_k
            )
            results = response.points
        except AttributeError:
            # Ancienne API (fallback pour versions < 1.7.0)
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                with_payload=True,
                limit=top_k
            )

        # Formater les résultats
        formatted_results = []
        for result in results:
            payload = getattr(result, "payload", None) or {}

            formatted_results.append({
                "id": str(result.id),
                "score": result.score,
                "text": payload.get("text", ""),
                "doc_id": payload.get("doc_id", ""),
                "metadata": payload
            })

        return formatted_results

    def delete_document(self, doc_id: str) -> None:
        """
        Supprime tous les chunks d'un document.

        Args:
            doc_id: ID du document
        """
        try:
            # Qdrant permet de filtrer par metadata
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id)
                        )
                    ]
                )
            )
            print(f"✅ Document '{doc_id}' supprimé")

        except Exception as e:
            print(f"⚠️ Erreur suppression document : {e}")

    def get_relevant_context(self, query: str, max_chars: int = 3000) -> str:
        """
        Récupère le contexte pertinent formaté pour les agents.

        Args:
            query: Requête
            max_chars: Nombre max de caractères

        Returns:
            Contexte formaté
        """
        results = self.search(query, top_k=5)

        if not results:
            return ""

        context_parts = ["=== DOCUMENTS DE RÉFÉRENCE PERTINENTS ===\n"]
        total_chars = 0

        for i, result in enumerate(results, 1):
            text = result['text']
            score = result['score']

            # Limiter la longueur
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

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de la collection.

        Returns:
            Statistiques
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "total_vectors": info.points_count,
                "vector_size": self.embedding_dim,
                "status": info.status
            }
        except Exception as e:
            return {"error": str(e)}


# Instance globale
_qdrant_service: Optional[QdrantRAGService] = None


def get_qdrant_service() -> QdrantRAGService:
    """Récupère l'instance globale du service Qdrant."""
    global _qdrant_service
    if _qdrant_service is None:
        # Mode en mémoire par défaut (pas besoin de serveur!)
        _qdrant_service = QdrantRAGService()
    return _qdrant_service
