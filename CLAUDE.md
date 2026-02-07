Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-celery provides Celery integration for pico-ioc. It uses:
- `@component`, `@factory`, `@provides`, `@configured` from pico-ioc
- `MethodInterceptor` for `CeleryClientInterceptor`
- `@configure` hook for task auto-discovery
- Auto-discovered via `pico_boot.modules` entry point

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- **NEVER change `version_scheme`** in pyproject.toml. It MUST remain `"post-release"`. Changing it to `"guess-next-dev"` causes `.dev0` versions to leak to PyPI. This was already fixed once — do not revert it.
- requires-python >= 3.11
- Commit messages: one line only
- Two distinct sides: worker (@task) and client (@send_task/@celery)
