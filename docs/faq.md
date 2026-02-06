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

### Tasks are not being discovered

Ensure your task modules are scanned by pico-ioc:

```python
from pico_ioc import init

container = init(modules=["myapp.tasks"], config=config)
```

### Dependencies not injected

Make sure your services are registered as components:

```python
from pico_ioc import component

@component
class MyService:
    pass
```

### TypeError: task can only decorate async methods

The `@task` decorator only works on `async def` methods. Convert your method to async:

```python
@task(name="tasks.process")
async def process(self, data: dict):  # Must be async
    ...
```
