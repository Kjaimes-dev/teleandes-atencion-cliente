from typing import Optional

from pydantic import BaseModel


class GestionIn(BaseModel):
    """Cuerpo del POST. Solo tipos: las reglas de negocio las valida el dominio."""

    documento: Optional[str] = None
    canal: str
    tipificacion: str
    observacion: Optional[str] = None


class GestionCreada(BaseModel):
    id: int
    fecha: str


class GestionOut(BaseModel):
    id: int
    documento: Optional[str]
    canal: str
    tipificacion: str
    observacion: str
    fecha: str
