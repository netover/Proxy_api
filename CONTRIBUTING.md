# Contributing to ProxyAPI

Thank you for your interest in contributing to ProxyAPI! We welcome contributions from the community and are grateful for your help in making ProxyAPI better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Community](#community)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.11 or later
- Git
- Docker & Docker Compose (recommended)
- A code editor (VS Code recommended)

### Fork and Clone

1. Fork the ProxyAPI repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/your-username/proxyapi.git
cd proxyapi
```

3. Set up the upstream remote:

```bash
git remote add upstream https://github.com/your-org/proxyapi.git
```

## Development Setup

### Quick Setup with Docker

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run tests
docker-compose -f docker-compose.dev.yml exec proxyapi pytest
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
python main.py
```

### IDE Setup

For the best development experience, we recommend:

- **VS Code** with Python extension
- **Pylance** for type checking
- **Black** for code formatting
- **Flake8** for linting

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes** - Fix issues in the codebase
- **Features** - Add new functionality
- **Documentation** - Improve docs, add examples
- **Tests** - Add or improve test coverage
- **Performance** - Optimize code performance
- **Security** - Security improvements

### Finding Issues to Work On

- Check [GitHub Issues](https://github.com/your-org/proxyapi/issues) for open issues
- Look for issues labeled `good first issue` or `help wanted`
- Check the [ROADMAP.md](ROADMAP.md) for planned features

## Development Workflow

### 1. Choose an Issue

- Select an issue to work on
- Comment on the issue to indicate you're working on it
- Wait for maintainer approval if required

### 2. Create a Branch

```bash
# Create and switch to a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Write clean, well-tested code
- Follow the coding standards
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_specific_feature.py

# Run with coverage
pytest --cov=src tests/

# Run linting
flake8 src/
black --check src/
mypy src/
```

### 5. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature description

- What was changed
- Why it was changed
- How it was implemented"

# Use conventional commit format:
# feat: new feature
# fix: bug fix
# docs: documentation
# style: formatting
# refactor: code restructuring
# test: adding tests
# chore: maintenance
```

### 6. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
# - Use a descriptive title
# - Provide detailed description
# - Link to related issues
# - Request review from maintainers
```

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters
- **Imports**: Grouped and sorted
- **Docstrings**: Google style
- **Type hints**: Required for new code

```python
# Good import style
from typing import Dict, List, Optional
import asyncio
import json

from src.core.config import settings
from src.services.logging import logger

# Bad import style
import os, sys
from src.core.config import *
```

### Code Structure

```
src/
├── api/           # API endpoints and routing
├── core/          # Core business logic
├── providers/     # AI provider integrations
├── services/      # Shared services
├── utils/         # Utility functions
└── models/        # Data models
```

### Naming Conventions

- **Classes**: PascalCase
- **Functions/Methods**: snake_case
- **Constants**: UPPER_SNAKE_CASE
- **Private methods**: _leading_underscore

### Error Handling

```python
# Good error handling
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise ServiceUnavailableError("Service temporarily unavailable")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise InternalServerError("Internal server error")
```

### Async/Await Best Practices

```python
# Good async patterns
async def process_items(items: List[Dict]) -> List[Result]:
    """Process items concurrently."""
    tasks = [process_single_item(item) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Avoid blocking operations in async functions
async def read_file_async(path: str) -> str:
    """Read file asynchronously."""
    async with aiofiles.open(path, 'r') as f:
        return await f.read()
```

## Testing

### Test Structure

```
tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
├── e2e/          # End-to-end tests
└── conftest.py   # Test configuration
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestModelDiscovery:
    @pytest.fixture
    async def discovery_service(self):
        """Set up test service."""
        service = ModelDiscovery()
        yield service
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_discover_models_success(self, discovery_service):
        """Test successful model discovery."""
        # Arrange
        mock_provider = Mock()
        mock_provider.get_available_models.return_value = [
            {"id": "gpt-4", "name": "GPT-4"}
        ]

        # Act
        models = await discovery_service.discover_models("openai")

        # Assert
        assert len(models) == 1
        assert models[0]["id"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_discover_models_provider_error(self, discovery_service):
        """Test handling of provider errors."""
        # Arrange
        mock_provider = Mock()
        mock_provider.get_available_models.side_effect = ProviderError("API limit exceeded")

        # Act & Assert
        with pytest.raises(ProviderError):
            await discovery_service.discover_models("openai")
```

### Test Coverage

- **Unit tests**: 95%+ coverage required
- **Integration tests**: Critical paths covered
- **Performance tests**: Load testing scenarios

## Submitting Changes

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: Detailed explanation of changes
- **Commits**: Logical, atomic commits
- **Tests**: All tests pass
- **Documentation**: Updated as needed

### PR Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Peer Review**: At least one maintainer reviews
3. **Approval**: Changes approved by maintainer
4. **Merge**: Changes merged to main branch

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to reproduce**: Step-by-step instructions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, etc.
- **Logs**: Relevant error logs
- **Screenshots**: If applicable

### Feature Requests

For feature requests, include:

- **Problem**: What problem does this solve?
- **Solution**: Proposed solution
- **Alternatives**: Considered alternatives
- **Use case**: How would this be used?

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions
- **Discord**: Real-time chat (link in README)
- **Twitter**: Updates and announcements

### Getting Help

- **Documentation**: Check the docs first
- **Issues**: Search existing issues
- **Discussions**: Ask the community
- **Discord**: Get real-time help

### Recognition

Contributors are recognized in:

- **README.md**: Contributors section
- **CHANGELOG.md**: Release notes
- **GitHub**: Contributor statistics

Thank you for contributing to ProxyAPI! 🚀