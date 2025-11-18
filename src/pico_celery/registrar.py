import inspect
import asyncio
from typing import Any, Callable, Type
from celery import Celery
from pico_ioc import component, configure, PicoContainer
from .decorators import PICO_CELERY_METHOD_META

@component
class PicoTaskRegistrar:
    def __init__(self, container: PicoContainer, celery_app: Celery):
        self._container = container
        self._celery_app = celery_app

    @configure
    def register_tasks(self) -> None:
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

    def _create_task_wrapper(self, component_cls: Type, method_name: str, container: PicoContainer) -> Callable[..., Any]:
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
