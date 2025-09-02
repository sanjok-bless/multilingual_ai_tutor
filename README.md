# multilingual_ai_tutor

![CI](https://github.com/sanjok-bless/multilingual_ai_tutor/workflows/CI/badge.svg)

Multilingual AI Tutor driven by LLM – an AI-powered language coach that helps you practice multiple languages in real time. It corrects mistakes, explains grammar, and provides instant feedback. Implemented with Python/FastAPI backend, Vue.js frontend, and OpenAI API integration.

## Quick Start
```bash
pip install uv && uv pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

## Prerequisites
- Python 3.13
- Recommended: [uv](https://docs.astral.sh/uv/getting-started/installation/) for faster package management

## Setup
```bash
# Install dependencies
# Using uv (recommended)
pip install uv
uv pip install -r backend/requirements.txt

# Or using pip
pip install -r backend/requirements.txt

# Install pre-commit hooks
pre-commit install
```

## Development

### Local Development
```bash
# Run backend
uvicorn backend.main:app --reload
```

### Testing & Code Quality
```bash
# Run tests
python -m pytest

# Run pre-commit checks manually
pre-commit run --all-files
```

### Continuous Integration
This project uses GitHub Actions for automated testing:
- **Triggers**: All pushes and pull requests
- **Checks**: Pre-commit hooks (ruff, bandit) + pytest
- **Python**: 3.13 on Ubuntu latest

## Contributing
All code changes are automatically tested via GitHub Actions. Before submitting:
1. Ensure tests pass locally: `python -m pytest`
2. Run pre-commit checks: `pre-commit run --all-files` (automatically runs if hooks installed)
3. Push changes - CI will run automatically
