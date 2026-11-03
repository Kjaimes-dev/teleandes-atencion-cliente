from fastapi import APIRouter, Depends

from src.api.dependencies import get_consultar_cliente
from src.api.schemas.cliente import ClienteOut
from src.application.use_cases.consultar_cliente import ConsultarCliente

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.get("/{documento}", response_model=ClienteOut)
def consultar_cliente(
    documento: str, caso: ConsultarCliente = Depends(get_consultar_cliente)
) -> ClienteOut:
    """Datos del cliente por documento."""
    c = caso.ejecutar(documento)
    return ClienteOut(
        documento=c.documento,
        nombre=c.nombre,
        celular=c.celular,
        plan=c.plan,
        estado=c.estado,
        saldo=c.saldo,
        fecha_corte=c.fecha_corte.isoformat(),
    )
