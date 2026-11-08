import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/config.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';
import 'fixtures/offline_v1.dart';

void main() {
  sqfliteFfiInit();
  late Directory directory;
  late List<Database> handles;
  setUp(() async {
    directory = await Directory.systemTemp.createTemp('fashionstore-a4-');
    handles = [];
  });
  tearDown(() async {
    for (final db in handles) {
      if (db.isOpen) await db.close();
    }
    await directory.delete(recursive: true);
  });
  Future<LocalDatabase> open(
      {String namespace = '7:11', String origin = newOrigin}) async {
    final db = await LocalDatabase.open(namespace,
        directory: directory.path,
        factory: databaseFactoryFfi,
        backendUrl: origin);
    handles.add(db.db);
    return db;
  }

  Future<LocalDatabase> old(String origin, {String namespace = '7:11'}) async {
    final db =
        await legacyDatabase(directory.path, origin, namespace: namespace);
    handles.add(db.db);
    return db;
  }

  Future<List<Map<String, dynamic>>> seed(String origin,
      {List<int> branches = const [101],
      List<String> kinds = const ['venta', 'reserva']}) async {
    final db = await old(origin);
    for (final branch in branches) {
      final snapshot = recoverySnapshot(branch);
      await db.saveSnapshot(snapshot);
      for (final kind in kinds) {
        await db.capture(
            snapshot: snapshot,
            kind: kind,
            customerId: kind == 'reserva' ? 1 : null,
            quantities: {1: 1},
            cash: '50.00');
      }
    }
    final result = await wires(db);
    await db.db.close();
    return result;
  }

  Future<LocalDatabase> raw(String filename, {bool readOnly = true}) async {
    final db = await databaseFactoryFfi.openDatabase(filename,
        options:
            OpenDatabaseOptions(readOnly: readOnly, singleInstance: false));
    handles.add(db);
    return LocalDatabase(db);
  }

  Future<Map<String, dynamic>> all(LocalDatabase db) async => {
        for (final table in [
          'product',
          'variant',
          'branch',
          'stock',
          'customer',
          'operation',
          'detail',
          'meta'
        ])
          table: await db.db.query(table,
              orderBy: table == 'detail'
                  ? 'operation_id,variant_id'
                  : table == 'stock'
                      ? 'branch_id,variant_id'
                      : table == 'meta'
                          ? 'key'
                          : 'id')
      };

  test(
      'A4: solo los dos alias aprobados comparten identidad; otros orígenes quedan separados',
      () {
    expect(
        offlineStorageIdentity(oldOrigin), offlineStorageIdentity(newOrigin));
    for (final origin in [
      'http://localhost:8002',
      'http://10.0.2.2:8002',
      '$newOrigin/',
      'https://fashionstore.aledevcv.me:444'
    ]) {
      expect(offlineStorageIdentity(origin), origin);
    }
  });
  test('A4: base canónica nueva se comparte en ambas direcciones entre alias',
      () async {
    final first = await open(origin: oldOrigin);
    await first.saveSnapshot(recoverySnapshot(101));
    await first.capture(
        snapshot: recoverySnapshot(101),
        kind: 'venta',
        quantities: {1: 1},
        cash: '50');
    final before = await wires(first);
    final filename = first.db.path;
    await first.db.close();
    final second = await open();
    expect(second.db.path, filename);
    expect(await wires(second), before);
    await second.db.close();
    final back = await open(origin: oldOrigin);
    expect(await wires(back), before);
  });
  test('SQLite v1 a v2 conserva intentos y solo resuelve al confirmar una revisión', () async {
    const origin = 'http://offline-audit.invalid:8002';
    final legacy = await old(origin);
    final catalog = recoverySnapshot(101);
    await legacy.saveSnapshot(catalog);
    final root = await legacy.capture(snapshot: catalog, kind: 'venta',
        quantities: {1: 1}, cash: '50');
    await legacy.applyResults([{'operation_id': root, 'state': 'EN_CONFLICTO'}]);
    final failed = await legacy.capture(snapshot: catalog, kind: 'venta',
        quantities: {1: 1}, cash: '50', original: root);
    await legacy.applyResults([{'operation_id': failed, 'state': 'RECHAZADA'}]);
    await legacy.db.update('operation', {'resolved': 1}, where: 'id=?', whereArgs: [root]);
    final before = await wires(legacy);
    await legacy.db.close();

    final db = await open(origin: origin);
    Future<Object?> resolved() async => (await db.operations()).firstWhere((row) => row['id'] == root)['resolved'];
    expect(await db.db.getVersion(), 2);
    expect(await wires(db), before);
    expect(await db.db.rawQuery('PRAGMA foreign_key_check'), isEmpty);
    expect(await resolved(), 0);
    Future<String> revise() => db.capture(snapshot: catalog, kind: 'venta',
        quantities: {1: 1}, cash: '50', original: root);
    final next = await revise();
    expect(await resolved(), 0);
    await expectLater(revise(), throwsStateError);
    expect((await db.catalog(101)).single['available'], 9);
    await db.applyResults([{'operation_id': next, 'state': 'CONFIRMADA'}]);
    expect(await resolved(), 1);
    expect((await db.catalog(101)).single['available'], 9);
    expect((await db.operations()).length, 3);
  });
  test(
      'A4: recupera v1, mantiene sucursales UUID device y detalles; fuente idéntica',
      () async {
    final expected = await seed(oldOrigin, branches: [101, 102]);
    final file = File(legacyPath(directory.path, oldOrigin));
    final bytes = await file.readAsBytes();
    final db = await open();
    expect(await wires(db), expected);
    expect((await db.db.query('detail')).length, 4);
    expect((await db.operations()).map((row) => row['branch_id']).toSet(),
        {101, 102});
    expect(await db.db.rawQuery('PRAGMA foreign_key_check'), isEmpty);
    expect(await file.readAsBytes(), bytes);
  });
  test('A4: une cuatro UUID antiguos y uno nuevo sin sumar stocks', () async {
    final a = await seed(oldOrigin, branches: [101, 102]);
    final b = await seed(newOrigin, kinds: ['reserva']);
    final db = await open();
    final expected = [...a, ...b]..sort((a, b) =>
        (a['operation_id'] as String).compareTo(b['operation_id'] as String));
    expect(await wires(db), expected);
    expect((await db.operations()).length, 5);
    final stock =
        await db.db.query('stock', where: 'branch_id=?', whereArgs: [101]);
    expect(stock.single['quantity'], 10);
    expect(await db.catalogNeedsRefresh(), true);
  });
  test('A4: solo el archivo del hostname actual también se recupera', () async {
    final expected = await seed(newOrigin);
    final db = await open(origin: oldOrigin);
    expect(await wires(db), expected);
  });
  test('A4: UUID idénticos en las dos fuentes no duplican cabecera ni detalles',
      () async {
    final expected = await seed(oldOrigin);
    await File(legacyPath(directory.path, oldOrigin))
        .copy(legacyPath(directory.path, newOrigin));
    final db = await open();
    expect(await wires(db), expected);
    expect((await db.db.query('detail')).length, 2);
  });
  for (final divergence in ['envelope', 'detail', 'state']) {
    test('A4: UUID con $divergence divergente revierte toda la importación',
        () async {
      await seed(oldOrigin);
      await File(legacyPath(directory.path, oldOrigin))
          .copy(legacyPath(directory.path, newOrigin));
      final source = await old(newOrigin);
      final row = (await source.operations()).first;
      if (divergence == 'envelope') {
        final envelope = jsonDecode(row['envelope'] as String);
        envelope['cash_received'] = '99.00';
        await source.db.update('operation', {'envelope': jsonEncode(envelope)},
            where: 'id=?', whereArgs: [row['id']]);
      }
      if (divergence == 'detail') {
        await source.db.update('detail', {'quantity': 2},
            where: 'operation_id=?', whereArgs: [row['id']]);
      }
      if (divergence == 'state') {
        await source.db.update('operation', {'state': 'CONFIRMADA'},
            where: 'id=?', whereArgs: [row['id']]);
      }
      await source.db.close();
      await expectLater(open(), throwsStateError);
      final filename = directory
          .listSync()
          .whereType<File>()
          .singleWhere((f) => f.path.contains('_stable_'))
          .path;
      final target = await raw(filename);
      expect(await target.operations(), isEmpty);
      expect(await target.meta('storage_identity'), isNull);
    });
  }
  for (final mismatch in ['tenant_id', 'author_id', 'branch_id']) {
    test('A4: rechaza envelope con $mismatch ajeno sin exponer operaciones',
        () async {
      await seed(oldOrigin);
      final source = await old(oldOrigin);
      final row = (await source.operations()).first;
      final value = jsonDecode(row['envelope'] as String);
      value[mismatch] = 999;
      await source.db.update('operation', {'envelope': jsonEncode(value)},
          where: 'id=?', whereArgs: [row['id']]);
      await source.db.close();
      await expectLater(open(), throwsStateError);
    });
  }
  test('A4: snapshot de otra cuenta se rechaza aunque el envelope sea propio',
      () async {
    await seed(oldOrigin);
    final source = await old(oldOrigin);
    final snapshot = (await source.snapshot())!;
    snapshot['author_id'] = 12;
    await source.db.update('meta', {'value': jsonEncode(snapshot)},
        where: 'key=?', whereArgs: ['snapshot']);
    await source.db.close();
    await expectLater(open(), throwsStateError);
  });
  test('A4: no recupera bases de otra empresa ni de otro usuario', () async {
    await seed(oldOrigin);
    for (final namespace in ['8:11', '7:12']) {
      final db = await open(namespace: namespace);
      expect(await db.operations(), isEmpty);
      expect(await db.snapshot(), isNull);
    }
  });
  test('A4: namespace inválido no abre base', () async {
    await expectLater(open(namespace: '../7:11'), throwsStateError);
    expect(directory.listSync(), isEmpty);
  });
  test('A4: host local mantiene su archivo existente sin importar cola HTTPS',
      () async {
    await seed(oldOrigin);
    final expected = await seed('http://localhost:8002');
    final db = await open(origin: 'http://localhost:8002');
    expect(db.db.path, legacyPath(directory.path, 'http://localhost:8002'));
    expect(await wires(db), expected);
    expect(await db.catalogNeedsRefresh(), false);
  });
  test('A4: no migra mientras la fuente tenga un bloqueo vigente', () async {
    await seed(oldOrigin);
    final source = await old(oldOrigin);
    await source.db.insert('meta', {
      'key': 'sync_lock',
      'value': jsonEncode({
        'owner': 'old',
        'expires': DateTime.now().millisecondsSinceEpoch + 60000
      })
    });
    await source.db.close();
    await expectLater(open(), throwsStateError);
    final released = await old(oldOrigin);
    await released.db.update(
        'meta',
        {
          'value': jsonEncode({'owner': 'old', 'expires': 0})
        },
        where: 'key=?',
        whereArgs: ['sync_lock']);
    await released.db.close();
    expect((await (await open()).operations()).length, 2);
  });
  test(
      'A4: ENVIANDO se recupera después de expirar lock sin alterar wire ni intentos',
      () async {
    final expected = await seed(oldOrigin);
    final source = await old(oldOrigin);
    await source.db.update('operation', {'state': 'ENVIANDO', 'attempts': 3});
    await source.db.close();
    final db = await open();
    expect(await wires(db), expected);
    expect(
        (await db.operations()).every(
            (row) => row['state'] == 'PENDIENTE' && row['attempts'] == 3),
        true);
    final untouched = await raw(legacyPath(directory.path, oldOrigin));
    expect(
        (await untouched.operations())
            .every((row) => row['state'] == 'ENVIANDO'),
        true);
  });
  test('A4: reabrir no duplica ni degrada CONFIRMADA a PENDIENTE antigua',
      () async {
    await seed(oldOrigin);
    final db = await open();
    final id = (await db.operations()).first['id'];
    await db.applyResults([
      {'operation_id': id, 'state': 'CONFIRMADA', 'server_id': 71}
    ]);
    final original = await wires(db);
    final before = await db.operations();
    await db.db.close();
    for (var i = 0; i < 3; i++) {
      final reopened = await open();
      expect(await wires(reopened), original);
      expect(await reopened.operations(), before);
      await reopened.db.close();
    }
  });
  test(
      'A4: cambio tardío de estado en fuente importada no reemplaza resultado canónico',
      () async {
    await seed(oldOrigin);
    final db = await open();
    await db.db.close();
    final source = await old(oldOrigin);
    await source.db.update('operation', {'state': 'RECHAZADA'});
    await source.db.close();
    await expectLater(open(), throwsStateError);
  });
  test('A4: referencias y enlace de revisión se conservan', () async {
    await seed(oldOrigin);
    final source = await old(oldOrigin);
    final original = (await source.operations()).first['id'] as String;
    await source.db.update('operation', {'state': 'EN_CONFLICTO'},
        where: 'id=?', whereArgs: [original]);
    final oldRow =
        (await source.operations()).firstWhere((row) => row['id'] == original);
    await source.capture(
        snapshot: (await source.snapshot())!,
        kind: oldRow['kind'] as String,
        customerId: oldRow['customer_id'] as int?,
        quantities: {1: 1},
        cash: '50',
        original: original);
    final expected = await all(source);
    await source.db.close();
    final db = await open();
    expect(
        await db.db.query('operation', orderBy: 'id'), expected['operation']);
    expect(await db.db.query('detail', orderBy: 'operation_id,variant_id'),
        expected['detail']);
    expect(await db.db.rawQuery('PRAGMA foreign_key_check'), isEmpty);
  });
  test('A4: exige catálogo fresco para capturas y mantiene wire de pendientes',
      () async {
    final expected = await seed(oldOrigin);
    final db = await open();
    expect(await db.catalogNeedsRefresh(), true);
    expect(await wires(db), expected);
    await expectLater(
        db.capture(
            snapshot: (await db.snapshot())!,
            kind: 'venta',
            quantities: {1: 1},
            cash: '50'),
        throwsStateError);
    final foreign = recoverySnapshot(101)..['tenant_id'] = 8;
    await expectLater(db.saveSnapshot(foreign), throwsStateError);
    expect(await db.catalogNeedsRefresh(), true);
    await db.saveSnapshot(recoverySnapshot(101));
    expect(await db.catalogNeedsRefresh(), false);
    await db.capture(
        snapshot: recoverySnapshot(101),
        kind: 'venta',
        quantities: {1: 1},
        cash: '50');
    await db.db.close();
    final reopened = await open();
    expect(await reopened.catalogNeedsRefresh(), false);
    expect((await reopened.operations()).length, 3);
  });
  test(
      'A4: error SQL real revierte fuentes completas y conserva base canónica previa',
      () async {
    final target = await open();
    await target.saveSnapshot(recoverySnapshot(101));
    await target.capture(
        snapshot: recoverySnapshot(101),
        kind: 'reserva',
        customerId: 1,
        quantities: {1: 1});
    final filename = target.db.path;
    final before = await all(target);
    await target.db.close();
    await seed(oldOrigin);
    final second = await seed(newOrigin, kinds: ['reserva']);
    final blocked = second.single['operation_id'];
    final setup = await raw(filename, readOnly: false);
    await setup.db.execute(
        "CREATE TRIGGER a4_injected_failure BEFORE INSERT ON detail WHEN NEW.operation_id='$blocked' BEGIN SELECT RAISE(ABORT,'a4 rollback test'); END");
    await setup.db.close();
    await expectLater(open(), throwsStateError);
    final check = await raw(filename);
    expect(await all(check), before);
    await check.db.close();
    final cleanup = await raw(filename, readOnly: false);
    await cleanup.db.execute('DROP TRIGGER a4_injected_failure');
    await cleanup.db.close();
    final recovered = await open();
    expect((await recovered.operations()).length, 4);
  });
  test('A4: fuente corrupta provoca rollback de la otra fuente válida',
      () async {
    await seed(oldOrigin);
    await File(legacyPath(directory.path, newOrigin))
        .writeAsString('not a SQLite database');
    await expectLater(open(), throwsStateError);
    final filename = directory
        .listSync()
        .whereType<File>()
        .singleWhere((file) => file.path.contains('_stable_'))
        .path;
    expect(await (await raw(filename)).operations(), isEmpty);
  });
  test('A4: FK huérfana en fuente se conserva y bloquea recuperación',
      () async {
    await seed(oldOrigin);
    final source = await old(oldOrigin);
    await source.db.execute('PRAGMA foreign_keys=OFF');
    await source.db.insert('detail', {
      'operation_id': 'orphan',
      'variant_id': 1,
      'quantity': 1,
      'price': 5000
    });
    await source.db.close();
    await expectLater(open(), throwsStateError);
  });
  test('A4: identidad canónica ajena se rechaza', () async {
    final db = await open();
    await db.db.update('meta', {'value': '{"namespace":"8:11"}'},
        where: 'key=?', whereArgs: ['storage_identity']);
    await db.db.close();
    await expectLater(open(), throwsStateError);
  });
  test(
      'A4: variante con producto incompatible entre fuentes revierte importación',
      () async {
    await seed(oldOrigin);
    await seed(newOrigin);
    final source = await old(newOrigin);
    await source.db.insert('product', {'id': 2, 'data': '{}'});
    await source.db.update('variant', {'product_id': 2});
    await source.db.close();
    await expectLater(open(), throwsStateError);
  });
  test('A4: versión de fuente desconocida no se migra silenciosamente',
      () async {
    await seed(oldOrigin);
    final source = await old(oldOrigin);
    await source.db.setVersion(2);
    await source.db.close();
    await expectLater(open(), throwsStateError);
  });
  test('A4: falta real de páginas SQLite revierte importación y conserva fuentes', () async {
    final target=await open();final filename=target.db.path;final before=await all(target);
    final pages=(await target.db.rawQuery('PRAGMA page_count')).single.values.single as int;
    await target.db.execute('PRAGMA max_page_count=$pages');
    await seed(oldOrigin);final source=await old(oldOrigin);
    await source.db.update('product',{'data':jsonEncode({'nombre':List.filled(500000,'A').join()})});
    await source.db.close();final file=File(legacyPath(directory.path,oldOrigin));final sourceBytes=await file.readAsBytes();
    await expectLater(open(),throwsStateError);
    expect(await all(await raw(filename)),before);expect(await file.readAsBytes(),sourceBytes);
  });
  test('A4: aperturas concurrentes de ambos alias importan cada UUID una sola vez', () async {
    final expected=await seed(oldOrigin);final values=await Future.wait([open(),open(origin:oldOrigin)]);
    for(final db in values){expect(await wires(db),expected);expect((await db.db.query('detail')).length,2);}
  });
}
