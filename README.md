# AI Commit Review (Study Mode)

A reusable GitHub Action that performs pedagogical AI-based reviews of Python commits **after they are created**.

## Purpose

This Action is designed for learning and self-review.
It intentionally runs **after commits**, not before, to avoid AI-driven code generation during development.

## How It Works

- Runs on every push
- Executes only if the commit message contains `[ai-commit-review-study]`
- Analyzes the commit diff
- Posts AI feedback directly as a **comment on the commit**

## Usage

### 1. Add OpenAI API key

In your repository:
- Go to **Settings → Secrets and variables → Actions**
- Add a secret named: OPENAI_API_KEY


### 2. Add a workflow to your project

```yaml
name: AI Commit Review For Study

on:
  push:

jobs:
  review:
    runs-on: ubuntu-latest

    if: contains(github.event.head_commit.message, '[ai-commit-review-study]')

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - uses: your-username/ai-commit-review-action@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
