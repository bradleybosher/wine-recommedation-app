"""Configure the 'sommelier' logger tree with a rotating file handler + stderr."""
import logging
import logging.handlers
from pathlib import Path


def configure_logging() -> logging.Logger:
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "api.log"

    root = logging.getLogger("sommelier")
    if root.handlers:
        return root

    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.addHandler(logging.StreamHandler())
    return root
