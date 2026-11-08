# Adición física A3 — migración 018

Estado: ensayada en PostgreSQL 17 y 16 efímeros; NO aplicada en la demostración persistente. El dump físico anterior se conserva como fotografía previa; no se presenta como regenerado ni se borran tablas/filas.

`traspaso_inventario` tiene PK `(tenant_id,operation_id)`, origen/destino, variante, cantidad, autor, IDs únicos de Salida/Entrada, hash canónico y resultado JSONB estable. Las FK compuestas conservan pertenencia por empresa hacia sucursales, variante, usuario y ambos movimientos. El índice aditivo `(tenant_id,id_movimiento)` habilita las referencias compuestas sin sustituir la PK existente.

RLS exige tenant; la lectura del vínculo completo requiere ambas asignaciones o Administrador, y su inserción exige los roles existentes de gestión. `validate_transfer_movements` comprueba tipo, sucursales, variante, cantidades y actor de las patas. El historial nuevo es inmutable. La función protectora de contexto fijo, sin devolver datos, consulta referencias con permisos del propietario para proteger incluso una pata cuyo vínculo esté oculto por RLS. Nuevos INSERT de tipo bruto Traspaso se rechazan; los históricos no se modifican.

El trigger `actualizar_stock_por_movimiento` conserva exactamente Entrada/Salida y continúa siendo el único mecanismo que cambia sus saldos. No existe ORM. Ver DDL real: `Parcial2_backend/database/migrations/018_inventory_transfers.sql`. La migración añade objetos e índices/triggers; debe aplicarse antes de activar el código nuevo y puede bloquear escrituras brevemente al instalar el índice/trigger. No hay migración de borrado ni recalculado retrospectivo.

Reglas, pruebas y aprobación pendiente: [A3](../CORRECCION_AUTORIZACION_A3.md).
