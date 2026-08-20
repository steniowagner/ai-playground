from agent.chunking import create_chunker
from agent.domain.document_chunk import DocumentChunk
from agent.embeddings.factory import create_embeddings_provider
from agent.ingestion.loaders.factory import create_document_loader
from agent.llm.factory import create_llm_client


def main() -> None:
    """
    client = create_llm_client("groq")
    answer = client.ask("What is retrieval-augmented generation?")
    print(answer)

    document = "International remote work requires advance approval from the"

    print(chunking.chunk(document))
    """

    local_document_loader = create_document_loader("local")
    document = local_document_loader.load(
        "/Users/steniowagner/dev/agents-playground/internal-knowledge-policy-assistant/agent/src/agent/documents/pdf/expense_policy.pdf"
    )
    chunking = create_chunker("hugging-face")

    document_chunks = [
        DocumentChunk(
            id=f"{document.id}:{chunk.index}",
            document_id=document.id,
            content=chunk.content,
            index=chunk.index,
            token_count=chunk.token_count,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            metadata={
                **document.metadata,
                "source": document.source,
                "document_type": document.type,
            },
        )
        for chunk in chunking.chunk(document.content)
    ]

    embeddings_provider = create_embeddings_provider("hugging-face")

    vectors = embeddings_provider.embed_documents(
        [document_chunk.content for document_chunk in document_chunks]
    )

    print(document_chunks)
