__all__ = ("LOGGING_FORMAT", "FILE_DATE_FORMAT", "ENCODE_DATETIME_FORMAT", "format_http")


LOGGING_FORMAT = "[PID: %(process)06d] %(asctime)s - %(levelname)-8s - %(message)s"
FILE_DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"
ENCODE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


def format_http(status: int, reason: str | None, /) -> str:
    f_reason = f" {reason}" if reason is not None else ""
    return f"{status}{f_reason}"
