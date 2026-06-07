from celery import Celery
from pico_boot import init
from pico_ioc import YamlTreeSource, configuration

config = configuration(YamlTreeSource("config.yml"))

container = init(
    modules=["tasks"],
    config=config,
)

# Get the Celery app instance for the worker
celery_app = container.get(Celery)
