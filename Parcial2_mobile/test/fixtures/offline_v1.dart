// Frozen pre-A4 schema fixture; do not replace with current schema creation.
import 'dart:convert';
import 'package:path/path.dart' as path;
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:uuid/uuid.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';

void resetRecoveryStorageForTest()=>FlutterSecureStorage.setMockInitialValues({});

const oldOrigin = 'https://fashionstore-v2.aledevcv.me';
const newOrigin = 'https://fashionstore.aledevcv.me';
String legacyPath(String directory, String origin,
        [String namespace = '7:11']) =>
    path.join(directory,
        'fashionstore_p2_${base64Url.encode(utf8.encode(origin)).replaceAll('=', '')}_${namespace.replaceAll(':', '_')}.db');
Future<LocalDatabase> legacyDatabase(String directory, String origin,
    {String namespace = '7:11'}) async {
  final db = await databaseFactoryFfi.openDatabase(
      legacyPath(directory, origin, namespace),
      options: OpenDatabaseOptions(
          version: 1,
          onConfigure: (db) async => db.execute('PRAGMA foreign_keys=ON'),
          onCreate: (db, version) async {
            for (final sql in [
              'CREATE TABLE product(id INTEGER PRIMARY KEY,data TEXT NOT NULL)',
              'CREATE TABLE variant(id INTEGER PRIMARY KEY,product_id INTEGER NOT NULL REFERENCES product(id),data TEXT NOT NULL)',
              'CREATE TABLE branch(id INTEGER PRIMARY KEY,name TEXT NOT NULL)',
              'CREATE TABLE stock(branch_id INTEGER NOT NULL REFERENCES branch(id),variant_id INTEGER NOT NULL REFERENCES variant(id),quantity INTEGER NOT NULL,PRIMARY KEY(branch_id,variant_id))',
              'CREATE TABLE customer(id INTEGER PRIMARY KEY,data TEXT NOT NULL)',
              "CREATE TABLE operation(id TEXT PRIMARY KEY,branch_id INTEGER NOT NULL REFERENCES branch(id),customer_id INTEGER REFERENCES customer(id),kind TEXT NOT NULL CHECK(kind IN ('venta','reserva')),occurred_at TEXT NOT NULL,envelope TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('PENDIENTE','ENVIANDO','CONFIRMADA','RECHAZADA','EN_CONFLICTO')),attempts INTEGER NOT NULL DEFAULT 0,result TEXT,reason TEXT NOT NULL DEFAULT '',accounted INTEGER NOT NULL DEFAULT 0,resolved INTEGER NOT NULL DEFAULT 0,original TEXT UNIQUE REFERENCES operation(id))",
              'CREATE TABLE detail(operation_id TEXT NOT NULL REFERENCES operation(id),variant_id INTEGER NOT NULL REFERENCES variant(id),quantity INTEGER NOT NULL CHECK(quantity>0),price INTEGER NOT NULL CHECK(price>=0),PRIMARY KEY(operation_id,variant_id))',
              'CREATE INDEX operation_state ON operation(state)',
              'CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)',
              "CREATE VIEW local_ventas AS SELECT * FROM operation WHERE kind='venta'",
              "CREATE VIEW local_reservas AS SELECT * FROM operation WHERE kind='reserva'",
            ]) {
              await db.execute(sql);
            }
            await db
                .insert('meta', {'key': 'device', 'value': const Uuid().v4()});
          }));
  return LocalDatabase(db, namespace: namespace);
}

Map<String, dynamic> recoverySnapshot(int branch, {int stock = 10}) => {
      'tenant_id': 7,
      'author_id': 11,
      'empresa': 'A4 aislada',
      'usuario': 'a4@example.invalid',
      'branch': {'id_sucursal': branch, 'nombre': 'Sucursal $branch'},
      'lease': 'isolated-fixture-only',
      'lease_expires': DateTime.now().millisecondsSinceEpoch ~/ 1000 + 3600,
      'can_sell': true,
      'downloaded_at': DateTime.now().toUtc().toIso8601String(),
      'products': [
        {
          'id_prenda': 1,
          'id_variante_prenda': 1,
          'nombre': 'Prueba',
          'sku': 'A4',
          'sku_variante': 'A4-1',
          'talla': 'M',
          'color': 'Azul',
          'precio_base': '50.00',
          'precio_adicional': '0.00',
          'stock': stock
        }
      ],
      'customers': [
        {'id_cliente': 1, 'nombre_completo': 'Cliente aislado'}
      ],
      'operation_results': []
    };
Future<List<Map<String, dynamic>>> wires(LocalDatabase db) async {
  final result = [for (final op in await db.operations()) await db.wire(op)];
  result.sort((a, b) =>
      (a['operation_id'] as String).compareTo(b['operation_id'] as String));
  return result;
}
