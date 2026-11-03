"""Repositorios en memoria para pruebas unitarias e integración."""
from dataclasses import replace
from datetime import date
from typing import Dict, List, Optional

from src.domain.entities.cliente import Cliente
from src.domain.entities.gestion import Gestion
from src.domain.exceptions import IdempotencyKeyDuplicada, RepositorioNoDisponible
from src.domain.repositories.cliente_repository import ClienteRepository
from src.domain.repositories.gestion_repository import GestionRepository
from src.domain.value_objects.documento import Documento

CLIENTES_SEED: List[Cliente] = [
    Cliente("1020304050", "Laura Gómez", "3001112233", "Plan Hogar 100", "activo", 0, date(2026, 11, 5)),
    Cliente("52123456", "Carlos Pérez", "3012223344", "Plan Móvil 20GB", "suspendido", 85000, date(2026, 10, 20)),
    Cliente("79876543", "Ana Ruiz", "3023334455", "Plan Combo Plus", "activo", 120500, date(2026, 11, 15)),
]


class ClienteRepositoryEnMemoria(ClienteRepository):
    def __init__(self, clientes: Optional[List[Cliente]] = None) -> None:
        origen = CLIENTES_SEED if clientes is None else clientes
        self._clientes: Dict[str, Cliente] = {c.documento: c for c in origen}

    def obtener_por_documento(self, documento: Documento) -> Optional[Cliente]:
        return self._clientes.get(documento.valor)


class GestionRepositoryEnMemoria(GestionRepository):
    def __init__(self) -> None:
        self._gestiones: List[Gestion] = []
        self._siguiente_id = 1

    def guardar(self, gestion: Gestion) -> Gestion:
        clave = gestion.idempotency_key
        # Imita el UNIQUE de MySQL: solo NULL puede repetirse, la cadena vacía no.
        if clave is not None and any(g.idempotency_key == clave for g in self._gestiones):
            raise IdempotencyKeyDuplicada(clave)
        guardada = replace(gestion, id=self._siguiente_id)
        self._siguiente_id += 1
        self._gestiones.append(guardada)
        return guardada

    def buscar_por_idempotency_key(self, clave: str) -> Optional[Gestion]:
        return next((g for g in self._gestiones if g.idempotency_key == clave), None)

    def listar_por_documento(self, documento: Documento) -> List[Gestion]:
        propias = [g for g in self._gestiones if g.documento == documento]
        return sorted(propias, key=lambda g: (g.fecha, g.id or 0), reverse=True)


class ClienteRepositoryNoDisponible(ClienteRepository):
    def obtener_por_documento(self, documento: Documento) -> Optional[Cliente]:
        raise RepositorioNoDisponible("Base de datos no responde")


class GestionRepositoryNoDisponible(GestionRepository):
    def guardar(self, gestion: Gestion) -> Gestion:
        raise RepositorioNoDisponible("Base de datos no responde")

    def buscar_por_idempotency_key(self, clave: str) -> Optional[Gestion]:
        raise RepositorioNoDisponible("Base de datos no responde")

    def listar_por_documento(self, documento: Documento) -> List[Gestion]:
        raise RepositorioNoDisponible("Base de datos no responde")
