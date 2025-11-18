import inspect
from typing import Any, Callable, Optional, runtime_checkable, Protocol
from celery import Celery
from pico_ioc import component, MethodCtx, MethodInterceptor, intercepted_by

PICO_CELERY_SENDER_META = "_pico_celery_sender_meta"

@runtime_checkable
class CeleryClient(Protocol):
    pass

def send_task(
    name: str,
    **celery_options: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.isfunction(func) and not inspect.ismethod(func):
            raise TypeError("send_task can only decorate methods or functions")
        metadata = {"name": name, "options": dict(celery_options)}
        setattr(func, PICO_CELERY_SENDER_META, metadata)
        return func
    return decorator

def celery(
    cls: Optional[type] = None,
    *,
    scope: str = "singleton",
    **kwargs: Any
):
    def decorate(c: type) -> type:
        has_send_tasks = False
        has_worker_tasks = False
        
        for name, method in inspect.getmembers(c, inspect.isfunction):
            if hasattr(method, PICO_CELERY_SENDER_META):
                has_send_tasks = True
                setattr(method, "_needs_interception", True)
            
            from .decorators import PICO_CELERY_METHOD_META
            if hasattr(method, PICO_CELERY_METHOD_META):
                has_worker_tasks = True
        
        if not has_send_tasks and not has_worker_tasks:
            raise ValueError(f"No @send_task or @task methods found on {c.__name__}")
        
        if has_send_tasks:
            if not issubclass(c, CeleryClient):
                raise TypeError(f"{c.__name__} with @send_task methods must inherit from CeleryClient")
            
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
    def __init__(self, celery_app: Celery):
        self._celery = celery_app
    
    def invoke(
        self,
        ctx: MethodCtx,
        call_next: Callable[[MethodCtx], Any]
    ) -> Any:
        try:
            original_func = getattr(ctx.cls, ctx.name)
            meta = getattr(original_func, PICO_CELERY_SENDER_META, None)
        except AttributeError:
            meta = None
        
        if not meta:
            return call_next(ctx)
        
        task_name = meta["name"]
        options = meta.get("options", {})
        
        return self._celery.send_task(
            task_name,
            args=ctx.args,
            kwargs=ctx.kwargs,
            **options
        )
