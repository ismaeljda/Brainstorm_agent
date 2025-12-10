"""
Orchestrateur intelligent pour le système multi-agents.
Gère la sélection des agents par pertinence et le débat entre agents.
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class Message:
    """Représente un message dans la conversation."""
    role: str  # 'user' ou agent_id ('facilitateur', 'strategie', etc.)
    content: str
    timestamp: float


@dataclass
class AgentScore:
    """Score de pertinence d'un agent."""
    agent_id: str
    score: float
    reasoning: str


class IntelligentOrchestrator:
    """
    Orchestrateur intelligent qui décide quel agent doit parler
    en fonction du contexte et de la pertinence.
    """

    def __init__(self, agents_config: Dict, meeting_context: Optional[Dict] = None):
        """
        Args:
            agents_config: Configuration des agents depuis agents/prompts.py
            meeting_context: Contexte du meeting (entreprise, objectif, etc.)
        """
        self.agents = agents_config
        self.conversation_history: List[Message] = []
        self.last_speaker: Optional[str] = None
        self.debate_mode = False
        self.turn_count = 0
        self.meeting_context = meeting_context or {}

    def add_message(self, role: str, content: str, timestamp: float = None):
        """Ajoute un message à l'historique."""
        import time
        if timestamp is None:
            timestamp = time.time()

        self.conversation_history.append(Message(role, content, timestamp))
        self.last_speaker = role
        self.turn_count += 1

    def _build_context_summary(self, last_n: int = 5) -> str:
        """Construit un résumé des derniers messages pour le contexte."""
        recent = self.conversation_history[-last_n:] if len(self.conversation_history) > last_n else self.conversation_history

        summary = []
        for msg in recent:
            role_name = msg.role if msg.role == 'user' else self.agents.get(msg.role, {}).get('name', msg.role)
            summary.append(f"[{role_name}]: {msg.content[:100]}...")

        return "\n".join(summary)

    def _score_agent_relevance(self, agent_id: str, context: str) -> AgentScore:
        """
        Score la pertinence d'un agent pour répondre au contexte actuel.

        Utilise GPT pour analyser:
        1. Expertise de l'agent par rapport au sujet
        2. Pertinence dans le flux de conversation
        3. Capacité à faire avancer le débat
        """
        agent_info = self.agents.get(agent_id, {})
        agent_name = agent_info.get('name', agent_id)
        agent_prompt = agent_info.get('prompt', '')

        scoring_prompt = f"""Analyse la pertinence de cet agent pour intervenir maintenant.

AGENT: {agent_name}
EXPERTISE: {agent_prompt[:300]}

CONTEXTE DE CONVERSATION:
{context}

CRITÈRES:
1. Expertise pertinente (0-40 points)
2. Timing approprié (0-30 points)
3. Apport au débat (0-30 points)

Réponds au format JSON:
{{"score": <0-100>, "reasoning": "<1-2 phrases>"}}"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un expert en orchestration de conversation multi-agents."},
                    {"role": "user", "content": scoring_prompt}
                ],
                temperature=0.3,
                max_tokens=150,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            return AgentScore(agent_id, result['score'], result['reasoning'])

        except Exception as e:
            print(f"⚠️ Erreur scoring {agent_id}: {e}")
            # Fallback: score aléatoire
            import random
            return AgentScore(agent_id, random.randint(20, 60), "Scoring par défaut")

    def select_next_speaker(self, allow_consecutive: bool = False) -> Tuple[str, str]:
        """
        Sélectionne l'agent le plus pertinent pour parler.

        Args:
            allow_consecutive: Permet au même agent de parler 2 fois de suite

        Returns:
            (agent_id, reasoning)
        """
        context = self._build_context_summary(last_n=5)

        # Scorer tous les agents
        scores: List[AgentScore] = []
        for agent_id in self.agents.keys():
            # Ne pas permettre au même agent de reparler immédiatement (sauf si allow_consecutive)
            if not allow_consecutive and agent_id == self.last_speaker:
                continue

            score = self._score_agent_relevance(agent_id, context)
            scores.append(score)

        # Trier par score décroissant
        scores.sort(key=lambda s: s.score, reverse=True)

        if not scores:
            # Fallback: facilitateur
            return 'facilitateur', "Aucun agent disponible, facilitateur par défaut"

        best = scores[0]
        print(f"🎯 Agent sélectionné: {best.agent_id} (score: {best.score:.1f}) - {best.reasoning}")

        return best.agent_id, best.reasoning

    def generate_agent_response(self, agent_id: str, instruction: Optional[str] = None) -> str:
        """
        Génère la réponse d'un agent en rebondissant naturellement sur la conversation.

        Args:
            agent_id: ID de l'agent qui doit parler
            instruction: Instruction optionnelle
        """
        agent_info = self.agents.get(agent_id, {})
        agent_prompt = agent_info.get('prompt', '')
        agent_name = agent_info.get('name', agent_id)

        # Construire le contexte du meeting
        context_str = ""
        if self.meeting_context:
            context_str = f"""
CONTEXTE DU MEETING:
- Entreprise/Projet: {self.meeting_context.get('companyName', 'N/A')}
- Contexte: {self.meeting_context.get('companyContext', 'N/A')}
- Objectif: {self.meeting_context.get('meetingObjective', 'N/A')}
"""

        # Enrichir le prompt pour encourager les rebonds
        enhanced_prompt = f"""{agent_prompt}
{context_str}
CONSIGNES DE CONVERSATION:
- Rebondis DIRECTEMENT sur ce qui vient d'être dit
- Apporte ton point de vue d'expert {agent_name}
- Sois réactif et engagé dans la discussion
- Complète, nuance, approuve ou challenge ce qui a été dit
- 2-3 phrases maximum, concis et percutant
- Adresse-toi aux autres agents par leur fonction si tu réagis à leurs propos
- Garde en tête le contexte et l'objectif du meeting"""

        # Construire l'historique avec identification des speakers
        messages = [
            {"role": "system", "content": enhanced_prompt}
        ]

        # Ajouter les derniers messages avec contexte
        recent_messages = self.conversation_history[-6:]
        for msg in recent_messages:
            role = "assistant" if msg.role != 'user' else "user"

            # Identifier le speaker
            if msg.role == 'user':
                speaker = "Utilisateur"
            else:
                speaker = self.agents.get(msg.role, {}).get('name', msg.role)

            formatted_content = f"[{speaker}]: {msg.content}"
            messages.append({"role": role, "content": formatted_content})

        # Instruction finale
        if instruction:
            messages.append({"role": "user", "content": instruction})
        else:
            messages.append({"role": "user", "content": f"À toi {agent_name}, réagis maintenant."})

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.8,  # Plus créatif pour des échanges naturels
                max_tokens=150
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ Erreur génération réponse {agent_id}: {e}")
            return f"Je rencontre un problème technique, désolé."

    def orchestrate_turn(self) -> Dict:
        """
        Orchestre un tour complet de conversation.
        Les agents rebondissent naturellement les uns sur les autres.

        Returns:
            Dict avec agent_id, message, reasoning
        """
        # Sélectionner le prochain agent le plus pertinent
        agent_id, reasoning = self.select_next_speaker(allow_consecutive=False)

        # Générer la réponse (l'agent rebondit automatiquement sur le contexte)
        message = self.generate_agent_response(agent_id)

        # Ajouter à l'historique
        self.add_message(agent_id, message)

        return {
            'agent_id': agent_id,
            'message': message,
            'reasoning': reasoning,
            'debate_mode': False,  # Plus de détection de débat
            'turn': self.turn_count
        }
