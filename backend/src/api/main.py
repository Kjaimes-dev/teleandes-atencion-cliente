"""Punto de entrada de la API de TeleAndes."""
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from config.logger_config import configurar_logging
from src.api.dependencies import cerrar_conexiones, get_verificador_salud
from src.api.error_handlers import registrar_manejadores
from src.api.routers import clientes, gestiones
from src.domain.exceptions import RepositorioNoDisponible

# Se lee del entorno y no de Settings para que el arranque no dependa de las variables de BD.
configurar_logging(os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        cerrar_conexiones()


app = FastAPI(title="TeleAndes - Atención al cliente", lifespan=lifespan)
registrar_manejadores(app)
app.include_router(clientes.router)
app.include_router(gestiones.router)


@app.get("/health")
def health(verificar: Callable[[], None] = Depends(get_verificador_salud)) -> JSONResponse:
    """Comprueba que la base de datos responde."""
    try:
        verificar()
    except RepositorioNoDisponible:
        return JSONResponse(
            status_code=503, content={"error": "Servicio no disponible, intente más tarde"}
        )
    return JSONResponse(status_code=200, content={"status": "ok"})

