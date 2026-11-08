import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/features/offline/local_database.dart';
import '../test/fixtures/offline_v1.dart';

void main(){
 sqfliteFfiInit();
 test('A4 aceptación posterior: recupera los cinco UUID de los archivos del diagnóstico sin alterar originales',()async{
  const directory=String.fromEnvironment('A4_AUDIT_DIR');
  final expected=<Map<String,dynamic>>[];final originals=<String,List<int>>{};
  for(final origin in [oldOrigin,newOrigin]){
   final filename=legacyPath(directory,origin);originals[filename]=await File(filename).readAsBytes();
   final source=await databaseFactoryFfi.openDatabase(filename,options:OpenDatabaseOptions(readOnly:true,singleInstance:false));
   expected.addAll(await wires(LocalDatabase(source)));await source.close();
  }
  expected.sort((a,b)=>(a['operation_id'] as String).compareTo(b['operation_id'] as String));
  expect(expected.length,5);
  final db=await LocalDatabase.open('7:11',directory:directory,factory:databaseFactoryFfi,backendUrl:newOrigin);
  expect(await wires(db),expected);expect((await db.db.query('detail')).length,5);await db.db.close();
  final reopened=await LocalDatabase.open('7:11',directory:directory,factory:databaseFactoryFfi,backendUrl:oldOrigin);
  expect(await wires(reopened),expected);expect(await reopened.db.rawQuery('PRAGMA foreign_key_check'),isEmpty);await reopened.db.close();
  for(final entry in originals.entries){expect(await File(entry.key).readAsBytes(),entry.value);}
 });
}
