// Ejecutar desde frontend/ con: node --test   (requiere Node 18 o superior)
import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  estaVencida, etiquetarCanal, formatearFechaLarga, formatearSaldo, hoyEnBogota,
} from '../js/format.js';

test('formatearSaldo usa pesos colombianos sin decimales', () => {
  assert.equal(formatearSaldo(85000), '$ 85.000');
  assert.equal(formatearSaldo(0), '$ 0');
  assert.equal(formatearSaldo(120500), '$ 120.500');
});

test('formatearFechaLarga no corre el día por la zona horaria', () => {
  assert.equal(formatearFechaLarga('2026-10-20'), '20 de octubre de 2026');
  assert.equal(formatearFechaLarga('2026-11-05'), '5 de noviembre de 2026');
  assert.equal(formatearFechaLarga('2026-01-01'), '1 de enero de 2026');
});

test('estaVencida compara contra la fecha de hoy recibida', () => {
  assert.equal(estaVencida('2026-10-20', '2026-11-02'), true);
  assert.equal(estaVencida('2026-11-02', '2026-11-02'), false);
  assert.equal(estaVencida('2026-11-15', '2026-11-02'), false);
});

test('hoyEnBogota devuelve AAAA-MM-DD con ceros', () => {
  assert.equal(hoyEnBogota(new Date('2026-11-02T15:00:00Z')), '2026-11-02');
  assert.equal(hoyEnBogota(new Date('2026-01-05T15:00:00Z')), '2026-01-05');
  assert.equal(hoyEnBogota(new Date('2026-12-15T15:00:00Z')), '2026-12-15');
});

test('hoyEnBogota respeta la zona horaria al cambiar de día', () => {
  // 03:00 UTC es 22:00 del día anterior en Bogotá (UTC-5).
  assert.equal(hoyEnBogota(new Date('2026-11-03T03:00:00Z')), '2026-11-02');
  assert.equal(hoyEnBogota(new Date('2026-11-03T05:00:00Z')), '2026-11-03');
});

test('estaVencida usa hoy de Bogotá con día de un dígito', () => {
  const hoy = hoyEnBogota(new Date('2026-11-02T15:00:00Z'));
  assert.equal(estaVencida('2026-11-05', hoy), false);
  assert.equal(estaVencida('2026-11-15', hoy), false);
  assert.equal(estaVencida('2026-10-20', hoy), true);
});

test('etiquetarCanal muestra nombres legibles', () => {
  assert.equal(etiquetarCanal('agente'), 'Agente');
  assert.equal(etiquetarCanal('ivr'), 'IVR');
  assert.equal(etiquetarCanal('whatsapp'), 'WhatsApp');
  assert.equal(etiquetarCanal('otro'), 'otro');
});
