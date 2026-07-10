import pytest
from celery import Celery
from pico_ioc import DictSource, configuration, init
from tests.user_components import UserService

TEST_DB_PATH = "/tmp/celery_test_e2e_broker.db"
BROKER_URL = f"sqla+sqlite:///{TEST_DB_PATH}"
BACKEND_URL = f"db+sqlite:///{TEST_DB_PATH}"

cfg = configuration(
    DictSource({"celery": {"broker_url": BROKER_URL, "backend_url": BACKEND_URL, "task_track_started": False}})
)

container = init(modules=["pico_celery", "tests.user_components"], config=cfg)

celery_app = container.get(Celery)


@pytest.mark.asyncio
async def test_full_declarative_client_e2e(celery_worker_process):
    worker = celery_worker_process("tests.test_full_e2e:celery_app")

    service = await container.aget(UserService)
    async_result = service.create_user_async("alice", "alice@example.com")

    result = async_result.get(timeout=10)

    assert result == {"id": 123, "username": "alice", "email": "alice@example.com"}
