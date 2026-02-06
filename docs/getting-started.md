# Getting Started

## Installation

Install Pico-Celery using pip:

```bash
pip install pico-celery
```

## Basic Setup

### 1. Configure the Celery broker

```python
from pico_ioc import configuration, DictSource

config = configuration(DictSource({
    "celery": {
        "broker_url": "redis://localhost:6379/0",
        "backend_url": "redis://localhost:6379/1",
    }
}))
```

### 2. Define tasks (Worker Side)

Tasks are `async` methods inside `@component` classes, decorated with `@task`:

```python
from pico_ioc import component
from pico_celery import task

@component(scope="prototype")
class NotificationTasks:
    def __init__(self, notification_service: NotificationService):
        self.service = notification_service

    @task(name="tasks.notify_user")
    async def notify_user(self, user_id: int, message: str):
        await self.service.notify(user_id, message)
```

### 3. Define clients (Client Side)

Clients use `@celery` class decorator and `@send_task` method decorator:

```python
from pico_celery import celery, send_task

@celery
class NotificationClient:
    @send_task(name="tasks.notify_user")
    def notify_user(self, user_id: int, message: str):
        pass  # Method body is never executed
```

The `CeleryClientInterceptor` intercepts method calls and converts them into `celery_app.send_task()` calls.

### 4. Initialize and use

```python
from pico_ioc import init

container = init(modules=["myapp"], config=config)

# In your service or endpoint:
client = container.get(NotificationClient)
result = client.notify_user(user_id=123, message="Hello!")
# Returns an AsyncResult (task sent to broker)
```

## Configuration

`CelerySettings` is a `@configured` dataclass with prefix `"celery"`:

| Field | Type | Description |
|-------|------|-------------|
| `broker_url` | `str` | Celery broker URL |
| `backend_url` | `str` | Celery result backend URL |
| `task_track_started` | `bool` | Track task started state (default: `False`) |

## Auto-Discovery

Pico-Celery registers itself via the `pico_boot.modules` entry point. When using `pico-boot` or `pico-stack`, the `CeleryFactory`, `PicoTaskRegistrar`, and `CeleryClientInterceptor` are auto-discovered.

## Running the Worker

```bash
celery -A myapp worker --loglevel=info -P eventlet
```

The `eventlet` pool is recommended for async task support.

## Next Steps

- Read the [Architecture](architecture.md) documentation
- Check the [FAQ](faq.md) for common questions
