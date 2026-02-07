"""Tests for client.py edge cases and error handling."""

from unittest.mock import MagicMock, patch

import pytest

from pico_celery.client import (
    PICO_CELERY_SENDER_META,
    CeleryClient,
    CeleryClientInterceptor,
    celery,
    send_task,
)


class TestSendTaskDecorator:
    """Tests for @send_task decorator."""

    def test_send_task_on_non_function_raises_type_error(self):
        """@send_task raises TypeError when applied to non-function."""
        with pytest.raises(TypeError, match="can only decorate methods or functions"):
            send_task(name="test_task")(42)  # int is not a function

    def test_send_task_on_class_raises_type_error(self):
        """@send_task raises TypeError when applied to class."""
        with pytest.raises(TypeError, match="can only decorate methods or functions"):

            @send_task(name="test_task")
            class NotAFunction:
                pass

    def test_send_task_sets_metadata(self):
        """@send_task sets metadata on decorated function."""

        @send_task(name="my_task", queue="high")
        def my_func():
            pass

        meta = getattr(my_func, PICO_CELERY_SENDER_META)
        assert meta["name"] == "my_task"
        assert meta["options"]["queue"] == "high"


class TestCeleryDecorator:
    """Tests for @celery decorator."""

    def test_celery_without_tasks_raises_value_error(self):
        """@celery raises ValueError when class has no task methods."""
        with pytest.raises(ValueError, match="No @send_task or @task methods found"):

            @celery
            class NoTasks(CeleryClient):
                def regular_method(self):
                    pass

    def test_celery_with_send_task_decorates_class(self):
        """@celery with @send_task methods decorates the class as a component."""

        @celery
        class TaskClient:
            @send_task(name="test_task")
            def send_something(self):
                pass

        # Class should be decorated with @component
        assert hasattr(TaskClient, "_pico_meta")

    def test_celery_with_worker_tasks_only(self):
        """@celery with only @task methods (no @send_task) decorates the class."""
        from pico_celery.decorators import task

        @celery
        class WorkerOnly:
            @task(name="worker.task")
            async def do_work(self):
                pass

        # Class should be decorated with @component
        assert hasattr(WorkerOnly, "_pico_meta")

    def test_celery_as_decorator_factory(self):
        """@celery() can be used with parentheses."""

        @celery(scope="prototype")
        class TaskClient(CeleryClient):
            @send_task(name="test_task")
            def do_task(self):
                pass

        # Should not raise and class should be decorated
        assert hasattr(TaskClient, "_pico_meta")


class TestCeleryClientInterceptor:
    """Tests for CeleryClientInterceptor."""

    def test_invoke_without_meta_calls_next(self):
        """Interceptor calls next when method has no send_task metadata."""
        mock_celery = MagicMock()
        interceptor = CeleryClientInterceptor(mock_celery)

        mock_ctx = MagicMock()
        mock_ctx.cls = MagicMock()
        mock_ctx.name = "some_method"
        # Method without PICO_CELERY_SENDER_META
        delattr(mock_ctx.cls, mock_ctx.name) if hasattr(mock_ctx.cls, mock_ctx.name) else None

        mock_call_next = MagicMock(return_value="next_result")

        # When getattr raises AttributeError
        mock_ctx.cls = type("TestClass", (), {})()
        result = interceptor.invoke(mock_ctx, mock_call_next)

        mock_call_next.assert_called_once_with(mock_ctx)
        assert result == "next_result"

    def test_invoke_with_meta_sends_task(self):
        """Interceptor sends task via Celery when method has metadata."""
        mock_celery = MagicMock()
        mock_celery.send_task.return_value = "async_result"
        interceptor = CeleryClientInterceptor(mock_celery)

        # Create a class with a method that has the metadata
        class TestClient:
            @send_task(name="test.task", queue="high")
            def my_task(self, arg1, arg2):
                pass

        mock_ctx = MagicMock()
        mock_ctx.cls = TestClient
        mock_ctx.name = "my_task"
        mock_ctx.args = ("value1",)
        mock_ctx.kwargs = {"arg2": "value2"}

        mock_call_next = MagicMock()

        result = interceptor.invoke(mock_ctx, mock_call_next)

        mock_celery.send_task.assert_called_once_with(
            "test.task",
            args=("value1",),
            kwargs={"arg2": "value2"},
            queue="high",
        )
        assert result == "async_result"
        mock_call_next.assert_not_called()
