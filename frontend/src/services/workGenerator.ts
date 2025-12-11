import type { WorkDeliverable, ConsultationNote, Agent } from '../types';

const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY || '';

interface GenerateWorkParams {
  agent: Agent;
  context: string;
  conversationTranscript: string;
  consultationNote: ConsultationNote;
}

const WORK_PROMPTS = {
  alexandre: {
    type: 'strategy' as const,
    systemPrompt: `Tu es Alexandre, consultant stratégique senior. Suite à une consultation vocale avec un client, tu dois produire un livrable écrit professionnel et actionnable.

Tu dois créer un document stratégique structuré en markdown comprenant:
1. Résumé exécutif (2-3 paragraphes)
2. Analyse de la situation actuelle (forces, faiblesses, opportunités, menaces)
3. Recommandations stratégiques priorisées (top 3-5 avec rationale)
4. Plan d'action détaillé sur 90 jours (avec timeline et responsabilités)
5. Métriques de succès et KPIs à suivre
6. Risques identifiés et plans de mitigation

Le document doit être concret, chiffré quand possible, et directement utilisable par le client pour prendre des décisions.`,
  },
  marie: {
    type: 'marketing' as const,
    systemPrompt: `Tu es Marie, experte en marketing digital. Suite à une consultation, tu dois produire un plan marketing actionnable.

Tu dois créer un document marketing structuré en markdown comprenant:
1. Résumé de la stratégie marketing recommandée
2. Analyse du funnel actuel et opportunités d'optimisation
3. Plan d'acquisition client détaillé (canaux, budget, timeline)
4. Stratégie de contenu et messaging
5. Campagnes prioritaires à lancer (3-5 campagnes avec briefs)
6. Budget prévisionnel et ROI attendu
7. Dashboard de métriques à suivre (CAC, conversion rates, etc.)

Inclus des templates concrets, des exemples de copy, et des recommendations d'outils.`,
  },
  thomas: {
    type: 'innovation' as const,
    systemPrompt: `Tu es Thomas, expert en innovation. Suite à une consultation, tu dois produire un plan d'innovation.

Tu dois créer un document innovation structuré en markdown comprenant:
1. Opportunités d'innovation identifiées
2. Analyse des tendances du marché pertinentes
3. Propositions d'innovation concrètes (3-5 idées détaillées)
4. Roadmap de transformation sur 6-12 mois
5. Ressources nécessaires et estimation d'effort
6. Métriques d'impact et critères de succès
7. Quick wins vs projets long terme

Le document doit balancer créativité et pragmatisme, avec des étapes concrètes de mise en œuvre.`,
  },
  sophie: {
    type: 'financial' as const,
    systemPrompt: `Tu es Sophie, consultante financière. Suite à une consultation, tu dois produire une analyse financière.

Tu dois créer un document financier structuré en markdown comprenant:
1. Analyse de la santé financière actuelle
2. Optimisations financières recommandées (top 5)
3. Projections financières sur 12-24 mois (scenarios optimiste/réaliste/pessimiste)
4. Plan de gestion de trésorerie
5. Recommandations de pricing et unit economics
6. KPIs financiers à monitorer (dashboard mensuel)
7. Stratégie de levée de fonds si pertinent

Tous les chiffres doivent être détaillés, sourcés, et les calculs expliqués.`,
  },
};

export async function generateWorkDeliverable(params: GenerateWorkParams): Promise<WorkDeliverable> {
  const { agent, context, conversationTranscript, consultationNote } = params;
  const workPrompt = WORK_PROMPTS[agent.id as keyof typeof WORK_PROMPTS];

  if (!workPrompt) {
    throw new Error(`No work generator configured for agent ${agent.id}`);
  }

  const userPrompt = `# Contexte du projet client
${context}

# Notes de consultation
**Agent:** ${consultationNote.agentName}
**Date:** ${consultationNote.timestamp}

**Résumé:** ${consultationNote.summary}

**Points clés discutés:**
${consultationNote.keyPoints.map(p => `- ${p}`).join('\n')}

**Recommandations données:**
${consultationNote.recommendations.map(r => `- ${r}`).join('\n')}

**Prochaines étapes:**
${consultationNote.nextSteps.map(s => `- ${s}`).join('\n')}

# Extrait de la conversation
${conversationTranscript}

---

Produis maintenant un livrable professionnel et actionnable basé sur cette consultation. Le document doit être en markdown, bien structuré, et directement utilisable par le client.`;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content: workPrompt.systemPrompt,
          },
          {
            role: 'user',
            content: userPrompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 3000,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.statusText}`);
    }

    const data = await response.json();
    const content = data.choices[0].message.content;

    const deliverable: WorkDeliverable = {
      id: `deliverable-${Date.now()}`,
      type: workPrompt.type,
      title: `${agent.name} - ${workPrompt.type === 'strategy' ? 'Plan Stratégique' : workPrompt.type === 'marketing' ? 'Plan Marketing' : workPrompt.type === 'innovation' ? 'Plan Innovation' : 'Analyse Financière'}`,
      content,
      agentId: agent.id,
      createdAt: new Date().toISOString(),
      status: 'ready',
    };

    return deliverable;
  } catch (error) {
    console.error('Error generating work deliverable:', error);
    throw error;
  }
}

export function downloadBusinessPlan(
  projectName: string,
  context: string,
  consultations: ConsultationNote[],
  deliverables: WorkDeliverable[]
): void {
  const markdown = `# Business Plan - ${projectName}

*Généré le ${new Date().toLocaleDateString('fr-FR', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
})}*

---

## Contexte du Projet

${context}

---

${consultations.length > 0 ? `
## Consultations Réalisées

${consultations.map((consultation, idx) => `
### ${idx + 1}. Consultation avec ${consultation.agentName}
*${new Date(consultation.timestamp).toLocaleDateString('fr-FR', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit'
})}*

**Résumé :** ${consultation.summary}

**Points clés :**
${consultation.keyPoints.map(p => `- ${p}`).join('\n')}

**Recommandations :**
${consultation.recommendations.map(r => `- ${r}`).join('\n')}

**Prochaines étapes :**
${consultation.nextSteps.map(s => `- ${s}`).join('\n')}

---
`).join('\n')}
` : ''}

${deliverables.length > 0 ? `
## Livrables Produits

${deliverables.map((deliverable, idx) => `
### ${idx + 1}. ${deliverable.title}
*Créé le ${new Date(deliverable.createdAt).toLocaleDateString('fr-FR')}*

${deliverable.content}

---
`).join('\n')}
` : ''}

---

*Document généré par la plateforme Business Plan AI*
`;

  // Créer et télécharger le fichier
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `business-plan-${projectName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.md`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
