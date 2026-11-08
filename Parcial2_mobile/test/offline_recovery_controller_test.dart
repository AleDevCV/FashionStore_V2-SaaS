import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/testing.dart';
import 'package:http/http.dart' as http;
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/api_client.dart';
import 'package:fashionstore_mobile/core/session_vault.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';
import 'package:fashionstore_mobile/features/offline/offline_controller.dart';
import 'fixtures/offline_v1.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();
  test('A4 controlador: recuperación fallida no abre cola ni programa envíos',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    SessionVault.active = '7:11';
    var calls = 0;
    await http.runWithClient(() async {
      final controller = OfflineController(
          api: ApiClient(baseUrl: 'http://isolated.invalid'),
          openDatabase: (_) async => throw StateError('A4 recovery test'));
      await expectLater(controller.open(), throwsStateError);
      expect(controller.local, isNull);
      await controller.sync();
      expect(calls, 0);
      controller.dispose();
    },
        () => MockClient((_) async {
              calls++;
              return http.Response('{}', 200);
            }));
  });
  test(
      'A4 controlador: refresh conserva historial y desactiva captura hasta renovar catálogo',
      () async {
    final dir = await Directory.systemTemp.createTemp('a4-controller-');
    try {
      final legacy = await legacyDatabase(dir.path, oldOrigin);
      await legacy.saveSnapshot(recoverySnapshot(101));
      await legacy.capture(
          snapshot: recoverySnapshot(101),
          kind: 'reserva',
          customerId: 1,
          quantities: {1: 1});
      await legacy.db.close();
      final db = await LocalDatabase.open('7:11',
          directory: dir.path, factory: databaseFactoryFfi);
      SessionVault.active = '7:11';
      final controller = OfflineController();
      controller.local = db;
      controller.namespace = '7:11';
      controller.snapshot = await db.snapshot();
      await controller.refresh();
      expect(controller.operations.length, 1);
      expect(controller.catalogRefreshRequired, true);
      expect(controller.validLease, false);
      await db.saveSnapshot(recoverySnapshot(101));
      await controller.refresh();
      expect(controller.validLease, true);
      await db.db.close();
      controller.dispose();
    } finally {
      await dir.delete(recursive: true);
    }
  });
}
