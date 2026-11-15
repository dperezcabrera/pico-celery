"""The public API is exactly what ``__all__`` declares (stability contract)."""

import pico_celery


def test_public_api_is_declared_and_importable():
    assert set(pico_celery.__all__) == {
        "CeleryClient",
        "CeleryClientInterceptor",
        "CeleryFactory",
        "CelerySettings",
        "PicoTaskRegistrar",
        "celery",
        "send_task",
        "task",
    }
    for name in pico_celery.__all__:
        assert getattr(pico_celery, name) is not None
