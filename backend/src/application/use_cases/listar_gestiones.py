from typing import List

from src.domain.entities.gestion import Gestion
from src.domain.exceptions import ClienteNoEncontrado
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.repositories.gestion_repository import GestionRepository
from src.domain.value_objects.documento import Documento


class ListarGestiones:
    """Caso de uso: historial de gestiones de un cliente, la más reciente primero."""

    def __init__(self, clientes: ClienteRepository, gestiones: GestionRepository) -> None:
        self._clientes = clientes
        self._gestiones = gestiones

    def ejecutar(self, documento: str) -> List[Gestion]:
        doc = Documento(documento)
        if self._clientes.obtener_por_documento(doc) is None:
            raise ClienteNoEncontrado(doc.valor)
        return self._gestiones.listar_por_documento(doc)
