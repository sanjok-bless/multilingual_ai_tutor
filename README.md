# multilingual_ai_tutor

![CI](https://github.com/sanjok-bless/multilingual_ai_tutor/workflows/CI/badge.svg)

Multilingual AI Tutor driven by LLM – an AI-powered language coach that helps you practice multiple languages in real time. It corrects mistakes, explains grammar, and provides instant feedback. Implemented with Python/FastAPI backend, Vue.js frontend, and OpenAI API integration.

## Quick Start
```bash
# Backend
pip install uv && uv pip install -r backend/requirements.txt
uvicorn backend.main:app --reload

# Frontend (new terminal)
npm install --prefix frontend
npm run dev --prefix frontend
```

## Prerequisites
- Python 3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (optional, for faster package management)
- Node.js 24

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework with automatic API documentation
- **LangChain** - Framework for LLM application development with OpenAI integration
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server for production deployment
- **pytest** - Testing framework with comprehensive test suite

### Frontend
- **Vue.js 3** - Progressive JavaScript framework with Composition API
- **Vuex 4** - State management for Vue.js applications
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework for rapid UI development
- **Vitest** - Fast unit testing framework built on Vite

## Setup
```bash
# Install backend dependencies
# Using uv (recommended)
pip install uv
uv pip install -r backend/requirements.txt

# Or using pip
pip install -r backend/requirements.txt

# Install frontend dependencies
npm install --prefix frontend

# Install pre-commit hooks
pre-commit install
```

## Development

### Local Development
```bash
# Run backend (Terminal 1)
uvicorn backend.main:app --reload

# Run frontend (Terminal 2)
npm run dev --prefix frontend
```

**Access Points:**
- Backend API: http://localhost:8000
- Frontend App: http://localhost:3000

### Testing & Code Quality
```bash
# Backend tests
python -m pytest

# Frontend tests
npm run test --prefix frontend

# Code quality checks
pre-commit run --all-files              # All quality checks (ruff, bandit, etc.)
```

### Continuous Integration
This project uses GitHub Actions with parallel test execution:
- **Triggers**: All pushes and pull requests
- **Pipeline**:
  1. Quality checks (pre-commit hooks: ruff, bandit, eslint + security, prettier)
  2. Backend tests (pytest on Python 3.13)
  3. Frontend tests (Vitest on Node.js 24)
- **Platform**: Ubuntu latest

### Production Build
```bash
# Build frontend for production
npm run build --prefix frontend

# Preview production build locally
npm run preview --prefix frontend
```

## Contributing
   - Commit your changes - pre-commit hooks will run automatically
   - Push to your branch - GitHub Actions CI will run automatically
   - All tests and quality checks must pass
