import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/foundation.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/api_client.dart';
import 'package:fashionstore_mobile/core/session_vault.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';
import 'package:fashionstore_mobile/features/offline/offline_controller.dart';
import 'fixtures/offline_v1.dart';

String identifier(int i) => '00000000-0000-4000-8000-${i.toString().padLeft(12,'0')}';
class SnapshotServer extends ApiClient {
 SnapshotServer():super(baseUrl:'http://isolated.invalid');
 final requests=<List<String>>[];
 final states=<String,String>{};
 bool wrongIdentity=false;
 bool offline=false;bool duplicate=false;bool wrongBranch=false;int? failAt;int stock=999;
 Future<void> Function(int)? onRequest;
 @override Future<dynamic> get(String path,{Map<String,String>? query}) async {
  final uri=Uri.parse(path);
  final ids=uri.queryParametersAll['operation_ids']??[];
  requests.add(ids);
  await onRequest?.call(requests.length);
  if(offline||requests.length==failAt)throw const SocketException('Controlled A5 connection interruption');
  if(ids.length>50)throw StateError('Existing API accepts at most 50 UUIDs');
  final value=recoverySnapshot(wrongBranch?2:int.parse(uri.queryParameters['branch_id']!),stock:stock);
  if(wrongIdentity)value['tenant_id']=8;
  value['operation_results']=[for(final id in ids)if(states.containsKey(id)){'operation_id':id,'state':states[id],'server_id':states[id]=='CONFIRMADA'?77:null}];
  if(duplicate)value['operation_results']=[...value['operation_results'],...value['operation_results']];
  return value;
 }
}
void main(){
 TestWidgetsFlutterBinding.ensureInitialized();sqfliteFfiInit();
 late Directory dir;late LocalDatabase local;late OfflineController controller;late SnapshotServer server;
 setUp(() async {
  dir=await Directory.systemTemp.createTemp('a5-reconciliation-');resetRecoveryStorageForTest();SessionVault.active='7:11';
  local=await LocalDatabase.open('7:11',directory:dir.path,factory:databaseFactoryFfi);
  await local.saveSnapshot(recoverySnapshot(1,stock:1000));await local.saveSnapshot(recoverySnapshot(2,stock:1000));
  server=SnapshotServer();controller=OfflineController(api:server);controller.namespace='7:11';controller.local=local;controller.snapshot=await local.snapshot();
 });
 tearDown(() async {controller.dispose();await local.db.close();SessionVault.active=null;});
 Future<void> seed(int count,{bool foreignPrefix=false}) async {
  await local.db.transaction((tx) async {
   for(var i=1;i<=count;i++){
    final state=i==count?'CONFIRMADA':i.isEven?'EN_CONFLICTO':'RECHAZADA';
    final branch=foreignPrefix&&i<count?2:1;final id=identifier(i);server.states[id]=state;
    final stamp=DateTime.utc(2026,1,1).subtract(Duration(seconds:i)).toIso8601String();
    await tx.insert('operation',{'id':id,'branch_id':branch,'kind':'venta','occurred_at':stamp,'envelope':jsonEncode({'operation_id':id,'version':1,'tenant_id':7,'author_id':11,'branch_id':branch,'device_id':identifier(999),'kind':'venta','occurred_at':stamp,'lease':'isolated-only','customer_id':null,'cash_received':'50.00','original_operation':null}),'state':state});
    await tx.insert('detail',{'operation_id':id,'variant_id':1,'quantity':1,'price':5000});
   }
  });
 }
 Future<void> verifyProgress(int count,{int rounds=1,bool foreignPrefix=false}) async {
  await seed(count,foreignPrefix:foreignPrefix);
  final before=await local.db.query('operation',columns:['id','envelope','occurred_at','branch_id'],orderBy:'id');
  for(var i=0;i<rounds;i++){await controller.download(1);}
  final tail=(await local.db.query('operation',where:'id=?',whereArgs:[identifier(count)])).single;
  final actual=(await local.catalog(1)).single['available'];
  final conflicts=foreignPrefix?0:(count-1)~/2;final expected=999-conflicts;
  debugPrint('A5_REPRO:${jsonEncode({'client':'Flutter SQLite FFI','queue':count,'rounds':rounds,'other_branch_prefix':foreignPrefix,'requested_unique':server.requests.expand((x)=>x).toSet().length,'HTTP_requests':server.requests.length,'tail_state':tail['state'],'tail_accounted':tail['accounted'],'available':actual,'expected':expected})}');
  expect(await local.db.query('operation',columns:['id','envelope','occurred_at','branch_id'],orderBy:'id'),before,reason:'History/UUID/envelope cannot disappear');
  expect((await local.db.query('detail')).length,count);
  expect(tail['accounted'],1,reason:'Every requested-branch confirmed result must become accounted despite terminal prefixes');
  expect(actual,expected,reason:'Do not subtract an already reflected confirmed operation twice');
 }
 for(final count in [1,49,50,51,125]){test('A5 cola $count: confirmada posterior no queda bloqueada',() async=>verifyProgress(count));}
 test('A5 tres descargas no repiten eternamente el prefijo 50',() async=>verifyProgress(51,rounds:3));
 test('A5 sucursal 2 no bloquea reconciliación de sucursal 1',() async=>verifyProgress(51,foreignPrefix:true));
 test('A5 sin resultado definitivo conserva PENDIENTE y ENVIANDO',() async {
  await seed(2);server.states.clear();
  await local.db.update('operation',{'state':'PENDIENTE'},where:'id=?',whereArgs:[identifier(1)]);
  await local.db.update('operation',{'state':'ENVIANDO'},where:'id=?',whereArgs:[identifier(2)]);
  await controller.download(1);
  expect((await local.db.query('operation',orderBy:'id')).map((r)=>r['state']),['PENDIENTE','ENVIANDO']);
  expect((await local.operations()).every((r)=>r['accounted']==0),isTrue);
 });
 test('A5 respuesta de otra empresa no cambia catálogo ni operación',() async {
  await seed(1);server.wrongIdentity=true;final before=await local.snapshot();
  await controller.download(1);expect(await local.snapshot(),before);expect((await local.operations()).single['accounted'],0);
 });
 test('A5 reinicio de SQLite no perpetúa bloqueo posterior a 50',() async {
  await seed(51);await controller.download(1);controller.dispose();await local.db.close();
  local=await LocalDatabase.open('7:11',directory:dir.path,factory:databaseFactoryFfi);
  controller=OfflineController(api:server);controller.namespace='7:11';controller.local=local;controller.snapshot=await local.snapshot();
  await controller.download(1);expect((await local.operations()).length,51);expect((await local.db.query('operation',where:'id=?',whereArgs:[identifier(51)])).single['accounted'],1);
 });
 test('A5 respuesta duplicada y descargas repetidas no duplican descuento',() async {
  await seed(1);server.duplicate=true;await controller.download(1);await controller.download(1);
  expect((await local.operations()).length,1);expect((await local.db.query('detail')).length,1);expect((await local.catalog(1)).single['available'],999);
 });
 test('A5 conexión interrumpida conserva cola y al reconectar progresa 125',() async {
  await seed(125);final before=await local.operations();final snapshotBefore=await local.snapshot();server.offline=true;
  await controller.download(1);expect(await local.operations(),before);expect(await local.snapshot(),snapshotBefore);
  server.offline=false;await controller.download(1);expect((await local.operations()).length,125);expect((await local.db.query('operation',where:'id=?',whereArgs:[identifier(125)])).single['accounted'],1);
 });
 test('A5 pendiente solo cambia a confirmada con respuesta explícita',() async {
  await seed(1);await local.db.update('operation',{'state':'PENDIENTE'},where:'id=?',whereArgs:[identifier(1)]);
  await controller.download(1);final op=(await local.operations()).single;expect(op['state'],'CONFIRMADA');expect(op['accounted'],1);
 });
 test('A5 sin candidatos renueva catálogo con una petición vacía',() async {
  await controller.download(1);expect(server.requests,[<String>[]]);expect((await local.snapshot())!['branch']['id_sucursal'],1);
 });
 test('A5 125 UUID se recorren exactamente una vez en lotes 50 50 25',() async {
  await seed(125);await controller.download(1);
  expect(server.requests.map((r)=>r.length),[50,50,25]);expect(server.requests.expand((r)=>r).toSet().length,125);
  expect(controller.message,contains('3/3'));expect(await local.db.query('detail'),hasLength(125));
 });
 Future<void> allConfirmed() async {
  await seed(125);for(final id in server.states.keys.toList()){server.states[id]='CONFIRMADA';}
  server.stock=875;await local.db.update('operation',{'state':'PENDIENTE'});
 }
 test('A5 fallo del segundo lote conserva primer lote y reintenta los 75 restantes',() async {
  await allConfirmed();server.failAt=2;await controller.download(1);
  expect((await local.operations()).where((r)=>r['accounted']==1).length,50);expect(controller.message,contains('parcial (1/3'));
  expect(await local.meta('sync_lock'),isNull);expect(controller.busy,false);
  server.failAt=null;server.requests.clear();await controller.download(1);
  expect(server.requests.map((r)=>r.length),[50,25]);expect((await local.operations()).every((r)=>r['accounted']==1),isTrue);expect((await local.catalog(1)).single['available'],875);
 });
 test('A5 fallo del tercer lote conserva 100 y reintenta 25',() async {
  await allConfirmed();server.failAt=3;await controller.download(1);
  expect((await local.operations()).where((r)=>r['accounted']==1).length,100);expect(controller.message,contains('parcial (2/3'));
  server.failAt=null;server.requests.clear();await controller.download(1);expect(server.requests.single,hasLength(25));expect((await local.catalog(1)).single['available'],875);
 });
 test('A5 rollback SQLite del segundo lote no deja medias confirmaciones',() async {
  await allConfirmed();await local.db.execute("CREATE TEMP TRIGGER a5_fail BEFORE UPDATE ON operation WHEN NEW.id='${identifier(75)}' BEGIN SELECT RAISE(ABORT,'Controlled A5 rollback'); END");
  await controller.download(1);expect((await local.operations()).where((r)=>r['accounted']==1).length,50);
  expect((await local.operations()).where((r)=>r['result']!=null).length,50);expect(controller.message,contains('parcial (1/3'));
  await local.db.execute('DROP TRIGGER a5_fail');await controller.download(1);expect((await local.operations()).every((r)=>r['accounted']==1),isTrue);
 });
 test('A5 UUID ausente al final de 125 conserva estado pendiente',() async {
  await seed(125);server.states.remove(identifier(125));await local.db.update('operation',{'state':'PENDIENTE'},where:'id=?',whereArgs:[identifier(125)]);
  await controller.download(1);expect(server.requests,hasLength(3));final tail=(await local.db.query('operation',where:'id=?',whereArgs:[identifier(125)])).single;expect(tail['state'],'PENDIENTE');expect(tail['accounted'],0);
 });
 test('A5 sucursal distinta en respuesta revierte su aplicación',() async {
  await seed(1);server.wrongBranch=true;final before=await local.snapshot();await controller.download(1);expect(await local.snapshot(),before);expect((await local.operations()).single['accounted'],0);
 });
 test('A5 cambio de sesión durante respuesta no escribe otra cuenta ni retiene bloqueo',() async {
  await seed(1);final before=await local.snapshot();server.onRequest=(_) async {SessionVault.active='8:22';};
  await controller.download(1);expect(await local.snapshot(),before);expect((await local.operations()).single['accounted'],0);expect(await local.meta('sync_lock'),isNull);SessionVault.active='7:11';
 });
 test('A5 bloqueo de otro proceso impide HTTP sin borrar la cola',() async {
  await seed(1);await local.db.insert('meta',{'key':'sync_lock','value':jsonEncode({'owner':'other-a5','expires':DateTime.now().millisecondsSinceEpoch+60000})});
  await controller.download(1);expect(server.requests,isEmpty);expect((await local.operations()),hasLength(1));expect(jsonDecode((await local.meta('sync_lock'))!)['owner'],'other-a5');
 });
}
