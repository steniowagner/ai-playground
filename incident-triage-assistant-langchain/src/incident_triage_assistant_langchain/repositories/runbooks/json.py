from pathlib import Path

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import RunbooksRepository
from .schema import FindRunbookByIdArgs

RUNBOOKS_DIR = Path(__file__).resolve().parents[4] / "data" / "runbooks"


class JSONRunbooksRepository(RunbooksRepository):
    def _read_runbooks(self) -> list[str]:
        runbook_dir = Path(RUNBOOKS_DIR)
        try:
            return [
                f.stem
                for f in runbook_dir.iterdir()
                if f.is_file() and f.suffix == ".md"
            ]
        except OSError as exc:
            raise RepositoryUnavailable("Runbooks repository is unavailable.") from exc

    def _find_runbook(self, runbook_id: str) -> str:
        runbook_path = RUNBOOKS_DIR / f"{runbook_id}.md"

        try:
            return runbook_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Runbooks repository contains invalid text data."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable("Runbooks repository is unavailable.") from exc

    def find_by_id(self, args: FindRunbookByIdArgs) -> str | None:
        runbooks = self._read_runbooks()

        if args.runbook_id not in runbooks:
            return None

        return self._find_runbook(args.runbook_id)
