from celery import Celery
from pico_ioc import factory, provides
from .config import CelerySettings

@factory
class CeleryFactory:
    @provides(Celery, scope="singleton")
    def create_celery_app(self, settings: CelerySettings) -> Celery:
        celery_app = Celery(
            "pico_celery_tasks",
            broker=settings.broker_url,
            backend=settings.backend_url,
        )
        celery_app.conf.update(
            task_track_started=settings.task_track_started,
        )
        return celery_app
