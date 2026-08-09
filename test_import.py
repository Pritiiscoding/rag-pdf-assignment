"""Test imports step by step to find where it hangs."""
print("Step 1: Basic imports...")
import os
from pathlib import Path
print("OK - Basic imports")

print("Step 2: Flask imports...")
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
print("OK - Flask imports")

print("Step 3: Config import...")
from src.config import settings
print("OK - Config import")

print("Step 4: Embeddings import...")
try:
    from src.embeddings import EmbeddingModel
    print("OK - Embeddings import")
except Exception as e:
    print(f"FAIL - Embeddings import: {e}")

print("Step 5: Other RAG imports...")
try:
    from src.rag_pipeline import RAGPipeline
    print("OK - RAG pipeline import")
except Exception as e:
    print(f"FAIL - RAG pipeline import: {e}")

print("All imports completed!")