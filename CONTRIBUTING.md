# Contributing to AI Chatbot

Thank you for your interest in contributing to the AI Chatbot project! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome diverse perspectives
- Report inappropriate behavior to maintainers

## Getting Started

### 1. Fork and Clone the Repository

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/AI-Chatbot.git
cd AI-Chatbot

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL-OWNER/AI-Chatbot.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
cd backend
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies with dev tools
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Making Changes

1. **Keep changes focused** - One feature/fix per pull request
2. **Follow code style** - Run `black backend/app` to format code
3. **Write tests** - Add tests for new functionality
4. **Update documentation** - Update relevant docs in `documentation/` folder

### Running Tests

```bash
cd backend
pytest testing/ --cov=app --cov-report=html
```

### Code Quality Checks

```bash
# Format code
black backend/app

# Lint
flake8 backend/app

# Type checking (if applicable)
mypy backend/app
```

## Submitting Changes

### 1. Commit Your Changes

```bash
git add .
git commit -m "feat: add new chat feature" # Use conventional commits
```

**Commit Message Format:**
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for test changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to GitHub and click **New Pull Request**
2. Set base: `ORIGINAL-OWNER/AI-Chatbot` → `main`
3. Set compare: `YOUR-USERNAME/AI-Chatbot` → `feature/your-feature-name`
4. Fill PR template with:
   - Description of changes
   - Related issues
   - Testing instructions
   - Screenshots (if UI changes)

### 4. Code Review Process

- Maintainers will review your changes
- Address feedback and make updates
- Push updates to the same branch (PR auto-updates)
- Once approved, maintainers will merge

## Reporting Issues

### Bug Reports

Create an issue with:
- Clear title describing the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (Python version, OS, etc.)
- Relevant logs or error messages

### Feature Requests

Create an issue with:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Any related issues or discussions

## Project Structure Guidelines

### Backend (`backend/`)

```
app/
├── api/           # API routes (one file per endpoint type)
├── services/      # Business logic (one service per domain)
├── models/        # Pydantic schemas
├── core/          # Configuration and constants
├── data/          # Data processing
├── scripts/       # One-off scripts
└── utils/         # Shared utilities
```

### Frontend (`frontend/`)

```
├── css/          # Stylesheets
├── js/           # JavaScript modules
├── index.html    # Main pages
└── assets/       # Images and resources
```

## Documentation

Update relevant documentation when:
- Adding new API endpoints
- Changing configuration
- Adding new features
- Fixing bugs related to docs

Documentation files:
- `documentation/ARCHITECTURE_FLOWS.md` - System architecture
- `documentation/CHAT_ENDPOINTS.md` - API endpoints
- `documentation/RAG_ARCHITECTURE.md` - RAG system design

## Performance Considerations

- Use async/await for I/O operations
- Cache expensive computations
- Profile code before optimizing
- Document performance-critical sections

## Security Guidelines

- Never commit sensitive data (API keys, passwords)
- Use `backend/.env.example` for required variables
- Follow OWASP security practices
- Run security scans on dependencies

## Release Process

Maintainers follow semantic versioning:
- `MAJOR.MINOR.PATCH` (e.g., 1.0.2)
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

## Questions?

- Open a Discussion on GitHub
- Check existing issues for similar questions
- Review documentation in `documentation/` folder

---

**Thank you for contributing!** 🎉
