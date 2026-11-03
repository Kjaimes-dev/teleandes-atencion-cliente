from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.cliente import Cliente
from src.domain.value_objects.documento import Documento


class ClienteRepository(ABC):
    """Puerto de consulta de clientes."""

    @abstractmethod
    def obtener_por_documento(self, documento: Documento) -> Optional[Cliente]:
        """Devuelve el cliente o None si no existe.

        Raises:
            RepositorioNoDisponible: si la persistencia no responde.
        """
