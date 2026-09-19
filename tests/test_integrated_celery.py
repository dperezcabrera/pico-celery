import os
import tempfile

import pytest
from celery import Celery
from pico_ioc import DictSource, component, configuration, init

from pico_celery import task

# The worker subprocess imports this module too, so the path travels in the environment;
# a fixed /tmp path made concurrent runs share one broker file.
TEST_DB_PATH = os.environ.setdefault(
    "PICO_CELERY_INTEGRATED_DB", os.path.join(tempfile.mkdtemp(prefix="pico-celery-"), "broker.db")
)
BROKER_URL = f"sqla+sqlite:///{TEST_DB_PATH}"
BACKEND_URL = f"db+sqlite:///{TEST_DB_PATH}"

cfg = configuration(
    DictSource({"celery": {"broker_url": BROKER_URL, "backend_url": BACKEND_URL, "task_track_started": False}})
)


@component
class MathService:
    def mul(self, x, y):
        return x * y


@component(scope="prototype")
class TaskComponent:
    last = None

    def __init__(self, math: MathService):
        self.math = math

    @task(name="tasks.multiply")
    async def multiply(self, x: int) -> int:
        TaskComponent.last = x
        return self.math.mul(x, 2)


container = init(modules=["pico_celery", __name__], config=cfg)

celery_app = container.get(Celery)


@pytest.mark.asyncio
async def test_full_worker_integration(celery_worker_process):
    celery_worker_process("tests.test_integrated_celery:celery_app")

    async_result = celery_app.send_task("tasks.multiply", args=[7])
    result = async_result.get(timeout=10)

    assert result == 14
