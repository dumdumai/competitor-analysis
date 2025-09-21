#!/bin/bash
# Project setup script

set -e

echo "🚀 Setting up Competitor Analysis System"
echo "========================================"

# Check Python version
echo "🐍 Checking Python version..."
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$PYTHON_VERSION" = "3.12" ] || [ "$PYTHON_VERSION" = "3.11" ] || [ "$PYTHON_VERSION" = "3.10" ]; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python 3.10+ required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✅ Using $PYTHON_CMD ($(${PYTHON_CMD} --version))"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing..."
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install frontend dependencies
if command -v npm &> /dev/null; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "⚠️  npm not found. Skipping frontend dependencies."
    echo "   Please install Node.js and run 'cd frontend && npm install'"
fi

# Copy environment file
echo "⚙️  Setting up environment..."
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "✅ Created backend/.env from example"
    else
        echo "⚠️  backend/.env.example not found"
    fi
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Next steps:"
echo "   1. Configure API keys in backend/.env"
echo "   2. Run './scripts/dev.sh' to start development environment"
echo "   3. Or use 'make local' for backend-only development"
echo ""
echo "📚 Available commands:"
echo "   make help    - Show all available commands"
echo "   make local   - Run backend locally"
echo "   make dev     - Run with Docker"
echo "   make test    - Run tests"