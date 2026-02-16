"""Auto-discovery and registration of ``@task``-decorated methods with Celery.

``PicoTaskRegistrar`` is a pico-ioc ``@component`` that runs during the
container's ``@configure`` phase. It scans all registered components for
methods carrying ``@task`` metadata and registers a synchronous wrapper
with the Celery application so that the worker can execute them.
"""

import asyncio
import inspect
from typing import Any, Callable, Type

from celery import Celery
from pico_ioc import PicoContainer, component, configure

from .decorators import PICO_CELERY_METHOD_META


@component
class PicoTaskRegistrar:
    """Discovers ``@task`` methods and registers them with the Celery app.

    This component is created during container initialisation. Its
    ``register_tasks`` method (annotated with ``@configure``) is called
    automatically by pico-ioc after all components are registered,
    ensuring that every ``@task``-decorated async method is made available
    to the Celery worker.

    Args:
        container: The pico-ioc ``PicoContainer`` used for component
            resolution at task execution time.
        celery_app: The ``Celery`` application instance (provided by
            ``CeleryFactory``) on which tasks are registered.
    """

    def __init__(self, container: PicoContainer, celery_app: Celery):
        self._container = container
        self._celery_app = celery_app

    @configure
    def register_tasks(self) -> None:
        """Scan all container components and register ``@task`` methods.

        Iterates over every component registered in the container's
        locator. For each class that has methods decorated with
        ``@task``, a synchronous wrapper is created and registered on the
        Celery application via ``celery_app.task()``.

        This method is invoked automatically by pico-ioc during the
        ``@configure`` lifecycle phase.
        """
        locator = getattr(self._container, "_locator", None)
        if locator is None:
            return
        metadata_map = getattr(locator, "_metadata", {})
        for md in metadata_map.values():
            component_cls = getattr(md, "concrete_class", None)
            if not inspect.isclass(component_cls):
                continue
            for method_name, method_func in inspect.getmembers(component_cls, inspect.isfunction):
                if not hasattr(method_func, PICO_CELERY_METHOD_META):
                    continue
                meta = getattr(method_func, PICO_CELERY_METHOD_META)
                task_name = meta.get("name")
                celery_options = meta.get("options", {})
                wrapper = self._create_task_wrapper(component_cls, method_name, self._container)
                self._celery_app.task(name=task_name, **celery_options)(wrapper)

    def _create_task_wrapper(
        self, component_cls: Type, method_name: str, container: PicoContainer
    ) -> Callable[..., Any]:
        """Build a sync wrapper that resolves the component and runs the async task.

        The wrapper handles event-loop detection: if no loop is running it
        uses ``asyncio.run()``; if a loop is already active (e.g. inside
        an ``eventlet``/``gevent`` worker) it offloads execution to a
        ``ThreadPoolExecutor`` to avoid blocking.

        Args:
            component_cls: The ``@component`` class that owns the task
                method.
            method_name: Name of the ``@task``-decorated method on
                *component_cls*.
            container: The ``PicoContainer`` used to resolve a fresh
                instance of *component_cls* for each execution.

        Returns:
            A synchronous callable suitable for registration with
            ``celery_app.task()``.
        """

        def sync_task_executor(*args: Any, **kwargs: Any) -> Any:
            async def run_task_logic() -> Any:
                component_instance = await container.aget(component_cls)
                task_method = getattr(component_instance, method_name)
                return await task_method(*args, **kwargs)

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, run_task_logic()).result()

            return asyncio.run(run_task_logic())

        return sync_task_executor
