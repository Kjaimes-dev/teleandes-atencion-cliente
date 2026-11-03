from typing import Optional

from sqlalchemy import text

from src.domain.entities.cliente import Cliente
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.value_objects.documento import Documento
from src.infrastructure.db.connection_manager import ConnectionManager

_SQL_POR_DOCUMENTO = text(
    "SELECT documento, nombre, celular, plan, estado, saldo, fecha_corte "
    "FROM clientes WHERE documento = :documento"
)


class MySQLClienteRepository(ClienteRepository):
    """Consulta de clientes sobre MySQL."""

    def __init__(self, conexiones: ConnectionManager) -> None:
        self._conexiones = conexiones

    def obtener_por_documento(self, documento: Documento) -> Optional[Cliente]:
        """Devuelve el cliente o None si no existe."""
        with self._conexiones.conexion() as conn:
            fila = conn.execute(_SQL_POR_DOCUMENTO, {"documento": documento.valor}).mappings().first()
        if fila is None:
            return None
        return Cliente(
            documento=fila["documento"],
            nombre=fila["nombre"],
            celular=fila["celular"],
            plan=fila["plan"],
            estado=fila["estado"],
            saldo=int(fila["saldo"]),
            fecha_corte=fila["fecha_corte"],
        )
