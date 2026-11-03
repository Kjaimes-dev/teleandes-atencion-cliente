import logging
import sys

_FORMATO = "%(asctime)s %(levelname)s %(name)s - %(message)s"


def configurar_logging(nivel: str = "INFO") -> None:
    """Configura el logging a stdout (lo recoge Docker). Idempotente."""
    raiz = logging.getLogger()
    if raiz.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMATO))
    raiz.addHandler(handler)
    raiz.setLevel(getattr(logging, nivel.upper(), logging.INFO))
