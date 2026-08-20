from agent.chunking import create_chunker
from agent.ingestion.loaders.factory import create_document_loader
from agent.llm.factory import create_llm_client


def main() -> None:
    """
    client = create_llm_client("groq")
    answer = client.ask("What is retrieval-augmented generation?")
    print(answer)

    document = "International remote work requires advance approval from the"

    chunking = create_chunker("hugging-face")
    print(chunking.chunk(document))
    """

    local_document_loader = create_document_loader("local")
    document = local_document_loader.load(
        "/Users/steniowagner/dev/agents-playground/internal-knowledge-policy-assistant/agent/src/agent/documents/pdf/expense_policy.pdf"
    )
    print(document)
