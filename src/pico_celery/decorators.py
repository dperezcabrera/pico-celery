from typing import Any, Callable
import inspect

PICO_CELERY_METHOD_META = "_pico_celery_method_meta"

def task(name: str, **celery_options: Any) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"@task decorator can only be applied to async methods, got: {func.__name__}")
        metadata = {"name": name, "options": celery_options}
        setattr(func, PICO_CELERY_METHOD_META, metadata)
        return func
    return decorator
