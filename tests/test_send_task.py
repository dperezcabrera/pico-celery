import pytest
from celery import Celery
from pico_ioc import DictSource, configuration, init
from tests.user_components import UserService


@pytest.mark.asyncio
async def test_task_client_sends_via_celery():
    cfg = configuration(
        DictSource({"celery": {"broker_url": "memory://", "backend_url": "rpc://", "task_track_started": False}})
    )

    container = init(modules=["pico_celery", "tests.user_components"], config=cfg)

    celery_app = container.get(Celery)
    assert "tasks.create_user" in celery_app.tasks

    service = container.get(UserService)
    result = service.create_user_async("alice", "alice@example.com")

    assert result is not None
    assert hasattr(result, "id")
