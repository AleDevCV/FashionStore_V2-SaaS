import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/api_client.dart';
import 'package:fashionstore_mobile/core/session_vault.dart';
import 'package:fashionstore_mobile/services/auth_service.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';
import 'package:fashionstore_mobile/features/offline/offline_controller.dart';
import '../test/fixtures/offline_v1.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();
  // Esta prueba usa exclusivamente HTTP al servidor tmpfs de loopback.
  // Flutter Test instala por defecto un cliente que devuelve 400 sin enviar tráfico.
  HttpOverrides.global = null;
  final bindings =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  setUp(() async {
    resetRecoveryStorageForTest();
    SessionVault.active = null;
    bindings.setMockMethodCallHandler(
        const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
        (_) async => null);
  });
  tearDown(() {
    bindings.setMockMethodCallHandler(
        const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
        null);
  });
  const fixturePath = String.fromEnvironment('A4_RUNTIME_FIXTURE');
  const evidencePath = String.fromEnvironment('A4_RUNTIME_EVIDENCE');
  test(
      'A4 HTTP: recupera SQLite real, reenvía respuesta perdida y conserva UUID sin duplicar',
      () async {
    final data = List<Map<String, dynamic>>.from(
        jsonDecode(await File(fixturePath).readAsString()));
    final owner = data.first;
    final snapshot = Map<String, dynamic>.from(owner['snapshot']);
    final namespace = owner['namespace'] as String;
    final token = (owner['header']['Authorization'] as String).substring(7);
    await AuthService().acceptToken(token);
    final dir = await Directory.systemTemp.createTemp('a4-http-');
    OfflineController? controller;
    try {
      final legacy =
          await legacyDatabase(dir.path, oldOrigin, namespace: namespace);
      await legacy.saveSnapshot(snapshot);
      final variant = snapshot['products'][0]['id_variante_prenda'] as int;
      final customer = snapshot['customers'][0]['id_cliente'] as int;
      await legacy.capture(
          snapshot: snapshot,
          kind: 'venta',
          quantities: {variant: 1},
          cash: '50.00');
      await legacy.capture(
          snapshot: snapshot,
          kind: 'reserva',
          customerId: customer,
          quantities: {variant: 1});
      final before = await wires(legacy);
      await legacy.db.close();
      final sourceFile = File(legacyPath(dir.path, oldOrigin, namespace));
      final sourceBytes = await sourceFile.readAsBytes();
      final api = ApiClient(
          baseUrl: 'http://127.0.0.1:18084',
          tokenProvider: () => AuthService().token);
      controller = OfflineController(
          api: api,
          openDatabase: (ns) => LocalDatabase.open(ns,
              directory: dir.path,
              factory: databaseFactoryFfi,
              backendUrl: newOrigin));
      await controller.open();
      expect(controller.namespace, namespace);
      expect(await wires(controller.current()), before);
      expect(controller.catalogRefreshRequired, true);
      expect(controller.validLease, false);
      // Primera confirmación central: simula respuesta perdida sin aplicarla a SQLite.
      final accepted = await api
          .post('/api/sincronizacion/lote', body: {'operations': before});
      expect(
          (accepted['results'] as List)
              .every((row) => row['state'] == 'CONFIRMADA'),
          true);
      expect(controller.operations.every((row) => row['state'] == 'PENDIENTE'),
          true);
      await controller.sync();
      expect(controller.operations.every((row) => row['state'] == 'CONFIRMADA'),
          true);
      expect(await wires(controller.current()), before);
      await controller.download(snapshot['branch']['id_sucursal'] as int);
      expect(controller.catalogRefreshRequired, false);
      expect(controller.validLease, true);
      final saved = await controller.current().operations();
      await controller.current().db.close();
      controller.dispose();
      controller = null;
      final reopened = await LocalDatabase.open(namespace,
          directory: dir.path,
          factory: databaseFactoryFfi,
          backendUrl: oldOrigin);
      expect(await reopened.operations(), saved);
      expect(await wires(reopened), before);
      expect(await reopened.catalogNeedsRefresh(), false);
      await reopened.db.close();
      expect(await sourceFile.readAsBytes(), sourceBytes);
      final repeated = await api
          .post('/api/sincronizacion/lote', body: {'operations': before});
      expect(repeated['results'], accepted['results']);
      await File(evidencePath).writeAsString(jsonEncode({
        'recovered': 2,
        'original_UUIDs': before.map((r) => r['operation_id']).toList(),
        'lost_response_retry_confirmed': true,
        'third_replay_same_result': true,
        'source_bytes_unchanged': true,
        'canonical_reopen_keeps_confirmed': true,
        'catalog_renewed_before_new_capture': true
      }));
    } finally {
      controller?.dispose();
      await dir.delete(recursive: true);
    }
  });
  test(
      'A4 HTTP: sesión de la segunda empresa abre otra base sin historial ajeno',
      () async {
    final rows = List<Map<String, dynamic>>.from(
        jsonDecode(await File(fixturePath).readAsString()));
    final dir = await Directory.systemTemp.createTemp('a4-isolation-http-');
    OfflineController? controller;
    try {
      final first = rows[0];
      final second = rows[1];
      final legacy = await legacyDatabase(dir.path, oldOrigin,
          namespace: first['namespace']);
      await legacy.saveSnapshot(Map<String, dynamic>.from(first['snapshot']));
      final product =
          first['snapshot']['products'][0]['id_variante_prenda'] as int;
      await legacy.capture(
          snapshot: Map<String, dynamic>.from(first['snapshot']),
          kind: 'venta',
          quantities: {product: 1},
          cash: '50.00');
      await legacy.db.close();
      await AuthService().acceptToken(
          (second['header']['Authorization'] as String).substring(7));
      controller = OfflineController(
          api: ApiClient(
              baseUrl: 'http://127.0.0.1:18084',
              tokenProvider: () => AuthService().token),
          openDatabase: (ns) => LocalDatabase.open(ns,
              directory: dir.path,
              factory: databaseFactoryFfi,
              backendUrl: newOrigin));
      await controller.open();
      expect(controller.namespace, second['namespace']);
      expect(controller.operations, isEmpty);
      expect(controller.snapshot, isNull);
      await controller.current().db.close();
      controller.dispose();
      controller = null;
    } finally {
      controller?.dispose();
      await dir.delete(recursive: true);
    }
  });
}
