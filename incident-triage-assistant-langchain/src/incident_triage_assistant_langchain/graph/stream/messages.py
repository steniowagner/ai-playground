def handle_message_event(payload: dict) -> None:
    if thinking:
        print(
            f"[Thinking] {thinking}",
            end="",
            flush=True,
        )
        print()

    if answer:
        print(
            f"[Answer] {answer}",
            end="",
            flush=True,
        )
        print()
