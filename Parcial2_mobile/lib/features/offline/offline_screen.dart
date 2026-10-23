import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'offline_controller.dart';
import 'local_database.dart';

class OfflineScreen extends StatefulWidget {
  const OfflineScreen({super.key});
  @override State<OfflineScreen> createState()=>_OfflineScreenState();
}
class _OfflineScreenState extends State<OfflineScreen> with WidgetsBindingObserver {
  final controller=OfflineController();final cash=TextEditingController(text:'0');
  int? branch,customer;String kind='reserva',filter='';String? revision;final quantities=<int,int>{};
  @override void initState(){super.initState();WidgetsBinding.instance.addObserver(this);controller.addListener(_update);controller.open().catchError((e){controller.message=e.toString();_update();});}
  void _update(){if(mounted)setState((){branch??=controller.snapshot?['branch']['id_sucursal'];});}
  @override void didChangeAppLifecycleState(AppLifecycleState state){if(state==AppLifecycleState.resumed)controller.sync();}
  @override void dispose(){WidgetsBinding.instance.removeObserver(this);controller.removeListener(_update);controller.dispose();cash.dispose();super.dispose();}
  int productQuantity(Map<String,dynamic> row)=>controller.catalog.where((r)=>r['id_prenda']==row['id_prenda']).fold(0,(sum,r)=>sum+(quantities[r['id_variante_prenda']]??0));
  int get total=>controller.catalog.fold(0,(sum,r)=>sum+(quantities[r['id_variante_prenda']]??0)*priceCents(r,productQuantity(r)));
  Future<void> save() async {
    try{await controller.capture(kind,customer,quantities,cash.text,original:revision);quantities.clear();revision=null;cash.text='0';_update();}catch(e){controller.message=e.toString();_update();}
  }
  Future<void> revise(Map<String,dynamic> op) async {
    if(controller.snapshot?['branch']['id_sucursal']!=op['branch_id']){controller.message='Descarga primero la sucursal original.';_update();return;}
    final data=Map<String,dynamic>.from(jsonDecode(op['envelope']));final details=await controller.current().db.query('detail',where:'operation_id=?',whereArgs:[op['id']]);
    if(!mounted)return;setState((){revision=op['id'];kind=op['kind'];customer=data['customer_id'];cash.text=data['cash_received']??'0';quantities.clear();for(final d in details){quantities[d['variant_id'] as int]=d['quantity'] as int;}});
  }
  Future<void> compensate(Map<String,dynamic> op) async {
    final reason=TextEditingController(),amount=TextEditingController(text:'0');
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Registrar compensación'),content:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:reason,decoration:const InputDecoration(labelText:'Motivo y constancia de devolución')),TextField(controller:amount,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Efectivo devuelto'))]),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Registrar'))]));
    if(ok==true){try{cents(amount.text);await controller.compensate(op['id'],reason.text,amount.text);}catch(e){controller.message=e.toString();_update();}}reason.dispose();amount.dispose();
  }
  @override Widget build(BuildContext context){
    final snap=controller.snapshot;final branches=controller.branches.isNotEmpty?controller.branches:snap==null?<Map<String,dynamic>>[]:[Map<String,dynamic>.from(snap['branch'])];
    return Scaffold(appBar:AppBar(title:const Text('Operación sin conexión'),actions:[IconButton(onPressed:controller.busy?null:controller.sync,icon:const Icon(Icons.sync),tooltip:'Sincronizar ahora')]),body:ListView(padding:const EdgeInsets.all(20),children:[
      const Text('Catálogo y caja local',style:TextStyle(fontFamily:'serif',fontSize:28)),const SizedBox(height:10),
      const Text('Las operaciones son provisionales hasta la aceptación central. La disponibilidad local puede haber cambiado.'),
      if(controller.message.isNotEmpty)Padding(padding:const EdgeInsets.symmetric(vertical:16),child:Text(controller.message,semanticsLabel:'Estado: ${controller.message}')),
      if(controller.busy)const LinearProgressIndicator(),
      if(branches.isNotEmpty)DropdownButtonFormField<int>(initialValue:branch,decoration:const InputDecoration(labelText:'Sucursal'),items:branches.map((b)=>DropdownMenuItem<int>(value:b['id_sucursal'],child:Text(b['nombre']))).toList(),onChanged:(v)=>setState(()=>branch=v)),
      const SizedBox(height:10),OutlinedButton.icon(onPressed:controller.busy||branch==null?null:()=>controller.download(branch!),icon:const Icon(Icons.download),label:const Text('Actualizar catálogo')),
      if(snap!=null)...[
       Text('${snap['empresa']} · ${snap['usuario']}\nCatálogo de ${snap['branch']['nombre']}\nActualizado: ${snap['downloaded_at']}\nPermiso local: ${controller.validLease?'vigente':'vencido; conecta para renovar'}'),
       const SizedBox(height:20),TextField(decoration:const InputDecoration(labelText:'Buscar prenda, talla o color'),onChanged:(v)=>setState(()=>filter=v.toLowerCase())),
       ...controller.catalog.where((r)=>'${r['nombre']} ${r['talla']} ${r['color']} ${r['sku_variante']}'.toLowerCase().contains(filter)).map((row)=>Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('${row['nombre']} · ${row['talla']} · ${row['color']}',style:const TextStyle(fontWeight:FontWeight.w600)),Text('Bs ${(priceCents(row,productQuantity(row))/100).toStringAsFixed(2)} · ${row['available']} disponibles localmente'),Row(children:[IconButton(onPressed:()=>setState(()=>quantities[row['id_variante_prenda']]=((quantities[row['id_variante_prenda']]??0)-1).clamp(0,10000)),icon:const Icon(Icons.remove),tooltip:'Quitar unidad'),Text('${quantities[row['id_variante_prenda']]??0}'),IconButton(onPressed:()=>setState(()=>quantities[row['id_variante_prenda']]=(quantities[row['id_variante_prenda']]??0)+1),icon:const Icon(Icons.add),tooltip:'Agregar unidad')])])))),
       const SizedBox(height:20),Text(revision==null?'Nueva operación':'Revisión del original: $revision',style:const TextStyle(fontSize:22)),
       DropdownButtonFormField<String>(initialValue:kind,decoration:const InputDecoration(labelText:'Tipo'),items:[const DropdownMenuItem(value:'reserva',child:Text('Reserva provisional')),if(snap['can_sell']==true)const DropdownMenuItem(value:'venta',child:Text('Venta de contado provisional'))],onChanged:(v)=>setState(()=>kind=v!)),
       DropdownButtonFormField<int>(initialValue:customer,decoration:const InputDecoration(labelText:'Cliente'),items:[const DropdownMenuItem<int>(value:null,child:Text('Mostrador (solo venta)')),...controller.customers.map((c)=>DropdownMenuItem<int>(value:c['id_cliente'],child:Text(c['nombre_completo'])))],onChanged:(v)=>setState(()=>customer=v)),
       Text('Total conocido: Bs ${(total/100).toStringAsFixed(2)}',style:const TextStyle(fontSize:25)),
       if(kind=='venta')TextField(controller:cash,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Efectivo realmente recibido')),
       FilledButton(onPressed:controller.busy||!controller.validLease?null:save,child:const Text('Guardar en el dispositivo')),
       if(revision!=null)TextButton(onPressed:()=>setState((){revision=null;quantities.clear();}),child:const Text('Cancelar revisión')),
      ],
      const SizedBox(height:25),const Text('Historial local',style:TextStyle(fontSize:24)),
      ...controller.operations.map((op)=>Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('${op['kind']} · ${op['state']}',style:const TextStyle(fontWeight:FontWeight.bold)),SelectableText('${op['id']}'),Text('Sucursal ${op['branch_id']} · ${op['occurred_at']}\nIntentos: ${op['attempts']}\n${op['reason']}'),if(op['result']!=null)Text('Resultado: ${jsonDecode(op['result'])['server_id']??jsonDecode(op['result'])['reason']??op['state']}'),if(op['resolved']==1)const Text('Resuelto; se conserva el historial.'),if(['EN_CONFLICTO','RECHAZADA'].contains(op['state']) && op['resolved']==0)Wrap(children:[TextButton(onPressed:()=>revise(op),child:const Text('Preparar revisión')),TextButton(onPressed:()=>compensate(op),child:const Text('Compensar'))]),TextButton(onPressed:() async{await Clipboard.setData(ClipboardData(text:jsonEncode(await controller.current().wire(op))));},child:const Text('Copiar operación para recuperación'))])))),
      if(controller.operations.isEmpty)const Text('No hay operaciones locales de esta cuenta.'),
    ]));
  }
}
