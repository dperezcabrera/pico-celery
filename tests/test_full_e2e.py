import pytest
import asyncio
import subprocess
import time
import sys
import os
from celery import Celery
from pico_ioc import init, configuration, DictSource, component
from pico_celery import task, celery, send_task, CeleryClient

TEST_DB_PATH = "/tmp/celery_test_e2e_broker.db"
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

@component(scope="prototype")
class UserTasks:
    @task(name="tasks.create_user")
    async def create_user(self, username: str, email: str) -> dict:
        return {"id": 123, "username": username, "email": email}


@celery
class UserTaskClient(CeleryClient):
    @send_task("tasks.create_user")
    def create_user(self, username: str, email: str):
        pass


@component
class UserService:
    def __init__(self, client: UserTaskClient):
        self.client = client
    
    def create_user_async(self, username: str, email: str):
        return self.client.create_user(username, email)

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
async def test_full_declarative_client_e2e(setup_sqlite_broker):
    python_path = os.pathsep.join([".", "src"])

    worker = subprocess.Popen(
        [
            sys.executable,
            "-m", "celery",
            "-A", "tests.test_full_e2e:celery_app",
            "worker",
            "-P", "solo",
            "-l", "info"
        ],
        env={**os.environ, "PYTHONPATH": python_path}
    )

    time.sleep(3.0)

    service = await container.aget(UserService)
    async_result = service.create_user_async("alice", "alice@example.com")
    
    result = async_result.get(timeout=10)

    worker.terminate()
    worker.wait(timeout=5)

    assert result == {"id": 123, "username": "alice", "email": "alice@example.com"}
