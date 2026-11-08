import 'dart:convert';
import 'package:path/path.dart' as path;
import 'package:sqflite/sqflite.dart';

const _tables = [
  'product',
  'variant',
  'branch',
  'stock',
  'customer',
  'operation',
  'detail',
  'meta'
];
const _mutable = [
  'state',
  'attempts',
  'result',
  'reason',
  'accounted',
  'resolved'
];

String _canonical(dynamic value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return '{${keys.map((key) => '${jsonEncode(key)}:${_canonical(value[key])}').join(',')}}';
  }
  if (value is List) return '[${value.map(_canonical).join(',')}]';
  return jsonEncode(value);
}

Map<String, dynamic> _meta(Map<String, List<Map<String, Object?>>> rows) =>
    {for (final row in rows['meta']!) row['key'] as String: row['value']};

Future<Map<String, List<Map<String, Object?>>>> _read(
    DatabaseExecutor db) async {
  final check = await db.rawQuery('PRAGMA integrity_check');
  if (check.length != 1 ||
      check.single.values.single != 'ok' ||
      (await db.rawQuery('PRAGMA foreign_key_check')).isNotEmpty) {
    throw StateError(
        'Integridad SQLite inválida. Los archivos originales se conservan.');
  }
  return {for (final name in _tables) name: await db.query(name)};
}

void _validate(Map<String, List<Map<String, Object?>>> rows, String namespace) {
  final parts = namespace.split(':').map(int.parse).toList();
  final meta = _meta(rows);
  final branches = rows['branch']!.map((row) => row['id']).toSet();
  if (meta['snapshot'] != null) {
    final snapshot = jsonDecode(meta['snapshot'] as String);
    if (snapshot['tenant_id'] != parts[0] ||
        snapshot['author_id'] != parts[1] ||
        !branches.contains(snapshot['branch']['id_sucursal'])) {
      throw StateError('La base no corresponde a la cuenta activa.');
    }
  }
  for (final row in rows['operation']!) {
    final envelope = jsonDecode(row['envelope'] as String);
    if (envelope['tenant_id'] != parts[0] ||
        envelope['author_id'] != parts[1] ||
        envelope['operation_id'] != row['id'] ||
        envelope['branch_id'] != row['branch_id'] ||
        envelope['kind'] != row['kind'] ||
        envelope['occurred_at'] != row['occurred_at'] ||
        envelope['customer_id'] != row['customer_id'] ||
        envelope['original_operation'] != row['original'] ||
        !branches.contains(row['branch_id']) ||
        !rows['detail']!.any((detail) => detail['operation_id'] == row['id'])) {
      throw StateError(
          'Identidad o referencias incompatibles. Se conserva el historial original.');
    }
  }
}

String _mutableValue(Map<String, Object?> row) =>
    _canonical({for (final key in _mutable) key: row[key]});
String _immutableValue(Map<String, Object?> row) => _canonical({
      for (final key in row.keys.where((key) => !_mutable.contains(key)))
        key: key == 'envelope' ? jsonDecode(row[key] as String) : row[key],
    });

Future<void> _references(
    Transaction tx, Map<String, List<Map<String, Object?>>> rows) async {
  for (final table in ['product', 'variant', 'branch', 'customer', 'stock']) {
    for (final row in rows[table]!) {
      if (table == 'variant') {
        final existing =
            await tx.query(table, where: 'id=?', whereArgs: [row['id']]);
        if (existing.isNotEmpty &&
            existing.single['product_id'] != row['product_id']) {
          throw StateError(
              'Referencias de catálogo incompatibles; se conservan ambas bases.');
        }
      }
      // Catálogos provisionales, nunca suma de stock ni REPLACE de referencias.
      await tx.insert(table, row, conflictAlgorithm: ConflictAlgorithm.ignore);
    }
  }
}

