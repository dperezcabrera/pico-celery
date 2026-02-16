# How to Configure Retry with Backoff for Tasks

This guide shows how to configure Celery retry behaviour and exponential backoff for pico-celery worker tasks.

## Basic Retry Configuration

Pass Celery task options directly through the `@task` decorator:

```python
from pico_ioc import component
from pico_celery import task

@component(scope="prototype")
class PaymentTasks:
    def __init__(self, payment_service: PaymentService):
        self.service = payment_service

    @task(
        name="tasks.charge_card",
        max_retries=5,
        default_retry_delay=60,  # seconds
    )
    async def charge_card(self, order_id: int, amount: float):
        try:
            await self.service.charge(order_id, amount)
        except PaymentGatewayError as exc:
            raise self.charge_card.retry(exc=exc)
```

The `max_retries` and `default_retry_delay` options are forwarded to `celery_app.task()` during registration by `PicoTaskRegistrar`.

## Exponential Backoff

Celery 5 supports automatic exponential backoff via the `retry_backoff` option:

```python
@component(scope="prototype")
class EmailTasks:
    def __init__(self, mailer: MailerService):
        self.mailer = mailer

    @task(
        name="tasks.send_email",
        bind=True,
        autoretry_for=(ConnectionError, TimeoutError),
        max_retries=5,
        retry_backoff=True,        # enables exponential backoff
        retry_backoff_max=600,     # cap at 10 minutes
        retry_jitter=True,         # add randomness to avoid thundering herd
    )
    async def send_email(self, to: str, subject: str, body: str):
        await self.mailer.send(to, subject, body)
```

With `retry_backoff=True`, Celery uses increasing delays: 1s, 2s, 4s, 8s, ... up to `retry_backoff_max`.

### Backoff Options Reference

| Option               | Type         | Description                                             |
| :------------------- | :----------- | :------------------------------------------------------ |
| `max_retries`        | `int`        | Maximum number of retry attempts                        |
| `default_retry_delay`| `int`        | Fixed delay in seconds between retries                  |
| `retry_backoff`      | `bool / int` | `True` for default base (1s), or an integer base value  |
| `retry_backoff_max`  | `int`        | Maximum backoff delay in seconds (default: 600)         |
| `retry_jitter`       | `bool`       | Add random jitter to backoff delay                      |
| `autoretry_for`      | `tuple`      | Exception types that trigger automatic retry            |

## Manual Retry with Custom Countdown

For full control over retry timing, use `self.retry()` inside the task:

```python
@component(scope="prototype")
class ImportTasks:
    def __init__(self, importer: DataImporter):
        self.importer = importer

    @task(name="tasks.import_data", bind=True, max_retries=3)
    async def import_data(self, self_task, file_path: str):
        try:
            await self.importer.run(file_path)
        except RateLimitError as exc:
            # Retry after progressively longer delays
            countdown = 2 ** self_task.request.retries * 30
            raise self_task.retry(exc=exc, countdown=countdown)
```

!!! note
    When using `bind=True`, Celery passes the task instance as the first argument after `self`. The pico-celery wrapper preserves this behaviour.

## Configuring Retry at the Client Side

When sending tasks from a `@celery` client, you can also set per-call options:

```python
from pico_celery import celery, send_task

@celery
class PaymentClient:
    @send_task(
        name="tasks.charge_card",
        queue="payments",
        countdown=5,  # delay initial execution by 5 seconds
    )
    def charge_card(self, order_id: int, amount: float):
        pass
```

These options are forwarded to `celery_app.send_task()` by the `CeleryClientInterceptor`.
