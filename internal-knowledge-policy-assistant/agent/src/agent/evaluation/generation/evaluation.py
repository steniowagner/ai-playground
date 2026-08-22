from dataclasses import dataclass

from agent.generation.answer import GenerationAnswer


@dataclass(frozen=True)
class GenerationEvaluation:
    question: str
    answer: GenerationAnswer
    expected_facts: list[str]
    expected_sources: set[str]
    expected_answerable: bool
    facts_found: list[str]
    sources_correct: bool
    answerability_correct: bool

    @property
    def is_correct(self) -> bool:
        all_facts_found = len(self.facts_found) == len(self.expected_facts)

        return all_facts_found and self.sources_correct and self.answerability_correct
