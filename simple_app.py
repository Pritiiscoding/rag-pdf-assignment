"""Simplified Flask app that works without ML dependencies for testing."""
import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = 'data/pdfs'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    return jsonify({'error': 'RAG pipeline not available in simplified mode. Please use full app.py with proper dependencies.'}), 501

@app.route('/api/query', methods=['POST'])
def query_documents():
    """Query the RAG pipeline with a question."""
    return jsonify({'error': 'RAG pipeline not available in simplified mode. Please use full app.py with proper dependencies.'}), 501

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the RAG system."""
    pdf_dir = Path(app.config['UPLOAD_FOLDER'])
    file_count = len(list(pdf_dir.glob('*.pdf'))) if pdf_dir.exists() else 0
    
    return jsonify({
        'status': 'simplified_mode',
        'uploaded_files': file_count,
        'message': 'Running in simplified mode - file upload works, but RAG processing requires full dependencies'
    }), 200

@app.route('/health')
def health_check():
    """Health check endpoint for cloud platforms."""
    return jsonify({'status': 'healthy', 'service': 'documind-ai', 'mode': 'simplified'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting DocuMind AI Web Application (Simplified Mode)...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print("NOTE: File upload works, but RAG processing requires full dependencies")
    
    app.run(host='0.0.0.0', port=port, debug=debug)