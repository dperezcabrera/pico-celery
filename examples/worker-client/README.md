# Worker-Client Example

A distributed task processing example using pico-celery.

## Requirements

- Python 3.11+
- Redis (for Celery broker)

## Setup

```bash
pip install -r requirements.txt
```

## Run

### Start the worker

```bash
celery -A worker.celery_app worker --loglevel=info
```

### Run the client

In another terminal:

```bash
python -m client
```

## Configuration

Set `CELERY_BROKER_URL` environment variable to change the broker:

```bash
export CELERY_BROKER_URL=redis://localhost:6379/0
```
