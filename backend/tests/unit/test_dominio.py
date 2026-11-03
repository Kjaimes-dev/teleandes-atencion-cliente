import pytest

from src.domain.entities.gestion import Gestion
from src.domain.exceptions import DatoInvalido
from src.domain.value_objects.canal import Canal
from src.domain.value_objects.documento import Documento
from src.domain.value_objects.tipificacion import Tipificacion


@pytest.mark.parametrize("valor", ["123456", "1234567890", "52123456"])
def test_documento_valido(valor: str) -> None:
    assert str(Documento(valor)) == valor


@pytest.mark.parametrize(
    "valor", ["12345", "12345678901", "12a456", "1.020.304", "", " 123456", "123456\n"]
)
def test_documento_invalido(valor: str) -> None:
    with pytest.raises(DatoInvalido):
        Documento(valor)


@pytest.mark.parametrize(
    "valor,esperado",
    [("ivr", Canal.IVR), ("whatsapp", Canal.WHATSAPP), ("agente", Canal.AGENTE)],
)
def test_canal_valido(valor: str, esperado: Canal) -> None:
    assert Canal.desde_texto(valor) is esperado


@pytest.mark.parametrize("valor", ["telegram", "IVR", ""])
def test_canal_invalido(valor: str) -> None:
    with pytest.raises(DatoInvalido):
        Canal.desde_texto(valor)


@pytest.mark.parametrize("t", list(Tipificacion))
def test_tipificacion_valida(t: Tipificacion) -> None:
    assert Tipificacion.desde_texto(t.value) is t


@pytest.mark.parametrize("valor", ["reclamo", "Queja", ""])
def test_tipificacion_invalida(valor: str) -> None:
    with pytest.raises(DatoInvalido):
        Tipificacion.desde_texto(valor)


def test_reclamo_sin_observacion_falla() -> None:
    with pytest.raises(DatoInvalido):
        Gestion.crear("1020304050", "ivr", "Reclamo", None)


def test_reclamo_con_observacion_solo_espacios_falla() -> None:
    with pytest.raises(DatoInvalido):
        Gestion.crear("1020304050", "ivr", "Reclamo", "   ")


def test_reclamo_con_observacion_ok() -> None:
    g = Gestion.crear("1020304050", "agente", "Reclamo", " cobro doble ")
    assert g.observacion == "cobro doble"
    assert g.id is None
    assert g.fecha.tzinfo is not None


def test_otra_tipificacion_sin_observacion_ok() -> None:
    assert Gestion.crear("1020304050", "ivr", "Otro", None).observacion == ""


def test_observacion_1000_ok_y_1001_falla() -> None:
    assert len(Gestion.crear("1020304050", "ivr", "Otro", "a" * 1000).observacion) == 1000
    with pytest.raises(DatoInvalido):
        Gestion.crear("1020304050", "ivr", "Otro", "a" * 1001)


# --- Gestión sin cliente identificado

@pytest.mark.parametrize("canal", ["ivr", "whatsapp"])
def test_gestion_sin_documento_con_observacion_ok(canal: str) -> None:
    g = Gestion.crear(None, canal, "Solicitud de asesor", "Transferida tras 3 errores en el menú")
    assert g.documento is None
    assert g.observacion == "Transferida tras 3 errores en el menú"


def test_gestion_sin_documento_canal_agente_falla() -> None:
    with pytest.raises(DatoInvalido):
        Gestion.crear(None, "agente", "Otro", "Sin documento")


@pytest.mark.parametrize("observacion", [None, "", "   "])
def test_gestion_sin_documento_exige_observacion(observacion: object) -> None:
    with pytest.raises(DatoInvalido):
        Gestion.crear(None, "ivr", "Solicitud de asesor", observacion)  # type: ignore[arg-type]


def test_documento_vacio_no_cuenta_como_ausente() -> None:
    # Solo None significa "sin documento"; una cadena vacía es un dato inválido.
    with pytest.raises(DatoInvalido):
        Gestion.crear("", "ivr", "Otro", "Observación")
