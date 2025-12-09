/**
 * Gestion du contexte organisationnel - Frontend
 */

let customFieldCount = 0;
let uploadedDocuments = [];

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadContext();
    setupDragAndDrop();
    setupFileInput();
});

/**
 * Charge le contexte existant depuis le serveur
 */
async function loadContext() {
    try {
        const response = await fetch('/api/context');

        if (response.ok) {
            const data = await response.json();

            if (data.context) {
                fillFormWithContext(data.context);
                showStatus('Contexte chargé avec succès', 'success');
            }
        }
    } catch (error) {
        console.error('Erreur lors du chargement:', error);
    }
}

/**
 * Remplit le formulaire avec les données du contexte
 */
function fillFormWithContext(context) {
    // Champs standards
    document.getElementById('company-name').value = context.company_name || '';
    document.getElementById('industry').value = context.industry || '';
    document.getElementById('strategic-goals').value = context.strategic_goals || '';
    document.getElementById('internal-constraints').value = context.internal_constraints || '';
    document.getElementById('target-audience').value = context.target_audience || '';
    document.getElementById('communication-tone').value = context.communication_tone || '';
    document.getElementById('free-description').value = context.free_description || '';

    // Champs personnalisés
    const container = document.getElementById('custom-fields-container');
    container.innerHTML = '';

    if (context.custom_fields) {
        Object.entries(context.custom_fields).forEach(([name, data]) => {
            addCustomField(name, data.field_type, data.value);
        });
    }

    // Documents
    if (context.documents) {
        uploadedDocuments = context.documents;
        renderDocumentsList();
    }
}

/**
 * Ajoute un champ personnalisé
 */
function addCustomField(name = '', type = 'text_short', value = '') {
    const container = document.getElementById('custom-fields-container');
    const fieldId = `custom-field-${customFieldCount++}`;

    const fieldDiv = document.createElement('div');
    fieldDiv.className = 'custom-field';
    fieldDiv.id = fieldId;

    fieldDiv.innerHTML = `
        <input type="text" placeholder="Nom du champ" value="${name}" data-field="name">
        <select data-field="type">
            <option value="text_short" ${type === 'text_short' ? 'selected' : ''}>Texte court</option>
            <option value="text_long" ${type === 'text_long' ? 'selected' : ''}>Texte long</option>
            <option value="number" ${type === 'number' ? 'selected' : ''}>Nombre</option>
            <option value="boolean" ${type === 'boolean' ? 'selected' : ''}>Oui/Non</option>
        </select>
        <input type="text" placeholder="Valeur" value="${value}" data-field="value">
        <button class="btn btn-danger" onclick="removeCustomField('${fieldId}')" style="padding: 10px 15px;">
            🗑️
        </button>
    `;

    container.appendChild(fieldDiv);
}

/**
 * Supprime un champ personnalisé
 */
function removeCustomField(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.remove();
    }
}

/**
 * Collecte les données du formulaire
 */
function collectFormData() {
    const context = {
        company_name: document.getElementById('company-name').value,
        industry: document.getElementById('industry').value,
        strategic_goals: document.getElementById('strategic-goals').value,
        internal_constraints: document.getElementById('internal-constraints').value,
        target_audience: document.getElementById('target-audience').value,
        communication_tone: document.getElementById('communication-tone').value,
        free_description: document.getElementById('free-description').value,
        custom_fields: {},
        documents: uploadedDocuments
    };

    // Collecter les champs personnalisés
    const customFields = document.querySelectorAll('.custom-field');
    customFields.forEach(field => {
        const name = field.querySelector('[data-field="name"]').value;
        const type = field.querySelector('[data-field="type"]').value;
        const value = field.querySelector('[data-field="value"]').value;

        if (name && value) {
            context.custom_fields[name] = {
                field_type: type,
                value: value
            };
        }
    });

    return context;
}

/**
 * Sauvegarde le contexte
 */
async function saveContext() {
    const context = collectFormData();

    // Validation
    if (!context.company_name || !context.industry) {
        showStatus('Veuillez remplir au moins le nom et le secteur', 'error');
        return;
    }

    try {
        const response = await fetch('/api/context', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ context })
        });

        if (response.ok) {
            showStatus('✅ Contexte sauvegardé avec succès !', 'success');
        } else {
            const error = await response.json();
            showStatus(`❌ Erreur: ${error.message}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Erreur réseau: ${error.message}`, 'error');
    }
}

