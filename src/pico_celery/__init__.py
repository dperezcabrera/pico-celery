"""Async-first Celery integration for pico-ioc.

pico-celery provides dependency-injected Celery task workers and declarative
task clients, bridging pico-ioc's inversion-of-control container with
Celery 5 distributed task execution.

Worker side:
    Use ``@task`` on ``async def`` methods inside ``@component`` classes to
    define tasks that are automatically discovered and registered by
    ``PicoTaskRegistrar``.

Client side:
    Use ``@celery`` on a class and ``@send_task`` on its methods to create
    declarative, injectable clients whose calls are transparently converted
    into ``celery_app.send_task()`` invocations by ``CeleryClientInterceptor``.

Example:
    .. code-block:: python

        from pico_ioc import component
        from pico_celery import task, celery, send_task

        @component(scope="prototype")
        class EmailTasks:
            def __init__(self, mailer: MailerService):
                self.mailer = mailer

            @task(name="tasks.send_email")
            async def send_email(self, to: str, body: str):
                await self.mailer.send(to, body)

        @celery
        class EmailClient:
            @send_task(name="tasks.send_email")
            def send_email(self, to: str, body: str):
                pass  # body is never executed
"""

from .client import (
    CeleryClient,
    CeleryClientInterceptor,
    celery,
    send_task,
)
from .config import CelerySettings
from .decorators import task
from .factory import CeleryFactory
from .registrar import PicoTaskRegistrar

__all__ = [
    "task",
    "send_task",
    "celery",
    "CeleryClient",
    "CeleryClientInterceptor",
    "CelerySettings",
    "CeleryFactory",
    "PicoTaskRegistrar",
]
