from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.gestion import Gestion
from src.domain.value_objects.documento import Documento


class GestionRepository(ABC):
    """Puerto de persistencia de gestiones.

    Todos los métodos pueden lanzar RepositorioNoDisponible si la
    persistencia no responde.
    """

    @abstractmethod
    def guardar(self, gestion: Gestion) -> Gestion:
        """Persiste la gestión y la devuelve con `id` asignado.

        Raises:
            IdempotencyKeyDuplicada: si la clave ya existe (violación del UNIQUE).
        """

    @abstractmethod
    def buscar_por_idempotency_key(self, clave: str) -> Optional[Gestion]:
        """Devuelve la gestión asociada a la clave o None."""

    @abstractmethod
    def listar_por_documento(self, documento: Documento) -> List[Gestion]:
        """Gestiones del cliente, de la más reciente a la más antigua."""
