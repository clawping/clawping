---
name: Feature Request
about: Suggest an idea or improvement for ClawPing
title: "[feat] "
labels: enhancement
assignees: ''
---

## Problem / Motivation

What problem does this feature solve? What are you trying to do that you can't do today?

> e.g. "I want to receive notifications on Discord but there's currently no Discord channel support."

## Proposed Solution

Describe the feature you'd like to see. Be as specific as possible.

> e.g. "Add a `discord` channel option that posts to a Discord webhook URL. The webhook URL would be set via `DISCORD_WEBHOOK_URL` env var."

## Example Usage

Show how you'd use this feature — a command, API call, or config snippet:

```bash
# Example curl
curl -X POST http://localhost:8000/reminders \
  -d '{ "channel": "discord", "message": "Deploy done", "delay": "1h" }'
```

## Alternatives Considered

Have you tried any workarounds? Are there other ways this could be implemented?

## Additional Context

Any related issues, links, or references that would help understand this request.

---

**Priority (your assessment):**
- [ ] Nice to have
- [ ] Important for my use case
- [ ] Blocking — I can't use ClawPing without this