/// Copia aditiva de alias aprobados. No abre archivos de otras cuentas.
/// La identidad y los marcadores se confirman con las operaciones, en una transacción.
Future<void> recoverOfflineDatabases({
  required Database target,
  required DatabaseFactory factory,
  required String directory,
  required String namespace,
  required String deployment,
  required List<String> legacyOrigins,
}) async {
  try {
    await target.transaction((tx) async {
      final current = await _read(tx);
      final identity = _canonical(
          {'deployment': deployment, 'namespace': namespace, 'version': 1});
      final meta = _meta(current);
      if (meta['sync_lock'] != null &&
          (jsonDecode(meta['sync_lock'] as String)['expires'] as int) >
              DateTime.now().millisecondsSinceEpoch) {
        throw StateError(
            'La cola está en uso. Espera a que termine antes de abrirla.');
      }
      if (meta['storage_identity'] != null &&
              meta['storage_identity'] != identity ||
          meta['storage_identity'] == null &&
              current['operation']!.isNotEmpty) {
        throw StateError(
            'La identidad de almacenamiento no coincide con la cuenta activa.');
      }
      _validate(current, namespace);
      if (meta['storage_identity'] == null) {
        await tx.insert('meta', {'key': 'storage_identity', 'value': identity});
      }
      // Las revisiones pueden referir una cabecera que se importa más adelante.
      await tx.execute('PRAGMA defer_foreign_keys=ON');
      var imported = 0;
      for (final origin in legacyOrigins) {
        final encoded =
            base64Url.encode(utf8.encode(origin)).replaceAll('=', '');
        final filename = path.join(directory,
            'fashionstore_p2_${encoded}_${namespace.replaceAll(':', '_')}.db');
        if (!await factory.databaseExists(filename)) continue;
        final source = await factory.openDatabase(filename,
            options:
                OpenDatabaseOptions(readOnly: true, singleInstance: false));
        late Map<String, List<Map<String, Object?>>> rows;
        try {
          if (await source.getVersion() != 1) {
            throw StateError(
                'Versión SQLite anterior incompatible; los archivos se conservan.');
          }
          rows = await source.transaction((read) async => _read(read),
              exclusive: false);
        } finally {
          await source.close();
        }
        _validate(rows, namespace);
        final sourceMeta = _meta(rows);
        if (sourceMeta['sync_lock'] != null &&
            (jsonDecode(sourceMeta['sync_lock'] as String)['expires'] as int) >
                DateTime.now().millisecondsSinceEpoch) {
          throw StateError(
              'La cola anterior está en uso. Espera a que termine antes de recuperar.');
        }
        final markerKey = 'recovered_source:$encoded';
        final markerRows =
            await tx.query('meta', where: 'key=?', whereArgs: [markerKey]);
        final marker = markerRows.isEmpty
            ? <String, dynamic>{}
            : Map<String, dynamic>.from(
                jsonDecode(markerRows.single['value'] as String));
        await _references(tx, rows);
        for (final row in rows['operation']!) {
          final id = row['id'] as String;
          final details = rows['detail']!
              .where((item) => item['operation_id'] == id)
              .toList()
            ..sort((a, b) =>
                (a['variant_id'] as int).compareTo(b['variant_id'] as int));
          final existing =
              await tx.query('operation', where: 'id=?', whereArgs: [id]);
          if (existing.isEmpty) {
            await tx.insert('operation', row);
            for (final detail in details) {
              await tx.insert('detail', detail);
            }
            imported++;
          } else {
            final savedDetails = await tx.query('detail',
                where: 'operation_id=?',
                whereArgs: [id],
                orderBy: 'variant_id');
            if (_immutableValue(existing.single) != _immutableValue(row) ||
                _canonical(savedDetails) != _canonical(details) ||
                marker[id] != _mutableValue(row) &&
                    _mutableValue(existing.single) != _mutableValue(row)) {
              throw StateError(
                  'UUID con contenido, detalles o estado divergente. Las bases se conservan; requiere revisión.');
            }
          }
          // Una fuente ya importada e intacta no reemplaza resultados centrales nuevos.
          marker[id] = _mutableValue(row);
        }
        if (meta['snapshot'] == null && sourceMeta['snapshot'] != null) {
          await tx.insert(
              'meta', {'key': 'snapshot', 'value': sourceMeta['snapshot']},
              conflictAlgorithm: ConflictAlgorithm.ignore);
        }
        final encodedMarker = jsonEncode(marker);
        if (markerRows.isEmpty) {
          await tx.insert('meta', {'key': markerKey, 'value': encodedMarker});
        } else {
          await tx.update('meta', {'value': encodedMarker},
              where: 'key=?', whereArgs: [markerKey]);
        }
      }
      if (imported > 0) {
        await tx.insert(
            'meta', {'key': 'catalog_refresh_required', 'value': '1'},
            conflictAlgorithm: ConflictAlgorithm.ignore);
      }
      if ((await tx.rawQuery('PRAGMA foreign_key_check')).isNotEmpty) {
        throw StateError(
            'Referencias incompletas; recuperación revertida y originales conservados.');
      }
    });
  } catch (error) {
    if (error is StateError) rethrow;
    // Sin valores de filas, credenciales ni envelopes en mensajes de UI.
    throw StateError(
        'No se pudo recuperar SQLite. Conserva los archivos originales y solicita revisión.');
  }
}
