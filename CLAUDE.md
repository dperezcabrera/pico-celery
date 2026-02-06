Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-celery provides Celery integration for pico-ioc. It uses:
- `@component`, `@factory`, `@provides`, `@configured` from pico-ioc
- `MethodInterceptor` for `CeleryClientInterceptor`
- `@configure` hook for task auto-discovery
- Auto-discovered via `pico_boot.modules` entry point

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- `version_scheme = "guess-next-dev"` (clean versions on tag)
- requires-python >= 3.11
- Commit messages: one line only
- Two distinct sides: worker (@task) and client (@send_task/@celery)
