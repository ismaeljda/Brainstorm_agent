# 🎙️ Configuration de l'Interface Vocale ElevenLabs

Guide pour intégrer la voix à ton système multi-agents de brainstorming.

## 📋 Prérequis

1. **Compte ElevenLabs**
   - Crée un compte sur [elevenlabs.io](https://elevenlabs.io)
   - Récupère ta clé API dans les paramètres

2. **Microphone fonctionnel**
   - Assure-toi que ton micro est configuré et autorisé

## 🚀 Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Note pour macOS**: Si `pyaudio` pose problème, installe d'abord PortAudio:
```bash
brew install portaudio
pip install pyaudio
```

**Note pour Linux**:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### 2. Configurer les clés API

Copie le fichier `.env.example` en `.env`:
```bash
cp .env.example src/.env
```

Édite le fichier `src/.env` et ajoute tes clés:
```env
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=votre-cle-elevenlabs-ici
```

### 3. (Optionnel) Choisir une voix

Par défaut, le système utilise une voix anglaise. Pour utiliser une voix française:

1. Liste les voix disponibles:
```bash
curl -X GET https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: VOTRE_CLE_API"
```

2. Copie l'ID de la voix souhaitée et ajoute-le dans `.env`:
```env
ELEVENLABS_VOICE_ID=l_id_de_la_voix_choisie
```

Voix recommandées pour le français:
- **Antoine** (voix masculine française)
- **Amélie** (voix féminine française)

## 🧪 Tester l'Interface Vocale

### Test rapide (text-to-speech uniquement)

```bash
python test_voice.py
# Choisis l'option 3
```

Cela teste uniquement la synthèse vocale sans utiliser le micro.

### Test simple (un échange)

```bash
python test_voice.py
# Choisis l'option 1
```

Le système va:
1. 🎤 Écouter ce que tu dis
2. 📝 Transcrire en texte
3. 🤖 Générer une réponse
4. 🔊 La lire à voix haute

### Test complet (conversation)

```bash
python test_voice.py
# Choisis l'option 2
```

Conversation en boucle. Dis "stop" ou "quitter" pour terminer.

## 🔧 Intégration avec tes Agents CrewAI

Le fichier `voice_interface.py` fournit une classe `VoiceInterface` avec:

### Méthodes principales

```python
from voice_interface import VoiceInterface

# Initialiser
voice = VoiceInterface()

# Écouter l'utilisateur (speech-to-text)
user_text = voice.listen()

# Faire parler l'agent (text-to-speech)
voice.speak("Voici ma réponse")

# Conversation complète avec callback
def my_agent_callback(user_input: str) -> str:
    # Ton code d'agent CrewAI ici
    return "Réponse de l'agent"

voice.conversation_loop(my_agent_callback)
```

### Exemple d'intégration

```python
from voice_interface import VoiceInterface
from orchestrator import Orchestrator

# Créer l'interface vocale
voice = VoiceInterface()

# Message de bienvenue
voice.speak("Bonjour ! Décrivez votre projet.")

# Écouter l'objectif
objective = voice.listen()

# Lancer les agents CrewAI
orchestrator = Orchestrator(objective=objective)
result = orchestrator.run_meeting()

# Lire le résultat
voice.speak(result)
```

## 🎯 Workflow Complet

```
┌─────────────────────────────────────────────────────────────┐
│  Utilisateur parle                                          │
│  "J'ai besoin d'un spécialiste marketing et d'un dev"       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Speech-to-Text (Google/Whisper)                            │
│  Transcription: "J'ai besoin d'un spécialiste..."           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Système Multi-Agents (CrewAI)                              │
│  • Créer agent Marketing                                    │
│  • Créer agent Dev                                          │
│  • Brainstorm collaboratif                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Résultat texte des agents                                  │
│  "Nous avons analysé votre projet. Le marketing..."         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Text-to-Speech (ElevenLabs)                                │
│  🔊 Lecture de la réponse vocale                            │
└─────────────────────────────────────────────────────────────┘
```

## 🐛 Dépannage

### Erreur: "ELEVENLABS_API_KEY non définie"
→ Vérifie que tu as bien créé le fichier `src/.env` avec ta clé API

### Erreur avec PyAudio
→ Sur macOS: `brew install portaudio && pip install pyaudio`
→ Sur Linux: `sudo apt-get install portaudio19-dev`

### Le micro ne fonctionne pas
→ Vérifie les permissions du système pour accéder au microphone
→ Sur macOS: Préférences Système → Sécurité → Microphone

### La voix est en anglais
→ Configure `ELEVENLABS_VOICE_ID` avec une voix française dans `.env`

### Latence trop importante
→ Utilise `gpt-4o-mini` au lieu de `gpt-4o` pour des réponses plus rapides
→ Considère streaming avec ElevenLabs (feature avancée)

## 💡 Prochaines Étapes

1. ✅ Teste l'interface vocale avec `test_voice.py`
2. Intègre la voix dans `main.py` avec tes agents existants
3. Ajoute la détection automatique de langue (français/anglais)
4. Implémente le streaming pour réduire la latence
5. Ajoute des voix différentes pour chaque agent (Marketing, Dev, etc.)

## 📚 Resources

- [Documentation ElevenLabs](https://elevenlabs.io/docs)
- [Voices disponibles](https://elevenlabs.io/voice-library)
- [API Reference](https://elevenlabs.io/docs/api-reference)
