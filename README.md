# Competitor Analysis System

> Multi-agent AI-powered competitor analysis system built with LangGraph orchestration

An advanced AI-powered competitor analysis platform that automates the entire competitive intelligence workflow using specialized agents for discovery, data collection, analysis, and reporting.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for different aspects of competitive analysis
- **Intelligent Discovery**: Automated competitor identification using Tavily search
- **Deep Analysis**: SWOT analysis, market positioning, and sentiment analysis
- **Quality Assurance**: Built-in data validation and quality scoring
- **Real-time Reporting**: Dynamic report generation with actionable insights
- **Modern Tech Stack**: FastAPI + React with Python 3.12 and uvicorn
- **Scalable Design**: Docker-based deployment with horizontal scaling support

## 🏗️ Architecture

### Multi-Agent System
Built on **LangGraph** with specialized agents:

- **SearchAgent**: Tavily-powered competitor discovery and data collection
- **AnalysisAgent**: LLM-powered competitive analysis (SWOT, positioning, sentiment)
- **QualityAgent**: Data validation and quality scoring
- **ReportAgent**: Report generation and delivery
- **CompetitorAnalysisCoordinator**: Main orchestrator managing agent workflow

### Tech Stack

**Backend:**
- FastAPI with Python 3.12+ and uvicorn
- LangGraph for agent workflow management
- OpenAI GPT-4 for analysis
- Tavily API for web intelligence
- MongoDB for data persistence
- Redis for caching

**Frontend:**
- React 18 + TypeScript
- Material-UI components
- Real-time WebSocket updates
- Data visualization components

**Infrastructure:**
- Docker & Docker Compose
- Uvicorn ASGI server
- Modern Python project structure with pyproject.toml

## 📁 Project Structure
```
competitor-analysis-system/
├── backend/
│   ├── agents/           # LangGraph agents
│   ├── api/             # FastAPI endpoints
│   ├── config/          # Configuration
│   ├── database/        # MongoDB models
│   ├── services/        # Business logic
│   └── utils/           # Utilities
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   └── types/       # TypeScript types
│   └── public/
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (3.10+ supported)
- **Node.js 16+** and npm
- **Docker & Docker Compose**
- **Git**

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd competitor-analysis-system

# Run automated setup
./scripts/setup.sh

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys

# Start development environment
./scripts/dev.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Configure environment
cp backend/.env.example backend/.env

# 5. Start services
make local
```

### Option 3: Docker Development

```bash
# Initialize project
make init

# Start development environment
make dev
```

## 🔧 Configuration

### Environment Variables

Create `backend/.env` with the following configuration:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Database Configuration
MONGODB_URI=mongodb://admin:admin123@localhost:27017/competitor_analysis?authSource=admin
REDIS_HOST=localhost
REDIS_PORT=6379

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=info
API_VERSION=v1

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### API Keys Setup

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Tavily API Key**: Get from [Tavily API](https://tavily.com/)

## 🌐 Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| MongoDB | localhost:27017 | Database |
| Redis | localhost:6379 | Cache |

## 📊 Usage

### Starting Analysis

```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/competitor-analysis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Your Company",
    "industry": "Technology",
    "description": "AI-powered solutions"
  }'

# Via Web Interface
# Navigate to http://localhost:3000
```

### Monitoring Progress

```bash
# WebSocket connection for real-time updates
ws://localhost:8000/ws/analysis/{analysis_id}

# REST API polling
GET /api/v1/competitor-analysis/status/{analysis_id}
```

### Retrieving Results

```bash
# Get completed analysis
GET /api/v1/competitor-analysis/results/{analysis_id}
```

## 🛠️ Development

### Available Commands

```bash
# Project management
make help          # Show all commands
make install       # Install dependencies
make init          # Initialize project

# Development
make local         # Run backend locally
make local-full    # Run full stack locally
make dev           # Docker development
make up            # Docker production

# Testing
make test          # Run all tests
./scripts/test.sh  # Run tests with coverage

# Docker operations
make build         # Build images
make logs          # View logs
make clean         # Clean containers

# Database
make db-shell      # MongoDB shell
make redis-cli     # Redis CLI
```

## 🔄 Workflow

1. **Client Onboarding** - Define objectives and scope
2. **Competitor Discovery** - AI identifies relevant competitors
3. **Data Collection** - Parallel gathering from multiple sources
4. **Data Validation** - Quality checks and verification
5. **Analysis** - Multiple analytical frameworks applied
6. **Insight Generation** - Synthesis and recommendations
7. **Report Delivery** - Custom reports and dashboards
8. **Continuous Monitoring** - Ongoing tracking (optional)

## 📈 Performance Metrics
- Analysis completion: < 4 hours
- Data accuracy: > 90%
- Competitor discovery: > 95% relevance
- System uptime: > 99.5%

## 🤝 Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- LangGraph for orchestration framework
- Tavily for intelligent web search
- OpenAI for GPT-4 capabilities

## 📞 Support
For support, email support@competitoranalysis.ai or open an issue in the repository.