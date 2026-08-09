"""Simple test to check if Flask can load without the RAG pipeline."""
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({'status': 'Flask is working!'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("Starting simple Flask test...")
    app.run(host='0.0.0.0', port=5000, debug=True)