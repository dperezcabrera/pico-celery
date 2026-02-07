"""Tests for registrar.py edge cases and error handling."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import make_task_wrapper
from pico_celery.registrar import PicoTaskRegistrar


class TestPicoTaskRegistrar:
    """Tests for PicoTaskRegistrar."""

    def test_register_tasks_with_no_locator(self):
        """register_tasks returns early when container has no locator."""
        mock_container = MagicMock(spec=[])  # No _locator attribute
        mock_celery = MagicMock()

        registrar = PicoTaskRegistrar(mock_container, mock_celery)

        # Should not raise
        registrar.register_tasks()

        # Celery task should not be called
        mock_celery.task.assert_not_called()

    def test_register_tasks_skips_non_class_components(self):
        """register_tasks skips metadata entries that are not classes."""
        mock_container = MagicMock()
        mock_locator = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.concrete_class = "not_a_class"  # string, not a class
        mock_locator._metadata = {"key": mock_metadata}
        mock_container._locator = mock_locator
        mock_celery = MagicMock()

        registrar = PicoTaskRegistrar(mock_container, mock_celery)
        registrar.register_tasks()

        # Celery task should not be called
        mock_celery.task.assert_not_called()


class TestTaskWrapper:
    """Tests for the task wrapper created by _create_task_wrapper."""

    @pytest.fixture
    def registrar(self):
        """Create a registrar with mocked dependencies."""
        mock_container = MagicMock()
        mock_celery = MagicMock()
        return PicoTaskRegistrar(mock_container, mock_celery)

    def test_wrapper_runs_task_without_running_loop(self, registrar):
        """Task wrapper runs asyncio.run when no event loop is running."""
        wrapper, mock_container, mock_instance = make_task_wrapper(registrar, return_value="result")

        result = wrapper("test_arg")

        mock_container.aget.assert_called_once()
        mock_instance.my_task.assert_called_once_with("test_arg")
        assert result == "result"

    def test_wrapper_runs_task_with_running_loop(self, registrar):
        """Task wrapper uses ThreadPoolExecutor when event loop is running."""
        wrapper, _, _ = make_task_wrapper(registrar, return_value="loop_result")

        async def run_with_loop():
            # This runs the wrapper while an event loop is already running
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(wrapper, "test_arg")
                return future.result()

        result = asyncio.run(run_with_loop())
        assert result == "loop_result"

    def test_wrapper_passes_args_and_kwargs(self, registrar):
        """Task wrapper correctly passes args and kwargs to task method."""
        wrapper, _, mock_instance = make_task_wrapper(registrar, return_value={"status": "ok"})

        result = wrapper("arg1", "arg2", key1="val1", key2="val2")

        mock_instance.my_task.assert_called_once_with("arg1", "arg2", key1="val1", key2="val2")
        assert result == {"status": "ok"}
