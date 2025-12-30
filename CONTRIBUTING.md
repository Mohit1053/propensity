# Contributing to Propensity - Unique ID Generator

Thank you for your interest in contributing! This document provides guidelines for contributing to the Unique ID Generator project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/propensity.git
   cd propensity
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/propensity.git
   ```

## How to Contribute

### Reporting Bugs

- Check existing issues first
- Include detailed steps to reproduce
- Provide sample data (anonymized if necessary)
- Include Python version and dependencies

### Suggesting Features

- Open an issue with the `enhancement` label
- Describe the feature and use case
- Explain performance implications

### Contributing Code

1. Create a feature branch
2. Make your changes
3. Add/update tests
4. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8+
- pip

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black isort flake8 mypy
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run benchmarks
python test_and_benchmark.py
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names

### Example

```python
def generate_unique_id(email: str, phone: str) -> int:
    """
    Generate a unique ID for a user based on email and phone.
    
    Args:
        email: User's email address
        phone: User's phone number
    
    Returns:
        Integer hash representing unique ID
    
    Raises:
        ValueError: If both email and phone are empty
    """
    if not email and not phone:
        raise ValueError("At least one identifier required")
    
    combined = f"{email}:{phone}"
    return hash(combined)
```

### Documentation

- Add docstrings to all public functions
- Include type hints
- Update README for new features
- Add usage examples

## Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Refactoring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance

### Examples

```
feat(union-find): add weighted quick union
fix(spam-filter): correct threshold calculation
perf(batch): optimize memory usage for large datasets
docs(readme): add BigQuery migration guide
```

## Pull Request Process

1. **Ensure tests pass** locally
2. **Update documentation** for any changes
3. **Update CHANGELOG.md**
4. **Fill out PR template** completely

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Performance impact considered
- [ ] CHANGELOG.md updated

## Performance Guidelines

Since this is a performance-critical library:

1. **Benchmark changes** using `test_and_benchmark.py`
2. **Document complexity** for new algorithms
3. **Consider memory usage** for large datasets
4. **Avoid unnecessary allocations** in hot paths

---

Thank you for contributing! 🙏
