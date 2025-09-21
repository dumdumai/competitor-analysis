#!/bin/bash
# Development startup script

set -e

echo "🚀 Starting Competitor Analysis System in Development Mode"
echo "=========================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run 'make install' first."
    exit 1
fi

# Check if backend/.env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file not found. Copying from example..."
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "✅ Created backend/.env from example. Please configure your API keys."
    else
        echo "❌ backend/.env.example not found. Please create backend/.env manually."
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Start databases
echo "🗄️  Starting databases..."
docker-compose up -d mongodb redis

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 5

# Start backend
echo "🖥️  Starting backend server..."
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir . &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

echo "✅ Development environment started!"
echo ""
echo "🌐 Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔍 Logs:"
echo "   Backend PID: $BACKEND_PID"
echo "   Use 'docker-compose logs -f mongodb redis' for database logs"
echo ""
echo "⚠️  Press Ctrl+C to stop all services"

# Keep script running and handle cleanup
trap "echo 'Stopping services...'; kill $BACKEND_PID 2>/dev/null; docker-compose stop mongodb redis; exit" INT

# Wait for backend process
wait $BACKEND_PID