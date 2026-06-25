# Plan Mode Extension

A reusable Pi extension that adds a toggleable **Plan Mode** for discussion and planning-only sessions.

## Purpose

Plan Mode lets Pi explore, read, and discuss a project without accidentally modifying files or running terminal commands. It is useful for:

- Creating development plans before writing code
- Reviewing existing code without changing it
- Discussing architecture or design safely

## Architecture

The extension is implemented in `.pi/extensions/plan-mode.ts` as a Pi extension module. It uses Pi's event system:

- `pi.registerShortcut()` to bind **Ctrl + P**.
- `pi.registerCommand()` to add a `/plan` command.
- `pi.on("session_start", ...)` to restore Plan Mode state from the session.
- `pi.on("tool_call", ...)` to block restricted tools while Plan Mode is enabled.
- `pi.on("before_agent_start", ...)` to inject planning-only instructions into the LLM context.
- `pi.appendEntry()` to persist Plan Mode state across session restarts.

### Restrictions enforced

When Plan Mode is **ON**:

| Operation | Allowed? | Notes |
|-----------|----------|-------|
| Read files | ✅ Yes | `read`, `grep`, `find`, `ls`, etc. |
| Write `docs/PLAN.md` | ✅ Yes | Only this file can be written or edited |
| Write other files | ❌ No | `write` and `edit` are blocked for any other path |
| Create new files | ❌ No | Only `docs/PLAN.md` is allowed |
| Delete files | ❌ No | No delete tool exists; `bash` is blocked to prevent `rm`/`mv` |
| Rename files | ❌ No | Blocked via disabled `bash` |
| Run terminal commands | ❌ No | `bash` tool is completely disabled |

When Plan Mode is **OFF**, all tools behave normally.

## Keyboard shortcut

- **Ctrl + P** — Toggle Plan Mode ON/OFF.

A notification appears each time the state changes:

- `Plan Mode: ON`
- `Plan Mode: OFF`

## How to use

```
# Toggle Plan Mode (same as Ctrl + P)
/plan
```

While Plan Mode is active, ask Pi to create a plan. Pi will write it to `docs/PLAN.md`.

## Enabling the extension

### Project-local (recommended for this repo)

The extension is already placed in `.pi/extensions/plan-mode.ts` and will be auto-discovered when Pi trusts the project.

### Reusing in other projects

Copy `.pi/extensions/plan-mode.ts` to the target project's `.pi/extensions/` directory, or copy it to your global Pi extensions directory:

```text
~/.pi/agent/extensions/plan-mode.ts
```

Then restart Pi or run `/reload`.

## Testing checklist

1. Press **Ctrl + P** — see `Plan Mode: ON`.
2. Ask: "Create a development plan for implementing authentication." — Pi writes/updates `docs/PLAN.md` only.
3. Ask: "Update README.md" — blocked with explanation.
4. Ask: "Edit src/index.ts" — blocked.
5. Ask: "Delete package.json" — blocked.
6. Ask: "Run npm test" — blocked.
7. Press **Ctrl + P** again — see `Plan Mode: OFF`.
8. Repeat steps 3–6 — all should succeed normally.
