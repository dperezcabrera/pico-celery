import pytest
from celery import Celery
from typing import Any

from pico_celery.decorators import task
from pico_celery.registrar import PicoTaskRegistrar


class SampleTasks:
    def __init__(self) -> None:
        self.called_with = None

    @task(name="sample.task")
    async def multiply(self, value: int) -> int:
        self.called_with = value
        return value * 2


class FakeMetadata:
    def __init__(self, concrete_class: type) -> None:
        self.concrete_class = concrete_class


class FakeLocator:
    def __init__(self, concrete_class: type) -> None:
        self._metadata = {"sample": FakeMetadata(concrete_class)}


class FakeContainer:
    def __init__(self, concrete_class: type) -> None:
        self._locator = FakeLocator(concrete_class)
        self._concrete_class = concrete_class
        self.last_instance: Any = None

    async def aget(self, cls: type) -> Any:
        if cls is self._concrete_class:
            instance = cls()
            self.last_instance = instance
            return instance
        raise RuntimeError("Unknown class requested")


@pytest.mark.asyncio
async def test_pico_celery_integration_registers_and_executes_task() -> None:
    celery_app = Celery("test_app", broker="memory://", backend="rpc://")
    container = FakeContainer(SampleTasks)
    registrar = PicoTaskRegistrar(container=container, celery_app=celery_app)

    registrar.register_tasks()

    assert "sample.task" in celery_app.tasks

    task_obj = celery_app.tasks["sample.task"]
    
    import asyncio
    result = await asyncio.get_event_loop().run_in_executor(
        None, 
        task_obj.run, 
        3
    )

    assert result == 6
    assert isinstance(container.last_instance, SampleTasks)
    assert container.last_instance.called_with == 3
