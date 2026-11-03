// Formateo de valores para mostrar. Sin dependencias del DOM.

const ZONA_HORARIA = 'America/Bogota';

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

const formatoPesos = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
  minimumFractionDigits: 0,
});

const formatoFechaHora = new Intl.DateTimeFormat('es-CO', {
  dateStyle: 'medium',
  timeStyle: 'short',
  timeZone: ZONA_HORARIA,
});

// Se piden las partes por separado: el orden, el separador y el relleno con ceros
// de un formato completo dependen del ICU de cada navegador.
const formatoPartesFecha = new Intl.DateTimeFormat('en-US', {
  timeZone: ZONA_HORARIA,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

/** 85000 -> "$ 85.000" */
export function formatearSaldo(valor) {
  // El formato de es-CO usa un espacio no separable tras el símbolo.
  return formatoPesos.format(valor).replace(/\s/g, ' ');
}

/** "2026-10-20" -> "20 de octubre de 2026" */
export function formatearFechaLarga(fechaIso) {
  // Se separa a mano: new Date("2026-10-20") se interpreta en UTC y en Colombia
  // mostraría el día anterior.
  const [anio, mes, dia] = fechaIso.split('-').map(Number);
  return `${dia} de ${MESES[mes - 1]} de ${anio}`;
}

/** Fecha y hora ISO 8601 con offset -> texto legible en hora de Bogotá. */
export function formatearFechaHora(fechaHoraIso) {
  return formatoFechaHora.format(new Date(fechaHoraIso));
}

const ETIQUETAS_CANAL = { ivr: 'IVR', whatsapp: 'WhatsApp', agente: 'Agente' };

/** "ivr" -> "IVR"; un canal desconocido se muestra tal cual. */
export function etiquetarCanal(canal) {
  return ETIQUETAS_CANAL[canal] ?? canal;
}

/** Fecha de hoy en Bogotá como AAAA-MM-DD. */
export function hoyEnBogota(ahora = new Date()) {
  const partes = Object.fromEntries(
    formatoPartesFecha.formatToParts(ahora).map((p) => [p.type, p.value]),
  );
  // padStart garantiza los ceros aunque el navegador no los entregue.
  return `${partes.year}-${partes.month.padStart(2, '0')}-${partes.day.padStart(2, '0')}`;
}

/** True si la fecha de corte (AAAA-MM-DD) es anterior a `hoy` (por defecto, hoy en Bogotá). */
export function estaVencida(fechaIso, hoy = hoyEnBogota()) {
  return fechaIso < hoy;
}
