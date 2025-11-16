from celery import Celery
from pico_celery.config import CelerySettings
from pico_celery.factory import CeleryFactory

def test_celery_factory_uses_settings():
    settings = CelerySettings(
        broker_url="memory://",
        backend_url="rpc://",
        task_track_started=False,
    )
    factory = CeleryFactory()
    app = factory.create_celery_app(settings)
    assert isinstance(app, Celery)
    assert app.conf.broker_url == "memory://"
    assert str(app.conf.result_backend).startswith("rpc://")
    assert app.conf.task_track_started is False
