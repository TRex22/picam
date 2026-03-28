# AGENTS.md — AI Agent Guidelines for PiCam V2

## Commit Format

All commits must follow:
```
[Phase X.Y] Short description of what was done
```

For chores/infra: `chore: description`
For docs: `docs: description`

Always append:
```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

## Task Tracking

- The living plan is at `PLAN.md` (repo root) and `.plan/v2-generated-plan.md`.
- Mark tasks `- [x]` when complete, `- [~]` when partial, `- [!]` when blocked.
- Add a dated completion note after each completed section.
- Commit the updated plan alongside the code changes.

## Testing Requirements

- All new modules in `src/` must have corresponding unit tests in `tests/unit/`.
- Camera-dependent code must be testable via `DemoBackend` without hardware.
- Integration tests may require a real Pi — mark with `@pytest.mark.integration`.
- Do not merge code that breaks existing passing tests.

## Tool Restrictions

- Do not run `git push --force` on `main` or `development` without explicit user confirmation.
- Do not delete any branch beginning with `archive/`.
- Do not touch the `v2-bootstrap` or `v1.5.0` tag.
- Do not modify `.github/workflows/` without reading the existing workflows first.
- Do not install system packages (`apt install`) — document required packages in `CLAUDE.md`.

## Code Style

- Python 3.11+, PEP 8, 4-space indentation.
- Type hints on all public methods.
- No bare `except:` — always catch specific exceptions.
- No `print()` in library code — use `logging`.
- Constants in `UPPER_SNAKE_CASE` at module level or in `settings/defaults.py`.

## Architecture Constraints

- Never reconfigure `Picamera2` at runtime (single-configuration model).
- Never call `tkinter` variable `.get()` from a non-main thread.
- GPIO imports must be guarded: `try: import gpiozero except ImportError: pass`.
- All file I/O paths must go through `pathlib.Path`, never raw strings.

## Demo Mode

- `DemoBackend` must pass all unit tests without camera hardware.
- When adding features that touch camera controls, add equivalent stub behaviour to `DemoBackend`.
