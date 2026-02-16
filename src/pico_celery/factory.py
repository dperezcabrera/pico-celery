"""Factory that creates a singleton Celery application from ``CelerySettings``.

The ``CeleryFactory`` is a pico-ioc ``@factory`` whose ``@provides``
method builds and configures a ``celery.Celery`` instance, making it
available for injection throughout the application.
"""

from celery import Celery
from pico_ioc import factory, provides

from .config import CelerySettings


@factory
class CeleryFactory:
    """IoC factory that provides a singleton ``Celery`` application.

    Registered with pico-ioc via the ``@factory`` decorator. Its
    ``create_celery_app`` method is discovered automatically and called
    once to produce the shared ``Celery`` instance.

    Example:
        The factory is auto-discovered; no manual instantiation is needed.
        Simply inject ``Celery`` wherever required:

        .. code-block:: python

            from celery import Celery
            from pico_ioc import component

            @component
            class MyService:
                def __init__(self, app: Celery):
                    self._app = app
    """

    @provides(Celery, scope="singleton")
    def create_celery_app(self, settings: CelerySettings) -> Celery:
        """Create and configure a ``Celery`` application instance.

        Args:
            settings: A ``CelerySettings`` instance populated from the
                pico-ioc configuration tree.

        Returns:
            A fully configured ``Celery`` application with the broker,
            backend, and tracking options applied.
        """
        celery_app = Celery(
            "pico_celery_tasks",
            broker=settings.broker_url,
            backend=settings.backend_url,
        )
        celery_app.conf.update(
            task_track_started=settings.task_track_started,
        )
        return celery_app
