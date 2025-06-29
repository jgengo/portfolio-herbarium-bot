# Contributing to Herbarium Bot

Thank you for considering a contribution!

## Development Setup

1. Fork the repository and clone your fork.
2. Install the dependencies:
   ```bash
   uv sync
   ```
3. Install the pre-commit hooks:
   ```bash
   pre-commit install
   ```
4. Create a new branch for your work:
   ```bash
   git checkout -b feat/my-feature
   ```

## Commit Messages

Use the `type(scope): summary` format, for example:
`feat(bot): add new command`.

Run the checks before committing:
```bash
pre-commit run --all-files
```

## Running Tests

If you add or update functionality, update the tests and run:
```bash
uv run pytest
```

## Pull Requests

Push your branch and open a pull request with a clear description of your changes.

We appreciate your help in making Herbarium Bot better!
