from typing import Any
from celery import Celery
from pico_celery.decorators import task, PICO_CELERY_METHOD_META
from pico_celery.registrar import PicoTaskRegistrar

class FakeMetadata:
    def __init__(self, concrete_class: type):
        self.concrete_class = concrete_class

class FakeLocator:
    def __init__(self, concrete_class: type):
        self._metadata = {"comp": FakeMetadata(concrete_class)}

class FakeContainer:
    def __init__(self, concrete_class: type):
        self._locator = FakeLocator(concrete_class)
        self._concrete_class = concrete_class

    async def aget(self, cls: type) -> Any:
        if cls is self._concrete_class:
            return cls()
        raise RuntimeError("Unknown class requested")

class SampleComponent:
    def __init__(self) -> None:
        self.called = False

    @task(name="sample.task")
    async def do_work(self, value: int) -> int:
        self.called = True
        return value * 2

def test_registrar_registers_task():
    celery_app = Celery("test_app", broker="memory://", backend="rpc://")
    container = FakeContainer(SampleComponent)
    registrar = PicoTaskRegistrar(container=container, celery_app=celery_app)
    registrar.register_tasks()
    assert "sample.task" in celery_app.tasks
