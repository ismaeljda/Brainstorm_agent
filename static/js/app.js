// Variables globales
let audioContext;
let audioInput;
let recorder;
let audioChunks = [];
let isRecording = false;
let conversationHistory = []; // Historique de la conversation
let autoRestart = true; // Redémarrer automatiquement après chaque réponse
let silenceDetectionEnabled = true; // Activer la détection de silence
let silenceTimer = null;
let analyser = null;
let silenceThreshold = 0.02; // Seuil de silence (augmenté pour mobile)
let silenceDuration = 2500; // Durée de silence avant arrêt (ms) - augmenté pour laisser le temps de parler
let recordingStartTime = null; // Timestamp du début d'enregistrement
let initialGracePeriod = 1000; // Ne pas détecter le silence pendant la première seconde

// Éléments DOM
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const statusBox = document.getElementById('status');
const statusText = document.getElementById('status-text');
const transcriptionCard = document.getElementById('transcription-card');
const transcriptionText = document.getElementById('transcription-text');
const translationCard = document.getElementById('translation-card');
const translationText = document.getElementById('translation-text');
const audioCard = document.getElementById('audio-card');
const audioPlayer = document.getElementById('audio-player');
const logContent = document.getElementById('log-content');

// Gestion des logs
function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString('fr-FR');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span>${message}`;
    logContent.insertBefore(logEntry, logContent.firstChild);
}

// Mise à jour du statut
function updateStatus(icon, text, className = '') {
    statusBox.className = 'status-box ' + className;
    statusBox.querySelector('.status-icon').textContent = icon;
    statusText.textContent = text;
}

// Classe pour enregistrer en WAV
class AudioRecorder {
    constructor(source, cfg) {
        this.config = cfg || {};
        this.bufferLen = this.config.bufferLen || 4096;
        this.numChannels = this.config.numChannels || 1;
        this.sampleRate = source.context.sampleRate;

        this.context = source.context;
        this.node = this.context.createScriptProcessor(this.bufferLen, this.numChannels, this.numChannels);

        this.buffers = [];
        for (let i = 0; i < this.numChannels; i++) {
            this.buffers[i] = [];
        }

        const self = this;
        this.node.onaudioprocess = function(e) {
            if (!self.recording) return;

            for (let i = 0; i < self.numChannels; i++) {
                self.buffers[i].push(new Float32Array(e.inputBuffer.getChannelData(i)));
            }
        };

        source.connect(this.node);
        this.node.connect(this.context.destination);
    }

    record() {
        this.recording = true;
    }

    stop() {
        this.recording = false;
    }

    clear() {
        for (let i = 0; i < this.numChannels; i++) {
            this.buffers[i] = [];
        }
    }

    getBuffer() {
        const buffers = [];
        for (let i = 0; i < this.numChannels; i++) {
            buffers.push(this.mergeBuffers(this.buffers[i]));
        }
        return buffers;
    }

    mergeBuffers(bufferArray) {
        const length = bufferArray.reduce((acc, buf) => acc + buf.length, 0);
        const result = new Float32Array(length);
        let offset = 0;
        for (let i = 0; i < bufferArray.length; i++) {
            result.set(bufferArray[i], offset);
            offset += bufferArray[i].length;
        }
        return result;
    }

    exportWAV() {
        const buffers = this.getBuffer();
        const interleaved = this.interleave(buffers);
        const dataview = this.encodeWAV(interleaved);
        const audioBlob = new Blob([dataview], { type: 'audio/wav' });
        return audioBlob;
    }

    interleave(buffers) {
        if (this.numChannels === 1) {
            return buffers[0];
        }
        const length = buffers[0].length;
        const result = new Float32Array(length * this.numChannels);
        for (let i = 0; i < length; i++) {
            for (let j = 0; j < this.numChannels; j++) {
                result[i * this.numChannels + j] = buffers[j][i];
            }
        }
        return result;
    }

    encodeWAV(samples) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);

        // RIFF identifier
        this.writeString(view, 0, 'RIFF');
        // file length
        view.setUint32(4, 36 + samples.length * 2, true);
        // RIFF type
        this.writeString(view, 8, 'WAVE');
        // format chunk identifier
        this.writeString(view, 12, 'fmt ');
        // format chunk length
        view.setUint32(16, 16, true);
        // sample format (raw)
        view.setUint16(20, 1, true);
        // channel count
        view.setUint16(22, this.numChannels, true);
        // sample rate
        view.setUint32(24, this.sampleRate, true);
        // byte rate (sample rate * block align)
        view.setUint32(28, this.sampleRate * this.numChannels * 2, true);
        // block align (channel count * bytes per sample)
        view.setUint16(32, this.numChannels * 2, true);
        // bits per sample
        view.setUint16(34, 16, true);
        // data chunk identifier
        this.writeString(view, 36, 'data');
        // data chunk length
        view.setUint32(40, samples.length * 2, true);

        // write the PCM samples
        this.floatTo16BitPCM(view, 44, samples);

        return view;
    }

    writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    floatTo16BitPCM(output, offset, input) {
        for (let i = 0; i < input.length; i++, offset += 2) {
            const s = Math.max(-1, Math.min(1, input[i]));
            output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
    }
}

// Détection de silence
function checkAudioLevel() {
    if (!analyser || !isRecording) return;

    const bufferLength = analyser.fftSize;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(dataArray);

    // Calculer le volume moyen (RMS normalisé entre 0 et 1)
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
        const normalized = (dataArray[i] - 128) / 128; // Normalise entre -1 et 1
        sum += normalized * normalized;
    }
    const rms = Math.sqrt(sum / bufferLength);

    // Log pour debug mobile (seulement occasionnellement)
    if (Math.random() < 0.03) {
        console.log('🎤 Niveau audio RMS:', rms.toFixed(4), '| Seuil:', silenceThreshold);
    }

    // Grace period: Ne pas détecter le silence pendant la première seconde
    const timeSinceStart = Date.now() - recordingStartTime;
    if (timeSinceStart < initialGracePeriod) {
        // Pendant le grace period, continuer sans détecter le silence
        if (isRecording) {
            requestAnimationFrame(checkAudioLevel);
        }
        return;
    }

    // Détection de silence (seuil augmenté pour mobile)
    if (rms < silenceThreshold) {
        // Silence détecté
        if (!silenceTimer && silenceDetectionEnabled) {
            silenceTimer = setTimeout(() => {
                if (isRecording) {
                    addLog('🔇 Silence détecté - Arrêt automatique', 'info');
                    stopRecording();
                }
            }, silenceDuration);
        }
    } else {
        // Son détecté - annuler le timer de silence
        if (silenceTimer) {
            clearTimeout(silenceTimer);
            silenceTimer = null;
        }
    }

    // Continuer à vérifier
    if (isRecording) {
        requestAnimationFrame(checkAudioLevel);
    }
}

// Démarrer l'enregistrement
async function startRecording() {
    try {
        addLog('Demande d\'accès au microphone...', 'info');

        // Demander l'accès au microphone
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });

        addLog('✓ Microphone activé', 'success');

        // Créer l'AudioContext
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioInput = audioContext.createMediaStreamSource(stream);

        // Créer l'analyseur pour la détection de silence
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.8;
        audioInput.connect(analyser);

        // Créer le recorder
        recorder = new AudioRecorder(audioInput, {
            numChannels: 1,
            bufferLen: 4096
        });

        // Démarrer l'enregistrement
        recorder.clear();
        recorder.record();
        isRecording = true;
        recordingStartTime = Date.now(); // Initialiser le timestamp pour le grace period

        // Démarrer la détection de silence
        if (silenceDetectionEnabled) {
            silenceTimer = null;
            checkAudioLevel();
        }

        // Mettre à jour l'interface
        startBtn.disabled = true;
        stopBtn.disabled = false;
        updateStatus('🔴', 'Parlez... (arrêt auto après silence)', 'recording');
        addLog('🎤 Enregistrement démarré - Détection de silence active', 'success');

    } catch (error) {
        console.error('Erreur microphone:', error);
        addLog('❌ Erreur: ' + error.message, 'error');
        updateStatus('❌', 'Erreur d\'accès au microphone', '');
    }
}

// Arrêter l'enregistrement
function stopRecording() {
    if (recorder && isRecording) {
        recorder.stop();
        isRecording = false;

        // Arrêter la détection de silence
        if (silenceTimer) {
            clearTimeout(silenceTimer);
            silenceTimer = null;
        }

        // Mettre à jour l'interface
        startBtn.disabled = false;
        stopBtn.disabled = true;
        updateStatus('⏳', 'Traitement en cours...', 'processing');

        // Traiter l'audio
        processAudio();
    }
}

// Traiter l'audio enregistré AVEC STREAMING
async function processAudio() {
    try {
        // Obtenir le WAV
        const wavBlob = recorder.exportWAV();

        addLog(`📦 Audio capturé: ${(wavBlob.size / 1024).toFixed(2)} KB`, 'info');

        if (wavBlob.size < 100) {
            throw new Error('Audio trop court ou vide');
        }

        const formData = new FormData();
        formData.append('audio', wavBlob, 'recording.wav');

        // Étape 1: Transcription
        updateStatus('📝', 'Transcription en cours...', 'processing');
        addLog('Envoi à Whisper pour transcription...', 'info');

        const transcribeResponse = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData
        });

        const transcribeData = await transcribeResponse.json();

        if (!transcribeData.success) {
            throw new Error(transcribeData.error || 'Erreur de transcription');
        }

        const userMessage = transcribeData.text;
        addLog('✓ Vous: ' + userMessage, 'success');

        // Afficher le message utilisateur
        transcriptionText.textContent = userMessage;
        transcriptionCard.style.display = 'block';

        // Ajouter le message utilisateur à l'historique
        conversationHistory.push({
            role: 'user',
            content: userMessage
        });

        // Étape 2 & 3: Streaming intelligent - GPT génère + Audio phrase par phrase
        updateStatus('🤖', 'L\'agent réfléchit...', 'processing');
        addLog('💭 Streaming intelligent activé...', 'info');

        let agentResponse = '';
        let audioQueue = [];
        let isPlaying = false;
        let streamDone = false;

        translationCard.style.display = 'block';

        // Fonction pour jouer le prochain audio dans la queue (OPTIMISÉE)
        const playNext = () => {
            if (audioQueue.length > 0 && !isPlaying) {
                isPlaying = true;
                const audioData = audioQueue.shift();

                // Décoder le base64 en blob
                const binaryString = atob(audioData);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const audioBlob = new Blob([bytes], { type: 'audio/mpeg' });
                const audioUrl = URL.createObjectURL(audioBlob);

                audioPlayer.src = audioUrl;
                audioCard.style.display = 'block';

                // Jouer immédiatement sans attendre
                audioPlayer.play().catch(err => {
                    console.error('Erreur lecture audio:', err);
                    isPlaying = false;
                    playNext(); // Essayer le suivant
                });

                // Quand ce chunk est terminé, jouer le suivant IMMÉDIATEMENT
                audioPlayer.onended = () => {
                    isPlaying = false;
                    URL.revokeObjectURL(audioUrl);

                    // Jouer immédiatement le prochain s'il existe
                    if (audioQueue.length > 0) {
                        setTimeout(() => playNext(), 50); // Délai minimal pour éviter les bugs
                    } else if (streamDone) {
                        // Tout est terminé
                        updateStatus('✅', 'À vous !', '');
                        addLog('✓ Tour terminé', 'success');

                        // Redémarrer automatiquement
                        if (autoRestart) {
                            setTimeout(() => {
                                addLog('🔄 Redémarrage automatique...', 'info');
                                startRecording();
                            }, 1000);
                        }
                    }
                };
            }
        };

        // Streamer la réponse
        const response = await fetch('/api/chat_and_speak_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: userMessage,
                history: conversationHistory
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let firstAudioReceived = false;

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));

                        if (data.type === 'text') {
                            // Afficher le texte en temps réel
                            agentResponse += data.content;
                            translationText.textContent = agentResponse;
                        } else if (data.type === 'audio') {
                            // Ajouter l'audio à la queue
                            console.log('🎵 Audio reçu, taille:', data.content.length, 'bytes');
                            audioQueue.push(data.content);

                            if (!firstAudioReceived) {
                                firstAudioReceived = true;
                                updateStatus('🔊', 'Lecture de la réponse...', 'speaking');
                                addLog('✓ Premier audio reçu, lecture...', 'success');
                                console.log('▶️ Lancement de la lecture audio');
                                playNext();
                            } else {
                                console.log('📥 Audio ajouté à la queue, total:', audioQueue.length);
                            }
                        } else if (data.type === 'done') {
                            streamDone = true;
                            addLog('✓ Agent: ' + agentResponse, 'success');

                            // Si plus d'audio en attente et qu'on ne joue rien, terminer
                            if (audioQueue.length === 0 && !isPlaying) {
                                updateStatus('✅', 'À vous !', '');
                                addLog('✓ Tour terminé', 'success');

                                if (autoRestart) {
                                    setTimeout(() => {
                                        addLog('🔄 Redémarrage automatique...', 'info');
                                        startRecording();
                                    }, 1000);
                                }
                            }
                        } else if (data.type === 'error') {
                            throw new Error(data.content);
                        }
                    } catch (parseError) {
                        console.error('Parse error:', parseError);
                    }
                }
            }
        }

        // Ajouter la réponse complète à l'historique
        conversationHistory.push({
            role: 'assistant',
            content: agentResponse
        });

    } catch (error) {
        console.error('Erreur de traitement:', error);
        addLog('❌ Erreur: ' + error.message, 'error');
        updateStatus('❌', 'Erreur: ' + error.message, '');
        startBtn.disabled = false;
    }
}

// Event listeners
startBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);

// Toggle de la détection de silence
const silenceToggle = document.getElementById('silence-detection-toggle');
if (silenceToggle) {
    silenceToggle.addEventListener('change', (e) => {
        silenceDetectionEnabled = e.target.checked;
        addLog(silenceDetectionEnabled ? '✓ Détection de silence activée' : '⚠️ Détection de silence désactivée', 'info');
    });
}

// Raccourci clavier: Espace pour démarrer/arrêter
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !e.repeat) {
        e.preventDefault();
        if (!isRecording && !startBtn.disabled) {
            startRecording();
        }
    }
});

document.addEventListener('keyup', (e) => {
    if (e.code === 'Space' && isRecording) {
        e.preventDefault();
        stopRecording();
    }
});

// Message de bienvenue
addLog('🎉 Application prête ! Streaming intelligent phrase-par-phrase activé ⚡', 'success');
