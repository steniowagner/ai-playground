from uuid import UUID, uuid4


def create_thread_id() -> UUID:
    return uuid4()
