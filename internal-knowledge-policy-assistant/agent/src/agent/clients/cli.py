from agent.application.bootstrap import create_policy_assistant


def main() -> None:
    assistant = create_policy_assistant()

    print("Internal Policy Assistant")
    print("Type 'exit' to quit.")

    while True:
        question = input("\nQuestion: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        answer = assistant.ask(
            question=question,
            top_k=5,
            min_score=0.4,
        )

        print(f"\n{answer.content}")

        if answer.sources:
            print("\nSources:")
            for source in answer.sources:
                print(f"- {source}")
