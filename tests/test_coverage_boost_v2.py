"""Coverage boost tests for pico-celery.

Targets uncovered lines in registrar.py:
- Lines 104-107: ThreadPoolExecutor path when event loop is already running
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from conftest import make_task_wrapper
from pico_celery.registrar import PicoTaskRegistrar


class TestWrapperWithRunningEventLoop:
    @pytest.fixture
    def registrar(self):
        return PicoTaskRegistrar(MagicMock(), MagicMock())

    @pytest.mark.asyncio
    async def test_wrapper_called_from_running_loop(self, registrar):
        """Lines 104-107: wrapper detects running event loop and uses ThreadPoolExecutor."""
        wrapper, _, _ = make_task_wrapper(registrar, return_value="from_running_loop")

        # Call wrapper directly from async context — asyncio.get_running_loop()
        # will return the running loop, triggering the ThreadPoolExecutor path
        result = wrapper("test_arg")
        assert result == "from_running_loop"
