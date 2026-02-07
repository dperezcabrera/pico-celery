import asyncio

import pytest
from celery import Celery

from conftest import FakeContainer
from pico_celery.decorators import task
from pico_celery.registrar import PicoTaskRegistrar


class SampleTasks:
    def __init__(self) -> None:
        self.called_with = None

    @task(name="sample.task")
    async def multiply(self, value: int) -> int:
        self.called_with = value
        return value * 2


@pytest.mark.asyncio
async def test_pico_celery_integration_registers_and_executes_task() -> None:
    celery_app = Celery("test_app", broker="memory://", backend="rpc://")
    container = FakeContainer(SampleTasks, key="sample")
    registrar = PicoTaskRegistrar(container=container, celery_app=celery_app)

    registrar.register_tasks()

    assert "sample.task" in celery_app.tasks

    task_obj = celery_app.tasks["sample.task"]

    result = await asyncio.get_event_loop().run_in_executor(None, task_obj.run, 3)

    assert result == 6
    assert isinstance(container.last_instance, SampleTasks)
    assert container.last_instance.called_with == 3
