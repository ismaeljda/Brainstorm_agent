from flask import Flask, request, jsonify
from flask_cors import CORS
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
import PyPDF2
import docx
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env (override system variables)
load_dotenv(override=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

print(f"🔑 Using OpenAI key ending with: ...{OPENAI_API_KEY[-4:]}")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Qdrant client (in-memory for development)
qdrant_client = QdrantClient(":memory:")

# Create collection
COLLECTION_NAME = "documents"
vector_size = 1536  # text-embedding-3-small produces 1536-dimensional vectors

try:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
except Exception as e:
    print(f"Collection already exists or error: {e}")

# Store uploaded documents metadata
documents_db = {}

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def extract_text_from_file(file_path, filename):
    """Extract text from various file formats"""
    extension = Path(filename).suffix.lower()

    try:
        if extension == '.pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text

        elif extension == '.docx':
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text

        elif extension in ['.txt', '.md', '.log']:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        elif extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        elif extension == '.csv':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        else:
            return ""
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
        return ""


def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)

    return chunks


@app.route('/upload', methods=['POST'])
def upload_document():
    """Upload and index a document"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save file
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, f"{doc_id}_{file.filename}")
    file.save(file_path)

    try:
        # Extract text
        text = extract_text_from_file(file_path, file.filename)

        if not text:
            return jsonify({"error": "Could not extract text from file"}), 400

        # Chunk text
        chunks = chunk_text(text)

        # Generate embeddings using OpenAI
        points = []
        for idx, chunk in enumerate(chunks):
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=chunk
            )
            embedding = response.data[0].embedding

            # Use hash of doc_id + idx as integer ID for Qdrant
            point_id = hash(f"{doc_id}_{idx}") & 0x7FFFFFFFFFFFFFFF  # Positive 64-bit int

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk,
                    "doc_id": doc_id,
                    "filename": file.filename,
                    "chunk_index": idx
                }
            )
            points.append(point)

        # Upload to Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        # Store metadata
        documents_db[doc_id] = {
            "id": doc_id,
            "filename": file.filename,
            "chunks_count": len(chunks),
            "status": "READY"
        }

        return jsonify({
            "documentId": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "status": "READY"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/search', methods=['POST'])
def search_documents():
    """Search through indexed documents using RAG"""
    data = request.json
    query = data.get('query', '')
    top_k = data.get('top_k', 3)

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        # Generate query embedding using OpenAI
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding

        # Search in Qdrant
        from qdrant_client.models import NamedVector, QueryRequest

        search_results = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=top_k
        ).points

        # Format results
        results = []
        for result in search_results:
            results.append({
                "text": result.payload["text"],
                "filename": result.payload["filename"],
                "score": result.score,
                "chunk_index": result.payload["chunk_index"]
            })

        return jsonify({
            "query": query,
            "results": results
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/documents', methods=['GET'])
def list_documents():
    """List all uploaded documents"""
    return jsonify(list(documents_db.values())), 200


@app.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a document and its chunks"""
    if doc_id not in documents_db:
        return jsonify({"error": "Document not found"}), 404

    try:
        # Delete from Qdrant (filter by doc_id)
        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector={"filter": {"must": [{"key": "doc_id", "match": {"value": doc_id}}]}}
        )

        # Delete metadata
        del documents_db[doc_id]

        return jsonify({"message": "Document deleted"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 RAG Server starting...")
    print(f"📚 Collection: {COLLECTION_NAME}")
    print(f"🤖 Embedding Model: OpenAI text-embedding-3-small")
    print(f"📊 Vector size: {vector_size}")
    print(f"🔑 OpenAI API Key: ✓ Set")
    app.run(port=5000, debug=True)
