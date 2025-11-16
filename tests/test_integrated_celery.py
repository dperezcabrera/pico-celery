import pytest
import asyncio
import subprocess
import time
import sys
import os
from celery import Celery
from pico_ioc import init, configuration, DictSource, component
from pico_celery import task

TEST_DB_PATH = "/tmp/celery_test_broker.db"
BROKER_URL = f"sqla+sqlite:///{TEST_DB_PATH}"
BACKEND_URL = f"db+sqlite:///{TEST_DB_PATH}"

cfg = configuration(
    DictSource({
        "celery": {
            "broker_url": BROKER_URL,
            "backend_url": BACKEND_URL,
            "task_track_started": False
        }
    })
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

container = init(
    modules=["pico_celery", __name__],
    config=cfg
)

celery_app = container.get(Celery)

@pytest.fixture
def setup_sqlite_broker(autouse=True):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.mark.asyncio
async def test_full_worker_integration(setup_sqlite_broker):
    python_path = os.pathsep.join([".", "src"])

    worker = subprocess.Popen(
        [
            sys.executable,
            "-m", "celery",
            "-A", "tests.test_integrated_celery:celery_app",
            "worker",
            "-P", "solo",
            "-l", "info"
        ],
        env={**os.environ, "PYTHONPATH": python_path}
    )

    time.sleep(3.0)

    async_result = celery_app.send_task("tasks.multiply", args=[7])
    result = async_result.get(timeout=10)

    worker.terminate()
    worker.wait(timeout=5)

    assert result == 14
