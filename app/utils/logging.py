
import logging
import uuid
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get() or ""


def set_request_id(value: str | None = None) -> str:
    rid = value or str(uuid.uuid4())
    request_id_var.set(rid)
    return rid


class CustomJsonFormatter(JsonFormatter):

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["request_id"] = get_request_id()
        if not log_record.get("timestamp"):
            log_record["timestamp"] = self.formatTime(record, self.datefmt)


def setup_logging(log_level: str = "INFO") -> None:
    log_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    log_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
