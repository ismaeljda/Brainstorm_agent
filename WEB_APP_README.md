# 🎙️ Interface Web Vocale Interactive

Application web permettant de parler en français et d'écouter la traduction en anglais avec une interface moderne et intuitive.

## 🚀 Démarrage Rapide

### 1. Activer l'environnement virtuel

```bash
source venv/bin/activate
```

### 2. Lancer l'application

```bash
python app.py
```

### 3. Ouvrir dans le navigateur

Ouvre ton navigateur et va sur: **http://localhost:5000**

## 🎯 Comment utiliser l'interface

### Méthode 1: Boutons

1. **Clique sur "Commencer à parler"** 🎤
   - Ton navigateur va demander l'autorisation d'accéder au micro
   - Autorise l'accès

2. **Parle en français** 🗣️
   - L'enregistrement est en cours (indicateur rouge)

3. **Clique sur "Arrêter"** ⏹️
   - L'application va automatiquement:
     - Transcrire ce que tu as dit (Whisper)
     - Traduire en anglais (GPT)
     - Générer l'audio (ElevenLabs)
     - Le jouer automatiquement 🔊

### Méthode 2: Barre d'espace (plus rapide!)

1. **Maintiens la barre d'espace** pour enregistrer
2. **Relâche** pour arrêter et lancer le traitement

## 📋 Workflow complet

```
┌─────────────────────────────────────────────────────────────┐
│  1. Clique "Commencer à parler"                             │
│     ↓                                                        │
│  2. Parle en français dans ton micro                        │
│     ↓                                                        │
│  3. Clique "Arrêter"                                        │
│     ↓                                                        │
│  4. Transcription (Whisper) → Affichage en français         │
│     ↓                                                        │
│  5. Traduction (GPT) → Affichage en anglais                 │
│     ↓                                                        │
│  6. Synthèse vocale (ElevenLabs) → Lecture automatique      │
│     ↓                                                        │
│  7. ✅ Terminé ! Prêt pour un nouvel enregistrement         │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 Fonctionnalités de l'interface

### Indicateurs visuels
- **🎤 Prêt à écouter** (violet) - État initial
- **🔴 Enregistrement en cours** (rouge animé) - Tu parles
- **⏳ Traitement en cours** (bleu) - Transcription/Traduction
- **🔊 Lecture de la réponse** (vert) - Audio en cours
- **✅ Terminé** (gris) - Prêt pour la prochaine

### Affichage des résultats
- **Transcription** - Ce que tu as dit en français
- **Traduction** - La version anglaise
- **Lecteur audio** - Contrôles pour rejouer la réponse

### Log d'activité
Un journal en temps réel de toutes les actions:
- ✓ Succès (vert)
- ⏳ Info (bleu)
- ❌ Erreurs (rouge)

## 🛠️ Architecture technique

### Backend (Flask)
- **`/api/transcribe`** - Transcrit l'audio en texte (Whisper)
- **`/api/translate`** - Traduit français → anglais (GPT)
- **`/api/speak`** - Génère l'audio de la traduction (ElevenLabs)

### Frontend (Vanilla JS)
- Enregistrement audio via `MediaRecorder API`
- Appels asynchrones aux endpoints
- Interface réactive et moderne

## 🔧 Personnalisation

### Changer la voix ElevenLabs

Modifie dans [src/.env](src/.env):
```env
ELEVENLABS_VOICE_ID=ton-voice-id-ici
```

Liste des voix disponibles:
```bash
curl -X GET https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: VOTRE_CLE_API"
```

### Changer le modèle GPT

Dans [app.py](app.py:105), ligne 105:
```python
model="gpt-4o-mini",  # Change en "gpt-4o" pour plus de qualité
```

### Changer la langue de transcription

Dans [app.py](app.py:44), ligne 44:
```python
language="fr"  # Change en "en" pour l'anglais, etc.
```

## 🐛 Dépannage

### Le micro ne fonctionne pas
- Vérifie que tu as autorisé l'accès au micro dans ton navigateur
- Chrome/Edge: Clique sur l'icône de cadenas à gauche de l'URL
- Firefox: Clique sur l'icône de micro dans la barre d'adresse
- Safari: Préférences → Sites web → Microphone

### Erreur "ELEVENLABS_API_KEY non définie"
- Vérifie que le fichier `src/.env` existe et contient ta clé
- Redémarre l'application après avoir modifié `.env`

### Erreur CORS
- L'app Flask a CORS activé par défaut
- Si problème, vérifie que tu accèdes bien via `http://localhost:5000`

### Audio ne se joue pas
- Vérifie que ton navigateur supporte l'audio MP3
- Essaie dans un autre navigateur (Chrome recommandé)
- Vérifie que le son n'est pas coupé

## 📱 Compatibilité navigateurs

| Navigateur | Desktop | Mobile |
|------------|---------|--------|
| Chrome     | ✅      | ✅     |
| Firefox    | ✅      | ✅     |
| Safari     | ✅      | ⚠️     |
| Edge       | ✅      | ✅     |

⚠️ Safari mobile peut avoir des limitations sur l'autoplay audio

## 🔐 Sécurité

**IMPORTANT**: Cette app est pour développement/hackathon uniquement!

Pour la production:
- ❌ Ne jamais exposer les clés API au frontend
- ✅ Ajouter authentification
- ✅ Limiter le taux de requêtes
- ✅ Valider et assainir les entrées
- ✅ Utiliser HTTPS

## 🎯 Prochaines étapes pour ton hackathon

1. **Multi-agents**: Remplace l'agent traducteur par tes agents de brainstorming
2. **Sélection de rôles**: Interface pour choisir quels agents tu veux (Marketing, Dev, etc.)
3. **Historique**: Sauvegarder les conversations
4. **Voix par agent**: Une voix différente pour chaque rôle
5. **Mode débat**: Les agents discutent entre eux vocalement

## 📚 Exemple de code pour intégrer tes agents CrewAI

Dans [app.py](app.py:78), remplace la fonction `translate_text`:

```python
@app.route('/api/agent', methods=['POST'])
def run_agent():
    """Exécute tes agents CrewAI."""
    try:
        data = request.json
        user_input = data.get('text', '')

        # Créer tes agents
        from orchestrator import Orchestrator
        orchestrator = Orchestrator(objective=user_input)

        # Lancer la réunion
        result = orchestrator.run_meeting()

        return jsonify({
            'success': True,
            'response': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

Puis dans [static/js/app.js](static/js/app.js:129), change l'appel API.

---

**Bon hackathon ! 🚀**
