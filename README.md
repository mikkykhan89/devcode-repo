# devcode-repo

A small Python project configured for VS Code, GitHub Copilot, and `pytest`.

## Prerequisites

- Python 3.9 or later
- Visual Studio Code with the **Python** and **GitHub Copilot** extensions

## Set up

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

In VS Code, run **Python: Select Interpreter** and choose `.venv`.

## Run the program

```bash
python python_process/user_table.py
```

You can also select **Run user_table** from VS Code's Run and Debug panel.

## Run tests

```bash
pytest
```

VS Code will discover the tests automatically.

## Copilot workflow

Project instructions live in `.github/copilot-instructions.md`. Ask Copilot to explain the current code first, keep changes small, add tests, and review the diff before you commit.

## Automated AI pull-request reviews

This repository includes a GitHub Actions reviewer. For each non-draft pull
request from this repository, it sends the PR diff and
`.github/ai-review-instructions.md` to OpenAI, then maintains one review
comment on the PR.

To enable it, add an `OPENAI_API_KEY` Actions secret in **Settings → Secrets
and variables → Actions**. Optionally add an `OPENAI_PR_REVIEW_MODEL`
repository variable to override the default `gpt-5.6-terra` model.

The workflow deliberately skips pull requests from forks so that an untrusted
contributor cannot access the secret. It also limits a reviewed diff to 100,000
characters and sends each request with `store: false`.
