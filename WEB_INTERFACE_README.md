# RAG Query System Web Interface

A modern web interface for the Scientific Papers RAG (Retrieval-Augmented Generation) Query System, built with FastAPI and React.

## Features

### Backend (FastAPI)
- **RESTful API** for RAG system interactions
- **Async processing** for better performance
- **CORS support** for frontend integration
- **Comprehensive error handling**
- **Health monitoring** and system statistics
- **Automatic API documentation** with Swagger UI

### Frontend (React)
- **Chat-like interface** for natural conversations
- **Real-time query processing** with loading indicators
- **Source citations** with expandable details
- **System statistics dashboard** 
- **Responsive design** with Material-UI components
- **Configurable query parameters** (number of documents to retrieve)

## Architecture

```
web_interface/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main FastAPI application
│   └── requirements.txt    # Backend dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js          # Main application component
│   │   ├── components/     # React components
│   │   │   ├── ChatInterface.js    # Chat UI component
│   │   │   └── SystemStats.js      # System stats component
│   │   └── services/       # API service layer
│   │       └── api.js      # HTTP client and API calls
│   ├── public/
│   └── package.json        # Frontend dependencies
```

## Quick Start

### Option 1: Start Both Services Together
```bash
./start_web_interface.sh
```

This will:
1. Install all dependencies
2. Start the FastAPI backend on port 8000
3. Start the React frontend on port 3000
4. Open your browser to http://localhost:3000

### Option 2: Start Services Separately

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

## Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **RAG system** already built (run `python rag_builder.py` first)
- **Local LLM** running (Ollama, llama.cpp, or OpenAI API key)

## API Endpoints

The FastAPI backend provides the following endpoints:

- `GET /` - API information
- `GET /api/health` - Health check
- `GET /api/stats` - System statistics
- `POST /api/query` - Query the RAG system
- `GET /api/documents` - List available documents
- `GET /api/config` - System configuration

### Example API Usage

```bash
# Health check
curl http://localhost:8000/api/health

# Query the system
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main findings?", "k": 5}'

# Get system stats
curl http://localhost:8000/api/stats
```

## Configuration

### Backend Configuration
The backend uses the same `config.py` file as the main RAG system. Key settings:

- **LLM Configuration**: Model type, name, parameters
- **Embedding Configuration**: Model and settings
- **Vector Database**: FAISS index location

### Frontend Configuration
Environment variables (create `.env` in `frontend/` directory):

```env
REACT_APP_API_URL=http://localhost:8000
```

## Development

### Backend Development
```bash
cd web_interface/backend
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

The backend will start with auto-reload enabled. API documentation is available at http://localhost:8000/docs

### Frontend Development
```bash
cd web_interface/frontend
npm install
npm start
```

The frontend will start with hot-reload enabled.

## Production Deployment

### Docker Deployment (Recommended)

Create `Dockerfile` for backend:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `Dockerfile` for frontend:
```dockerfile
FROM node:16-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
EXPOSE 80
```

### Manual Deployment

1. **Backend**:
   - Use production WSGI server (gunicorn with uvicorn workers)
   - Configure reverse proxy (nginx)
   - Set up SSL certificates
   - Configure environment variables

2. **Frontend**:
   - Build production bundle: `npm run build`
   - Serve with nginx or similar web server
   - Configure API URL for production

## Troubleshooting

### Common Issues

1. **Backend won't start**:
   - Check if RAG system is built (`embeddings/` directory exists)
   - Verify LLM is running (Ollama, etc.)
   - Check Python dependencies are installed

2. **Frontend can't connect to backend**:
   - Verify backend is running on port 8000
   - Check CORS configuration
   - Verify API URL in frontend configuration

3. **Queries timeout**:
   - Increase timeout in `api.js`
   - Check LLM performance and configuration
   - Monitor system resources

### Logs and Debugging

- **Backend logs**: Check terminal output or configure logging to file
- **Frontend logs**: Open browser developer tools console
- **API debugging**: Use the Swagger UI at http://localhost:8000/docs

## Performance Optimization

### Backend
- Use connection pooling for database connections
- Implement response caching for frequent queries
- Monitor memory usage with large document collections

### Frontend
- Enable React production builds for deployment
- Implement proper error boundaries
- Use React.memo for expensive components

## Security Considerations

### Production Security
- Enable HTTPS/SSL
- Configure proper CORS origins
- Implement rate limiting
- Use environment variables for sensitive configuration
- Consider authentication for multi-user deployments

## Contributing

1. Create feature branch from `main`
2. Make changes in `web_interface/` directory
3. Test both backend and frontend
4. Submit pull request

## License

Same as the main RAG Query System project.