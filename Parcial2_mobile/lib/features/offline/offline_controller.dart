import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:uuid/uuid.dart';
import '../../core/api_client.dart';
import '../../core/config.dart';
import '../../core/session_vault.dart';
import '../../services/auth_service.dart';
import 'local_database.dart';

class OfflineController extends ChangeNotifier {
  LocalDatabase? local;
  Map<String,dynamic>? snapshot;
  List<Map<String,dynamic>> catalog=[],customers=[],operations=[],branches=[];
  String message=''; bool busy=false;String? namespace;
  final String owner=const Uuid().v4();
  Timer? _timer;StreamSubscription<List<ConnectivityResult>>? _connection;
  final ApiClient api=ApiClient(baseUrl:apiBaseUrl,tokenProvider:()=>AuthService().token);
  int failures=0;
  bool get validLease=>snapshot!=null && (snapshot!['lease_expires'] as int)*1000>DateTime.now().millisecondsSinceEpoch;
  Future<void> open() async {
    namespace=SessionVault.active;
    if(namespace==null){message='Inicia sesión y descarga el catálogo para preparar este dispositivo.';notifyListeners();return;}
    local=await LocalDatabase.open(namespace!);snapshot=await local!.snapshot();await refresh();
    _connection=Connectivity().onConnectivityChanged.listen((_)=>schedule());schedule();
    if(AuthService().autenticado){try{final ctx=await api.get('/api/contexto');branches=List<Map<String,dynamic>>.from(ctx['sucursales']);}catch(e){message=e.toString();}notifyListeners();}
  }
  LocalDatabase current(){if(local==null || namespace!=SessionVault.active)throw StateError('Selecciona la cuenta original del dispositivo.');return local!;}
  Future<void> refresh() async {
    final db=current();operations=await db.operations();customers=await db.customers();catalog=snapshot==null?[]:await db.catalog(snapshot!['branch']['id_sucursal']);notifyListeners();
  }
  Future<bool> lock() async {
    return current().db.transaction((tx) async {
      final rows=await tx.query('meta',where:'key=?',whereArgs:['sync_lock']);final lock=rows.isEmpty?null:jsonDecode(rows.first['value'] as String);
      if(lock!=null && lock['owner']!=owner && lock['expires']>DateTime.now().millisecondsSinceEpoch)return false;
      await tx.rawInsert('INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',['sync_lock',jsonEncode({'owner':owner,'expires':DateTime.now().millisecondsSinceEpoch+60000})]);return true;
    });
  }
  Future<void> unlock() async {final db=current();await db.db.transaction((tx) async {final rows=await tx.query('meta',where:'key=?',whereArgs:['sync_lock']);if(rows.isNotEmpty && jsonDecode(rows.first['value'] as String)['owner']==owner)await tx.delete('meta',where:'key=?',whereArgs:['sync_lock']);});}
  Future<void> download(int branch) async {
    if(busy)return;busy=true;notifyListeners();var acquired=false;
    try{
      acquired=await lock();if(!acquired)throw StateError('Otra operación está usando la cola.');
      final pending=(await current().operations()).where((o)=>o['accounted']==0).take(50);
      final query='branch_id=$branch${pending.map((o)=>'&operation_ids=${o['id']}').join()}';
      final value=Map<String,dynamic>.from(await api.get('/api/offline/catalogo?$query'));
      if('${value['tenant_id']}:${value['author_id']}'!=namespace)throw StateError('La respuesta pertenece a otra cuenta.');
      await current().saveSnapshot(value);snapshot=value;await refresh();message='Catálogo guardado en SQLite. Es un subconjunto de la sucursal, con disponibilidad estimada.';
    }catch(e){message=e.toString();}finally{if(acquired)await unlock();busy=false;notifyListeners();}
  }
  Future<void> capture(String kind,int? customer,Map<int,int> quantities,String cash,{String? original}) async {
    if(busy)return;busy=true;notifyListeners();
    try{await current().capture(snapshot:snapshot!,kind:kind,customerId:customer,quantities:quantities,cash:cash,original:original);await refresh();message='Operación provisional guardada. Conserva el efectivo y espera confirmación central.';schedule();}finally{busy=false;notifyListeners();}
  }
  Future<void> sync() async {
    if(busy || local==null || !AuthService().autenticado || namespace!=SessionVault.active)return;
    busy=true;notifyListeners();var acquired=false;var batch=<Map<String,dynamic>>[];
    try{
      acquired=await lock();if(!acquired)return;
      batch=await current().db.query('operation',where:"state='PENDIENTE'",orderBy:'occurred_at',limit:20);if(batch.isEmpty)return;
      final payload=<Map<String,dynamic>>[];
      for(final op in batch){payload.add(await current().wire(op));}
      await current().db.transaction((tx) async {for(final op in batch){await tx.rawUpdate("UPDATE operation SET state='ENVIANDO',attempts=attempts+1 WHERE id=?",[op['id']]);}});
      final response=await api.post('/api/sincronizacion/lote',body:{'operations':payload});
      final results=List<dynamic>.from(response['results']);await current().applyResults(results);
      for(final op in batch){if(!results.any((r)=>r['operation_id']==op['id']))await current().db.update('operation',{'state':'PENDIENTE','reason':'Sin resultado central; se reintentará.'},where:'id=?',whereArgs:[op['id']]);}
      failures=0;message='Resultados centrales guardados. El historial permanece en el dispositivo.';
    }catch(e){failures++;message=e.toString();for(final op in batch){await current().db.update('operation',{'state':'PENDIENTE','reason':message},where:'id=?',whereArgs:[op['id']]);}}
    finally{if(acquired)await unlock();busy=false;await refresh();schedule();}
  }
  Future<void> compensate(String id,String reason,String amount) async {
    await api.post('/api/conflictos/$id/compensar',body:{'motivo':reason,'compensacion':amount});
    await current().db.update('operation',{'resolved':1,'reason':reason},where:'id=?',whereArgs:[id]);await refresh();
  }
  void schedule(){_timer?.cancel();if(local==null)return;_timer=Timer(Duration(seconds:(5*(1<<failures.clamp(0,4))).clamp(5,60)),()=>unawaited(sync()));}
  @override void dispose(){_timer?.cancel();_connection?.cancel();local?.db.close();super.dispose();}
}
