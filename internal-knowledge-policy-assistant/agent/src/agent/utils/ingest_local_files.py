from pathlib import Path

from agent.ingestion.pipeline import IngestionPipeline


def ingest_directory(pipeline: IngestionPipeline, directory: Path) -> None:
    supported_extensions = {".md", ".pdf"}

    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            pipeline.ingest(str(file_path))


def ingest_local_files(
    pipeline: IngestionPipeline,
) -> None:
    base_documents_directory = Path(__file__).resolve().parent.parent / "documents"

    markdown_directory = base_documents_directory / "md"
    ingest_directory(pipeline, markdown_directory)

    pdf_directory = base_documents_directory / "pdf"
    ingest_directory(pipeline, pdf_directory)
