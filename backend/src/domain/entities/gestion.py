from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from src.domain.exceptions import DatoInvalido
from src.domain.value_objects.canal import Canal
from src.domain.value_objects.documento import Documento
from src.domain.value_objects.tipificacion import Tipificacion

ZONA_HORARIA = ZoneInfo("America/Bogota")
OBSERVACION_MAX = 1000


@dataclass(frozen=True)
class Gestion:
    """Atención registrada a un cliente. `id` es None hasta que se persiste."""

    documento: Optional[Documento]  # None solo en gestiones de canales ivr y whatsapp
    canal: Canal
    tipificacion: Tipificacion
    observacion: str
    fecha: datetime  # con zona America/Bogota
    idempotency_key: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def crear(
        cls,
        documento: Optional[str],
        canal: str,
        tipificacion: str,
        observacion: Optional[str],
        idempotency_key: Optional[str] = None,
    ) -> "Gestion":
        """Valida las reglas de negocio y construye la gestión con la fecha actual."""
        canal_vo = Canal.desde_texto(canal)
        tip_vo = Tipificacion.desde_texto(tipificacion)
        texto = (observacion or "").strip()

        # Solo se admite una gestión sin cliente cuando aún no se pudo identificar
        # (llamada transferida antes de pedir el documento, por ejemplo). El agente
        # siempre atiende a un cliente concreto.
        if documento is None:
            if canal_vo is Canal.AGENTE:
                raise DatoInvalido("El documento es obligatorio para el canal agente")
            # Sin cliente, la observación es la única explicación de la atención.
            if not texto:
                raise DatoInvalido("La observación es obligatoria cuando no se informa documento")
            doc = None
        else:
            doc = Documento(documento)

        if len(texto) > OBSERVACION_MAX:
            raise DatoInvalido(f"La observación no puede superar {OBSERVACION_MAX} caracteres")
        # Un reclamo sin detalle no es accionable.
        if tip_vo is Tipificacion.RECLAMO and not texto:
            raise DatoInvalido("La observación es obligatoria cuando la tipificación es Reclamo")

        ahora = datetime.now(ZONA_HORARIA)
        # DATETIME(3) guarda milisegundos: se trunca aquí para que la respuesta del
        # POST, el replay idempotente y el listado muestren la misma fecha.
        ahora = ahora.replace(microsecond=ahora.microsecond // 1000 * 1000)

        return cls(
            documento=doc,
            canal=canal_vo,
            tipificacion=tip_vo,
            observacion=texto,
            fecha=ahora,
            idempotency_key=idempotency_key,
        )
