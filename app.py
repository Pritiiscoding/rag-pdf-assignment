"""Flask web application for PDF RAG with file upload and Q&A interface."""
import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.config import settings
from src.rag_pipeline import RAGPipeline

app = Flask(__name__)
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = settings.pdf_dir
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize RAG pipeline
rag_pipeline = None


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_pipeline():
    """Get or initialize RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline(settings)
    return rag_pipeline


@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'path': filepath
        }), 200
    
    return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400


@app.route('/api/files', methods=['GET'])
def list_files():
    """List all uploaded PDF files."""
    pdf_dir = Path(app.config['UPLOAD_FOLDER'])
    if not pdf_dir.exists():
        return jsonify({'files': []}), 200
    
    files = []
    for pdf_file in pdf_dir.glob('*.pdf'):
        files.append({
            'name': pdf_file.name,
            'size': pdf_file.stat().st_size,
            'path': str(pdf_file)
        })
    
    return jsonify({'files': files}), 200


@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a specific PDF file."""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': 'File deleted successfully'}), 200
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ingest', methods=['POST'])
def ingest_documents():
    """Ingest all PDF files into the RAG pipeline."""
    try:
        pipeline = get_pipeline()
        chunk_count = pipeline.ingest()
        return jsonify({
            'message': 'Documents ingested successfully',
            'chunks_indexed': chunk_count
        }), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
def query_documents():
    """Query the RAG pipeline with a question."""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question']
        pipeline = get_pipeline()
        result = pipeline.query(question)
        
        # Convert result to JSON-serializable format
        response = {
            'answer': result.answer,
            'found': result.found,
            'citations': [
                {
                    'doc_name': c.doc_name,
                    'page_number': c.page_number,
                    'snippet': c.snippet[:300] + '...' if len(c.snippet) > 300 else c.snippet,
                    'score': c.score
                }
                for c in result.citations
            ]
        }
        
        return jsonify(response), 200
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the RAG system."""
    try:
        pipeline = get_pipeline()
        collection_exists = pipeline.store.collection_exists()
        
        pdf_dir = Path(app.config['UPLOAD_FOLDER'])
        file_count = len(list(pdf_dir.glob('*.pdf'))) if pdf_dir.exists() else 0
        
        return jsonify({
            'collection_exists': collection_exists,
            'uploaded_files': file_count,
            'qdrant_url': settings.qdrant_url,
            'embedding_model': settings.embedding_model,
            'llm_model': settings.openrouter_model
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint for cloud platforms."""
    return jsonify({'status': 'healthy', 'service': 'documind-ai'}), 200


@app.route('/health')
def health_check():
    """Health check endpoint for cloud platforms."""
    return jsonify({'status': 'healthy', 'service': 'documind-ai'}), 200


# For Gunicorn compatibility
application = app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting DocuMind AI Web Application...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Qdrant URL: {settings.qdrant_url}")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)