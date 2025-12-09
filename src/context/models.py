"""
Modèles de données pour le contexte organisationnel.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


@dataclass
class CustomField:
    """Champ personnalisé du contexte."""
    name: str
    field_type: str  # 'text_short', 'text_long', 'number', 'boolean'
    value: Any

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OrganizationalContext:
    """Contexte organisationnel complet d'une entreprise."""

    # Champs standards
    company_name: str = ""
    industry: str = ""
    strategic_goals: str = ""
    internal_constraints: str = ""
    target_audience: str = ""
    communication_tone: str = ""
    free_description: str = ""

    # Champs personnalisés
    custom_fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Métadonnées
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Documents RAG
    documents: List[Dict[str, Any]] = field(default_factory=list)

    def add_custom_field(self, name: str, field_type: str, value: Any) -> None:
        """Ajoute un champ personnalisé."""
        self.custom_fields[name] = {
            "field_type": field_type,
            "value": value
        }
        self.updated_at = datetime.now().isoformat()

    def remove_custom_field(self, name: str) -> None:
        """Supprime un champ personnalisé."""
        if name in self.custom_fields:
            del self.custom_fields[name]
            self.updated_at = datetime.now().isoformat()

    def add_document(self, filename: str, file_path: str, doc_type: str, metadata: Dict[str, Any] = None) -> None:
        """Ajoute un document au contexte."""
        doc = {
            "filename": filename,
            "file_path": file_path,
            "doc_type": doc_type,
            "uploaded_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.documents.append(doc)
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return asdict(self)

    def to_json(self) -> str:
        """Convertit en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrganizationalContext':
        """Crée une instance depuis un dictionnaire."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'OrganizationalContext':
        """Crée une instance depuis JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def format_for_agents(self) -> str:
        """
        Formate le contexte pour injection dans les prompts agents.

        Returns:
            Contexte formaté en texte lisible
        """
        lines = ["=== CONTEXTE ORGANISATIONNEL ===\n"]

        if self.company_name:
            lines.append(f"🏢 Entreprise : {self.company_name}")

        if self.industry:
            lines.append(f"🏭 Secteur : {self.industry}")

        if self.strategic_goals:
            lines.append(f"🎯 Objectifs stratégiques : {self.strategic_goals}")

        if self.internal_constraints:
            lines.append(f"⚠️ Contraintes internes : {self.internal_constraints}")

        if self.target_audience:
            lines.append(f"👥 Public cible : {self.target_audience}")

        if self.communication_tone:
            lines.append(f"💬 Ton de communication : {self.communication_tone}")

        if self.free_description:
            lines.append(f"📝 Description : {self.free_description}")

        # Champs personnalisés
        if self.custom_fields:
            lines.append("\n📋 Informations complémentaires :")
            for field_name, field_data in self.custom_fields.items():
                value = field_data['value']
                lines.append(f"  • {field_name} : {value}")

        # Documents
        if self.documents:
            lines.append(f"\n📄 Documents de référence ({len(self.documents)} fichiers disponibles)")

        lines.append("\n⚠️ IMPORTANT : Vous DEVEZ tenir compte de ce contexte dans TOUTES vos réponses.")
        lines.append("Citez explicitement quelle partie du contexte influence vos décisions.\n")

        return "\n".join(lines)


@dataclass
class RAGDocument:
    """Document indexé dans le système RAG."""
    doc_id: str
    filename: str
    content: str
    chunks: List[str] = field(default_factory=list)
    embeddings_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    uploaded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
