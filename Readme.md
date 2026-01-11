# 🔍 Document Search Engine

A modern, intelligent document search engine built with Django, HTMX, Qdrant, and Celery. Features hybrid semantic + keyword search, background processing, and real-time analytics.

## ✨ Features

### 📄 Document Processing
- **Multi-format support**: Upload PDF, DOC, DOCX, and TXT files
- **Smart chunking**: Automatic text segmentation for optimal embedding
- **Vector embeddings**: Powered by OpenAI's `text-embedding-3-small` model
- **Background indexing**: Async processing with Celery for non-blocking uploads
- **Reindexing**: Update document vectors with live progress tracking
- **Clean deletion**: Remove documents and associated vectors atomically

### 🔎 Advanced Search
- **Hybrid search**: Combines semantic understanding with keyword matching
- **Document-level aggregation**: Intelligently groups chunks by source document
- **Smart highlighting**: Visual snippet matching in search results
- **Relevance filtering**: Configurable threshold to control result quality
- **Zero-JavaScript fallback**: Full functionality without client-side scripts
- **Search analytics**: Track and analyze user queries in real-time

### 🧠 Vector Intelligence
- **Chunk-level embeddings**: Granular semantic understanding of document sections
- **Document-level embeddings**: Centroid-based whole-document vectors
- **Related recommendations**: Discover similar documents automatically

### 🎨 User Experience
- **HTMX-powered**: Smooth partial page updates without full reloads
- **Minimal JavaScript**: Progressive enhancement approach
- **Clean interface**: Responsive Bootstrap-based design
- **Real-time feedback**: Live updates during indexing and processing

## 🛠️ Tech Stack

- **Backend**: Django
- **Vector Database**: Qdrant
- **Task Queue**: Celery + Redis/RabbitMQ
- **Frontend**: HTMX + Bootstrap
- **Embeddings**: OpenAI API (text-embedding-3-small)

## 📋 Prerequisites

- Python 3.8+
- Qdrant (local or cloud instance)
- Redis or RabbitMQ (for Celery)
- OpenAI API key

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone 
cd document-search-engine
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
OPENAI_API_KEY=your-openai-api-key
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=  # Optional for local instance
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Start Qdrant
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or download and run locally from https://qdrant.tech
```

### 7. Start Celery worker
```bash
celery -A document_search_engine worker -l info
```

### 8. Run development server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## 📖 Usage

### Uploading Documents
1. Navigate to the upload page
2. Select document (PDF, DOC, DOCX, TXT)
3. Click upload and monitor background processing progress
4. Documents are automatically chunked, embedded, and indexed

### Searching
1. Enter your search query in the search box
2. Results show relevant documents with highlighted snippets
3. Click "Clear search" to reset
4. Adjust relevance threshold in settings for precision/recall tuning

### Managing Documents
- **View all documents**: See your indexed document library
- **Reindex**: Update embeddings for specific documents
- **Delete**: Remove documents and all associated vectors
- **Related documents**: Discover similar content automatically

### Analytics
- View search query trends
- Monitor popular searches
- Track user engagement patterns

## 🏗️ Architecture
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Django    │─────▶│   Celery    │─────▶│   Qdrant    │
│   (Web)     │      │  (Workers)  │      │  (Vectors)  │
└─────────────┘      └─────────────┘      └─────────────┘
       │                     │
       │                     │
       ▼                     ▼
┌─────────────┐      ┌─────────────┐
│    HTMX     │      │  OpenAI API │
│  (Frontend) │      │ (Embeddings)│
└─────────────┘      └─────────────┘
```

## 🔧 Configuration

### Search Settings
Adjust in `settings.py` or admin interface:
- `CHUNK_SIZE`: Characters per chunk (default: 500)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50)
- `RELEVANCE_THRESHOLD`: Minimum similarity score (default: 0.7)
- `MAX_RESULTS`: Maximum search results (default: 10)

### Celery Configuration
Configure task queues and workers in `celery.py`:
- Adjust concurrency for your hardware
- Set up periodic tasks for maintenance
- Configure result backends

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Qdrant](https://qdrant.tech) for the excellent vector database
- [HTMX](https://htmx.org) for modern HTML-driven interactions
- [OpenAI](https://openai.com) for embedding models
- [Django](https://djangoproject.com) for the robust web framework
- [Celery](https://docs.celeryq.dev) for distributed task processing

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Built with ❤️ using Django, HTMX, Qdrant, and Celery