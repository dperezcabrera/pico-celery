# Claude Code Skills

Pico-Celery includes pre-designed skills for [Claude Code](https://claude.ai/claude-code) that enable AI-assisted development following pico-framework patterns and best practices.

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Pico Celery Task** | `/pico-celery-task` | Creates Celery tasks integrated with pico-ioc |
| **Pico Test Generator** | `/pico-tests` | Generates tests for pico-framework components |

---

## Pico Celery Task

Creates Celery tasks as async methods inside IoC-managed components.

### Basic Task

```python
from pico_celery import task, celery, CeleryClient

@celery
class MyTaskClient(CeleryClient):
    @task(name="tasks.process")
    async def process(self, item_id: int) -> dict:
        return {"status": "done", "item_id": item_id}
```

### With Retry and Options

```python
@celery
class MyTaskClient(CeleryClient):
    @task(
        name="tasks.process",
        bind=True,
        max_retries=3,
        default_retry_delay=60,
        autoretry_for=(ConnectionError,),
    )
    async def process(self, item_id: int) -> dict:
        ...
```

### Declarative Client

```python
@celery
class NotificationClient(CeleryClient):
    @send_task(name="notifications.send", queue="notifications")
    def send_notification(self, user_id: int, message: str):
        pass  # Method body is never executed; sends task to Celery
```

---

## Pico Test Generator

Generates tests for any pico-framework component.

### Testing Tasks

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from pico_ioc import init, configuration, DictSource

@pytest.mark.asyncio
async def test_task_logic(mock_service):
    cfg = configuration(DictSource({}))
    container = init(modules=[UserTasks], config=cfg)
    task = await container.aget(UserTasks)
    result = await task.create_user("test", "test@example.com")
    assert result == {"id": 1}
```

---

## Installation

```bash
# Project-level (recommended)
mkdir -p .claude/skills/pico-celery-task
# Copy the skill YAML+Markdown to .claude/skills/pico-celery-task/SKILL.md

mkdir -p .claude/skills/pico-tests
# Copy the skill YAML+Markdown to .claude/skills/pico-tests/SKILL.md

# Or user-level (available in all projects)
mkdir -p ~/.claude/skills/pico-celery-task
mkdir -p ~/.claude/skills/pico-tests
```

## Usage

```bash
# Invoke directly in Claude Code
/pico-celery-task send_notification
/pico-tests UserTaskClient
```

See the full skill templates in the [pico-framework skill catalog](https://github.com/dperezcabrera/pico-celery).
