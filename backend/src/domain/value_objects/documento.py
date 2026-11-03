import re
from dataclasses import dataclass

from src.domain.exceptions import DatoInvalido

_PATRON = re.compile(r"[0-9]{6,10}")


@dataclass(frozen=True)
class Documento:
    """Documento de identidad: solo dígitos, entre 6 y 10."""

    valor: str

    def __post_init__(self) -> None:
        # fullmatch estricto: normalizar puntos y espacios es tarea de cada canal.
        if not isinstance(self.valor, str) or not _PATRON.fullmatch(self.valor):
            raise DatoInvalido("El documento debe ser numérico, de 6 a 10 dígitos")

    def __str__(self) -> str:
        return self.valor
