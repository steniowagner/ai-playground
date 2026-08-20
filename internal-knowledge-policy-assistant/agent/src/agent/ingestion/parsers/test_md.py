from pathlib import Path

from agent.ingestion.parsers.md import MDParser


def test_parse_reads_complete_utf8_document(tmp_path: Path) -> None:
    document_path = tmp_path / "policy.md"
    content = "# Política\n\nFuncionários podem trabalhar remotamente."
    document_path.write_text(content, encoding="utf-8")

    result = MDParser().parse(document_path)

    assert result == content
