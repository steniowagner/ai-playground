from pathlib import Path

from incident_triage_assistant.tools.query_logs.schema import Log

from .base import LogsRepository
from .schema import FindLogsArgs

LOGS_FILE = Path(__file__).resolve().parents[4] / "data" / "fixtures" / "logs.jsonl"


class JSONLogsRepository(LogsRepository):
    def _read_logs(self) -> list[Log]:
        logs = []

        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    log = Log.model_validate_json(line)
                    logs.append(log)

        return logs

    def _filter_by_message_content(
        self, args: FindLogsArgs, logs: list[Log]
    ) -> list[Log]:
        if not args.contains:
            return logs

        return [log for log in logs if args.contains in log.message]

    def _filter_by_severity(self, args: FindLogsArgs, logs: list[Log]) -> list[Log]:
        if args.severity is None:
            return logs

        return [log for log in logs if log.severity in args.severity]

    def _filter_by_optional_filters(
        self, args: FindLogsArgs, logs: list[Log]
    ) -> list[Log]:
        filtered_logs = self._filter_by_message_content(args, logs)
        filtered_logs = self._filter_by_severity(args, filtered_logs)
        sorted_logs = sorted(filtered_logs, key=lambda log: log.timestamp)

        return sorted_logs

    def _filter_logs(self, args: FindLogsArgs, all_logs: list[Log]) -> list[Log]:
        logs = [
            log
            for log in all_logs
            if log.service == args.service
            and log.environment == args.environment
            and args.start_time <= log.timestamp
            and log.timestamp <= args.end_time
        ]

        return self._filter_by_optional_filters(args, logs)

    def find(self, args: FindLogsArgs) -> list[Log]:
        all_logs = self._read_logs()
        return self._filter_logs(args, all_logs)[: args.limit]
