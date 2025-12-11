import type { WorkDeliverable, ConsultationNote, Agent } from '../types';

const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY || '';

interface GenerateWorkParams {
  agent: Agent;
  context: string;
  conversationTranscript: string;
  consultationNote: ConsultationNote;
}

const WORK_PROMPTS = {
  professor: {
    type: 'lesson' as const,
    systemPrompt: `Tu es Professeur Martin, un enseignant pédagogue. Suite à une leçon avec un étudiant, tu dois produire un document récapitulatif pédagogique.

Tu dois créer un document de leçon structuré en markdown comprenant:
1. Résumé de la leçon (2-3 paragraphes)
2. Concepts clés abordés (avec définitions claires)
3. Exemples concrets et analogies utilisées
4. Points importants à retenir
5. Exercices recommandés pour s'entraîner
6. Conseils pour réviser efficacement
7. Prochaines étapes d'apprentissage

Le document doit être clair, pédagogique, encourageant et adapté au niveau de l'étudiant.`,
  },
};

export async function generateWorkDeliverable(params: GenerateWorkParams): Promise<WorkDeliverable> {
  const { agent, context, conversationTranscript, consultationNote } = params;
  const workPrompt = WORK_PROMPTS[agent.id as keyof typeof WORK_PROMPTS];

  if (!workPrompt) {
    throw new Error(`No work generator configured for agent ${agent.id}`);
  }

  const userPrompt = `# Contexte de l'étudiant
${context}

# Notes de la leçon
**Professeur:** ${consultationNote.agentName}
**Date:** ${consultationNote.timestamp}

**Résumé:** ${consultationNote.summary}

**Points clés abordés:**
${consultationNote.keyPoints.map(p => `- ${p}`).join('\n')}

**Conseils donnés:**
${consultationNote.recommendations.map(r => `- ${r}`).join('\n')}

**Prochaines étapes:**
${consultationNote.nextSteps.map(s => `- ${s}`).join('\n')}

# Extrait de la conversation
${conversationTranscript}

---

Produis maintenant un document récapitulatif pédagogique basé sur cette leçon. Le document doit être en markdown, bien structuré, encourageant et directement utilisable par l'étudiant pour réviser.`;

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
      title: `${agent.name} - Résumé de Leçon`,
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
  const markdown = `# Notes de Cours - ${projectName}

*Généré le ${new Date().toLocaleDateString('fr-FR', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
})}*

---

## Mes Objectifs d'Apprentissage

${context}

---

${consultations.length > 0 ? `
## Leçons Suivies

${consultations.map((consultation, idx) => `
### ${idx + 1}. Leçon avec ${consultation.agentName}
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

**Conseils :**
${consultation.recommendations.map(r => `- ${r}`).join('\n')}

**À faire :**
${consultation.nextSteps.map(s => `- ${s}`).join('\n')}

---
`).join('\n')}
` : ''}

${deliverables.length > 0 ? `
## Résumés et Exercices

${deliverables.map((deliverable, idx) => `
### ${idx + 1}. ${deliverable.title}
*Créé le ${new Date(deliverable.createdAt).toLocaleDateString('fr-FR')}*

${deliverable.content}

---
`).join('\n')}
` : ''}

---

*Document généré par votre plateforme d'apprentissage*
`;

  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `notes-cours-${projectName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.md`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
