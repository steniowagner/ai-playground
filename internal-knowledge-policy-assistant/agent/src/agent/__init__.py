from agent.chunking import create_chunker
from agent.llm.factory import create_llm_client


def main() -> None:
    client = create_llm_client("groq")
    answer = client.ask("What is retrieval-augmented generation?")
    print(answer)

    document = """
    International remote work requires advance approval from the
    employee's manager, Human Resources, and Information Security.

    Employees may work internationally for up to 15 working days per
    calendar year. Requests must be submitted at least 30 days before
    departure.
    """

    chunking = create_chunker("hugging-face")
    print(chunking.chunk(document))
