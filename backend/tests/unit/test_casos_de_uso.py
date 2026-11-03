import pytest

from src.application.use_cases.consultar_cliente import ConsultarCliente
from src.application.use_cases.listar_gestiones import ListarGestiones
from src.application.use_cases.registrar_gestion import RegistrarGestion
from src.domain.entities.gestion import Gestion
from src.domain.exceptions import (
    ClienteNoEncontrado,
    DatoInvalido,
    IdempotencyKeyDuplicada,
    RepositorioNoDisponible,
)
from tests.fakes import (
    ClienteRepositoryEnMemoria,
    ClienteRepositoryNoDisponible,
    GestionRepositoryEnMemoria,
)
from typing import Optional


def test_consultar_cliente_existente() -> None:
    c = ConsultarCliente(ClienteRepositoryEnMemoria()).ejecutar("52123456")
    assert c.nombre == "Carlos Pérez"
    assert c.estado == "suspendido"
    assert c.saldo == 85000


def test_consultar_cliente_inexistente() -> None:
    with pytest.raises(ClienteNoEncontrado):
        ConsultarCliente(ClienteRepositoryEnMemoria()).ejecutar("999999")


def test_consultar_cliente_documento_invalido() -> None:
    with pytest.raises(DatoInvalido):
        ConsultarCliente(ClienteRepositoryEnMemoria()).ejecutar("abc")


def test_consultar_cliente_repo_caido() -> None:
    with pytest.raises(RepositorioNoDisponible):
        ConsultarCliente(ClienteRepositoryNoDisponible()).ejecutar("52123456")


def _registrar() -> RegistrarGestion:
    return RegistrarGestion(ClienteRepositoryEnMemoria(), GestionRepositoryEnMemoria())


def test_registrar_gestion_nueva() -> None:
    g, creada = _registrar().ejecutar("1020304050", "ivr", "Consulta de saldo", None)
    assert creada is True
    assert g.id == 1


def test_registrar_cliente_inexistente() -> None:
    with pytest.raises(ClienteNoEncontrado):
        _registrar().ejecutar("999999", "ivr", "Otro", None)


def test_registrar_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        _registrar().ejecutar("1020304050", "ivr", "Reclamo", "")


def test_registrar_idempotente_misma_clave() -> None:
    caso = _registrar()
    g1, c1 = caso.ejecutar("1020304050", "ivr", "Otro", None, "clave-1")
    g2, c2 = caso.ejecutar("1020304050", "ivr", "Otro", None, "clave-1")
    assert (c1, c2) == (True, False)
    assert g1.id == g2.id


def test_registrar_claves_distintas_crean_dos() -> None:
    caso = _registrar()
    g1, _ = caso.ejecutar("1020304050", "ivr", "Otro", None, "a")
    g2, _ = caso.ejecutar("1020304050", "ivr", "Otro", None, "b")
    assert g1.id != g2.id


def test_registrar_sin_clave_no_deduplica() -> None:
    caso = _registrar()
    g1, _ = caso.ejecutar("1020304050", "ivr", "Otro", None)
    g2, _ = caso.ejecutar("1020304050", "ivr", "Otro", None)
    assert g1.id != g2.id


class _RepoCarrera(GestionRepositoryEnMemoria):
    """buscar devuelve None la primera vez; otra petición gana antes de guardar."""

    def __init__(self) -> None:
        super().__init__()
        self._busquedas = 0

    def buscar_por_idempotency_key(self, clave: str) -> Optional[Gestion]:
        self._busquedas += 1
        if self._busquedas == 1:
            return None
        return super().buscar_por_idempotency_key(clave)

    def guardar(self, gestion: Gestion) -> Gestion:
        if not self._gestiones:
            super().guardar(gestion)  # la petición ganadora
        return super().guardar(gestion)  # lanza IdempotencyKeyDuplicada


def test_registrar_carrera_devuelve_existente() -> None:
    caso = RegistrarGestion(ClienteRepositoryEnMemoria(), _RepoCarrera())
    g, creada = caso.ejecutar("1020304050", "ivr", "Otro", None, "carrera")
    assert creada is False
    assert g.id == 1


def test_registrar_duplicada_sin_existente_propaga() -> None:
    class _Roto(GestionRepositoryEnMemoria):
        def guardar(self, gestion: Gestion) -> Gestion:
            raise IdempotencyKeyDuplicada("x")

    caso = RegistrarGestion(ClienteRepositoryEnMemoria(), _Roto())
    with pytest.raises(IdempotencyKeyDuplicada):
        caso.ejecutar("1020304050", "ivr", "Otro", None, "x")


def test_listar_vacio_y_orden_descendente() -> None:
    clientes, repo = ClienteRepositoryEnMemoria(), GestionRepositoryEnMemoria()
    listar = ListarGestiones(clientes, repo)
    assert listar.ejecutar("1020304050") == []
    registrar = RegistrarGestion(clientes, repo)
    registrar.ejecutar("1020304050", "ivr", "Otro", None)
    registrar.ejecutar("1020304050", "agente", "Otro", None)
    registrar.ejecutar("79876543", "agente", "Otro", None)
    assert [g.id for g in listar.ejecutar("1020304050")] == [2, 1]


def test_listar_cliente_inexistente() -> None:
    with pytest.raises(ClienteNoEncontrado):
        ListarGestiones(ClienteRepositoryEnMemoria(), GestionRepositoryEnMemoria()).ejecutar("999999")


def test_listar_documento_invalido() -> None:
    with pytest.raises(DatoInvalido):
        ListarGestiones(ClienteRepositoryEnMemoria(), GestionRepositoryEnMemoria()).ejecutar("12")


# --- Gestión sin cliente identificado

def test_registrar_sin_documento_no_consulta_cliente() -> None:
    # Un repositorio de clientes caído no debe afectar a una gestión sin documento.
    caso = RegistrarGestion(ClienteRepositoryNoDisponible(), GestionRepositoryEnMemoria())
    gestion, creada = caso.ejecutar(None, "ivr", "Solicitud de asesor", "Transferida al asesor")
    assert creada is True
    assert gestion.documento is None
    assert gestion.id is not None


def test_registrar_sin_documento_es_idempotente() -> None:
    caso = RegistrarGestion(ClienteRepositoryEnMemoria(), GestionRepositoryEnMemoria())
    primera, creada1 = caso.ejecutar(None, "ivr", "Otro", "Motivo", "llamada-1-asesor")
    segunda, creada2 = caso.ejecutar(None, "ivr", "Otro", "Motivo", "llamada-1-asesor")
    assert (creada1, creada2) == (True, False)
    assert primera.id == segunda.id


def test_registrar_whatsapp_con_documento_inexistente_404() -> None:
    caso = RegistrarGestion(ClienteRepositoryEnMemoria(), GestionRepositoryEnMemoria())
    with pytest.raises(ClienteNoEncontrado):
        caso.ejecutar("99999999", "whatsapp", "Otro", "Observación")
