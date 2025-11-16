import pytest
import asyncio
from pico_celery.decorators import task, PICO_CELERY_METHOD_META

def test_task_decorator_requires_async():
    def sync_func():
        return 1
    with pytest.raises(TypeError):
        task(name="sync_task")(sync_func)

@pytest.mark.asyncio
async def test_task_decorator_sets_metadata():
    @task(name="example_task", queue="default")
    async def sample(arg: int) -> int:
        return arg + 1
    meta = getattr(sample, PICO_CELERY_METHOD_META, None)
    assert meta is not None
    assert meta["name"] == "example_task"
    assert meta["options"]["queue"] == "default"
    result = await sample(1)
    assert result == 2
