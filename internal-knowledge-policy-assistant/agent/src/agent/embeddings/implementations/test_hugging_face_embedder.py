from agent.embeddings.implementations import hugging_face
from agent.embeddings.implementations.hugging_face import HuggingFaceEmbedder


class FakeEmbeddings:
    def __init__(self, values: list[list[float]]) -> None:
        self._values = values

    def tolist(self) -> list[list[float]]:
        return self._values

    def __getitem__(self, index: int) -> "FakeEmbedding":
        return FakeEmbedding(self._values[index])


class FakeEmbedding:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


class FakeSentenceTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.document_calls: list[tuple[list[str], bool, bool]] = []
        self.query_calls: list[tuple[list[str], bool, bool]] = []

    def encode_document(
        self,
        texts: list[str],
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> FakeEmbeddings:
        self.document_calls.append(
            (texts, convert_to_numpy, normalize_embeddings)
        )
        return FakeEmbeddings([[1.0, 0.0] for _ in texts])

    def encode_query(
        self,
        texts: list[str],
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> FakeEmbeddings:
        self.query_calls.append((texts, convert_to_numpy, normalize_embeddings))
        return FakeEmbeddings([[0.0, 1.0]])


def test_embed_documents_uses_document_encoding(monkeypatch) -> None:
    monkeypatch.setattr(
        hugging_face,
        "SentenceTransformer",
        FakeSentenceTransformer,
    )
    embedder = HuggingFaceEmbedder()

    result = embedder.embed_documents(["first", "second"])

    assert result == [[1.0, 0.0], [1.0, 0.0]]
    assert embedder._model.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert embedder._model.document_calls == [
        (["first", "second"], True, True)
    ]


def test_embed_documents_skips_model_for_empty_input(monkeypatch) -> None:
    monkeypatch.setattr(
        hugging_face,
        "SentenceTransformer",
        FakeSentenceTransformer,
    )
    embedder = HuggingFaceEmbedder()

    assert embedder.embed_documents([]) == []
    assert embedder._model.document_calls == []


def test_embed_query_uses_query_encoding(monkeypatch) -> None:
    monkeypatch.setattr(
        hugging_face,
        "SentenceTransformer",
        FakeSentenceTransformer,
    )
    embedder = HuggingFaceEmbedder()

    result = embedder.embed_query("remote work")

    assert result == [0.0, 1.0]
    assert embedder._model.query_calls == [(["remote work"], True, True)]
