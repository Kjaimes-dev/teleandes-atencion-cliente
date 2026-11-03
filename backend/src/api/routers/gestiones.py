from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Query, Response

from src.api.dependencies import get_listar_gestiones, get_registrar_gestion
from src.api.schemas.gestion import GestionCreada, GestionIn, GestionOut
from src.application.use_cases.listar_gestiones import ListarGestiones
from src.application.use_cases.registrar_gestion import RegistrarGestion
from src.domain.entities.gestion import Gestion
from src.domain.exceptions import DatoInvalido

router = APIRouter(prefix="/api/gestiones", tags=["gestiones"])

IDEMPOTENCY_KEY_MAX = 64


def _id_persistido(g: Gestion) -> int:
    """Id de una gestión ya guardada; si falta, el repositorio incumplió su contrato."""
    if g.id is None:
        raise ValueError("La gestión devuelta por el repositorio no tiene id")
    return g.id


def _a_salida(g: Gestion) -> GestionOut:
    return GestionOut(
        id=_id_persistido(g),
        documento=str(g.documento) if g.documento is not None else None,
        canal=g.canal.value,
        tipificacion=g.tipificacion.value,
        observacion=g.observacion,
        fecha=g.fecha.isoformat(timespec="milliseconds"),
    )


@router.post("", response_model=GestionCreada, status_code=201)
def registrar_gestion(
    cuerpo: GestionIn,
    response: Response,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    caso: RegistrarGestion = Depends(get_registrar_gestion),
) -> GestionCreada:
    """Registra una gestión; 201 si es nueva, 200 si se reutilizó por la clave."""
    # Una cabecera vacía equivale a no enviarla; guardar "" chocaría con el UNIQUE.
    clave = (idempotency_key or "").strip() or None
    if clave is not None and len(clave) > IDEMPOTENCY_KEY_MAX:
        raise DatoInvalido(f"Idempotency-Key no puede superar {IDEMPOTENCY_KEY_MAX} caracteres")
    gestion, creada = caso.ejecutar(
        cuerpo.documento, cuerpo.canal, cuerpo.tipificacion, cuerpo.observacion, clave
    )
    if not creada:
        response.status_code = 200
    return GestionCreada(id=_id_persistido(gestion), fecha=gestion.fecha.isoformat(timespec="milliseconds"))


@router.get("", response_model=List[GestionOut])
def listar_gestiones(
    documento: Optional[str] = Query(default=None),
    caso: ListarGestiones = Depends(get_listar_gestiones),
) -> List[GestionOut]:
    """Historial del cliente; el documento es obligatorio."""
    if documento is None:
        raise DatoInvalido("El parámetro documento es obligatorio")
    return [_a_salida(g) for g in caso.ejecutar(documento)]
