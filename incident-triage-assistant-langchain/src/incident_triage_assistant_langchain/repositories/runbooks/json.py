from pathlib import Path

from .base import RunbooksRepository

RUNBOOKS_DIR = Path(__file__).resolve().parents[4] / "data" / "runbooks"


class JSONRunbooksRepository(RunbooksRepository):
    def _read_runbooks(self) -> list[str]:
        runbook_dir = Path(RUNBOOKS_DIR)

        return [
            f.stem for f in runbook_dir.iterdir() if f.is_file() and f.suffix == ".md"
        ]

    def _read_runbook(self, runbook_id: str) -> str:
        runbook_path = Path(RUNBOOKS_DIR / f"{runbook_id}.md")
        return runbook_path.read_text(encoding="utf-8")

    def find_by_id(self, runbook_id: str) -> str | None:
        runbooks = self._read_runbooks()

        if runbook_id not in runbooks:
            return None

        return self._read_runbook(runbook_id)
