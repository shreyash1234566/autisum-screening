# AutiScreen Contribution Guidelines

Welcome to the AutiScreen project! This document outlines our git workflow, commit rules, branch limits, and coding style guidelines. Following these rules ensures code quality, stability, and clean git histories.

---

## 1. Branching Strategy and Branch Limits

To keep the project clean, direct pushes to the `main` branch are strictly prohibited. All changes must be made via pull requests (PRs) from isolated feature branches.

### Branch Namespaces
Use the following prefix conventions when naming branches:
* `feat/` — For new features or extensions (e.g., `feat/add-asd-gaze-model`).
* `fix/` — For bug fixes and patches (e.g., `fix/postgres-child-foreign-key`).
* `test/` — For testing suite improvements and negative validations (e.g., `test/negative-api-coverage`).
* `docs/` — For documentation work and repository hardening (e.g., `docs/api-documentation`).
* `refactor/` — For code structural changes without behavior updates (e.g., `refactor/unify-db-sessions`).

### PR & Review Guidelines
* All pull requests require at least one approving review from a maintainer.
* The CI pipeline must run and pass 100% of the test suite (`tests/docker-compose.test.yml`) before any merge.
* Squashing commits on merge is preferred to keep the git history clean.

---

## 2. Commit Message Guidelines

We follow the **Conventional Commits** specification. Commit messages should have the following structure:

```text
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Allowed Types
* `feat`: A new feature or endpoint.
* `fix`: A bug fix.
* `docs`: Documentation updates.
* `style`: Code formatting changes (whitespaces, semicolons, etc.) that do not affect logic.
* `refactor`: A code change that neither fixes a bug nor adds a feature.
* `test`: Adding missing tests or correcting existing ones.
* `chore`: Build processes, tooling updates, or dependency management.

### Examples
* `feat(backend): add language field validation for child registration`
* `fix(db): add ALTER TABLE migration for processing_note in PostgreSQL`
* `docs(readme): update onboarding checklist for backend setup`

---

## 3. Coding Standards & Linters

### Backend (Python / FastAPI)
* **Style Guide:** Standard [PEP-8](https://peps.python.org/pep-0008/) conventions.
* **Imports:** Sorted cleanly: Standard library, third-party libraries, local imports.
* **Linter & Formatter:** We use `ruff` to lint and format python code.
  * Run linter: `ruff check .`
  * Run formatter: `ruff format .`
* **Type Hints:** Required on all new function signatures and router inputs.
* **Validations:** Request validation must be handled at the Pydantic layer (`BaseModel` + `@field_validator`) rather than inline router checks.

### Frontend (Javascript / React)
* **Linter & Formatter:** ESLint + Prettier.
* **Design Philosophy:** Keep components modular, focused, and reusable. Avoid hardcoding styles; use HSL-tailored custom CSS design systems located in `index.css`.
* **State Management:** Keep state close to where it is used. Use custom React context only for application-wide states (e.g., theme, session settings).

### Mobile (Dart / Flutter)
* **Analyzer:** Follow the official Flutter lint settings defined in `analysis_options.yaml`.
* **Platform Channels:** Ensure platform channel calls are properly wrapped in try-catch blocks and handle `PlatformException` gracefully.
