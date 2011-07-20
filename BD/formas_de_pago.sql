INSERT INTO modo_pago(id, nombre, cobro_automatico) VALUES 
  (1, 'Efectivo', FALSE), 
  (2, 'Transferencia', FALSE), 
  (3, 'Recibo', FALSE), 
  (4, 'Pagaré', FALSE), 
  (5, 'Confirming', TRUE), 
  (6, 'Cheque', FALSE), 
  (7, 'Giro', FALSE)
;
SELECT setval('modo_pago_id_seq', 7);
INSERT INTO periodo_pago(id, nombre, numero_vencimientos, dia_inicio, dias_entre_vencimientos) VALUES 
  (1, '90', 1, 90, 0), 
  (2, '30-60', 2, 30, 30), 
  (3, '30-60-90', 3, 30, 30), 
  (4, '30-60-120', 3, 30, 30), 
  (5, '30-60-120-180', 4, 30, 30), 
  (6, '60-90', 2, 60, 30), 
  (7, '90-120', 2, 90, 30), 
  (8, '120', 1, 120, 0), 
  (9, '180', 1, 120, 0)
;
SELECT setval('periodo_pago_id_seq', 9);
INSERT INTO forma_de_pago(modo_pago_id, periodo_pago_id, descripcion, retencion) VALUES 
(1, NULL, 'Al contado, sin retención', 0.0), 
(4, 1, 'Pagaré 90 con 20% de retención', 0.2), 
(4, 8, 'Pagaré 120', 0.0), 
(4, 9, 'Pagaré 180 (10% de retención)', 0.1), 
(4, 2, 'Pagaré 30-60', 0.0), 
(5, 1, 'Confirming 90 (10% de retención)', 0.1), 
(5, 7, 'Confirming 90-120, sin retención', 0.0), 
(2, 1, 'Transferencia a 90 días', 0.0), 
(3, 9, 'Recibo 180 días sin retención', 0.0), 
(6, NULL, 'Cheque', 0.0) 
;
-- Y tipos de facturas:
INSERT INTO serie_numerica(prefijo, contador, sufijo) VALUES
('F2011/', 1, ''), 
('', 1, '')
;

INSERT INTO tipo_factura(serie_numerica_id, nombre, descripcion) VALUES
(1, 'ventas', 'Facturas de venta.'), 
(2, 'servicios', 'Facturas de servicios prestados.')
;

