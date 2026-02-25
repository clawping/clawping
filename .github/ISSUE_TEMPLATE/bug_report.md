---
name: Bug Report
about: Something is broken or behaving unexpectedly
title: "[bug] "
labels: bug
assignees: ''
---

## Description

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Start ClawPing with `...`
2. Send request `...`
3. Observe `...`

**Minimal reproduction (curl or code):**

```bash
curl -X POST http://localhost:8000/... \
  -H "Authorization: Bearer $API_KEY" \
  -d '{ ... }'
```

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened. Include the full error message or response.

```
# Error output or response here
```

## Environment

| Field | Value |
|-------|-------|
| ClawPing version | `v0.x.x` |
| Python version | `3.x.x` |
| OS | `Ubuntu 22.04 / macOS 14 / Windows 11` |
| Deployment | `bare metal / Docker / docker-compose` |

## Logs

Paste relevant logs here (from `docker logs clawping` or terminal output):

```
# logs here
```

## Additional Context

Any other context, screenshots, or notes.
