from enum import Enum

from src.domain.exceptions import DatoInvalido


class Tipificacion(str, Enum):
    """Lista cerrada de motivos con los que se clasifica una gestión."""

    CONSULTA_SALDO = "Consulta de saldo"
    CONSULTA_ESTADO = "Consulta de estado"
    RECLAMO = "Reclamo"
    SOLICITUD_ASESOR = "Solicitud de asesor"
    OTRO = "Otro"

    @classmethod
    def desde_texto(cls, valor: str) -> "Tipificacion":
        try:
            return cls(valor)
        except ValueError:
            validos = ", ".join(t.value for t in cls)
            raise DatoInvalido(f"Tipificación inválida. Valores permitidos: {validos}") from None
