# RAG Web Interface Management Scripts

This directory contains scripts to manage the RAG (Retrieval-Augmented Generation) web interface with both FastAPI backend and React frontend.

## 📁 Available Scripts

### Starting Services

- **`start_web_interface.sh`** - Starts both backend and frontend
- **`start_backend.sh`** - Starts only the FastAPI backend (port 8000)
- **`start_frontend.sh`** - Starts only the React frontend (port 3000)

### Stopping Services

- **`stop_web_interface.sh`** - Stops both backend and frontend
- **`stop_backend.sh`** - Stops only the FastAPI backend
- **`stop_frontend.sh`** - Stops only the React frontend

## 🚀 Quick Start

```bash
# Start the complete interface
./start_web_interface.sh

# Stop the complete interface
./stop_web_interface.sh
```

## 🔧 Individual Service Management

### Backend Only
```bash
# Start backend
./start_backend.sh

# Stop backend
./stop_backend.sh
```

### Frontend Only
```bash
# Start frontend
./start_frontend.sh

# Stop frontend
./stop_frontend.sh
```

## 🌐 Service URLs

- **Frontend (React)**: http://localhost:3000
- **Backend (FastAPI)**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📊 Port Information

- **Port 3000**: React development server
- **Port 8000**: FastAPI backend server

## 🔍 Troubleshooting

### Port Already in Use
If you get "port already in use" errors:
```bash
# Stop all services
./stop_web_interface.sh

# Wait a moment and restart
./start_web_interface.sh
```

### Manual Port Check
```bash
# Check what's using port 8000
lsof -i :8000

# Check what's using port 3000
lsof -i :3000
```

### Force Kill Processes
```bash
# Kill process on port 8000
kill $(lsof -ti:8000)

# Kill process on port 3000
kill $(lsof -ti:3000)
```

## 🏗️ Architecture

```
RAG Web Interface
├── Backend (FastAPI)
│   ├── Port: 8000
│   ├── API endpoints: /api/*
│   └── RAG system integration
└── Frontend (React)
    ├── Port: 3000
    ├── Material-UI components
    └── Chat interface
```

## 📝 Logs

- **Backend logs**: Displayed in terminal when running start_backend.sh
- **Frontend logs**: Displayed in terminal when running start_frontend.sh
- **Combined logs**: Use start_web_interface.sh to see both

## ⚙️ Configuration

### Backend Configuration
- Located in: `web_interface/backend/main_simple.py`
- Environment: Virtual environment in `web_interface/backend/venv/`

### Frontend Configuration
- Located in: `web_interface/frontend/src/`
- Package management: `web_interface/frontend/package.json`

## 🔄 Development Workflow

1. **Start development**:
   ```bash
   ./start_web_interface.sh
   ```

2. **Make changes** to backend or frontend code

3. **Frontend**: Changes auto-reload (hot reload enabled)

4. **Backend**: Restart backend for changes:
   ```bash
   ./stop_backend.sh
   ./start_backend.sh
   ```

5. **Stop when done**:
   ```bash
   ./stop_web_interface.sh
   ```

## 🚨 Emergency Stop

If services become unresponsive:
```bash
# Nuclear option - kill all Python and Node processes
pkill -f python
pkill -f node
```

## 📈 System Requirements

- **Python 3.8+** with virtual environment
- **Node.js 16+** with npm
- **Available ports**: 3000, 8000
- **RAG system files**: embeddings/, data/ directories