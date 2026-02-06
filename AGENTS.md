# pico-celery

Async-first Celery integration for pico-ioc. Declarative task workers and clients with DI.

## Commands

```bash
pip install -e .                  # Install in dev mode
pytest tests/ -v                  # Run tests
pytest --cov=pico_celery --cov-report=term-missing tests/  # Coverage
tox                               # Full matrix (3.11-3.14)
mkdocs serve -f mkdocs.yml       # Local docs
```

## Project Structure

```
src/pico_celery/
  __init__.py          # Public API exports
  decorators.py        # @task decorator (worker side)
  config.py            # CelerySettings (@configured dataclass)
  factory.py           # CeleryFactory - creates singleton Celery app
  registrar.py         # PicoTaskRegistrar - auto-discovers @task methods, registers with Celery
  client.py            # @celery, @send_task decorators, CeleryClientInterceptor
```

## Key Concepts

### Worker Side
- **`@task(name="tasks.x")`**: Marks async methods as Celery tasks. Only works on `async def`
- **`PicoTaskRegistrar`**: `@configure` hook that discovers all `@task` methods via container metadata and registers them with Celery app
- **Execution**: Wrapper resolves component from container (`container.aget()`), calls async method. Handles event loop management

### Client Side
- **`@celery`**: Class decorator (like `@repository`). Works with and without parentheses
- **`@send_task(name="tasks.x")`**: Marks methods as task senders. Method body is never executed
- **`CeleryClientInterceptor`**: AOP interceptor that converts method calls into `celery_app.send_task()`

### Configuration
- **`CelerySettings`**: `@configured(prefix="celery")` dataclass with `broker_url`, `backend_url`, `task_track_started`
- **`CeleryFactory`**: `@factory` creating singleton `Celery` app from settings

## Code Style

- Python 3.11+
- `@task` only on async methods (raises TypeError otherwise)
- Metadata keys: `PICO_CELERY_METHOD_META`, `PICO_CELERY_SENDER_META`
- Prototype scope for worker components (fresh instance per task)

## Testing

- pytest + pytest-asyncio
- Mock Celery app for unit tests
- Test both worker registration and client interception paths

## Boundaries

- Do not modify `_version.py`
- Worker tasks must be `async def`
- Client `@send_task` method bodies are never executed
