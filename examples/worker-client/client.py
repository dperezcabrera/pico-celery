from pico_boot import init
from pico_ioc import configuration, YamlTreeSource
from pico_celery import celery


@celery(name="add")
def add(x: int, y: int) -> int: ...


@celery(name="multiply")
def multiply(x: int, y: int) -> int: ...


def main():
    config = configuration(YamlTreeSource("config.yml"))

    container = init(
        modules=[__name__],
        config=config,
    )

    # Send tasks to the worker
    result = add.delay(4, 6)
    print(f"4 + 6 = {result.get(timeout=10)}")

    result = multiply.delay(3, 7)
    print(f"3 * 7 = {result.get(timeout=10)}")


if __name__ == "__main__":
    main()
