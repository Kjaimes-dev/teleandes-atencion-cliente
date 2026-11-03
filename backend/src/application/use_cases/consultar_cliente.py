from src.domain.entities.cliente import Cliente
from src.domain.exceptions import ClienteNoEncontrado
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.value_objects.documento import Documento


class ConsultarCliente:
    """Caso de uso: obtener los datos de un cliente por su documento."""

    def __init__(self, clientes: ClienteRepository) -> None:
        self._clientes = clientes

    def ejecutar(self, documento: str) -> Cliente:
        doc = Documento(documento)
        cliente = self._clientes.obtener_por_documento(doc)
        if cliente is None:
            raise ClienteNoEncontrado(doc.valor)
        return cliente
