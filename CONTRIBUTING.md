# Contribution Guide

Thank you for your interest in contributing to the ClimateWise project! To ensure consistency and quality across the codebase, please follow these guidelines.

## 1. Language

**All code, comments, documentation, and commit messages MUST be in English.**

This is crucial for the long-term maintainability of the project and for enabling collaboration with a broader community.

## 2. Code Style and Quality

We use a set of automated tools to maintain a consistent code style. Before committing any code, please ensure it adheres to the standards set by these tools.

### Backend (Python)

- **Formatting:** We use `black` for uncompromising code formatting and `isort` for organizing imports.
- **Linting:** We use `flake8` to check for style errors and potential bugs.
- **Type Checking:** We use `mypy` for static type analysis.

These checks will be enforced automatically by pre-commit hooks, which you should install as described in the development setup.

### Frontend (TypeScript/React)

- **Formatting:** We use `prettier` for code formatting.
- **Linting:** We use `eslint` to identify and report on patterns in the code.

## 3. Commits and Pull Requests

- **Commit Messages:** Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps in automating changelogs and understanding the history of the project.
  - Example: `feat(api): add endpoint for user listing`
  - Example: `fix(auth): correct password hashing logic`
  - Example: `docs(readme): update setup instructions`

- **Pull Requests:**
  - Ensure your branch is up-to-date with the `main` branch before submitting a pull request.
  - Provide a clear description of the changes you have made.
  - Ensure all automated checks (CI/CD pipeline) are passing.

## 4. Development Setup

To get started, clone the repository and follow the setup instructions in the main `README.md`.

To ensure code quality checks are run automatically before you commit, install the pre-commit hooks:

```bash
# Install pre-commit (if you haven't already)
pip install pre-commit

# Set up the git hook scripts
pre-commit install
```
