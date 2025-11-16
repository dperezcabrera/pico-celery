from dataclasses import dataclass
from pico_ioc import configured

@configured(target="self", prefix="celery", mapping="tree")
@dataclass
class CelerySettings:
    broker_url: str = "redis://localhost:6379/0"
    backend_url: str = "redis://localhost:6379/1"
    task_track_started: bool = True
