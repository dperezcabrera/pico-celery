import pytest
from celery import Celery
from pico_ioc import init, configuration, DictSource, component
from pico_celery import task, celery, send_task, CeleryClient

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


@pytest.mark.asyncio
async def test_task_client_sends_via_celery():
    cfg = configuration(
        DictSource({
            "celery": {
                "broker_url": "memory://",
                "backend_url": "rpc://",
                "task_track_started": False
            }
        })
    )
    
    container = init(
        modules=["pico_celery", __name__],
        config=cfg
    )
    
    celery_app = container.get(Celery)
    assert "tasks.create_user" in celery_app.tasks
    
    service = container.get(UserService)
    result = service.create_user_async("alice", "alice@example.com")
    
    assert result is not None
    assert hasattr(result, "id")
