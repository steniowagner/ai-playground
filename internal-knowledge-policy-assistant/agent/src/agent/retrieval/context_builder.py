from agent.domain.search_result import SearchResult


class ContextBuilder:
    def _format_result(self, search_result: SearchResult) -> str:
        file_name = search_result.chunk.metadata["filename"]
        score = search_result.score

        return "\n".join(
            [
                f"[Source: {file_name}]",
                f"[Score: {score:.4f}]",
                search_result.chunk.content,
            ]
        )

    def build(self, search_results: list[SearchResult]) -> str:
        sections = [
            self._format_result(search_result) for search_result in search_results
        ]

        return "\n\n---\n\n".join(sections)
