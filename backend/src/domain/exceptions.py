class ErrorDominio(Exception):
    """Base de los errores de negocio; la API los traduce a códigos HTTP."""


class DatoInvalido(ErrorDominio):
    """Un dato de entrada incumple una regla de validación (HTTP 400)."""


class ClienteNoEncontrado(ErrorDominio):
    """No existe un cliente con el documento consultado (HTTP 404)."""

    def __init__(self, documento: str) -> None:
        super().__init__(f"No existe un cliente con documento {documento}")
        self.documento = documento


class IdempotencyKeyDuplicada(ErrorDominio):
    """
    Lo lanza el repositorio al guardar cuando la clave ya existe (UNIQUE).
    El caso de uso la captura y devuelve la gestión original; no llega a la API.
    """


class RepositorioNoDisponible(ErrorDominio):
    """La persistencia no responde o falló la conexión (HTTP 503)."""
