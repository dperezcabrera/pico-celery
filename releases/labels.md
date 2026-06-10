# GitHub Topics — pico-celery

## Topics actuales

_(ninguno)_

## Topics propuestos (10)

```
pico-framework
dependency-injection
ioc
celery
task-queue
async
asyncio
distributed-computing
worker
celery-tasks
```

### Justificación

| Topic | Razón |
|---|---|
| `pico-framework` | Ecosistema compartido |
| `dependency-injection` | Core del ecosistema |
| `ioc` | Abreviatura estándar |
| `celery` | Integración principal |
| `task-queue` | Categoría de lo que hace Celery |
| `async` | Tasks son `async def` |
| `asyncio` | Framework async subyacente |
| `distributed-computing` | Caso de uso principal |
| `worker` | Lado worker con @task |
| `celery-tasks` | Refuerza discoverability específica |

### Descartados de pyproject.toml

| Keyword PyPI | Razón para no incluir en GitHub |
|---|---|
| `spring boot` | No es un framework Spring, la analogía confunde en GitHub topics |
| `controller` | No aplica — pico-celery no tiene controllers |

## Comando para aplicar

```bash
gh repo edit dperezcabrera/pico-celery --add-topic pico-framework,dependency-injection,ioc,celery,task-queue,async,asyncio,distributed-computing,worker,celery-tasks
```
