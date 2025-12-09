"""
Module de gestion du contexte organisationnel et RAG.
"""

from .models import OrganizationalContext, CustomField, RAGDocument
from .storage import ContextStorage

# Service RAG (Pinecone - legacy)
from .rag_service import RAGService, get_rag_service

# Service RAG Production (Qdrant + Inngest)
from .qdrant_service import QdrantRAGService, get_qdrant_service

__all__ = [
    'OrganizationalContext',
    'CustomField',
    'RAGDocument',
    'ContextStorage',
    'RAGService',  # Legacy Pinecone
    'get_rag_service',  # Legacy Pinecone
    'QdrantRAGService',  # Production Qdrant
    'get_qdrant_service',  # Production Qdrant
]
