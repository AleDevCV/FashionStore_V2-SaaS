import 'dart:convert';
import 'package:path/path.dart' as path;
import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';
import '../../core/config.dart';

int cents(dynamic value) {
  final text = (value ?? 0).toString();
  if (!RegExp(r'^\d+(\.\d{1,2})?$').hasMatch(text)) {
    throw StateError('Importe inválido.');
  }
  final parts = text.split('.');
  final result = int.parse(parts[0]) * 100 + int.parse(parts.length > 1 ? parts[1].padRight(2, '0') : '0');
  if (result > 999999999999) throw StateError('Importe fuera de rango.');
  return result;
}

int priceCents(Map<String,dynamic> row, int quantity) {
  var price = cents(row['precio_base']);
  if (row['precio_mayorista'] != null && quantity >= (row['umbral_mayorista'] ?? 6)) {
    final wholesale = cents(row['precio_mayorista']);
    if (wholesale < price) price = wholesale;
  }
  final day = DateTime.now().toUtc().toIso8601String().substring(0,10);
  if (row['precio_oferta'] != null && (row['oferta_inicio'] == null || row['oferta_inicio'].compareTo(day) <= 0) && (row['oferta_fin'] == null || row['oferta_fin'].compareTo(day) >= 0)) {
    final offer = cents(row['precio_oferta']);
    if (offer < price) price = offer;
  }
  return price + cents(row['precio_adicional']);
}

