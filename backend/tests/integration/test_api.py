from typing import Callable, Dict, Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_cliente_repository,
    get_gestion_repository,
    get_verificador_salud,
)
from src.api.main import app
from src.domain.exceptions import RepositorioNoDisponible
from tests.fakes import (
    ClienteRepositoryEnMemoria,
    ClienteRepositoryNoDisponible,
    GestionRepositoryEnMemoria,
    GestionRepositoryNoDisponible,
)

DOC = "1020304050"


def _cuerpo(**cambios: object) -> Dict[str, object]:
    base: Dict[str, object] = {
        "documento": DOC,
        "canal": "ivr",
        "tipificacion": "Consulta de saldo",
        "observacion": "ok",
    }
    base.update(cambios)
    return base


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    clientes, gestiones = ClienteRepositoryEnMemoria(), GestionRepositoryEnMemoria()
    app.dependency_overrides[get_cliente_repository] = lambda: clientes
    app.dependency_overrides[get_gestion_repository] = lambda: gestiones
    app.dependency_overrides[get_verificador_salud] = lambda: (lambda: None)
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_caido() -> Iterator[TestClient]:
    app.dependency_overrides[get_cliente_repository] = lambda: ClienteRepositoryNoDisponible()
    app.dependency_overrides[get_gestion_repository] = lambda: GestionRepositoryNoDisponible()
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _es_error(resp) -> None:  # type: ignore[no-untyped-def]
    assert set(resp.json().keys()) == {"error"}
    assert isinstance(resp.json()["error"], str)


# --- GET /api/clientes/{documento}

def test_consultar_cliente_200(cliente: TestClient) -> None:
    r = cliente.get("/api/clientes/79876543")
    assert r.status_code == 200
    j = r.json()
    assert j["nombre"] == "Ana Ruiz"
    assert j["estado"] == "activo"
    assert j["saldo"] == 120500
    assert j["fecha_corte"] == "2026-11-15"


def test_consultar_cliente_suspendido(cliente: TestClient) -> None:
    j = cliente.get("/api/clientes/52123456").json()
    assert j["estado"] == "suspendido"
    assert j["saldo"] == 85000


def test_consultar_cliente_documento_mal_formado_400(cliente: TestClient) -> None:
    r = cliente.get("/api/clientes/12345")
    assert r.status_code == 400
    _es_error(r)


def test_consultar_cliente_con_letras_400(cliente: TestClient) -> None:
    assert cliente.get("/api/clientes/abc12345").status_code == 400


def test_consultar_cliente_404(cliente: TestClient) -> None:
    r = cliente.get("/api/clientes/999999")
    assert r.status_code == 404
    _es_error(r)


def test_consultar_cliente_503(cliente_caido: TestClient) -> None:
    r = cliente_caido.get(f"/api/clientes/{DOC}")
    assert r.status_code == 503
    _es_error(r)


# --- POST /api/gestiones

def test_registrar_gestion_201(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo())
    assert r.status_code == 201
    j = r.json()
    assert j["id"] == 1
    assert "fecha" in j


def test_registrar_documento_inexistente_404(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(documento="999999"))
    assert r.status_code == 404
    _es_error(r)


def test_registrar_documento_mal_formado_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(documento="1.020.304"))
    assert r.status_code == 400
    _es_error(r)


def test_registrar_canal_invalido_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(canal="telegram"))
    assert r.status_code == 400
    _es_error(r)


def test_registrar_tipificacion_invalida_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(tipificacion="Queja"))
    assert r.status_code == 400
    _es_error(r)


def test_registrar_reclamo_sin_observacion_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(tipificacion="Reclamo", observacion=""))
    assert r.status_code == 400
    _es_error(r)


def test_registrar_reclamo_sin_campo_observacion_400(cliente: TestClient) -> None:
    cuerpo = _cuerpo(tipificacion="Reclamo")
    del cuerpo["observacion"]
    assert cliente.post("/api/gestiones", json=cuerpo).status_code == 400


def test_registrar_observacion_1001_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(observacion="a" * 1001))
    assert r.status_code == 400
    _es_error(r)


def test_registrar_observacion_1000_201(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(observacion="a" * 1000))
    assert r.status_code == 201


def test_registrar_cuerpo_vacio_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json={})
    assert r.status_code == 400
    _es_error(r)


def test_registrar_sin_cuerpo_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones")
    assert r.status_code == 400
    _es_error(r)


def test_registrar_idempotency_key_larga_400(cliente: TestClient) -> None:
    r = cliente.post(
        "/api/gestiones", json=_cuerpo(), headers={"Idempotency-Key": "k" * 65}
    )
    assert r.status_code == 400
    _es_error(r)


def test_registrar_idempotency_key_64_201(cliente: TestClient) -> None:
    r = cliente.post(
        "/api/gestiones", json=_cuerpo(), headers={"Idempotency-Key": "k" * 64}
    )
    assert r.status_code == 201


def test_registrar_idempotente_201_luego_200(cliente: TestClient) -> None:
    h = {"Idempotency-Key": "abc-123"}
    r1 = cliente.post("/api/gestiones", json=_cuerpo(), headers=h)
    r2 = cliente.post("/api/gestiones", json=_cuerpo(), headers=h)
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    assert len(cliente.get(f"/api/gestiones?documento={DOC}").json()) == 1


def test_registrar_idempotency_key_vacia_se_ignora(cliente: TestClient) -> None:
    # Una cabecera vacía no debe chocar con el UNIQUE: cada petición crea su gestión.
    h = {"Idempotency-Key": ""}
    r1 = cliente.post("/api/gestiones", json=_cuerpo(), headers=h)
    r2 = cliente.post("/api/gestiones", json=_cuerpo(), headers=h)
    assert (r1.status_code, r2.status_code) == (201, 201)
    assert r1.json()["id"] != r2.json()["id"]


