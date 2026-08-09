"""Flask web application for PDF RAG with file upload and Q&A interface."""
import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
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

# Processing state
processing_state = {
    'status': 'idle',
    'progress': 0,
    'message': '',
    'error': None,
    'start_time': None
}
processing_lock = threading.Lock()


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_pipeline():
    """Get or initialize RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline(settings)
    return rag_pipeline


def cleanup_old_files():
    """Remove files older than max_file_age_hours."""
    if not settings.auto_cleanup_files:
        return
    
    try:
        pdf_dir = Path(app.config['UPLOAD_FOLDER'])
        if not pdf_dir.exists():
            return
        
        max_age = timedelta(hours=settings.max_file_age_hours)
        current_time = datetime.now()
        
        for pdf_file in pdf_dir.glob('*.pdf'):
            file_age = current_time - datetime.fromtimestamp(pdf_file.stat().st_mtime)
            if file_age > max_age:
                try:
                    pdf_file.unlink()
                    print(f"[CLEANUP] Removed old file: {pdf_file.name}")
                except Exception as e:
                    print(f"[CLEANUP] Failed to remove {pdf_file.name}: {e}")
    except Exception as e:
        print(f"[CLEANUP] Error during cleanup: {e}")


def update_processing_state(status, progress=0, message='', error=None):
    """Update the global processing state."""
    with processing_lock:
        processing_state['status'] = status
        processing_state['progress'] = progress
        processing_state['message'] = message
        processing_state['error'] = error
        if status == 'processing' and processing_state['start_time'] is None:
            processing_state['start_time'] = time.time()
        elif status == 'idle':
            processing_state['start_time'] = None


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
    """Ingest all PDF files into the RAG pipeline (asynchronous)."""
    with processing_lock:
        if processing_state['status'] == 'processing':
            return jsonify({'error': 'Processing already in progress'}), 400
    
    # Check if files exist first
    pdf_dir = Path(app.config['UPLOAD_FOLDER'])
    if not pdf_dir.exists():
        return jsonify({'error': 'Upload directory does not exist'}), 404
    
    pdf_files = list(pdf_dir.glob('*.pdf'))
    if not pdf_files:
        return jsonify({'error': 'No PDF files found to process'}), 404
    
    def run_ingestion():
        try:
            print("[INGEST] Starting document ingestion...")
            update_processing_state('processing', 5, f'Found {len(pdf_files)} PDF files to process')
            
            # Clean up old files first
            print("[INGEST] Cleaning up old files...")
            cleanup_old_files()
            update_processing_state('processing', 10, 'Cleaned up old files')
            
            # Initialize pipeline
            print("[INGEST] Initializing pipeline...")
            update_processing_state('processing', 15, 'Initializing RAG pipeline...')
            pipeline = get_pipeline()
            
            update_processing_state('processing', 25, 'Loading embedding model...')
            print(f"[INGEST] Using API embeddings: {settings.use_api_embeddings}")
            
            # Perform ingestion
            print("[INGEST] Running ingestion...")
            update_processing_state('processing', 30, 'Processing PDF files...')
            chunk_count = pipeline.ingest()
            print(f"[INGEST] Completed: {chunk_count} chunks indexed")
            update_processing_state('processing', 100, f'Successfully indexed {chunk_count} chunks')
            
            # Mark as complete
            update_processing_state('idle', 100, f'Completed: {chunk_count} chunks indexed')
            
        except FileNotFoundError as e:
            print(f"[INGEST] File not found error: {e}")
            update_processing_state('idle', 0, '', f'File not found: {str(e)}')
        except Exception as e:
            print(f"[INGEST] Error during ingestion: {e}")
            import traceback
            traceback.print_exc()
            update_processing_state('idle', 0, '', f'Processing error: {str(e)}')
    
    # Start background thread
    thread = threading.Thread(target=run_ingestion)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Ingestion started in background',
        'status': 'processing',
        'files_to_process': len(pdf_files)
    }), 202


@app.route('/api/ingest/status', methods=['GET'])
def get_ingest_status():
    """Get the current status of document ingestion."""
    with processing_lock:
        state = processing_state.copy()
    
    # Calculate elapsed time if processing
    if state['status'] == 'processing' and state['start_time']:
        state['elapsed_time'] = time.time() - state['start_time']
    
    return jsonify(state), 200


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
        
        pdf_dir = Path(app.config['UPLOAD_FOLDER'])
        file_count = len(list(pdf_dir.glob('*.pdf'))) if pdf_dir.exists() else 0
        
        return jsonify({
            'status': 'ok',
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting DocuMind AI Web Application...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Qdrant URL: {settings.qdrant_url}")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Using API embeddings: {settings.use_api_embeddings}")
    
    # Clean up old files on startup
    cleanup_old_files()
    
    app.run(host='0.0.0.0', port=port, debug=debug)
