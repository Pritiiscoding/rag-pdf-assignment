"""Flask web application for PDF RAG with file upload and Q&A interface."""
import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Try to load config and RAG pipeline, but don't fail if dependencies are missing
settings = None
RAG_AVAILABLE = False
RAGPipeline = None
rag_pipeline = None
pipeline_init_error = None

# Simple configuration fallback
class SimpleSettings:
    pdf_dir = 'data/pdfs'
    auto_cleanup_files = True
    max_file_age_hours = 24
    use_api_embeddings = True
    qdrant_url = 'http://localhost:6333'
    embedding_model = 'sentence-transformers/all-MiniLM-L6-v2'
    openrouter_model = 'meta-llama/llama-3.1-8b-instruct:free'

try:
    from src.config import settings
    print("[INFO] Configuration loaded successfully")
except Exception as e:
    print(f"[WARN] Could not load configuration: {e}")
    settings = SimpleSettings()

try:
    from src.rag_pipeline import RAGPipeline
    RAG_AVAILABLE = True
    print("[INFO] RAG pipeline imports successful")
except Exception as e:
    RAG_AVAILABLE = False
    print(f"[WARN] RAG pipeline not available: {e}")
    print("[WARN] Basic file upload will work, but processing will fail")

app = Flask(__name__)
CORS(app)

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Upload folder - will be set from config if available
UPLOAD_FOLDER = 'data/pdfs'
if settings:
    UPLOAD_FOLDER = settings.pdf_dir
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize RAG pipeline (lazy initialization)
rag_pipeline = None
pipeline_init_error = None

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
    global rag_pipeline, pipeline_init_error
    
    if not RAG_AVAILABLE:
        raise RuntimeError("RAG pipeline dependencies not available. Please check error logs and install required packages.")
    
    if rag_pipeline is None and pipeline_init_error is None:
        try:
            print("[PIPELINE] Initializing RAG pipeline...")
            rag_pipeline = RAGPipeline(settings)
            print("[PIPELINE] RAG pipeline initialized successfully")
        except Exception as e:
            pipeline_init_error = str(e)
            print(f"[PIPELINE] Failed to initialize RAG pipeline: {e}")
            raise RuntimeError(f"RAG pipeline initialization failed: {e}")
    
    if pipeline_init_error:
        raise RuntimeError(f"RAG pipeline not available: {pipeline_init_error}")
    
    return rag_pipeline


def cleanup_old_files():
    """Remove files older than max_file_age_hours."""
    if not settings or not settings.auto_cleanup_files:
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
    if not RAG_AVAILABLE:
        return jsonify({'error': 'RAG pipeline not available. Please check dependencies and configuration.'}), 501
    
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
    if not RAG_AVAILABLE:
        return jsonify({'error': 'RAG pipeline not available. Please check dependencies and configuration.'}), 501
    
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

        response = {
            'status': 'ok',
            'uploaded_files': file_count,
            'rag_available': RAG_AVAILABLE
        }
        
        if settings:
            response['qdrant_url'] = settings.qdrant_url
            response['embedding_model'] = settings.embedding_model
            response['llm_model'] = settings.openrouter_model
            response['use_api_embeddings'] = settings.use_api_embeddings
        else:
            response['config_error'] = 'Configuration not available'
        
        # Try to get pipeline status if available
        if not RAG_AVAILABLE:
            response['pipeline_status'] = 'not_available'
            response['message'] = 'RAG pipeline dependencies not installed. File upload works, but processing requires ML dependencies.'
        elif pipeline_init_error:
            response['pipeline_status'] = 'error'
            response['pipeline_error'] = pipeline_init_error
        elif rag_pipeline:
            try:
                collection_exists = rag_pipeline.store.collection_exists()
                response['pipeline_status'] = 'ready'
                response['collection_exists'] = collection_exists
            except Exception as e:
                response['pipeline_status'] = 'error'
                response['pipeline_error'] = str(e)
        else:
            response['pipeline_status'] = 'not_initialized'
        
        return jsonify(response), 200
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
