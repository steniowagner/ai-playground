from pathlib import Path

from agent.utils import ingest_local_files as ingestion_utils


class FakePipeline:
    def __init__(self) -> None:
        self.sources: list[str] = []

    def ingest(self, source: str) -> None:
        self.sources.append(source)


def test_ingest_directory_processes_supported_files_recursively(
    tmp_path: Path,
) -> None:
    nested_directory = tmp_path / "nested"
    nested_directory.mkdir()
    markdown_path = tmp_path / "policy.md"
    pdf_path = nested_directory / "guide.PDF"
    ignored_path = tmp_path / "notes.txt"
    markdown_path.write_text("policy", encoding="utf-8")
    pdf_path.write_bytes(b"pdf")
    ignored_path.write_text("notes", encoding="utf-8")
    pipeline = FakePipeline()

    ingestion_utils.ingest_directory(pipeline, tmp_path)  # type: ignore[arg-type]

    assert set(pipeline.sources) == {str(markdown_path), str(pdf_path)}


def test_ingest_directory_accepts_empty_directory(tmp_path: Path) -> None:
    pipeline = FakePipeline()

    ingestion_utils.ingest_directory(pipeline, tmp_path)  # type: ignore[arg-type]

    assert pipeline.sources == []


def test_ingest_local_files_uses_markdown_and_pdf_directories(monkeypatch) -> None:
    directories: list[Path] = []
    pipeline = FakePipeline()

    def fake_ingest_directory(fake_pipeline, directory: Path) -> None:
        assert fake_pipeline is pipeline
        directories.append(directory)

    monkeypatch.setattr(
        ingestion_utils,
        "ingest_directory",
        fake_ingest_directory,
    )

    ingestion_utils.ingest_local_files(pipeline)  # type: ignore[arg-type]

    assert [directory.name for directory in directories] == ["md", "pdf"]
    assert all(directory.parent.name == "documents" for directory in directories)
