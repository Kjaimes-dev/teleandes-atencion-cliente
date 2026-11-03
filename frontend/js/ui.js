// Manipulación del DOM. Los datos del servidor se insertan con textContent, nunca con innerHTML.

import {
  estaVencida, etiquetarCanal, formatearFechaHora, formatearFechaLarga, formatearSaldo,
} from './format.js';

const $ = (id) => document.getElementById(id);

export const TIPIFICACIONES = [
  'Consulta de saldo',
  'Consulta de estado',
  'Reclamo',
  'Solicitud de asesor',
  'Otro',
];
export const OBSERVACION_MAX = 1000;

export function cargarTipificaciones() {
  const selector = $('tipificacion');
  // Sin valor por defecto: el agente debe elegir la tipificación a conciencia.
  selector.add(new Option('Seleccione una tipificación', ''));
  for (const nombre of TIPIFICACIONES) {
    selector.add(new Option(nombre, nombre));
  }
}

const MENSAJE_OK_MS = 5000;
let temporizadorMensaje = null;

/** El aviso de éxito se retira solo; los de error se quedan hasta que el asesor actúe. */
export function mostrarMensaje(texto, tipo) {
  const area = $('mensaje');
  // Un aviso nuevo cancela el temporizador del anterior para que no lo oculte.
  clearTimeout(temporizadorMensaje);
  area.textContent = texto;
  area.className = `mensaje mensaje-${tipo}`;
  area.hidden = false;
  if (tipo === 'ok') temporizadorMensaje = setTimeout(limpiarMensaje, MENSAJE_OK_MS);
}

export function limpiarMensaje() {
  const area = $('mensaje');
  clearTimeout(temporizadorMensaje);
  area.textContent = '';
  area.hidden = true;
}

export function setCargando(boton, cargando, textoCargando) {
  // El texto va en su propio span para no borrar el ícono del botón.
  const texto = boton.querySelector('.boton-texto') ?? boton;
  if (cargando) {
    boton.dataset.textoOriginal = texto.textContent;
    texto.textContent = textoCargando;
  } else if (boton.dataset.textoOriginal) {
    texto.textContent = boton.dataset.textoOriginal;
  }
  boton.disabled = cargando;
}

export function mostrarFicha(cliente) {
  const suspendido = cliente.estado === 'suspendido';

  $('ficha-nombre').textContent = cliente.nombre;
  $('ficha-plan').textContent = cliente.plan;
  $('ficha-estado').textContent = suspendido ? 'Suspendido' : 'Activo';
  $('ficha-saldo').textContent = formatearSaldo(cliente.saldo);
  // Solo se resalta cuando hay deuda; un saldo en cero se ve normal.
  $('ficha-saldo').classList.toggle('saldo-pendiente', cliente.saldo > 0);
  $('ficha-corte').textContent = formatearFechaLarga(cliente.fecha_corte);
  $('etiqueta-vencida').hidden = !estaVencida(cliente.fecha_corte);

  const etiqueta = $('etiqueta-estado');
  etiqueta.textContent = suspendido ? 'SUSPENDIDO' : 'ACTIVO';
  etiqueta.className = `etiqueta ${suspendido ? 'etiqueta-suspendido' : 'etiqueta-activo'}`;
  $('ficha').classList.toggle('suspendido', suspendido);

  $('ficha').hidden = false;
  $('gestion').hidden = false;
  $('historial').hidden = false;
}

export function ocultarCliente() {
  for (const id of ['ficha', 'gestion', 'historial']) {
    $(id).hidden = true;
  }
  limpiarFormularioGestion();
}

const CANALES_CONOCIDOS = ['ivr', 'whatsapp', 'agente'];

function crearEtiquetaCanal(canal) {
  const etiqueta = document.createElement('span');
  // La clase de color solo se aplica a canales conocidos; el texto siempre va con textContent.
  const clase = CANALES_CONOCIDOS.includes(canal) ? ` etiqueta-canal-${canal}` : '';
  etiqueta.className = `etiqueta etiqueta-canal${clase}`;
  etiqueta.textContent = etiquetarCanal(canal);
  return etiqueta;
}

export function mostrarHistorial(gestiones) {
  const cuerpo = $('tabla-historial').tBodies[0];
  cuerpo.replaceChildren();

  $('historial-vacio').hidden = gestiones.length > 0;
  $('tabla-historial').hidden = gestiones.length === 0;

  for (const g of gestiones) {
    const fila = cuerpo.insertRow();
    fila.insertCell().textContent = formatearFechaHora(g.fecha);
    fila.insertCell().append(crearEtiquetaCanal(g.canal));
    fila.insertCell().textContent = g.tipificacion;
    const celdaObservacion = fila.insertCell();
    celdaObservacion.className = 'observacion';
    celdaObservacion.textContent = g.observacion || '—';
  }
}

export function actualizarContador() {
  $('contador-observacion').textContent = `${$('observacion').value.length} / ${OBSERVACION_MAX}`;
}

/** Marca la observación como obligatoria cuando la tipificación es Reclamo. */
export function actualizarObligatoriedad() {
  const obligatoria = $('tipificacion').value === 'Reclamo';
  $('marca-obligatorio').hidden = !obligatoria;
  $('observacion').setAttribute('aria-required', String(obligatoria));
  if (!obligatoria) limpiarErrorObservacion();
}

export function mostrarErrorTipificacion(texto) {
  const error = $('error-tipificacion');
  error.textContent = texto;
  error.hidden = false;
  $('tipificacion').focus();
}

export function limpiarErrorTipificacion() {
  $('error-tipificacion').hidden = true;
}

export function mostrarErrorObservacion(texto) {
  const error = $('error-observacion');
  error.textContent = texto;
  error.hidden = false;
  $('observacion').classList.add('invalido');
  $('observacion').focus();
}

export function limpiarErrorObservacion() {
  $('error-observacion').hidden = true;
  $('observacion').classList.remove('invalido');
}

export function limpiarFormularioGestion() {
  $('tipificacion').selectedIndex = 0;
  $('observacion').value = '';
  limpiarErrorTipificacion();
  limpiarErrorObservacion();
  actualizarContador();
  actualizarObligatoriedad();
}

export function leerFormularioGestion() {
  return {
    tipificacion: $('tipificacion').value,
    observacion: $('observacion').value.trim(),
  };
}
