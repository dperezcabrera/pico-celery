from celery import Celery

from conftest import FakeContainer
from pico_celery.decorators import PICO_CELERY_METHOD_META, task
from pico_celery.registrar import PicoTaskRegistrar


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
