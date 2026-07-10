from pico_ioc import component

from pico_celery import CeleryClient, celery, send_task, task


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
