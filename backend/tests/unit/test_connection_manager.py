import pytest

from src.domain.exceptions import RepositorioNoDisponible
from src.infrastructure.db.connection_manager import ConnectionManager


class _EngineQueFalla:
    """Engine cuyo connect() lanza la excepción indicada."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def connect(self) -> None:
        raise self._error


def _manager_con(error: Exception) -> ConnectionManager:
    # Se omite __init__ para no crear un engine real; solo interesa conexion().
    manager = ConnectionManager.__new__(ConnectionManager)
    manager._engine = _EngineQueFalla(error)  # type: ignore[assignment]
    return manager


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("'cryptography' package is required for caching_sha2_password"),
        ConnectionRefusedError("conexión rechazada"),
    ],
)
def test_fallo_al_abrir_conexion_es_repositorio_no_disponible(error: Exception) -> None:
    with pytest.raises(RepositorioNoDisponible):
        with _manager_con(error).conexion():
            pass


def test_verificar_conexion_traduce_el_fallo() -> None:
    with pytest.raises(RepositorioNoDisponible):
        _manager_con(RuntimeError("fallo del driver")).verificar_conexion()
