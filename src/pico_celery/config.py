from dataclasses import dataclass
from typing import Optional
from pico_ioc import configured

@configured(target="self", prefix="celery", mapping="tree")
@dataclass
class CelerySettings:
    broker_url: str
    backend_url: str
    
    task_track_started: bool = True
