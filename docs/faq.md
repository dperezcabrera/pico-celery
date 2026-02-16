# Frequently Asked Questions

## General

### What is Pico-Celery?

Pico-Celery integrates pico-ioc with Celery 5, enabling dependency injection for both task workers and task clients. It has two sides:

- **Worker**: `@task` marks async methods on `@component` classes as Celery tasks
- **Client**: `@celery` + `@send_task` provides declarative, injectable task clients

### What Python versions are supported?

Pico-Celery requires Python 3.11 or later.

## Worker Side

### How do I define a task?

Use `@task` on an `async def` method inside a `@component` class:

```python
from pico_ioc import component
from pico_celery import task

@component(scope="prototype")
class MyTasks:
    def __init__(self, service: MyService):
        self.service = service

    @task(name="tasks.process")
    async def process(self, data: dict):
        return await self.service.process(data)
```

### Why must tasks be async?

Pico-Celery is async-native. The `@task` decorator enforces `async def` and raises `TypeError` for sync methods. Use an `eventlet` or `gevent` worker pool.

### What scope should task components use?

Use `prototype` scope for task components. Each task execution gets a fresh instance, ensuring state isolation between concurrent tasks.

## Client Side

### How do I send a task?

Define a client class with `@celery` and `@send_task`:

```python
from pico_celery import celery, send_task

@celery
class MyClient:
    @send_task(name="tasks.process")
    def process(self, data: dict):
        pass  # Body is never executed
```

The `CeleryClientInterceptor` intercepts method calls and converts them into `celery_app.send_task()` calls. The method body is never executed.

### Can I pass Celery options to send_task?

Yes, pass them as keyword arguments:

```python
@send_task(name="tasks.process", queue="high_priority", countdown=10)
def process(self, data: dict):
    pass
```

## Configuration

### How do I configure the Celery broker?

Use pico-ioc configuration with the `"celery"` prefix:

```python
from pico_ioc import configuration, DictSource

config = configuration(DictSource({
    "celery": {
        "broker_url": "redis://localhost:6379/0",
        "backend_url": "redis://localhost:6379/1",
    }
}))
```

### Can I use different configurations for different environments?

Yes, use environment-specific configuration sources:

```python
from pico_ioc import configuration, EnvSource, DictSource

config = configuration(
    EnvSource(prefix="CELERY_"),
    DictSource({"celery": {"broker_url": "redis://localhost:6379/0"}})
)
```

## Troubleshooting

This section documents every error message emitted by pico-celery with the exact text, its cause, and how to fix it.

---

### `TypeError: @task decorator can only be applied to async methods, got: <method_name>`

**Source:** `pico_celery.decorators.task`

**Cause:** The `@task` decorator was applied to a synchronous function or method. pico-celery only supports `async def` task handlers.

**Fix:** Convert the method to an async coroutine:

```python
# Wrong
@task(name="tasks.process")
def process(self, data: dict):  # sync -- raises TypeError
    ...

# Correct
@task(name="tasks.process")
async def process(self, data: dict):  # async
    ...
```

---

### `TypeError: send_task can only decorate methods or functions`

**Source:** `pico_celery.client.send_task`

**Cause:** The `@send_task` decorator was applied to something that is not a function or method (e.g. a class or a property).

**Fix:** Apply `@send_task` only to regular methods or functions:

```python
# Wrong
@send_task(name="tasks.process")
class NotAMethod:  # raises TypeError
    pass

# Correct
@send_task(name="tasks.process")
def process(self, data: dict):
    pass
```

---

### `ValueError: No @send_task or @task methods found on <ClassName>`

**Source:** `pico_celery.client.celery`

**Cause:** A class was decorated with `@celery` but none of its methods are decorated with `@send_task` or `@task`. The `@celery` decorator requires at least one task-related method.

**Fix:** Add at least one `@send_task` or `@task` method to the class:

```python
# Wrong -- no task methods
@celery
class EmptyClient:
    def regular_method(self):  # raises ValueError
        pass

# Correct
@celery
class MyClient:
    @send_task(name="tasks.process")
    def process(self, data: dict):
        pass
```

---

### Tasks are not being discovered

**Cause:** The modules containing your `@component` classes with `@task` methods are not being scanned by pico-ioc.

**Fix:** Ensure your task modules are included in the `modules` list when initialising the container:

```python
from pico_ioc import init

container = init(modules=["myapp.tasks"], config=config)
```

If using `pico-boot`, verify that your package is listed in the `pico_boot.modules` entry point in `pyproject.toml`.

---

### Dependencies not injected into task components

**Cause:** The services required by your task component are not registered as pico-ioc components.

**Fix:** Decorate every dependency with `@component`:

```python
from pico_ioc import component

@component
class MyService:
    pass

@component(scope="prototype")
class MyTasks:
    def __init__(self, service: MyService):  # MyService must be a @component
        self.service = service
```

---

### Task executes but the component has stale state

**Cause:** The task component is using `singleton` scope, so the same instance is reused across all task executions.

**Fix:** Use `prototype` scope for task components to get a fresh instance per execution:

```python
@component(scope="prototype")  # not "singleton"
class MyTasks:
    def __init__(self, service: MyService):
        self.service = service
```

---

### `RuntimeError` or event loop errors in worker

**Cause:** The Celery worker already has a running event loop (e.g. with `eventlet` or `gevent` pool), and `asyncio.run()` cannot create a nested loop.

**How pico-celery handles it:** `PicoTaskRegistrar._create_task_wrapper` detects a running loop and offloads the async task to a `ThreadPoolExecutor` automatically. If you see this error, it may indicate a conflict with another library that patches the event loop.

**Fix:** Ensure you are using a compatible worker pool:

```bash
celery -A myapp worker --loglevel=info -P eventlet
```

---

### Client method body is executed instead of sending a task

**Cause:** The class is not decorated with `@celery`, so the `CeleryClientInterceptor` is not wired and the method body runs directly.

**Fix:** Add the `@celery` decorator to the class:

```python
@celery  # required for interception
class MyClient:
    @send_task(name="tasks.process")
    def process(self, data: dict):
        pass  # this body should never execute
```
