from time import sleep

SERVICE_EXECUTION_DELAY_SECONDS = 3


def wait_for_service_execution() -> None:
    sleep(SERVICE_EXECUTION_DELAY_SECONDS)
