# Pico-Celery

Async-first Celery integration for pico-ioc. Declarative task workers and clients with DI.

## Features

- **Worker Side**: Define Celery tasks as `async` methods on `@component` classes with `@task`
- **Client Side**: Declarative task clients with `@celery` and `@send_task` decorators
- **Dependency Injection**: Full constructor-based DI via pico-ioc
- **Auto-Discovery**: Automatic task registration via `PicoTaskRegistrar`
- **Configuration**: `CelerySettings` via pico-ioc's `@configured`

## Quick Start

### Worker: Define tasks

```python
from pico_ioc import component
from pico_celery import task

@component(scope="prototype")
class EmailTasks:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    @task(name="tasks.send_email")
    async def send_email(self, to: str, subject: str, body: str):
        await self.email_service.send(to, subject, body)
```

### Client: Send tasks

```python
from pico_celery import celery, send_task

@celery
class EmailClient:
    @send_task(name="tasks.send_email")
    def send_email(self, to: str, subject: str, body: str):
        pass  # Body is never executed
```

## Installation

```bash
pip install pico-celery
```

## Requirements

- Python 3.11+
- pico-ioc >= 2.2.0
- Celery 5.3+

## Documentation

- [Getting Started](getting-started.md) - Installation and basic usage
- [Architecture](architecture.md) - Design and implementation details
- [How-To: Retry with Backoff](how-to/retry.md) - Configure retry and exponential backoff
- [How-To: Testing](how-to/testing.md) - Test tasks without a broker
- [How-To: Periodic Tasks](how-to/periodic-tasks.md) - Set up scheduled tasks with Celery Beat
- [FAQ](faq.md) - Frequently asked questions and troubleshooting

## License

MIT License - see LICENSE file for details.
