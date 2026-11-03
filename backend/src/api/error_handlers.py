"""Traduce excepciones a respuestas JSON uniformes {"error": "mensaje"}."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions import ClienteNoEncontrado, DatoInvalido, RepositorioNoDisponible

logger = logging.getLogger(__name__)

# Pydantic reporta en inglés; se traducen los tipos de error más comunes.
_MENSAJES_VALIDACION = {
    "missing": "campo obligatorio",
    "string_type": "debe ser texto",
    "json_invalid": "el cuerpo no es un JSON válido",
    "model_attributes_type": "el cuerpo debe ser un objeto JSON",
}

_MENSAJES_HTTP = {
    404: "Recurso no encontrado",
    405: "Método no permitido",
    415: "Tipo de contenido no soportado",
}


def _error(codigo: int, mensaje: str) -> JSONResponse:
    return JSONResponse(status_code=codigo, content={"error": mensaje})


async def _dato_invalido(_: Request, exc: DatoInvalido) -> JSONResponse:
    return _error(400, str(exc))


async def _cliente_no_encontrado(_: Request, exc: ClienteNoEncontrado) -> JSONResponse:
    return _error(404, str(exc))


async def _no_disponible(_: Request, exc: RepositorioNoDisponible) -> JSONResponse:
    logger.error("Repositorio no disponible: %s", exc)
    return _error(503, "Servicio no disponible, intente más tarde")


async def _validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    partes = []
    for e in exc.errors():
        # Se omite el origen (body/query/header) para dejar solo el nombre del campo.
        ruta = e.get("loc", ())[1:]
        motivo = _MENSAJES_VALIDACION.get(e.get("type", ""), "valor inválido")
        # En un JSON mal formado loc trae la posición del error (un entero), no un campo.
        if ruta and all(isinstance(p, str) for p in ruta):
            partes.append(f"{'.'.join(ruta)}: {motivo}")
        else:
            partes.append(motivo)
    return _error(400, "Solicitud inválida: " + "; ".join(partes))


async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error(exc.status_code, _MENSAJES_HTTP.get(exc.status_code, str(exc.detail)))


async def _generico(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado", exc_info=exc)
    return _error(500, "Error interno del servidor")


def registrar_manejadores(app: FastAPI) -> None:
    """Registra todos los manejadores en la aplicación."""
    app.add_exception_handler(DatoInvalido, _dato_invalido)  # type: ignore[arg-type]
    app.add_exception_handler(ClienteNoEncontrado, _cliente_no_encontrado)  # type: ignore[arg-type]
    app.add_exception_handler(RepositorioNoDisponible, _no_disponible)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validacion)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _generico)
