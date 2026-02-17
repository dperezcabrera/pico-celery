from pico_ioc import component
from pico_celery import task


@component
class MathTasks:
    """Task definitions for the worker side."""

    @task(name="add")
    def add(self, x: int, y: int) -> int:
        """Add two numbers."""
        return x + y

    @task(name="multiply")
    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        return x * y
