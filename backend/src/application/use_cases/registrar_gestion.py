import logging
from typing import Optional, Tuple

from src.domain.entities.gestion import Gestion
from src.domain.exceptions import ClienteNoEncontrado, IdempotencyKeyDuplicada
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.repositories.gestion_repository import GestionRepository

logger = logging.getLogger(__name__)


class RegistrarGestion:
    """Caso de uso: registrar una atención de forma idempotente."""

    def __init__(self, clientes: ClienteRepository, gestiones: GestionRepository) -> None:
        self._clientes = clientes
        self._gestiones = gestiones

    def ejecutar(
        self,
        documento: Optional[str],
        canal: str,
        tipificacion: str,
        observacion: Optional[str],
        idempotency_key: Optional[str] = None,
    ) -> Tuple[Gestion, bool]:
        """Devuelve (gestion, creada). `creada` es False si se reutilizó una existente."""
        gestion = Gestion.crear(documento, canal, tipificacion, observacion, idempotency_key)

        if gestion.documento is not None:
            if self._clientes.obtener_por_documento(gestion.documento) is None:
                raise ClienteNoEncontrado(gestion.documento.valor)

        if idempotency_key:
            existente = self._gestiones.buscar_por_idempotency_key(idempotency_key)
            if existente is not None:
                return existente, False

        try:
            return self._gestiones.guardar(gestion), True
        except IdempotencyKeyDuplicada:
            # Dos peticiones simultáneas con la misma clave: esta perdió la carrera
            # contra el UNIQUE, así que se devuelve la gestión que ganó.
            existente = (
                self._gestiones.buscar_por_idempotency_key(idempotency_key)
                if idempotency_key
                else None
            )
            if existente is None:
                logger.error("Clave de idempotencia duplicada sin gestión asociada")
                raise
            return existente, False
