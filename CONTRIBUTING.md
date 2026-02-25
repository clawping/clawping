# Contributing to ClawPing

Thanks for your interest in contributing. This document covers everything you need to get started.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Issues](#reporting-issues)

---

## Development Setup

### 1. Fork & Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/clawping.git
cd clawping
```

### 2. Create a Branch

Always work on a feature branch, never directly on `main`.

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Set Up the Environment

```bash
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install black isort pytest pytest-asyncio
```

### 4. Configure Environment

```bash
cp .env.example .env
# Fill in test credentials (a test Telegram bot is fine)
```

### 5. Run the Dev Server

```bash
make dev
# Server running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

---

## Code Style

ClawPing uses **black** for formatting and **isort** for import ordering. Both are enforced on PRs.

**Format before committing:**

```bash
make format
```

**Check without modifying:**

```bash
make lint
```

### Guidelines

- Follow existing patterns in the codebase
- Use type hints on all function signatures
- Keep functions focused — one thing, done well
- Write docstrings for public functions and classes
- Async all the way — use `async`/`await` consistently; no blocking calls in async context
- Prefer `httpx.AsyncClient` over `requests` for HTTP
- Use Pydantic models for all request/response schemas

---

## Submitting a Pull Request

1. **Make sure your branch is up to date** with `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run lint and tests** before pushing:
   ```bash
   make lint
   make test
   ```

3. **Push your branch:**
   ```bash
   git push origin feat/your-feature-name
   ```

4. **Open a PR** on GitHub against the `main` branch.

5. **Fill out the PR template** — describe what the PR does, link any related issues, and check off the checklist.

6. A maintainer will review your PR. Be responsive to feedback — discussions help improve the code.

### PR Tips

- Keep PRs focused and small. One feature or fix per PR.
- Link the related issue: `Closes #42`
- Add tests for new features or bug fixes where possible
- Update the README or docs if your change affects public behavior

---

## Reporting Issues

Use [GitHub Issues](https://github.com/claw-ecosystem/clawping/issues) to report bugs or request features.

### Bug Reports

Use the **Bug Report** template. Include:
- Steps to reproduce (exact commands or request payloads)
- Expected vs. actual behavior
- Your environment (Python version, OS, deployment method)
- Relevant logs or error messages

### Feature Requests

Use the **Feature Request** template. Explain:
- What problem you're solving
- How you'd expect it to work
- Any alternative approaches you've considered

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Discord notification channel
fix: handle SMTP connection timeout gracefully
docs: update API reference for /conditions endpoint
chore: upgrade APScheduler to 3.10.4
refactor: extract delay parser into utils module
```

---

## Questions?

Open a [Discussion](https://github.com/claw-ecosystem/clawping/discussions) or drop into the Telegram community.
