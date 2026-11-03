// Cliente HTTP de la API. Todo error se traduce a ApiError con un mensaje legible.

const TIMEOUT_MS = 8000;

export class ApiError extends Error {
  constructor(mensaje, estado = null) {
    super(mensaje);
    this.estado = estado;
  }
}

async function solicitar(url, opciones = {}) {
  const controlador = new AbortController();
  // Sin timeout, una API colgada dejaría el botón en "cargando" para siempre.
  const temporizador = setTimeout(() => controlador.abort(), TIMEOUT_MS);

  let respuesta;
  try {
    respuesta = await fetch(url, { ...opciones, signal: controlador.signal });
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new ApiError('El servicio tardó demasiado en responder. Intente de nuevo.');
    }
    throw new ApiError('No hay conexión con el servicio. Verifique la red e intente de nuevo.');
  } finally {
    clearTimeout(temporizador);
  }

  let cuerpo = null;
  try {
    cuerpo = await respuesta.json();
  } catch {
    // Cuerpo vacío o no JSON (p. ej. un proxy devolviendo HTML): se usa un mensaje genérico.
  }

  if (!respuesta.ok) {
    const mensaje = cuerpo?.error
      ?? (respuesta.status >= 500
        ? 'El servicio no está disponible en este momento. Intente más tarde.'
        : 'No fue posible completar la solicitud.');
    throw new ApiError(mensaje, respuesta.status);
  }
  return cuerpo;
}

export function consultarCliente(documento) {
  return solicitar(`/api/clientes/${encodeURIComponent(documento)}`);
}

export function listarGestiones(documento) {
  return solicitar(`/api/gestiones?documento=${encodeURIComponent(documento)}`);
}

export function registrarGestion(gestion, claveIdempotencia) {
  return solicitar('/api/gestiones', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': claveIdempotencia,
    },
    body: JSON.stringify(gestion),
  });
}
