from agent.chunking.base import Chunk, Chunker
from transformers import AutoTokenizer, PreTrainedTokenizerBase


class HuggingFaceFixedSizeChunker(Chunker):
    def __init__(
        self,
        chunk_size: int = 256,
        chunk_overlap: int = 32,
    ):
        self._validate_chunk_config(chunk_size, chunk_overlap)

        self._tokenizer: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2", use_fast=True
        )
        self._chunk_overlap = chunk_overlap
        self._chunk_size = chunk_size

    def _validate_chunk_config(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError('"chunk_size" must be greater than zero')

        if chunk_overlap < 0:
            raise ValueError('"chunk_overlap" cannot be negative')

        if chunk_overlap >= chunk_size:
            raise ValueError('"chunk_overlap" must be smaller than chunk_size')

    def _handle_chunk_input_text(self, text: str) -> list[Chunk]:
        encoding = self._tokenizer(
            text,
            add_special_tokens=False,
            return_attention_mask=False,
            return_token_type_ids=False,
            return_offsets_mapping=True,
            truncation=False,
        )

        offsets: list[tuple[int, int]] = encoding["offset_mapping"]
        token_ids: list[int] = encoding["input_ids"]
        chunks: list[Chunk] = []

        step_size = self._chunk_size - self._chunk_overlap
        for chunk_index, token_start in enumerate(range(0, len(token_ids), step_size)):
            token_end = min(
                token_start + self._chunk_size,
                len(token_ids),
            )

            chunk_offsets = offsets[token_start:token_end]
            if not chunk_offsets:
                continue

            start_char = chunk_offsets[0][0]
            end_char = chunk_offsets[-1][1]

            chunk = Chunk(
                content=text[start_char:end_char],
                index=chunk_index,
                token_count=token_end - token_start,
                start_char=start_char,
                end_char=end_char,
            )

            chunks.append(chunk)

            if token_end == len(token_ids):
                break

        return chunks

    def chunk(self, text: str) -> list[Chunk]:
        if not text or not text.strip():
            return []

        chunks = self._handle_chunk_input_text(text=text)

        return chunks
