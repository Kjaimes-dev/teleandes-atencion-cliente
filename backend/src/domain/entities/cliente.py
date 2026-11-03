from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Cliente:
    documento: str
    nombre: str
    celular: str
    plan: str
    estado: str  # "activo" | "suspendido"
    saldo: int  # pesos colombianos, sin decimales
    fecha_corte: date
