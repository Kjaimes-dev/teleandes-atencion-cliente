import dataclasses
import logging
from typing import List, Mapping, Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.domain.entities.gestion import ZONA_HORARIA, Gestion
from src.domain.exceptions import IdempotencyKeyDuplicada
from src.domain.repositories.gestion_repository import GestionRepository
from src.domain.value_objects.canal import Canal
from src.domain.value_objects.documento import Documento
from src.domain.value_objects.tipificacion import Tipificacion
from src.infrastructure.db.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

_MYSQL_DUPLICADO = 1062
_UNIQUE_IDEMPOTENCY = "uq_gestiones_idempotency_key"

_COLUMNAS = "id, documento, canal, tipificacion, observacion, fecha, idempotency_key"

_SQL_INSERTAR = text(
    "INSERT INTO gestiones (documento, canal, tipificacion, observacion, fecha, idempotency_key) "
    "VALUES (:documento, :canal, :tipificacion, :observacion, :fecha, :idempotency_key)"
)
_SQL_POR_CLAVE = text(f"SELECT {_COLUMNAS} FROM gestiones WHERE idempotency_key = :clave")
_SQL_POR_DOCUMENTO = text(
    f"SELECT {_COLUMNAS} FROM gestiones WHERE documento = :documento ORDER BY fecha DESC, id DESC"
)


def _codigo_mysql(exc: IntegrityError) -> Optional[int]:
    """Código de error de MySQL, si el driver lo entrega."""
    args = getattr(exc.orig, "args", ())
    return args[0] if args and isinstance(args[0], int) else None


def _a_gestion(fila: Mapping) -> Gestion:
    """Reconstruye la entidad; la BD guarda hora de Bogotá sin zona y aquí se restituye."""
    return Gestion(
        id=int(fila["id"]),
        documento=Documento(fila["documento"]) if fila["documento"] is not None else None,
        canal=Canal(fila["canal"]),
        tipificacion=Tipificacion(fila["tipificacion"]),
        observacion=fila["observacion"],
        fecha=fila["fecha"].replace(tzinfo=ZONA_HORARIA),
        idempotency_key=fila["idempotency_key"],
    )


class MySQLGestionRepository(GestionRepository):
    """Persistencia de gestiones sobre MySQL."""

    def __init__(self, conexiones: ConnectionManager) -> None:
        self._conexiones = conexiones

    def guardar(self, gestion: Gestion) -> Gestion:
        """Inserta la gestión y la devuelve con el id generado."""
        parametros = {
            "documento": gestion.documento.valor if gestion.documento is not None else None,
            "canal": gestion.canal.value,
            "tipificacion": gestion.tipificacion.value,
            "observacion": gestion.observacion,
            # DATETIME no guarda zona: se persiste la hora local de Bogotá.
            "fecha": gestion.fecha.astimezone(ZONA_HORARIA).replace(tzinfo=None),
            "idempotency_key": gestion.idempotency_key,
        }
        try:
            with self._conexiones.conexion() as conn:
                resultado = conn.execute(_SQL_INSERTAR, parametros)
                nuevo_id = int(resultado.lastrowid)
        except IntegrityError as exc:
            if _codigo_mysql(exc) == _MYSQL_DUPLICADO and _UNIQUE_IDEMPOTENCY in str(exc.orig):
                raise IdempotencyKeyDuplicada(
                    "Ya existe una gestión con esa idempotency key"
                ) from exc
            # FK u otras restricciones: no son un reintento idempotente.
            logger.error("Violación de integridad al guardar la gestión: %s", exc)
            raise
        return dataclasses.replace(gestion, id=nuevo_id)

    def buscar_por_idempotency_key(self, clave: str) -> Optional[Gestion]:
        """Devuelve la gestión asociada a la clave o None."""
        with self._conexiones.conexion() as conn:
            fila = conn.execute(_SQL_POR_CLAVE, {"clave": clave}).mappings().first()
        return _a_gestion(fila) if fila is not None else None

    def listar_por_documento(self, documento: Documento) -> List[Gestion]:
        """Gestiones del cliente, de la más reciente a la más antigua."""
        with self._conexiones.conexion() as conn:
            filas = conn.execute(_SQL_POR_DOCUMENTO, {"documento": documento.valor}).mappings().all()
        return [_a_gestion(f) for f in filas]
