# AI Coding Skills

[Claude Code](https://code.claude.com) and [OpenAI Codex](https://openai.com/index/introducing-codex/) skills for AI-assisted development with pico-celery.

## Installation

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- celery
```

Or install all pico-framework skills:

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash
```

### Platform-specific

```bash
# Claude Code only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --claude celery

# OpenAI Codex only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --codex celery
```

## Available Commands

### `/add-celery-task`

Creates a Celery task with pico-celery. Use when adding background jobs, async workers, or task client senders.

**Two sides:** worker-side task (`@task` decorator) and client-side sender (`@send_task`/`@celery` decorator). Generates both by default.

```
/add-celery-task send_notification
/add-celery-task process_payment
```

### `/add-component`

Creates a new pico-ioc component with dependency injection. Use when adding services, factories, or interceptors.

```
/add-component NotificationService
```

### `/add-tests`

Generates tests for existing pico-framework components. Creates unit tests for tasks and services.

```
/add-tests EmailWorker
/add-tests NotificationService
```

## More Information

See [pico-skills](https://github.com/dperezcabrera/pico-skills) for the full list of skills, selective installation, and details.
