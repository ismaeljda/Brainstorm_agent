# 🔍 Nouvel Agent : INSPECTEUR

## Caractéristiques

### Rôle
Agent de recherche et d'investigation qui:
- Effectue des recherches internet quand l'utilisateur le demande
- Répond aux questions factuelles et générales
- Sert de **filet de sécurité** quand aucun autre agent n'est pertinent

### Personnalité
- Curieux et méthodique
- Précis et factuel
- Ton neutre et informatif
- Style: "D'après mes recherches..." / "Voici ce que j'ai trouvé..."

### Couleur
- **Rouge (#ff0000)** - Pour se distinguer visuellement

### Intégration
✅ Ajouté dans `config.py`
✅ Prompt créé dans `prompts.py`
✅ Intégré dans l'orchestrateur
✅ Interface carousel avec navigation
✅ Style brutalist conservé

## Interface Carousel

### Nouveau Design
- **Scroll horizontal** avec 5 agents
- **Boutons de navigation** : PREV / NEXT
- **Style brutalist** : bordures noires 2px, fond blanc
- **Responsive** : s'adapte à toutes les tailles

### Agents disponibles
1. Facilitateur (blanc) - Sélectionné par défaut
2. Stratège (bleu)
3. Tech Lead (vert)
4. Creative (violet)
5. **Inspecteur (rouge)** - NOUVEAU

## Utilisation

L'inspecteur intervient automatiquement quand:
- User demande une recherche internet
- Question factuelle posée
- Aucun autre agent n'est pertinent

Exemple: "Quelles sont les tendances IA en 2025 ?"
→ L'Inspecteur répond avec des faits et données

