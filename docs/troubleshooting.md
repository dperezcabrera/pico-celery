# Troubleshooting

## `ConfigurationError: missing required prefix "celery"`

pico-celery activates whenever it is installed and the container boots with
plugin auto-discovery. Either provide the `celery:` config block
(`broker_url`, `backend_url`), or exclude the plugin
(`PICO_BOOT_AUTO_PLUGINS=false` + explicit `modules=[...]`) in apps and test
suites that do not use it — pico-testing does this for you.

## My @task method never registers

- The class must be a `@component` in a registered module.
- Task discovery happens at container startup: the worker must boot a
  container (`pico_boot.init` in the worker process), not just import celery.
- Check the task name: `@task(name="tasks.create_user")` registers exactly
  that name; the client's `@send_task` must match it.

## The client sends but nothing executes

`@celery`/`@send_task` only enqueue. Run a worker against the same broker
with the same registered modules — the worker side is where `@task` bodies
execute.

## AsyncResult.get() hangs in tests

With the in-memory broker (`memory://`) there is no worker; `get()` waits
forever. Assert on task registration and message dispatch instead, or run
the sqlite-broker e2e pattern from the how-to with a worker subprocess.

## Sync method inside an async task fails mid-retry

Retries re-invoke the method directly (see pico-resilience notes): combine
decorators with `@retryable` on top so the whole task body is what retries.

## Worker cannot import my module

The worker process needs the same PYTHONPATH/venv as the app. In containers,
install the app package; in dev, launch the worker from the project root.