def test_fecha_del_201_coincide_con_el_listado(cliente: TestClient) -> None:
    creada = cliente.post("/api/gestiones", json=_cuerpo()).json()
    listada = cliente.get(f"/api/gestiones?documento={DOC}").json()[0]
    assert creada["fecha"] == listada["fecha"]
    assert creada["fecha"].endswith("-05:00")


def test_mensajes_de_error_en_espanol(cliente: TestClient) -> None:
    faltante = cliente.post("/api/gestiones", json={}).json()["error"]
    assert "campo obligatorio" in faltante
    assert cliente.get("/ruta-inexistente-api").json()["error"] == "Recurso no encontrado"
    assert cliente.delete("/api/gestiones").json()["error"] == "Método no permitido"


def test_json_mal_formado_no_muestra_posicion_como_campo(cliente: TestClient) -> None:
    r = cliente.post(
        "/api/gestiones", content="{no es json", headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 400
    assert r.json() == {"error": "Solicitud inválida: el cuerpo no es un JSON válido"}


def _sin_documento(**cambios: object) -> Dict[str, object]:
    cuerpo = _cuerpo(**cambios)
    del cuerpo["documento"]
    return cuerpo


def test_registrar_ivr_sin_documento_201(cliente: TestClient) -> None:
    r = cliente.post(
        "/api/gestiones",
        json=_sin_documento(
            tipificacion="Solicitud de asesor",
            observacion="Transferida al asesor tras 3 errores en el menú",
        ),
    )
    assert r.status_code == 201
    assert set(r.json()) == {"id", "fecha"}


def test_registrar_agente_sin_documento_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_sin_documento(canal="agente"))
    assert r.status_code == 400
    _es_error(r)


def test_registrar_sin_documento_y_sin_observacion_400(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_sin_documento(observacion=""))
    assert r.status_code == 400
    _es_error(r)


def test_registrar_whatsapp_documento_inexistente_404(cliente: TestClient) -> None:
    r = cliente.post("/api/gestiones", json=_cuerpo(canal="whatsapp", documento="99999999"))
    assert r.status_code == 404
    _es_error(r)


def test_registrar_sin_documento_idempotente_201_luego_200(cliente: TestClient) -> None:
    h = {"Idempotency-Key": "llamada-77-asesor"}
    cuerpo = _sin_documento(tipificacion="Solicitud de asesor", observacion="Servicio caído")
    r1 = cliente.post("/api/gestiones", json=cuerpo, headers=h)
    r2 = cliente.post("/api/gestiones", json=cuerpo, headers=h)
    assert (r1.status_code, r2.status_code) == (201, 200)
    assert r1.json() == r2.json()


def test_gestion_sin_documento_no_aparece_en_el_listado_de_un_cliente(cliente: TestClient) -> None:
    cliente.post("/api/gestiones", json=_sin_documento(observacion="Sin cliente"))
    assert cliente.get(f"/api/gestiones?documento={DOC}").json() == []


def test_registrar_503(cliente_caido: TestClient) -> None:
    r = cliente_caido.post("/api/gestiones", json=_cuerpo())
    assert r.status_code == 503
    _es_error(r)


# --- GET /api/gestiones

def test_listar_vacio_200(cliente: TestClient) -> None:
    r = cliente.get(f"/api/gestiones?documento={DOC}")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_orden_descendente(cliente: TestClient) -> None:
    for obs in ("primera", "segunda", "tercera"):
        cliente.post("/api/gestiones", json=_cuerpo(observacion=obs))
    r = cliente.get(f"/api/gestiones?documento={DOC}")
    assert r.status_code == 200
    assert [g["observacion"] for g in r.json()] == ["tercera", "segunda", "primera"]
    assert [g["id"] for g in r.json()] == [3, 2, 1]


def test_listar_solo_del_cliente(cliente: TestClient) -> None:
    cliente.post("/api/gestiones", json=_cuerpo(documento="79876543"))
    assert cliente.get(f"/api/gestiones?documento={DOC}").json() == []


def test_listar_sin_documento_400(cliente: TestClient) -> None:
    r = cliente.get("/api/gestiones")
    assert r.status_code == 400
    _es_error(r)


def test_listar_documento_mal_formado_400(cliente: TestClient) -> None:
    assert cliente.get("/api/gestiones?documento=12").status_code == 400


def test_listar_cliente_inexistente_404(cliente: TestClient) -> None:
    r = cliente.get("/api/gestiones?documento=999999")
    assert r.status_code == 404
    _es_error(r)


def test_listar_503(cliente_caido: TestClient) -> None:
    r = cliente_caido.get(f"/api/gestiones?documento={DOC}")
    assert r.status_code == 503
    _es_error(r)


# --- /health y otros

def test_health_200(cliente: TestClient) -> None:
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_503(cliente: TestClient) -> None:
    def caido() -> None:
        raise RepositorioNoDisponible("sin conexión")

    app.dependency_overrides[get_verificador_salud] = lambda: caido
    r = cliente.get("/health")
    assert r.status_code == 503
    _es_error(r)


def test_ruta_inexistente_json_error(cliente: TestClient) -> None:
    r = cliente.get("/api/no-existe")
    assert r.status_code == 404
    _es_error(r)


def test_error_inesperado_500(cliente: TestClient) -> None:
    class _Roto(ClienteRepositoryEnMemoria):
        def obtener_por_documento(self, documento):  # type: ignore[no-untyped-def]
            raise RuntimeError("fallo")

    app.dependency_overrides[get_cliente_repository] = lambda: _Roto()
    r = cliente.get(f"/api/clientes/{DOC}")
    assert r.status_code == 500
    assert r.json() == {"error": "Error interno del servidor"}
