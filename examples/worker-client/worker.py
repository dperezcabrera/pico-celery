from pico_boot import init
from pico_ioc import configuration, YamlTreeSource

config = configuration(YamlTreeSource("config.yml"))

container = init(
    modules=["tasks"],
    config=config,
)

# Get the Celery app instance for the worker
from celery import Celery

celery_app = container.get(Celery)
