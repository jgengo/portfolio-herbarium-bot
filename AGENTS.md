# Codex Contribution Guidelines

This repository uses **Python 3.12+** and expects contributions to follow these rules. They apply to the entire project.

## Development workflow

1. **Install dependencies** using `uv sync`.
2. Before committing, run the pre-commit hooks on modified files:
   ```bash
   uv run pre-commit run --files <changed files>
   ```
   This runs `isort`, `black` (line length 119) and `mypy`.
3. Execute tests with:
   ```bash
   uv run pytest -vv
   ```

## Coding style

- Use four spaces for indentation and keep lines under **119** characters.
- Write functions with type hints for all parameters and return values.
- Prefer `| None` syntax for optional types.
- Use dataclasses for structured data where appropriate.
- Write Google‑style docstrings for all public functions and classes.
- Keep modules small and focused. Place shared helpers in the `herbabot` package.

## Commit messages

Use the `type(scope): summary` format where possible, for example:
`feat(bot): add welcome handler`.

## Pull requests

Pull request descriptions should briefly explain the motivation and major changes. The template in
`.github/PULL_REQUEST_TEMPLATE.md` may be used.
