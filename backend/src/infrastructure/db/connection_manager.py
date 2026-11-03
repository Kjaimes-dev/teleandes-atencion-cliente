import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, InterfaceError, OperationalError

from config.settings import Settings
from src.domain.exceptions import ErrorDominio, RepositorioNoDisponible

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Administra el engine y entrega conexiones con commit/rollback explícitos."""

    def __init__(self, settings: Settings) -> None:
        url = URL.create(
            drivername="mysql+pymysql",
            username=settings.db_user,
            password=settings.db_password,  # URL.create escapa los caracteres especiales
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            query={"charset": "utf8mb4"},
        )
        # pool_pre_ping descarta conexiones muertas antes de usarlas.
        self._engine: Engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": settings.db_connect_timeout},
        )

    @contextmanager
    def conexion(self) -> Iterator[Connection]:
        """Abre una conexión; confirma al salir bien, revierte ante error y siempre cierra."""
        try:
            conn = self._engine.connect()
        except Exception as exc:
            # Cualquier fallo al abrir (red, credenciales, o el driver, que lanza
            # RuntimeError si le falta un paquete de autenticación) deja la BD
            # inutilizable: se registra el motivo y se responde 503.
            logger.error("No fue posible abrir la conexión a la base de datos: %s", exc)
            raise RepositorioNoDisponible("La base de datos no está disponible") from exc

        try:
            yield conn
            conn.commit()
        except Exception as exc:
            self._revertir(conn)
            self._registrar_y_traducir(exc)
            raise
        finally:
            conn.close()

    def verificar_conexion(self) -> None:
        """Ejecuta SELECT 1; lanza RepositorioNoDisponible si la BD no responde."""
        with self.conexion() as conn:
            conn.execute(text("SELECT 1"))

    def cerrar(self) -> None:
        """Libera el pool de conexiones (cierre de la aplicación)."""
        self._engine.dispose()

    @staticmethod
    def _revertir(conn: Connection) -> None:
        try:
            conn.rollback()
        except Exception:
            # Si la conexión ya murió el rollback falla; el error original es el relevante.
            logger.warning("Falló el rollback; la conexión probablemente se perdió", exc_info=True)

    @staticmethod
    def _registrar_y_traducir(exc: Exception) -> None:
        """Traduce fallos de conectividad a RepositorioNoDisponible; el resto se registra.

        Si no lanza, el llamador relanza la excepción original.
        """
        if isinstance(exc, ErrorDominio):
            # Los errores de negocio no son fallos de infraestructura.
            return
        if isinstance(exc, IntegrityError):
            # Lo clasifica y registra el repositorio: una clave duplicada es esperada.
            return
        if isinstance(exc, (OperationalError, InterfaceError)) or (
            isinstance(exc, DBAPIError) and exc.connection_invalidated
        ):
            logger.error("Fallo de conexión con la base de datos: %s", exc)
            raise RepositorioNoDisponible("La base de datos no está disponible") from exc
        logger.error("Error en la operación de base de datos: %s", exc, exc_info=True)
