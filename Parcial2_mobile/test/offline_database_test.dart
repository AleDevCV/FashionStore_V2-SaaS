import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';

Map<String,dynamic> snapshot(int branch,{int stock=5,int tenant=1})=>{
 'tenant_id':tenant,'author_id':1,'empresa':'demo','usuario':'admin@example.com','branch':{'id_sucursal':branch,'nombre':'Sucursal $branch'},'lease':'signed-lease-test-placeholder','lease_expires':DateTime.now().millisecondsSinceEpoch~/1000+3600,'can_sell':true,'downloaded_at':DateTime.now().toUtc().toIso8601String(),
 'products':[{'id_prenda':1,'id_variante_prenda':1,'nombre':'Camisa','sku':'P1','sku_variante':'V1','talla':'M','color':'Azul','precio_base':'50.00','precio_adicional':'0.00','stock':stock}],
 'customers':[{'id_cliente':1,'nombre_completo':'Cliente demo'}],'operation_results':[]};

void main(){
 sqfliteFfiInit();late Directory directory;late LocalDatabase local;
 setUp(() async{directory=await Directory.systemTemp.createTemp('fashionstore-p2-test-');local=await LocalDatabase.open('1:1',directory:directory.path,factory:databaseFactoryFfi);await local.saveSnapshot(snapshot(1));});
 tearDown(() async{await local.db.close();await directory.delete(recursive:true);});
 test('venta, detalles y UUID sobreviven a cerrar SQLite y reabrir',() async{
   final id=await local.capture(snapshot:snapshot(1),kind:'venta',quantities:{1:2},cash:'100');
   final before=await local.wire((await local.operations()).single);
   await local.db.update('operation',{'state':'ENVIANDO'},where:'id=?',whereArgs:[id]);await local.db.close();
   local=await LocalDatabase.open('1:1',directory:directory.path,factory:databaseFactoryFfi);
   final op=(await local.operations()).single;expect(op['state'],'PENDIENTE');expect(await local.wire(op),before);expect((await local.catalog(1)).single['available'],3);
 });
 test('una FK inválida revierte cabecera y detalles completos',() async{
   await expectLater(local.capture(snapshot:snapshot(1),kind:'reserva',customerId:999,quantities:{1:1}),throwsA(isA<DatabaseException>()));
   expect(await local.operations(),isEmpty);expect(await local.db.query('detail'),isEmpty);
 });
 test('descargas de otra sucursal conservan su propio stock y pendientes',() async{
   await local.capture(snapshot:snapshot(1),kind:'reserva',customerId:1,quantities:{1:2});await local.saveSnapshot(snapshot(2,stock:19));
   expect((await local.catalog(1)).single['available'],3);expect((await local.catalog(2)).single['available'],19);
 });
 test('confirmación reconciliada no descuenta dos veces la venta local',() async{
   final id=await local.capture(snapshot:snapshot(1),kind:'venta',quantities:{1:1},cash:'50');
   await local.applyResults([{'operation_id':id,'state':'CONFIRMADA','server_id':77}]);expect((await local.catalog(1)).single['available'],4);
   final updated=snapshot(1,stock:4);updated['operation_results']=[{'operation_id':id,'state':'CONFIRMADA','server_id':77}];await local.saveSnapshot(updated);
   expect((await local.catalog(1)).single['available'],4);expect((await local.operations()).single['accounted'],1);
 });
 test('cuentas diferentes no comparten operaciones ni catálogo',() async{
   final other=await LocalDatabase.open('2:1',directory:directory.path,factory:databaseFactoryFfi);expect(await other.operations(),isEmpty);expect(await other.catalog(1),isEmpty);await other.db.close();
 });
 test('dinero local conserva centavos y rechaza fracciones excesivas',(){expect(cents('19.90'),1990);expect(()=>cents('19.999'),throwsStateError);});
}
