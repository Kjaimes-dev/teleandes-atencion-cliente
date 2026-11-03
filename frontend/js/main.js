import { ApiError, consultarCliente, listarGestiones, registrarGestion } from './api.js';
import * as ui from './ui.js';

const CANAL = 'agente';
const PATRON_DOCUMENTO = /^[0-9]{6,10}$/;

const $ = (id) => document.getElementById(id);

// Documento del cliente que se está atendiendo; null mientras no haya uno cargado.
let documentoActual = null;
// Una clave por gestión: si el envío falla se reutiliza al reintentar, y un doble
// clic nunca genera dos gestiones. Se renueva solo cuando la gestión se guarda.
let claveIdempotencia = null;
let enviando = false;

function nuevaClave() {
  // randomUUID solo existe en contextos seguros (https o localhost).
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/** El canal normaliza lo que el agente digita; la API exige solo dígitos. */
function normalizarDocumento(texto) {
  return texto.replace(/[.\s]/g, '');
}

function textoError(error) {
  return error instanceof ApiError ? error.message : 'Ocurrió un error inesperado. Intente de nuevo.';
}

async function alConsultar(evento) {
  evento.preventDefault();
  // Cambiar de cliente a mitad de un guardado mezclaría el aviso y el historial.
  if (enviando) return;
  const boton = $('btn-consultar');
  const documento = normalizarDocumento($('documento').value);

  ui.limpiarMensaje();
  ui.ocultarCliente();
  documentoActual = null;

  if (!PATRON_DOCUMENTO.test(documento)) {
    ui.mostrarMensaje('El documento debe ser numérico, de 6 a 10 dígitos.', 'error');
    $('documento').focus();
    return;
  }

  ui.setCargando(boton, true, 'Consultando…');
  try {
    const [cliente, gestiones] = await Promise.all([
      consultarCliente(documento),
      listarGestiones(documento),
    ]);
    documentoActual = documento;
    claveIdempotencia = null;
    ui.mostrarFicha(cliente);
    ui.mostrarHistorial(gestiones);
  } catch (error) {
    ui.mostrarMensaje(textoError(error), 'error');
  } finally {
    ui.setCargando(boton, false);
  }
}

async function alGuardar(evento) {
  evento.preventDefault();
  if (enviando || documentoActual === null) return;

  const { tipificacion, observacion } = ui.leerFormularioGestion();
  ui.limpiarErrorTipificacion();
  ui.limpiarErrorObservacion();
  ui.limpiarMensaje();

  if (tipificacion === '') {
    ui.mostrarErrorTipificacion('Seleccione una tipificación.');
    return;
  }

  // La API también lo valida; aquí se evita el viaje de ida y vuelta.
  if (tipificacion === 'Reclamo' && observacion === '') {
    ui.mostrarErrorObservacion('La observación es obligatoria cuando la tipificación es Reclamo.');
    return;
  }

  // Se marca antes de cualquier await para que un segundo clic ya encuentre el bloqueo.
  enviando = true;
  const boton = $('btn-guardar');
  ui.setCargando(boton, true, 'Guardando…');
  $('btn-consultar').disabled = true;
  claveIdempotencia ??= nuevaClave();

  try {
    await registrarGestion(
      { documento: documentoActual, canal: CANAL, tipificacion, observacion },
      claveIdempotencia,
    );
    claveIdempotencia = null;
    ui.limpiarFormularioGestion();
    ui.mostrarMensaje('Gestión guardada correctamente.', 'ok');
    // El historial es secundario: si falla, la gestión ya quedó guardada.
    try {
      ui.mostrarHistorial(await listarGestiones(documentoActual));
    } catch (error) {
      ui.mostrarMensaje(
        `Gestión guardada, pero no se pudo actualizar el historial. ${textoError(error)}`,
        'error',
      );
    }
  } catch (error) {
    ui.mostrarMensaje(textoError(error), 'error');
  } finally {
    enviando = false;
    $('btn-consultar').disabled = false;
    ui.setCargando(boton, false);
  }
}

ui.cargarTipificaciones();
ui.actualizarContador();
ui.actualizarObligatoriedad();

$('form-consulta').addEventListener('submit', alConsultar);
$('form-gestion').addEventListener('submit', alGuardar);
$('observacion').addEventListener('input', () => {
  ui.actualizarContador();
  ui.limpiarErrorObservacion();
});
$('tipificacion').addEventListener('change', () => {
  ui.limpiarErrorTipificacion();
  ui.actualizarObligatoriedad();
});
