# 📚 DocuMind AI - Intelligent PDF Document Analysis
 
A modern, AI-powered web application for analyzing PDF documents through natural language queries. Upload your PDFs, process them with advanced embedding models, and ask questions to get intelligent answers with accurate citations.
 
![DocuMind AI](https://img.shields.io/badge/DocuMind-AI-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Flask](https://img.shields.io/badge/Flask-3.0-red)
![License](https://img.shields.io/badge/License-MIT-yellow)
 
## ✨ Features
 
- 📤 **Easy PDF Upload** - Drag & drop or click to upload documents
- 🔄 **Background Processing** - Async document ingestion without blocking
- 📊 **Progress Tracking** - Real-time status updates for long operations
- 💬 **Natural Language Q&A** - Ask questions in plain English
- 📚 **Accurate Citations** - Every answer includes document sources and page numbers
- 💾 **Storage Optimized** - API embeddings and automatic cleanup for cloud deployment
- 🎨 **Modern UI** - Beautiful, responsive interface with smooth animations
- 🚀 **Production Ready** - Deploy to Render or Vercel with one click
- 🔒 **Secure** - Environment variable configuration for sensitive data
 
## 🏗️ Architecture
 
```
PDF Upload → Text Extraction → Chunking → Embedding → Vector Storage
                                                        ↓
User Question → Embedding → Similarity Search → LLM Generation → Answer + Citations
```
 
## 🛠️ Tech Stack
 
- **Backend**: Flask (Python)
- **AI/ML**: 
  - Sentence Transformers (local embeddings) or OpenAI API (cloud-optimized)
  - OpenRouter (LLM API)
  - Qdrant (vector database)
- **Frontend**: HTML5, CSS3, JavaScript (no frameworks)
- **Deployment**: Render, Vercel
 
## 🚀 Quick Start
 
### Local Development
 
1. **Clone the repository**
```bash
git clone https://github.com/yourusername/documind-ai.git
cd documind-ai
```
 
2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
 
3. **Install dependencies**
```bash
pip install -r requirements.txt
```
 
4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
```
 
5. **Run the application**
```bash
python app.py
```
 
6. **Open in browser**
Navigate to `http://localhost:5000`
 
## 🌐 Cloud Deployment
 
### Deploy to Render
1. Push code to GitHub
2. Import repository in Render
3. Configure environment variables:
   - `OPENROUTER_API_KEY` - Your OpenRouter API key
   - `QDRANT_URL` - Your Qdrant Cloud URL
   - `QDRANT_API_KEY` - Your Qdrant Cloud API key
   - `USE_API_EMBEDDINGS=true` - Recommended for cloud deployment
   - `OPENAI_API_KEY` - Required if using API embeddings
4. Deploy automatically

**Note**: The `render.yaml` is pre-configured for optimal cloud deployment with API embeddings enabled and automatic file cleanup.
 
### Deploy to Vercel
1. Push code to GitHub
2. Import repository in Vercel
3. Configure environment variables:
   - `OPENROUTER_API_KEY` - Your OpenRouter API key
   - `QDRANT_URL` - Your Qdrant Cloud URL
   - `QDRANT_API_KEY` - Your Qdrant Cloud API key
   - `USE_API_EMBEDDINGS=true` - Recommended for cloud deployment
   - `OPENAI_API_KEY` - Required if using API embeddings
4. Deploy automatically
 
📖 **See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide**
 
## 🔑 Required Environment Variables
 
### Core Requirements
- `OPENROUTER_API_KEY` - Get from [OpenRouter](https://openrouter.ai/)
- `QDRANT_URL` - Your Qdrant Cloud URL
- `QDRANT_API_KEY` - Your Qdrant Cloud API key

### Optional (Recommended for Cloud)
- `USE_API_EMBEDDINGS=true` - Use OpenAI embeddings (saves ~120MB storage)
- `OPENAI_API_KEY` - Required if using API embeddings (get from OpenAI)

## 💾 Storage Optimization for Cloud Deployment

The application includes built-in storage optimization for cloud platforms like Render:

### API-Based Embeddings
- Set `USE_API_EMBEDDINGS=true` to use OpenAI embeddings instead of local models
- This saves ~120MB+ of storage by avoiding large model downloads
- Requires `OPENAI_API_KEY` when enabled

### Automatic File Cleanup
- `AUTO_CLEANUP_FILES=true` - Automatically removes old PDF files
- `MAX_FILE_AGE_HOURS=24` - Files older than 24 hours are automatically deleted
- Prevents storage accumulation on cloud platforms

### Cloud Deployment Configuration
The `render.yaml` is pre-configured with:
- API embeddings enabled by default
- 5-minute timeout for long-running operations
- Automatic file cleanup enabled
- Optimized worker configuration
 
## 📖 Usage
 
1. **Upload Documents**
   - Drag & drop PDF files or click to browse
   - Files are automatically saved to the server
 
2. **Process Documents**
   - Click "Process Documents" button
   - Documents are processed in the background (async)
   - Monitor progress via status updates
   - Documents are chunked, embedded, and stored in vector database
 
3. **Ask Questions**
   - Type your question in the chat interface
   - Get AI-powered answers with citations
   - View source documents and page numbers
 
## 🎨 Features
 
### Document Management
- Upload multiple PDF files
- Delete unwanted documents
- View file sizes and names
- Automatic file validation
 
### AI-Powered Q&A
- Natural language understanding
- Context-aware responses
- Accurate source citations
- Similarity scores for relevance
 
### User Interface
- Responsive design (mobile-friendly)
- Modern gradient styling
- Smooth animations
- Real-time status updates
- Error handling and notifications
 
## 🔧 Configuration
 
### RAG Pipeline Settings
- `CHUNK_SIZE`: Text chunk size (default: 800)
- `CHUNK_OVERLAP`: Chunk overlap (default: 150)
- `TOP_K`: Number of results to retrieve (default: 5)
- `EMBEDDING_MODEL`: Embedding model (default: sentence-transformers/all-MiniLM-L6-v2)
- `USE_API_EMBEDDINGS`: Use OpenAI API embeddings instead of local models (default: false)
- `OPENAI_API_KEY`: OpenAI API key (required if USE_API_EMBEDDINGS=true)

### Storage Management
- `AUTO_CLEANUP_FILES`: Automatically remove old PDF files (default: true)
- `MAX_FILE_AGE_HOURS`: Maximum age of files before cleanup in hours (default: 24)
 
### LLM Settings
- `OPENROUTER_MODEL`: LLM model (default: meta-llama/llama-3.1-8b-instruct:free)
- `OPENROUTER_BASE_URL`: API endpoint (default: https://openrouter.ai/api/v1)
 
## 📊 API Endpoints
 
- `GET /` - Main web interface
- `POST /api/upload` - Upload PDF files
- `GET /api/files` - List uploaded files
- `DELETE /api/files/<filename>` - Delete a file
- `POST /api/ingest` - Process documents (async, returns 202)
- `GET /api/ingest/status` - Check processing status and progress
- `POST /api/query` - Ask questions
- `GET /api/status` - System status
- `GET /health` - Health check
 
## 🧪 Testing
 
### Local Testing
```bash
# Test file upload
curl -X POST -F "file=@test.pdf" http://localhost:5000/api/upload
 
# Test query
curl -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is this document about?"}' \
  http://localhost:5000/api/query
```
 
## 🐛 Troubleshooting
 
### Common Issues
 
**Build fails on deployment**
- Check Python version compatibility
- Verify all dependencies in requirements.txt
- Check build logs for specific errors
 
**Qdrant connection errors**
- Verify Qdrant Cloud URL and API key
- Check cluster status in Qdrant dashboard
- Ensure network connectivity
 
**OpenRouter API errors**
- Verify API key is valid
- Check model availability
- Monitor API usage limits

**Storage limits on cloud platforms**
- Enable `USE_API_EMBEDDINGS=true` to avoid large model downloads
- Ensure `AUTO_CLEANUP_FILES=true` is enabled
- Check `MAX_FILE_AGE_HOURS` setting for file retention

**Preprocessing timeout**
- Processing now runs in background - check `/api/ingest/status` for progress
- Large PDFs may take longer to process
- Monitor logs for specific error messages
 
## 📈 Performance
 
### Optimization Tips
- Enable `USE_API_EMBEDDINGS=true` for cloud deployment to save storage
- Use smaller chunk size for quicker ingestion on large documents
- Use free OpenRouter models to reduce costs
- Monitor `/api/ingest/status` for processing progress
- Adjust `MAX_FILE_AGE_HOURS` for storage management
 
### Benchmarks
- **Document Ingestion**: ~1-2 seconds per page (runs in background)
- **Query Response**: ~2-5 seconds per question
- **File Upload**: <1 second per MB
- **Storage Usage**: ~50MB with API embeddings (vs ~170MB with local models)
 
## 🔒 Security
 
- Environment variables for sensitive data
- File type validation (PDFs only)
- File size limits (16MB max)
- Secure filename handling
- CORS configuration
 
## 🤝 Contributing
 
Contributions are welcome! Please follow these steps:
 
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
 
## 📝 License
 
This project is licensed under the MIT License.
 
## 🙏 Acknowledgments
 
- [Sentence Transformers](https://www.sbert.net/) for embedding models
- [OpenRouter](https://openrouter.ai/) for LLM API
- [Qdrant](https://qdrant.tech/) for vector database
- [Flask](https://flask.palletsprojects.com/) for web framework
 
## 📞 Support
 
- 📖 [Documentation](DEPLOYMENT.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/documind-ai/issues)
- 💬 [Discussions](https://github.com/yourusername/documind-ai/discussions)
 
## 🎯 Roadmap
 
- [ ] User authentication
- [ ] Document history
- [ ] Export functionality
- [ ] Multiple language support
- [ ] Advanced search filters
- [ ] Batch document processing
- [ ] API key management UI
- [ ] Usage analytics dashboard
 
---
 
Made by priti
 
**Transform document analysis with AI** 🚀
