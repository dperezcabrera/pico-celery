"""Client-side decorators and interceptor for sending Celery tasks.

This module provides:

* ``CeleryClient`` -- a runtime-checkable ``Protocol`` used as a marker
  interface for client classes.
* ``@send_task`` -- method decorator that marks a method as a task sender.
* ``@celery`` -- class decorator that registers a class as a pico-ioc
  component and wires ``CeleryClientInterceptor`` to its ``@send_task``
  methods.
* ``CeleryClientInterceptor`` -- a ``MethodInterceptor`` that intercepts
  calls to ``@send_task`` methods and converts them into
  ``celery_app.send_task()`` invocations.
"""

import inspect
from typing import Any, Callable, Optional, Protocol, runtime_checkable

from celery import Celery
from pico_ioc import MethodCtx, MethodInterceptor, component, intercepted_by

from .decorators import PICO_CELERY_METHOD_META

PICO_CELERY_SENDER_META = "_pico_celery_sender_meta"
"""str: Attribute name used to store sender metadata on decorated methods."""


@runtime_checkable
class CeleryClient(Protocol):
    """Marker protocol for Celery client classes.

    Classes decorated with ``@celery`` may optionally implement this
    protocol. It carries no methods -- its sole purpose is to provide a
    type that can be used for ``isinstance`` checks and type-hint
    annotations.
    """

    pass


def send_task(name: str, **celery_options: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark a method as a Celery task sender.

    When a method decorated with ``@send_task`` is called on a class
    that has been decorated with ``@celery``, the
    ``CeleryClientInterceptor`` intercepts the call and converts it into
    ``celery_app.send_task()``. The method body is **never executed**.

    Args:
        name: The Celery task name to send
            (e.g. ``"tasks.send_email"``).
        **celery_options: Additional keyword arguments forwarded to
            ``celery_app.send_task()`` (e.g. ``queue``, ``countdown``,
            ``eta``, ``expires``).

    Returns:
        A decorator that attaches sender metadata to the function and
        returns the original function unchanged.

    Raises:
        TypeError: If the target is not a function or method.

    Example:
        .. code-block:: python

            from pico_celery import celery, send_task

            @celery
            class NotificationClient:
                @send_task(name="tasks.notify", queue="high")
                def notify(self, user_id: int, msg: str):
                    pass  # body is never executed
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.isfunction(func) and not inspect.ismethod(func):
            raise TypeError("send_task can only decorate methods or functions")
        metadata = {"name": name, "options": dict(celery_options)}
        setattr(func, PICO_CELERY_SENDER_META, metadata)
        return func

    return decorator


def celery(cls: Optional[type] = None, *, scope: str = "singleton", **kwargs: Any):
    """Class decorator that registers a Celery client or worker component.

    Scans the decorated class for methods marked with ``@send_task`` or
    ``@task``. For ``@send_task`` methods it wires the
    ``CeleryClientInterceptor`` via pico-ioc's ``@intercepted_by``.
    The class is then registered as a pico-ioc ``@component``.

    Can be used with or without parentheses::

        @celery
        class MyClient: ...

        @celery(scope="prototype")
        class MyClient: ...

    Args:
        cls: The class to decorate. Passed automatically when the
            decorator is used without parentheses.
        scope: The pico-ioc scope for the component. Defaults to
            ``"singleton"``.
        **kwargs: Additional keyword arguments forwarded to
            ``pico_ioc.component()``.

    Returns:
        The decorated class registered as a pico-ioc component, or a
        decorator if *cls* is ``None``.

    Raises:
        ValueError: If the class contains no ``@send_task`` or ``@task``
            methods (exact message:
            ``"No @send_task or @task methods found on <ClassName>"``).

    Example:
        .. code-block:: python

            from pico_celery import celery, send_task

            @celery
            class OrderClient:
                @send_task(name="tasks.place_order")
                def place_order(self, order_id: int):
                    pass
    """

    def decorate(c: type) -> type:
        has_send_tasks = False
        has_worker_tasks = False

        for name, method in inspect.getmembers(c, inspect.isfunction):
            if hasattr(method, PICO_CELERY_SENDER_META):
                has_send_tasks = True
                setattr(method, "_needs_interception", True)

            if hasattr(method, PICO_CELERY_METHOD_META):
                has_worker_tasks = True

        if not has_send_tasks and not has_worker_tasks:
            raise ValueError(f"No @send_task or @task methods found on {c.__name__}")

        if has_send_tasks:
            for name, method in inspect.getmembers(c, inspect.isfunction):
                if getattr(method, "_needs_interception", False):
                    intercepted_method = intercepted_by(CeleryClientInterceptor)(method)
                    setattr(c, name, intercepted_method)

        return component(c, scope=scope, **kwargs)

    if cls is not None:
        return decorate(cls)
    return decorate


@component
class CeleryClientInterceptor(MethodInterceptor):
    """AOP interceptor that converts method calls into ``send_task`` invocations.

    Registered as a pico-ioc ``@component`` and injected with the
    ``Celery`` application. When a ``@send_task``-decorated method is
    called, this interceptor reads the stored metadata and delegates to
    ``celery_app.send_task()``.

    Args:
        celery_app: The ``Celery`` application instance provided by
            ``CeleryFactory``.
    """

    def __init__(self, celery_app: Celery):
        self._celery = celery_app

    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        """Intercept a method call and dispatch it as a Celery task.

        If the called method carries ``@send_task`` metadata, the
        interceptor extracts the task name and options and calls
        ``celery_app.send_task()``. Otherwise the call is forwarded to
        the next handler in the interceptor chain.

        Args:
            ctx: The method invocation context containing the class,
                method name, positional args, and keyword args.
            call_next: Callable to invoke the next interceptor or the
                original method.

        Returns:
            A ``celery.result.AsyncResult`` when the method is a
            ``@send_task`` sender, or the result of *call_next* for
            non-sender methods.
        """
        try:
            original_func = getattr(ctx.cls, ctx.name)
            meta = getattr(original_func, PICO_CELERY_SENDER_META, None)
        except AttributeError:
            meta = None

        if not meta:
            return call_next(ctx)

        task_name = meta["name"]
        options = meta.get("options", {})

        return self._celery.send_task(task_name, args=ctx.args, kwargs=ctx.kwargs, **options)
