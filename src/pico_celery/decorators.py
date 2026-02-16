"""Worker-side ``@task`` decorator for marking async methods as Celery tasks.

This module provides the ``@task`` decorator used on ``async def`` methods
inside pico-ioc ``@component`` classes. Decorated methods are later
discovered by ``PicoTaskRegistrar`` and registered with the Celery
application.
"""

import inspect
from typing import Any, Callable

PICO_CELERY_METHOD_META = "_pico_celery_method_meta"
"""str: Attribute name used to store task metadata on decorated methods."""


def task(name: str, **celery_options: Any) -> Callable[[Callable], Callable]:
    """Mark an async method as a Celery task.

    The decorated method must be an ``async def`` coroutine. The decorator
    attaches metadata (task name and Celery options) to the function so
    that ``PicoTaskRegistrar`` can discover and register it at startup.

    Args:
        name: The Celery task name used for routing (e.g. ``"tasks.send_email"``).
        **celery_options: Additional keyword arguments forwarded to
            ``celery_app.task()`` during registration (e.g. ``queue``,
            ``max_retries``, ``default_retry_delay``).

    Returns:
        A decorator that attaches task metadata to the function and
        returns the original function unchanged.

    Raises:
        TypeError: If the decorated function is not an ``async def``
            coroutine function.

    Example:
        .. code-block:: python

            from pico_ioc import component
            from pico_celery import task

            @component(scope="prototype")
            class NotificationTasks:
                @task(name="tasks.notify", queue="high")
                async def notify(self, user_id: int, msg: str):
                    ...
    """

    def decorator(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"@task decorator can only be applied to async methods, got: {func.__name__}")
        metadata = {"name": name, "options": celery_options}
        setattr(func, PICO_CELERY_METHOD_META, metadata)
        return func

    return decorator
