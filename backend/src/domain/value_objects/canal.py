from enum import Enum

from src.domain.exceptions import DatoInvalido


class Canal(str, Enum):
    """Canal por el que se atendió al cliente."""

    IVR = "ivr"
    WHATSAPP = "whatsapp"
    AGENTE = "agente"

    @classmethod
    def desde_texto(cls, valor: str) -> "Canal":
        try:
            return cls(valor)
        except ValueError:
            validos = ", ".join(c.value for c in cls)
            raise DatoInvalido(f"Canal inválido. Valores permitidos: {validos}") from None
