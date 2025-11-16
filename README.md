# 📦 pico-celery

[![PyPI](https://img.shields.io/pypi/v/pico-celery.svg)](https://pypi.org/project/pico-celery/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-celery)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-celery/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-celery/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-celery)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-celery\&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-celery)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-celery\&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-celery)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-celery\&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-celery)

# Pico-Celery

**Pico-Celery** integrates **[Pico-IoC](https://github.com/dperezcabrera/pico-ioc)** with **Celery 5**, giving you true inversion of control for background task execution.

It lets you define Celery tasks as **async methods inside IoC-managed components**, with automatic discovery, dependency injection, and container-scoped execution.

> 🐍 Requires Python 3.10+
> ⚡ **Async-native**: tasks run as real `async def`, with no thread pools
> 🔧 Works with Celery 5.x
> 🧩 Full constructor-based DI
> 🚀 Perfect for FastAPI apps, worker daemons, and distributed pipelines

With pico-celery, you get predictable scoping, a clean separation of concerns, and a unified dependency model across HTTP, CLI, and background execution.

-----

## 🎯 Why pico-celery?

Celery is powerful, but typical usage introduces:

  * Module-level tasks
  * Global Celery apps
  * No dependency injection
  * Shared mutable state
  * Difficult testing setups

**pico-celery fixes all of that**:

  * Tasks become async methods inside components
  * Dependency injection is constructor-based
  * Task handlers are resolved through Pico-IoC
  * Each execution receives a fresh instance (`prototype` scope)
  * Workers bootstrap the IoC container exactly once
  * No global state, no magic imports, no tight coupling

| Feature | Default Celery | pico-celery |
| :--- | :--- | :--- |
| **Task Definition** | Global functions | Component methods |
| **Dependency Injection** | None | Constructor injection |
| **State Isolation** | Manual | Automatic (`prototype` scope) |
| **Testability** | Hard | Container-managed |
| **Async Tasks** | Requires custom pools | First-class async |
| **Task Clients** | Manual (`app.send_task`) | Declarative (`@send_task`) |

-----

## 🧱 Core Features

  * **`@task`** decorator for async component methods
  * **`@celery`** and **`@send_task`** decorators for declarative, injectable clients
  * Automatic task discovery inside Pico-IoC
  * Dependency injection for all task handlers
  * Container-scoped execution (`prototype` by default)
  * Async-safe task execution wrappers
  * Unified config via `CelerySettings`
  * Method interception for client-side task sending

-----

## 📦 Installation

```bash
pip install pico-celery
```

You will also need:

```bash
pip install pico-ioc celery
```

If using Redis (recommended):

```bash
pip install celery[redis]
```

-----

## 🚀 Quick Example

This example shows both a *worker* and a *client* that sends the task.

### 1\. Define a Task Component (Worker)

This component defines the task logic and its dependencies.

```python
# my_app/tasks.py
from pico_ioc import component
from pico_celery import task
from my_app.services import UserService # Your business logic

@component(scope="prototype")
class UserTasks:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    @task(name="tasks.create_user")
    async def create_user(self, username: str, email: str) -> dict:
        # Real async logic with injected dependencies
        user = await self.user_service.create(username, email)
        return user.to_dict()
```

### 2\. Define a Task Client (Sender)

This is a declarative client that your web API (e.g., FastAPI) can inject and use.

```python
# my_app/clients.py
from pico_celery import celery, send_task, CeleryClient

@celery # Marks it as a pico-celery client component
class UserTaskClient(CeleryClient):

    @send_task(name="tasks.create_user")
    def create_user(self, username: str, email: str):
        # This body is never executed.
        # pico-celery intercepts the call and sends it to Celery.
        pass
```

### 3\. Create the Worker Entrypoint

This file (`worker.py`) is what Celery will use to boot up.

```python
# my_app/worker.py
from pico_ioc import init, configuration, DictSource
from celery import Celery

# Your application's configuration (broker, backend, etc.)
cfg = configuration(DictSource({
    "celery": {
        "broker_url": "redis://localhost:6379/0",
        "backend_url": "redis://localhost:6379/1"
    }
}))

# Modules to scan for @component, @task, @celery
modules = [
    "pico_celery",
    "my_app.services",
    "my_app.tasks",
    "my_app.clients"
]

# Initialize the container
container = init(modules=modules, config=cfg)

# Get the IoC-managed Celery app
# The PicoTaskRegistrar has already found and registered
# the 'tasks.create_user' task.
celery_app = container.get(Celery)
```

### 4\. Run the Worker

You will need an async pool like `eventlet` or `gevent`.

```bash
# Install the pool: pip install eventlet
celery -A my_app.worker:celery_app worker -P eventlet -l info
```

### 5\. Use the Client in your API

Your web API (e.g., FastAPI) can now inject the `UserTaskClient` and use it.

```python
# my_app/main.py
from fastapi import FastAPI
from pico_ioc import init
from my_app.clients import UserTaskClient
from my_app.worker import container # Reuse the worker's container

app = FastAPI()

@app.post("/users/")
async def create_user_endpoint(username: str, email: str):
    # Resolve the client from the container
    client = await container.aget(UserTaskClient)
    
    # Call the client method
    # This sends the task to Celery and returns an AsyncResult
    result = client.create_user(username, email)
    
    return {"message": "Task submitted", "task_id": result.id}
```

-----

## 🔄 Task Execution Semantics (Worker)

When Celery receives a task:

```
Celery Worker
     ↓
Async Wrapper (generated by PicoTaskRegistrar)
     ↓
await container.aget(UserTasks)  (Resolves component + dependencies)
     ↓
component_instance.create_user(...) (Executes your async method)
     ↓
await self.user_service.create(...)
     ↓
'prototype' scope is destroyed
```

**Key benefits:**

  * True async execution.
  * No global state.
  * Fully injected services.
  * Guaranteed isolation via `prototype` scope.

-----

## 🧪 Testing with Pico-IoC

You can test your task logic just like any other component, **with no Celery worker needed**.

```python
import pytest
from pico_ioc import init, configuration, DictSource
from my_app.tasks import UserTasks
from unittest.mock import AsyncMock, MagicMock

# Mock the dependencies
@pytest.fixture
def mock_user_service():
    service = AsyncMock()
    service.create.return_value = MagicMock(to_dict=lambda: {"id": 1})
    return service

@pytest.mark.asyncio
async def test_user_task_logic(mock_user_service):
    cfg = configuration(DictSource({}))
    
    # Initialize the container with only the task
    container = init(modules=[UserTasks], config=cfg)
    
    # Register the mocked dependency
    container.register_instance(mock_user_service)

    # Resolve the task component
    task_component = await container.aget(UserTasks)
    
    # Call the async method directly
    result = await task_component.create_user("test", "test@example.com")

    # Assert the logic
    assert result == {"id": 1}
    mock_user_service.create.assert_called_with("test", "test@example.com")
    
    await container.cleanup_all_async()
```

-----

## ⚙️ How It Works

  * **`@task`** (in `decorators.py`) flags `async` methods inside components.
  * **`PicoTaskRegistrar`** (in `registrar.py`) is a component that scans IoC metadata upon configuration.
  * For each `@task` method found, it generates an async *wrapper*.
  * This *wrapper* is what gets registered with Celery (`celery_app.task(...)`).
  * When Celery executes the task, it invokes the *wrapper*, which in turn uses `await container.aget(Component)` to get a fresh instance (thanks to `prototype`) and then calls your original method, ensuring DI.
  * **`@send_task`** (in `client.py`) flags methods on client classes.
  * **`@celery`** (in `client.py`) applies an interceptor (`CeleryClientInterceptor`) to all methods flagged with `@send_task`.
  * When you call a client method (e.g., `client.create_user(...)`), the interceptor activates, extracts the `@send_task` metadata (like the task name) and the call arguments, and executes `self._celery.send_task(...)` on your behalf.

-----

## 💡 Architecture Overview

`pico-celery` manages both sides: the **Worker** (execution) and the **Client** (sending).

### Worker Flow (Task Execution)

```
       ┌─────────────────────────────┐
       │        Celery Worker        │
       └─────────────┬─────────────┘
                     │
         Async Wrapper (from pico-celery)
                     │
       ┌─────────────▼─────────────┐
       │         pico-celery       │
       │  (@task, Registrar, Scopes) │
       └─────────────┬─────────────┘
                     │
          IoC Resolution (await aget)
                     │
       ┌─────────────▼─────────────┐
       │           Pico-IoC        │
       │ (Container, Scopes, DI)   │
       └─────────────┬─────────────┘
                     │
      Your Business Logic (Services, Repos)
```

### Client Flow (Task Sending)

```
       ┌─────────────────────────────┐
       │      Your App (e.g., FastAPI) │
       └─────────────┬─────────────┘
                     │
     Call to: client.create_user(...)
                     │
       ┌─────────────▼─────────────┐
       │         pico-celery       │
       │ (@celery, @send_task, Interceptor)
       └─────────────┬─────────────┘
                     │
      Intercepts call and transforms it into:
      celery_app.send_task("tasks.create_user", ...)
                     │
       ┌─────────────▼─────────────┐
       │       Broker (e.g., Redis)  │
       └─────────────────────────────┘
```

-----

## 📝 License

MIT
