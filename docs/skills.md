# Claude Code Skills

[Claude Code](https://code.claude.com) skills for AI-assisted development with pico-celery.

## Installation

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- celery
```

Or install all pico-framework skills:

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/add-celery-task` | Add Celery worker tasks and client senders |
| `/add-component` | Add components, factories, interceptors, settings |
| `/add-tests` | Generate tests for pico-framework components |

## Usage

```
/add-celery-task send_notification
/add-component NotificationService
/add-tests EmailWorker
```

## More Information

See [pico-skills](https://github.com/dperezcabrera/pico-skills) for the full list of skills, selective installation, and details.
