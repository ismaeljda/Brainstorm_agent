"""
Orchestrateur de réunion multi-agents avec conversation naturelle.
Gère l'intervention intelligente des agents selon le contexte.
"""

import os
from typing import List, Dict, Optional
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from agents.config import AGENTS_CONFIG, RESET_COLOR, HUMAN_COLOR
from agents.prompts import AGENTS_PROMPTS


class Orchestrator:
    """
    Orchestrateur de réunion multi-agents.
    Gère une conversation fluide où les agents interviennent selon leur expertise.
    """

    def __init__(self, objective: str, model: str = "gpt-4o-mini"):
        """
        Initialise l'orchestrateur.

        Args:
            objective: Objectif de la réunion
            model: Modèle LLM à utiliser (défaut: gpt-4o-mini)
        """
        self.objective = objective
        self.model = model
        self.llm = ChatOpenAI(model=model, temperature=0.7)

        # Historique de la conversation
        self.conversation_history: List[Dict[str, str]] = []

        # Créer les agents CrewAI
        self.agents = self._create_agents()

        # Statut de la réunion
        self.meeting_active = True
        self.consensus_detected = False

    def _create_agents(self) -> Dict[str, Agent]:
        """
        Crée les agents CrewAI avec leurs configurations.

        Returns:
            Dictionnaire des agents créés
        """
        agents = {}

        for agent_id, config in AGENTS_CONFIG.items():
            agent = Agent(
                role=config["role"],
                goal="\n".join(config["goals"]),
                backstory=AGENTS_PROMPTS[agent_id],
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )
            agents[agent_id] = agent

        return agents

    def speak(self, agent_id: str, message: str) -> None:
        """
        Affiche un message d'un agent avec style terminal.

        Args:
            agent_id: Identifiant de l'agent
            message: Message à afficher
        """
        if agent_id == "human":
            color = HUMAN_COLOR
            name = "Humain"
        else:
            color = AGENTS_CONFIG[agent_id]["color"]
            name = AGENTS_CONFIG[agent_id]["name"]

        print(f"\n{color}[{name}]{RESET_COLOR}")
        print(f"{message}")
        print("-" * 80)

        # Ajouter à l'historique
        self.conversation_history.append({
            "agent": agent_id,
            "message": message
        })

    def _build_context(self) -> str:
        """
        Construit le contexte de conversation pour l'agent.

        Returns:
            Contexte formaté de la conversation
        """
        if not self.conversation_history:
            return f"OBJECTIF DE LA RÉUNION : {self.objective}\n\nLa réunion commence."

        context = f"OBJECTIF DE LA RÉUNION : {self.objective}\n\n"
        context += "HISTORIQUE DE LA CONVERSATION :\n"

        for entry in self.conversation_history[-10:]:  # Garder les 10 dernières interventions
            agent_id = entry["agent"]
            if agent_id == "human":
                name = "Humain"
            else:
                name = AGENTS_CONFIG[agent_id]["name"]
            context += f"\n[{name}] : {entry['message']}\n"

        return context

    def _select_next_speaker(self, context: str) -> Optional[str]:
        """
        Utilise un LLM pour déterminer intelligemment quel agent doit parler.

        Args:
            context: Contexte actuel de la conversation

        Returns:
            ID de l'agent qui doit parler, ou None si personne
        """
        # Le facilitateur ouvre toujours
        if not self.conversation_history:
            return "facilitateur"

        # Identifier le dernier intervenant (pour éviter qu'il reparle immédiatement)
        last_speaker = self.conversation_history[-1]["agent"] if self.conversation_history else None

        # Si l'humain vient de parler, on peut laisser n'importe quel agent répondre
        # Mais si un agent vient de parler, il ne peut PAS reparler immédiatement
        excluded_agents = []
        if last_speaker and last_speaker != "human":
            excluded_agents.append(last_speaker)

        # Liste des agents disponibles
        available_agents = []
        agent_descriptions = {
            "strategie": "Stratège Business - Expertise : analyse marché, viabilité économique, ROI, risques business",
            "tech": "Tech Lead - Expertise : faisabilité technique, architecture, technologies, code, développement",
            "creatif": "Creative Thinker - Expertise : design, UX/UI, innovation, branding, expérience utilisateur",
            "facilitateur": "Facilitateur - Uniquement pour synthétiser ou clarifier si confusion/besoin de structure"
        }

        for agent_id, description in agent_descriptions.items():
            if agent_id not in excluded_agents:
                available_agents.append(f"- {description}")

        # Construire le prompt de sélection
        excluded_msg = f"\n⚠️ IMPORTANT : {AGENTS_CONFIG[last_speaker]['name']} vient JUSTE de parler, il NE PEUT PAS reparler maintenant." if excluded_agents else ""

        selection_prompt = f"""Contexte de la réunion :
{context}
{excluded_msg}

AGENTS DISPONIBLES (qui peuvent parler maintenant) :
{chr(10).join(available_agents)}
- NONE - Si aucun agent n'a besoin de parler

Analyse le dernier message et détermine QUEL AGENT DOIT PARLER MAINTENANT.

RÈGLES IMPORTANTES :
- Si le message parle de "code", "développeur", "techniquement", "faisable", "technique" → Tech Lead
- Si le message parle de "business", "marché", "rentabilité", "risque", "économique" → Stratège Business
- Si le message parle de "design", "UX", "utilisateur", "créatif", "interface" → Creative Thinker
- Le Facilitateur intervient SEULEMENT si besoin de synthèse ou clarification
- Si l'humain pose une question multi-domaines, choisis l'agent le PLUS pertinent (pas plusieurs)
- Si aucun agent n'est pertinent → NONE

Réponds UNIQUEMENT avec un mot : strategie, tech, creatif, facilitateur, ou none"""

        try:
            response = self.llm.invoke(selection_prompt)
            choice = response.content.strip().lower()

            # Vérifier que le choix n'est pas un agent exclu
            if choice in ["strategie", "tech", "creatif", "facilitateur"] and choice not in excluded_agents:
                return choice
            else:
                return None
        except Exception as e:
            # Fallback sur système de mots-clés amélioré
            return self._fallback_speaker_selection(context, excluded_agents)

    def _fallback_speaker_selection(self, context: str, excluded_agents: List[str] = None) -> Optional[str]:
        """
        Système de fallback basé sur mots-clés améliorés.

        Args:
            context: Contexte de la conversation
            excluded_agents: Liste des agents qui ne peuvent pas parler

        Returns:
            ID de l'agent ou None
        """
        if excluded_agents is None:
            excluded_agents = []

        context_lower = context.lower()
        last_message = self.conversation_history[-1]["message"].lower() if self.conversation_history else ""

        # Mots-clés améliorés
        tech_keywords = ["technique", "technologie", "code", "développeur", "dev", "faisable",
                        "architecture", "stack", "api", "database", "performance",
                        "implementation", "techniquement", "programmer", "coder"]

        business_keywords = ["business", "marché", "market", "économique", "risque", "rentabilité",
                           "stratégie", "concurrent", "roi", "revenu", "viabilité", "monetisation"]

        creative_keywords = ["design", "designer", "ux", "ui", "créatif", "utilisateur",
                           "branding", "expérience", "interface", "visuel", "graphique"]

        # Priorité au dernier message
        if any(kw in last_message for kw in tech_keywords) and "tech" not in excluded_agents:
            return "tech"
        if any(kw in last_message for kw in business_keywords) and "strategie" not in excluded_agents:
            return "strategie"
        if any(kw in last_message for kw in creative_keywords) and "creatif" not in excluded_agents:
            return "creatif"

        # Sinon chercher dans tout le contexte récent
        if any(kw in context_lower for kw in tech_keywords) and "tech" not in excluded_agents:
            return "tech"
        if any(kw in context_lower for kw in business_keywords) and "strategie" not in excluded_agents:
            return "strategie"
        if any(kw in context_lower for kw in creative_keywords) and "creatif" not in excluded_agents:
            return "creatif"

        return None

    def _get_agent_response(self, agent_id: str, context: str) -> str:
        """
        Obtient la réponse d'un agent via CrewAI.

        Args:
            agent_id: Identifiant de l'agent
            context: Contexte de la conversation

        Returns:
            Réponse de l'agent
        """
        agent = self.agents[agent_id]

        # Créer une tâche pour l'agent
        task = Task(
            description=f"{context}\n\nRéponds selon ton expertise et ton rôle.",
            expected_output="Une intervention pertinente et concise (max 5-6 phrases)",
            agent=agent
        )

        # Exécuter avec CrewAI
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()

        # Extraire le texte de la réponse
        if hasattr(result, 'raw'):
            return result.raw
        else:
            return str(result)

    def _detect_consensus(self) -> bool:
        """
        Détecte si un consensus émerge de la conversation.

        Returns:
            True si consensus détecté
        """
        # Simple heuristique : consensus si 3+ derniers messages sont positifs
        if len(self.conversation_history) < 5:
            return False

        recent_messages = [entry["message"].lower() for entry in self.conversation_history[-3:]]

        positive_indicators = ["d'accord", "valide", "ok", "parfait", "exactement",
                              "je suis pour", "allons-y", "approuvé", "validé",
                              "consensus", "go"]

        positive_count = sum(
            1 for msg in recent_messages
            if any(indicator in msg for indicator in positive_indicators)
        )

        return positive_count >= 2

    def _check_facilitator_should_close(self) -> bool:
        """
        Vérifie si le facilitateur devrait clôturer la réunion.

        Returns:
            True si clôture recommandée
        """
        # Clôturer si :
        # 1. Consensus détecté
        if self._detect_consensus():
            return True

        # 2. Discussion trop longue (>20 interventions)
        if len(self.conversation_history) > 20:
            return True

        # 3. Plus d'activité depuis facilitateur
        facilitator_messages = [
            entry for entry in self.conversation_history
            if entry["agent"] == "facilitateur"
        ]

        if len(facilitator_messages) > 3 and "synthèse finale" in facilitator_messages[-1]["message"].lower():
            return True

        return False

    def run_meeting(self) -> str:
        """
        Lance et orchestre la réunion complète.

        Returns:
            Synthèse finale de la réunion
        """
        print("\n" + "=" * 80)
        print("🎯 RÉUNION MULTI-AGENTS")
        print("=" * 80)
        print(f"Objectif : {self.objective}")
        print("\nTapez votre message pour intervenir (ou 'exit' pour quitter)")
        print("=" * 80)

        # 1. Le facilitateur ouvre la réunion
        context = self._build_context()
        opening = self._get_agent_response("facilitateur", context)
        self.speak("facilitateur", opening)

        # 2. Boucle de conversation
        turn_count = 0
        max_turns = 30  # Limite de sécurité

        while self.meeting_active and turn_count < max_turns:
            turn_count += 1

            # Vérifier si l'humain veut intervenir
            human_input = self._get_human_input_async()

            if human_input:
                if human_input.lower() == "exit":
                    self.meeting_active = False
                    break

                self.speak("human", human_input)

            # Déterminer quel agent doit parler
            context = self._build_context()

            # Vérifier si le facilitateur doit clôturer
            if self._check_facilitator_should_close():
                closing = self._get_agent_response("facilitateur",
                                                   context + "\n\nFormalise la SYNTHÈSE FINALE et clôture la réunion.")
                self.speak("facilitateur", closing)
                self.meeting_active = False
                break

            # Sélection intelligente du prochain intervenant
            next_speaker = self._select_next_speaker(context)

            if next_speaker:
                response = self._get_agent_response(next_speaker, context)
                self.speak(next_speaker, response)
            elif turn_count % 5 == 0:
                # Seulement tous les 5 tours, le facilitateur synthétise si personne ne parle
                synthesis = self._get_agent_response("facilitateur",
                                                     context + "\n\nFais une synthèse rapide des points clés.")
                self.speak("facilitateur", synthesis)

        # 3. Synthèse finale
        if turn_count >= max_turns:
            final_context = self._build_context()
            final_summary = self._get_agent_response("facilitateur",
                                                     final_context + "\n\nFormalise la SYNTHÈSE FINALE.")
            self.speak("facilitateur", final_summary)

        print("\n" + "=" * 80)
        print("✅ RÉUNION TERMINÉE")
        print("=" * 80)

        return self._generate_summary()

    def _get_human_input_async(self) -> Optional[str]:
        """
        Récupère l'input humain de manière non-bloquante.

        Returns:
            Input de l'humain ou None
        """
        try:
            print(f"\n{HUMAN_COLOR}[Votre intervention (Entrée pour passer)] :{RESET_COLOR} ", end="")
            user_input = input().strip()
            return user_input if user_input else None
        except KeyboardInterrupt:
            return "exit"

    def _generate_summary(self) -> str:
        """
        Génère un résumé structuré de la réunion.

        Returns:
            Résumé formaté
        """
        summary = f"\n📋 RÉSUMÉ DE LA RÉUNION\n"
        summary += f"Objectif : {self.objective}\n"
        summary += f"Nombre d'interventions : {len(self.conversation_history)}\n\n"

        summary += "Participants :\n"
        participants = set(entry["agent"] for entry in self.conversation_history)
        for participant in participants:
            if participant == "human":
                summary += "  - Humain\n"
            else:
                summary += f"  - {AGENTS_CONFIG[participant]['name']}\n"

        return summary