/**
 * Prévisualise le contexte
 */
async function previewContext() {
    const context = collectFormData();

    try {
        const response = await fetch('/api/context/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ context })
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('preview-content').textContent = data.formatted;
            document.getElementById('preview-container').style.display = 'block';

            // Scroll vers la prévisualisation
            document.getElementById('preview-container').scrollIntoView({
                behavior: 'smooth'
            });
        }
    } catch (error) {
        showStatus(`❌ Erreur: ${error.message}`, 'error');
    }
}

/**
 * Réinitialise le contexte
 */
async function clearContext() {
    if (!confirm('⚠️ Êtes-vous sûr de vouloir réinitialiser tout le contexte ?')) {
        return;
    }

    try {
        const response = await fetch('/api/context', {
            method: 'DELETE'
        });

        if (response.ok) {
            // Vider le formulaire
            document.getElementById('company-name').value = '';
            document.getElementById('industry').value = '';
            document.getElementById('strategic-goals').value = '';
            document.getElementById('internal-constraints').value = '';
            document.getElementById('target-audience').value = '';
            document.getElementById('communication-tone').value = '';
            document.getElementById('free-description').value = '';
            document.getElementById('custom-fields-container').innerHTML = '';
            uploadedDocuments = [];
            renderDocumentsList();

            showStatus('✅ Contexte réinitialisé', 'success');
        }
    } catch (error) {
        showStatus(`❌ Erreur: ${error.message}`, 'error');
    }
}

/**
 * Configure le drag & drop
 */
function setupDragAndDrop() {
    const uploadArea = document.getElementById('upload-area');

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', async (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = Array.from(e.dataTransfer.files);
        await uploadFiles(files);
    });
}

/**
 * Configure l'input file
 */
function setupFileInput() {
    const fileInput = document.getElementById('file-input');

    fileInput.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        await uploadFiles(files);
        fileInput.value = ''; // Reset input
    });
}

/**
 * Upload des fichiers
 */
async function uploadFiles(files) {
    for (const file of files) {
        await uploadFile(file);
    }
}

/**
 * Upload un fichier individuel
 */
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        showStatus(`📤 Upload de ${file.name}...`, 'success');

        const response = await fetch('/api/context/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();

            uploadedDocuments.push({
                filename: file.name,
                file_path: data.file_path,
                doc_type: file.type,
                uploaded_at: new Date().toISOString()
            });

            renderDocumentsList();
            showStatus(`✅ ${file.name} uploadé avec succès`, 'success');
        } else {
            const error = await response.json();
            showStatus(`❌ Erreur upload ${file.name}: ${error.message}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche la liste des documents
 */
function renderDocumentsList() {
    const container = document.getElementById('documents-list');

    if (uploadedDocuments.length === 0) {
        container.innerHTML = '<p style="color: #666; padding: 20px; text-align: center;">Aucun document importé</p>';
        return;
    }

    container.innerHTML = uploadedDocuments.map((doc, index) => `
        <div class="document-item">
            <div class="document-info">
                <div class="document-icon">📄</div>
                <div>
                    <strong>${doc.filename}</strong><br>
                    <small style="color: #666;">Uploadé le ${new Date(doc.uploaded_at).toLocaleString('fr-FR')}</small>
                </div>
            </div>
            <button class="btn btn-danger" onclick="removeDocument(${index})" style="padding: 8px 16px;">
                🗑️ Supprimer
            </button>
        </div>
    `).join('');
}

/**
 * Supprime un document
 */
async function removeDocument(index) {
    const doc = uploadedDocuments[index];

    try {
        const response = await fetch(`/api/context/document/${encodeURIComponent(doc.filename)}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            uploadedDocuments.splice(index, 1);
            renderDocumentsList();
            showStatus('✅ Document supprimé', 'success');
        }
    } catch (error) {
        showStatus(`❌ Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche un message de statut
 */
function showStatus(message, type) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = `status-message status-${type}`;
    statusEl.style.display = 'block';

    setTimeout(() => {
        statusEl.style.display = 'none';
    }, 5000);
}
