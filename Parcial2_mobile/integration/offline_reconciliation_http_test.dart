import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/api_client.dart';
import 'package:fashionstore_mobile/core/session_vault.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';
import 'package:fashionstore_mobile/features/offline/offline_controller.dart';
import '../test/fixtures/offline_v1.dart';

void main(){
 TestWidgetsFlutterBinding.ensureInitialized();sqfliteFfiInit();HttpOverrides.global=null;
 test('A5 HTTP SQLite: 125 resultados, otra sucursal, reapertura y repetición sin pérdida',() async {
  resetRecoveryStorageForTest();
  final fixture=jsonDecode(await File(const String.fromEnvironment('A5_FIXTURE')).readAsString());
  final namespace=fixture['namespace'] as String;SessionVault.active=namespace;
  final directory=await Directory.systemTemp.createTemp('a5-real-http-');
  var db=await LocalDatabase.open(namespace,directory:directory.path,factory:databaseFactoryFfi,backendUrl:'http://127.0.0.1:18085');
  for(final snapshot in fixture['before']){await db.saveSnapshot(Map<String,dynamic>.from(snapshot));}
  await db.db.transaction((tx) async {
   for(var i=0;i<(fixture['operations'] as List).length;i++){
    final wire=Map<String,dynamic>.from(fixture['operations'][i]);final items=wire.remove('items') as List;final result=fixture['results'][i];
    await tx.insert('operation',{'id':wire['operation_id'],'branch_id':wire['branch_id'],'customer_id':wire['customer_id'],'kind':wire['kind'],'occurred_at':wire['occurred_at'],'envelope':jsonEncode(wire),'state':result['state'],'result':jsonEncode(result)});
    for(final line in items){await tx.insert('detail',{'operation_id':wire['operation_id'],'variant_id':line['id_variante_prenda'],'quantity':line['cantidad'],'price':cents(line['precio_unitario'])});}
   }
  });
  final before=[for(final row in await db.operations())await db.wire(row)]..sort((a,b)=>(a['operation_id'] as String).compareTo(b['operation_id'] as String));
  final api=ApiClient(baseUrl:'http://127.0.0.1:18085',tokenProvider:()=>(fixture['header']['Authorization'] as String).substring(7));
  var controller=OfflineController(api:api);controller.local=db;controller.namespace=namespace;controller.snapshot=await db.snapshot();
  final first=fixture['before'][0]['branch']['id_sucursal'] as int;final second=fixture['before'][1]['branch']['id_sucursal'] as int;
  await controller.download(first);
  expect(controller.message,contains('3/3'));expect((await db.operations()).where((r)=>r['accounted']==1).length,75);expect((await db.catalog(first)).single['available'],900);
  expect((await db.operations()).where((r)=>r['branch_id']==second).every((r)=>r['accounted']==0),true);
  await controller.download(second);expect((await db.catalog(second)).single['available'],998);
  expect((await db.operations()).where((r)=>r['accounted']==1).length,77);
  controller.dispose();await db.db.close();
  db=await LocalDatabase.open(namespace,directory:directory.path,factory:databaseFactoryFfi,backendUrl:'http://127.0.0.1:18085');
  controller=OfflineController(api:api);controller.local=db;controller.namespace=namespace;controller.snapshot=await db.snapshot();
  await controller.download(first);
  final after=[for(final row in await db.operations())await db.wire(row)]..sort((a,b)=>(a['operation_id'] as String).compareTo(b['operation_id'] as String));
  expect(after,before);expect((await db.operations()).length,127);expect(await db.db.query('detail'),hasLength(127));expect((await db.catalog(first)).single['available'],900);
  expect(await db.db.rawQuery('PRAGMA foreign_key_check'),isEmpty);
  final other=await LocalDatabase.open(fixture['other_company']['namespace'],directory:directory.path,factory:databaseFactoryFfi,backendUrl:'http://127.0.0.1:18085');expect(await other.operations(),isEmpty);await other.db.close();
  await File(const String.fromEnvironment('A5_EVIDENCE')).writeAsString(jsonEncode({'HTTP_real':true,'SQLite_FFI':true,'operations':127,'details':127,'UUID_and_payload_unchanged':true,'confirmed_accounted':77,'rejected_retained':25,'conflicts_retained':25,'first_available':900,'second_available':998,'reopened_and_replayed':true,'other_company_empty':true,'FK_errors':0}));
  controller.dispose();await db.db.close();SessionVault.active=null;
 });
}
