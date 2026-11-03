from pydantic import BaseModel


class ClienteOut(BaseModel):
    documento: str
    nombre: str
    celular: str
    plan: str
    estado: str
    saldo: int
    fecha_corte: str  # YYYY-MM-DD
