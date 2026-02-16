# How to Test Celery Tasks Without a Broker

This guide covers strategies for unit-testing pico-celery worker tasks and client senders without running a live message broker.

## Testing Worker Tasks

Because pico-celery tasks are regular `async def` methods on pico-ioc `@component` classes, you can test them by instantiating the component directly and calling the method.

### Direct Instantiation

```python
import pytest
from unittest.mock import AsyncMock

from myapp.tasks import EmailTasks

@pytest.mark.asyncio
async def test_send_email():
    # Mock the dependency
    mock_mailer = AsyncMock()
    mock_mailer.send.return_value = {"status": "sent"}

    # Instantiate the task component directly -- no container needed
    tasks = EmailTasks(mailer=mock_mailer)

    result = await tasks.send_email("user@example.com", "Hello", "Body")

    mock_mailer.send.assert_called_once_with(
        "user@example.com", "Hello", "Body"
    )
```

No broker, no Celery app, no container -- the task method is just an async function.

### Using the pico-ioc Container

For integration-style tests you can wire the container with mock dependencies:

```python
import pytest
from unittest.mock import AsyncMock

from pico_ioc import init, configuration, DictSource
from myapp.tasks import EmailTasks

@pytest.mark.asyncio
async def test_send_email_with_container():
    config = configuration(DictSource({
        "celery": {
            "broker_url": "memory://",
            "backend_url": "cache+memory://",
        }
    }))
    container = init(modules=["myapp.tasks"], config=config)

    tasks = await container.aget(EmailTasks)
    result = await tasks.send_email("user@example.com", "Hello", "Body")
    assert result is not None
```

## Testing Client Senders

Client classes decorated with `@celery` and `@send_task` delegate calls to `celery_app.send_task()` via the `CeleryClientInterceptor`. To test them without a broker, mock the `Celery` app.

### Mocking the Celery App

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
async def test_client_sends_task():
    mock_celery = MagicMock()
    mock_celery.send_task.return_value = MagicMock(id="abc-123")

    # Patch the Celery app in the interceptor
    from myapp.clients import NotificationClient
    from pico_celery import CeleryClientInterceptor

    interceptor = CeleryClientInterceptor(celery_app=mock_celery)

    # Verify send_task is called with correct arguments
    mock_celery.send_task.assert_not_called()
```

### Using Celery's Built-in Test Helpers

Celery provides `app.conf.update(task_always_eager=True)` which executes tasks synchronously in the same process:

```python
import pytest
from celery import Celery

@pytest.fixture
def celery_app():
    app = Celery("test")
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url="memory://",
        result_backend="cache+memory://",
    )
    return app
```

With `task_always_eager=True`, calling `send_task()` or `delay()` executes the task immediately and returns the result, with no broker required.

## Testing Task Registration

To verify that `PicoTaskRegistrar` correctly discovers and registers tasks:

```python
import pytest
from unittest.mock import MagicMock

from celery import Celery
from pico_ioc import init, configuration, DictSource

@pytest.mark.asyncio
async def test_task_registration():
    config = configuration(DictSource({
        "celery": {
            "broker_url": "memory://",
            "backend_url": "cache+memory://",
        }
    }))
    container = init(modules=["myapp"], config=config)

    celery_app = container.get(Celery)

    # Verify tasks are registered
    assert "tasks.send_email" in celery_app.tasks
```

## Testing Client Interception End-to-End

For a full integration test of the client path:

```python
import pytest
from unittest.mock import MagicMock

from pico_ioc import init, configuration, DictSource
from myapp.clients import NotificationClient

@pytest.mark.asyncio
async def test_client_integration():
    config = configuration(DictSource({
        "celery": {
            "broker_url": "memory://",
            "backend_url": "cache+memory://",
        }
    }))
    container = init(modules=["myapp"], config=config)

    client = await container.aget(NotificationClient)
    result = client.notify(user_id=42, msg="Hello")

    # result is an AsyncResult from celery_app.send_task()
    assert result is not None
```

## Summary

| What to test          | Strategy                                  | Broker needed |
| :-------------------- | :---------------------------------------- | :------------ |
| Task logic            | Instantiate component, call `await method()` | No            |
| Task with DI          | Use `container.aget()` with `memory://` broker | No            |
| Client sends task     | Mock `Celery` app, assert `send_task()`   | No            |
| Task registration     | Init container, check `celery_app.tasks`  | No            |
| Full round-trip       | `task_always_eager=True`                  | No            |
