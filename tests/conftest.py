"""Shared test fixtures for pico-celery tests."""

import os
import subprocess
import sys
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── Fake container hierarchy (shared by test_integrated, test_registrar_registration) ──


class FakeMetadata:
    def __init__(self, concrete_class: type) -> None:
        self.concrete_class = concrete_class


class FakeLocator:
    def __init__(self, concrete_class: type, key: str = "comp") -> None:
        self._metadata = {key: FakeMetadata(concrete_class)}


class FakeContainer:
    def __init__(self, concrete_class: type, key: str = "comp") -> None:
        self._locator = FakeLocator(concrete_class, key)
        self._concrete_class = concrete_class
        self.last_instance: Any = None

    async def aget(self, cls: type) -> Any:
        if cls is self._concrete_class:
            instance = cls()
            self.last_instance = instance
            return instance
        raise RuntimeError("Unknown class requested")


# ── Celery worker subprocess fixture ──


@pytest.fixture
def celery_worker_process():
    """Factory fixture: launches a Celery worker subprocess and terminates it after the test."""
    workers: list[subprocess.Popen] = []

    def _start(app_path: str, startup_wait: float = 3.0) -> subprocess.Popen:
        python_path = os.pathsep.join([".", "src"])
        worker = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                app_path,
                "worker",
                "-P",
                "solo",
                "-l",
                "info",
            ],
            env={**os.environ, "PYTHONPATH": python_path},
        )
        time.sleep(startup_wait)
        workers.append(worker)
        return worker

    yield _start

    for w in workers:
        w.terminate()
        w.wait(timeout=5)


# ── Mock task-wrapper helper (test_registrar_coverage) ──


def make_task_wrapper(registrar, *, return_value="result"):
    """Build a mock container + instance and a wrapper via registrar._create_task_wrapper.

    Returns (wrapper, mock_container, mock_instance).
    """
    mock_container = MagicMock()
    mock_instance = MagicMock()
    mock_instance.my_task = AsyncMock(return_value=return_value)
    mock_container.aget = AsyncMock(return_value=mock_instance)

    class MockComponent:
        async def my_task(self, *args, **kwargs):
            pass

    wrapper = registrar._create_task_wrapper(MockComponent, "my_task", mock_container)
    return wrapper, mock_container, mock_instance
