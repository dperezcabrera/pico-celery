"""Configuration dataclass for the Celery application.

``CelerySettings`` is populated automatically from the pico-ioc
configuration tree under the ``celery`` prefix using the
``@configured`` decorator.
"""

from dataclasses import dataclass

from pico_ioc import configured


@configured(target="self", prefix="celery", mapping="tree")
@dataclass
class CelerySettings:
    """Settings required to create a Celery application instance.

    Fields are populated from the pico-ioc configuration source under
    the ``"celery"`` prefix. For example, a ``DictSource`` entry of
    ``{"celery": {"broker_url": "redis://..."}}`` maps to
    ``CelerySettings.broker_url``.

    Attributes:
        broker_url: URL of the message broker
            (e.g. ``"redis://localhost:6379/0"``).
        backend_url: URL of the result backend
            (e.g. ``"redis://localhost:6379/1"``).
        task_track_started: When ``True``, Celery reports a ``STARTED``
            state when a worker begins executing a task. Defaults to
            ``True``.

    Example:
        .. code-block:: python

            from pico_ioc import configuration, DictSource

            config = configuration(DictSource({
                "celery": {
                    "broker_url": "redis://localhost:6379/0",
                    "backend_url": "redis://localhost:6379/1",
                }
            }))
    """

    broker_url: str
    backend_url: str

    task_track_started: bool = True
