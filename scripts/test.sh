#!/bin/bash
# Test runner script

set -e

echo "🧪 Running Competitor Analysis System Tests"
echo "==========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run './scripts/setup.sh' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run backend tests
echo "🐍 Running backend tests..."
cd backend
if [ -d "tests" ]; then
    pytest tests/ -v --cov=. --cov-report=term-missing
else
    echo "⚠️  Backend tests directory not found"
fi
cd ..

# Run frontend tests
if command -v npm &> /dev/null && [ -d "frontend/node_modules" ]; then
    echo "⚛️  Running frontend tests..."
    cd frontend
    npm test -- --coverage --watchAll=false
    cd ..
else
    echo "⚠️  Frontend not set up. Run 'cd frontend && npm install'"
fi

echo "✅ Tests completed!"