"""Inyección de dependencias; las pruebas sobreescriben repositorios y verificador."""
from functools import lru_cache
from typing import Callable

from fastapi import Depends

from config.settings import get_settings
from src.application.use_cases.consultar_cliente import ConsultarCliente
from src.application.use_cases.listar_gestiones import ListarGestiones
from src.application.use_cases.registrar_gestion import RegistrarGestion
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.repositories.gestion_repository import GestionRepository
from src.infrastructure.db.connection_manager import ConnectionManager
from src.infrastructure.db.repositories.mysql_cliente_repository import MySQLClienteRepository
from src.infrastructure.db.repositories.mysql_gestion_repository import MySQLGestionRepository


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """Un solo manager por proceso; crear el engine no abre conexiones."""
    return ConnectionManager(get_settings())


def cerrar_conexiones() -> None:
    """Libera el pool al apagar, solo si el manager llegó a crearse."""
    if get_connection_manager.cache_info().currsize:
        get_connection_manager().cerrar()


def get_cliente_repository() -> ClienteRepository:
    return MySQLClienteRepository(get_connection_manager())


def get_gestion_repository() -> GestionRepository:
    return MySQLGestionRepository(get_connection_manager())


def get_verificador_salud() -> Callable[[], None]:
    """Función que lanza RepositorioNoDisponible si la BD no responde."""
    return get_connection_manager().verificar_conexion


def get_consultar_cliente(
    clientes: ClienteRepository = Depends(get_cliente_repository),
) -> ConsultarCliente:
    return ConsultarCliente(clientes)


def get_registrar_gestion(
    clientes: ClienteRepository = Depends(get_cliente_repository),
    gestiones: GestionRepository = Depends(get_gestion_repository),
) -> RegistrarGestion:
    return RegistrarGestion(clientes, gestiones)


def get_listar_gestiones(
    clientes: ClienteRepository = Depends(get_cliente_repository),
    gestiones: GestionRepository = Depends(get_gestion_repository),
) -> ListarGestiones:
    return ListarGestiones(clientes, gestiones)