/// Archivo por empresa y usuario; cabeceras y detalles se guardan en una transacción.
class LocalDatabase {
  final Database db;
  LocalDatabase(this.db);
  static Future<LocalDatabase> open(String namespace, {String? directory, DatabaseFactory? factory}) async {
    if (!RegExp(r'^\d+:\d+$').hasMatch(namespace)) throw StateError('Identidad local inválida.');
    final origin=base64Url.encode(utf8.encode(apiBaseUrl)).replaceAll('=','');
    final database = await (factory ?? databaseFactory).openDatabase(path.join(directory ?? await getDatabasesPath(), 'fashionstore_p2_${origin}_${namespace.replaceAll(':','_')}.db'), options: OpenDatabaseOptions(version:1,
      onConfigure:(db) async => db.execute('PRAGMA foreign_keys=ON'),
      onCreate:(db,version) async {
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
        ]) { await db.execute(sql); }
        await db.insert('meta',{'key':'device','value':const Uuid().v4()});
      }));
    final local = LocalDatabase(database);
    final lock = await local.meta('sync_lock');
    if (lock == null || (jsonDecode(lock)['expires'] as int) < DateTime.now().millisecondsSinceEpoch) {
      await database.update('operation',{'state':'PENDIENTE'},where:"state='ENVIANDO'");
    }
    return local;
  }
  Future<String?> meta(String key) async {final rows=await db.query('meta',where:'key=?',whereArgs:[key]);return rows.isEmpty?null:rows.first['value'] as String;}
  Future<Map<String,dynamic>?> snapshot() async {final value=await meta('snapshot');return value==null?null:Map<String,dynamic>.from(jsonDecode(value));}
  Future<List<Map<String,dynamic>>> operations() => db.query('operation',orderBy:'occurred_at DESC');
  Future<List<Map<String,dynamic>>> customers() async => (await db.query('customer')).map((r)=>Map<String,dynamic>.from(jsonDecode(r['data'] as String))).toList();
  Future<List<Map<String,dynamic>>> catalog(int branchId) async {
    final rows=await db.rawQuery("SELECT v.id,v.data AS variant,p.data AS product,s.quantity-COALESCE((SELECT SUM(d.quantity) FROM detail d JOIN operation o ON o.id=d.operation_id WHERE d.variant_id=v.id AND o.branch_id=s.branch_id AND o.accounted=0 AND o.resolved=0 AND o.state!='RECHAZADA'),0) AS available FROM stock s JOIN variant v ON v.id=s.variant_id JOIN product p ON p.id=v.product_id WHERE s.branch_id=? ORDER BY v.id",[branchId]);
    return rows.map((r)=> <String,dynamic>{...jsonDecode(r['product'] as String),...jsonDecode(r['variant'] as String),'available':(r['available'] as int)<0?0:r['available']}).toList();
  }
  Future<void> saveSnapshot(Map<String,dynamic> snapshot) async {
    final branch=Map<String,dynamic>.from(snapshot['branch']);final branchId=branch['id_sucursal'];
    await db.transaction((tx) async {
      await tx.insert('branch',{'id':branchId,'name':branch['nombre']},conflictAlgorithm:ConflictAlgorithm.ignore);
      await tx.update('branch',{'name':branch['nombre']},where:'id=?',whereArgs:[branchId]);
      await tx.delete('stock',where:'branch_id=?',whereArgs:[branchId]);
      for(final raw in snapshot['products']) {
        final row=Map<String,dynamic>.from(raw);final productId=row['id_prenda'];final variantId=row['id_variante_prenda'];
        final variant=<String,dynamic>{for(final k in ['id_variante_prenda','id_prenda','sku_variante','talla','color','precio_adicional']) k:row[k]};
        final product=Map<String,dynamic>.from(row)..removeWhere((k,v)=>['id_variante_prenda','sku_variante','talla','color','precio_adicional','stock'].contains(k));
        // UPDATE/INSERT evita REPLACE, que borraría referencias de cabeceras antiguas.
        await tx.insert('product',{'id':productId,'data':jsonEncode(product)},conflictAlgorithm:ConflictAlgorithm.ignore);
        await tx.update('product',{'data':jsonEncode(product)},where:'id=?',whereArgs:[productId]);
        await tx.insert('variant',{'id':variantId,'product_id':productId,'data':jsonEncode(variant)},conflictAlgorithm:ConflictAlgorithm.ignore);
        await tx.update('variant',{'data':jsonEncode(variant)},where:'id=?',whereArgs:[variantId]);
        await tx.insert('stock',{'branch_id':branchId,'variant_id':variantId,'quantity':row['stock']});
      }
      for(final customer in snapshot['customers']) {
        await tx.insert('customer',{'id':customer['id_cliente'],'data':jsonEncode(customer)},conflictAlgorithm:ConflictAlgorithm.ignore);
        await tx.update('customer',{'data':jsonEncode(customer)},where:'id=?',whereArgs:[customer['id_cliente']]);
      }
      for(final result in snapshot['operation_results'] ?? []) {
        await tx.rawUpdate('UPDATE operation SET state=?,result=?,reason=?,accounted=CASE WHEN branch_id=? AND ?=\'CONFIRMADA\' THEN 1 ELSE accounted END WHERE id=?',[result['state'],jsonEncode(result),result['reason']??'',branchId,result['state'],result['operation_id']]);
      }
      await tx.insert('meta',{'key':'snapshot','value':jsonEncode(snapshot)},conflictAlgorithm:ConflictAlgorithm.replace);
    });
  }
  Future<String> capture({required Map<String,dynamic> snapshot,required String kind,int? customerId,required Map<int,int> quantities,String? cash,String? original}) async {
    if ((snapshot['lease_expires'] as int)*1000<=DateTime.now().millisecondsSinceEpoch) throw StateError('El permiso offline venció. Conecta para renovarlo.');
    if (kind=='venta' && snapshot['can_sell']!=true) throw StateError('Esta cuenta no puede vender.');
    if (kind=='reserva' && customerId==null) throw StateError('Selecciona un cliente descargado.');
    final available=await catalog(snapshot['branch']['id_sucursal']);final rows={for(final r in available) r['id_variante_prenda'] as int:r};final totals=<int,int>{};
    final selection=quantities.entries.where((e)=>e.value>0).toList();if(selection.isEmpty)throw StateError('Agrega una variante.');
    for(final entry in selection){final row=rows[entry.key];if(row==null || entry.value>10000)throw StateError('Variante o cantidad inválida.');totals[row['id_prenda']]=(totals[row['id_prenda']]??0)+entry.value;}
    final oldDetails=original==null?<Map<String,dynamic>>[]:await db.query('detail',where:'operation_id=?',whereArgs:[original]);
    final items=<Map<String,dynamic>>[];var total=0;
    for(final entry in selection){final row=rows[entry.key]!;final old=oldDetails.where((d)=>d['variant_id']==entry.key);final credit=old.isEmpty?0:old.first['quantity'] as int;if(entry.value>(row['available'] as int)+credit)throw StateError('Stock local insuficiente.');final price=priceCents(row,totals[row['id_prenda']]!);items.add({'id_variante_prenda':entry.key,'cantidad':entry.value,'precio_unitario':(price/100).toStringAsFixed(2)});total+=price*entry.value;}
    if(kind=='venta' && cents(cash)<total)throw StateError('El efectivo recibido no cubre el total.');
    final id=const Uuid().v4();final stamp=DateTime.now().toUtc().toIso8601String();
    final envelope={'operation_id':id,'version':1,'tenant_id':snapshot['tenant_id'],'author_id':snapshot['author_id'],'branch_id':snapshot['branch']['id_sucursal'],'device_id':await meta('device'),'kind':kind,'occurred_at':stamp,'lease':snapshot['lease'],'customer_id':customerId,'cash_received':kind=='venta'?(cents(cash)/100).toStringAsFixed(2):null,'original_operation':original};
    await db.transaction((tx) async {
      if(original!=null){final old=await tx.query('operation',where:'id=? AND state IN (\'EN_CONFLICTO\',\'RECHAZADA\') AND resolved=0',whereArgs:[original]);if(old.isEmpty)throw StateError('El original no admite revisión.');await tx.update('operation',{'resolved':1},where:'id=?',whereArgs:[original]);}
      await tx.insert('operation',{'id':id,'branch_id':envelope['branch_id'],'customer_id':customerId,'kind':kind,'occurred_at':stamp,'envelope':jsonEncode(envelope),'state':'PENDIENTE','original':original});
      for(final item in items){await tx.insert('detail',{'operation_id':id,'variant_id':item['id_variante_prenda'],'quantity':item['cantidad'],'price':cents(item['precio_unitario'])});}
    });return id;
  }
  Future<Map<String,dynamic>> wire(Map<String,dynamic> op) async {
    final items=await db.query('detail',where:'operation_id=?',whereArgs:[op['id']],orderBy:'variant_id');
    return {...jsonDecode(op['envelope'] as String),'items':items.map((d)=>{'id_variante_prenda':d['variant_id'],'cantidad':d['quantity'],'precio_unitario':((d['price'] as int)/100).toStringAsFixed(2)}).toList()};
  }
  Future<void> applyResults(List<dynamic> results) async => db.transaction((tx) async {for(final result in results){await tx.update('operation',{'state':result['state'],'result':jsonEncode(result),'reason':result['reason']??''},where:'id=?',whereArgs:[result['operation_id']]);}});
}
