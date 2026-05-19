---
name: commit-standards
description: Commit message format (type(scope): message), atomic commit rules, scope reference, and pre-commit checklist for Routiq. Use when committing or discussing how to structure commits.
---

# Commit Standards for Routiq

## Format

```
<type>(<scope>): <message>
```

- **type**: `feat`, `fix`, `update`, `refactor`, `docs`, `chore`
- **scope** (optional): lowercase package or module name, e.g. `(api)`, `(chat)`, `(db)`
- **message**: present tense, imperative mood, lowercase, no period

Good: `fix(chat): Add session.add before session.refresh for new conversations`

Bad: `Fixed bug in chat service` (past tense), `Added session.add...` (not imperative)

## Atomic commits

Each commit must contain **one logical change**. A commit should be safe to revert independently without collateral damage.

### How to split

If a change touches multiple concerns, split it:

| If you are… | Make commits like… |
|---|---|
| Refactoring + fixing | `refactor(api): ...` then `fix(chat): ...` |
| Moving files + editing code | `update(db): ...` then `fix(chat): ...` |
| Multiple unrelated fixes | One `fix(scope)` per fix |
| New feature + docs | `feat: ...` then `docs: ...` |

### Guidelines

- One commit = one concern. If you're tempted to write "and" in the message, split it.
- New files get their own commit (use `--intent-to-add` if needed).
- `git add -p` to stage only the relevant hunks per commit.
- If two commits depend on each other (e.g., rename a class then use it), order them so each commit leaves a working state.
- Don't mix generated artifacts with hand-written code.

## Scope reference

| Scope | Package |
|---|---|
| `(api)` | `src/api/` — route structure |
| `(chat)` | `src/api/chat/` — chat business logic |
| `(conversation)` | `src/api/conversation/` — conversation queries |
| `(db)` | `src/db/` — models, session |
| `(config)` | `src/config/` — settings, prompts |
| `(providers)` | `src/providers/` — LLM wrappers |
| `(memory)` | `src/memory/` — context, summarization |
| `(skills)` | `.opencode/skills/` |
| no scope | App-wide: `build`, `ci`, `deps`, `docs` |

## Push

After committing, push to `develop`:

```powershell
git push
```

If rewriting pushed history, use `git push --force-with-lease` (never bare `--force`).

## Pre-commit checklist

1. `git diff --cached` — is this exactly one logical change?
2. Does the commit message follow `<type>(<scope>): <imperative message>`?
3. Can this commit be reverted without breaking unrelated code?
4. Are there any debugging artifacts (`print()`, TODO, commented code)?
