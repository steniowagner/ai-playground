class EvaluationCaseNotFoundError(LookupError):
    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        super().__init__(f"Evaluation case not found: {case_id}")
