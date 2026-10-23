import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/api_client.dart';
import '../../core/config.dart';
import '../../core/push_service.dart';
import '../../services/auth_service.dart';

class CambiosScreen extends StatefulWidget {
 const CambiosScreen({super.key});
 @override State<CambiosScreen> createState()=>_CambiosScreenState();
}
class _CambiosScreenState extends State<CambiosScreen> with WidgetsBindingObserver {
 final api=ApiClient(baseUrl:apiBaseUrl,tokenProvider:()=>AuthService().token);final reason=TextEditingController();final quantity=TextEditingController(text:'1');
 List<dynamic> eligible=[],changes=[],notifications=[];Map<String,dynamic>? selected;String message='';bool busy=false;
 @override void initState(){super.initState();WidgetsBinding.instance.addObserver(this);load();}
 @override void didChangeAppLifecycleState(AppLifecycleState state){if(state==AppLifecycleState.resumed)load();}
 Future<void> load() async{try{final result=await Future.wait([api.get('/api/cambios/elegibles'),api.get('/api/cambios'),api.get('/api/notificaciones')]);if(mounted)setState((){eligible=result[0];changes=result[1];notifications=result[2];selected=null;});}catch(e){if(mounted)setState(()=>message=e.toString());}}
 Future<void> request() async {
  if(selected==null)return;setState(()=>busy=true);try{await api.post('/api/cambios',body:{'id_venta':selected!['id_venta'],'id_variante_prenda':selected!['id_variante_prenda'],'cantidad':int.tryParse(quantity.text)??0,'motivo':reason.text});reason.clear();message='Solicitud registrada para inspección de la prenda sin uso.';await load();}catch(e){message=e.toString();}finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> action(Map item,String name) async {
  setState(()=>busy=true);try{final response=await api.post('/api/cambios/${item['id_cambio']}/$name',body:{});if(name=='pago'){final uri=Uri.parse(response['url_pago']);if(uri.scheme!='https'||uri.host!='checkout.stripe.com')throw StateError('Destino de pago no permitido.');await launchUrl(uri,mode:LaunchMode.externalApplication);}else{await load();}}catch(e){message=e.toString();}finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> read(Map note) async{try{await api.patch('/api/notificaciones/${note['id_notificacion']}/leida',body:{});await load();}catch(e){if(mounted)setState(()=>message=e.toString());}}
 @override void dispose(){WidgetsBinding.instance.removeObserver(this);reason.dispose();quantity.dispose();super.dispose();}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Cambios y notificaciones'),actions:[IconButton(onPressed:load,icon:const Icon(Icons.refresh),tooltip:'Actualizar')]),body:ListView(padding:const EdgeInsets.all(20),children:[
  const Text('Solicitar un cambio',style:TextStyle(fontSize:26)),const Text('Dentro de siete días desde la entrega, una vez por unidad y con la prenda sin uso. La recepción física y el reemplazo se gestionan en la sucursal original.'),
  DropdownButtonFormField<Map<String,dynamic>>(initialValue:selected,isExpanded:true,decoration:const InputDecoration(labelText:'Compra y prenda entregada'),items:eligible.map((x){final item=Map<String,dynamic>.from(x);return DropdownMenuItem(value:item,child:Text('Venta ${item['id_venta']} · ${item['nombre']} · ${item['talla']}',overflow:TextOverflow.ellipsis));}).toList(),onChanged:(v)=>setState(()=>selected=v)),
  TextField(controller:quantity,keyboardType:TextInputType.number,decoration:const InputDecoration(labelText:'Unidades')),TextField(controller:reason,maxLength:1000,maxLines:3,decoration:const InputDecoration(labelText:'Motivo')),
  FilledButton(onPressed:busy||selected==null?null:request,child:const Text('Registrar solicitud')),if(busy)const LinearProgressIndicator(),if(message.isNotEmpty)Text(message),
  const SizedBox(height:24),const Text('Seguimiento',style:TextStyle(fontSize:24)),
  ...changes.map((item)=>Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('Solicitud ${item['id_cambio']} · ${item['estado']}',style:const TextStyle(fontWeight:FontWeight.bold)),Text('${item['motivo']}\nCrédito: Bs ${item['credito']}\nDiferencia: ${item['diferencia']==null?'A definir':'Bs ${item['diferencia']}'}'),if(item['estado']=='PagoPendiente')FilledButton(onPressed:busy?null:()=>action(item,'pago'),child:const Text('Pagar diferencia en Stripe')),if(!['Entregado','Reembolsado','Cancelado','Rechazado'].contains(item['estado']))TextButton(onPressed:busy?null:()=>action(item,'cancelar'),child:const Text('Cancelar solicitud'))])))),
  if(changes.isEmpty)const Text('No hay solicitudes para esta cuenta.'),const SizedBox(height:24),const Text('Bandeja de notificaciones',style:TextStyle(fontSize:24)),ValueListenableBuilder<String>(valueListenable:PushService.message,builder:(_,value,__)=>Text(value)),
  ...notifications.map((note)=>Card(child:ListTile(title:Text(note['titulo']),subtitle:Text(note['mensaje']),trailing:note['leida']==true?const Icon(Icons.done):TextButton(onPressed:()=>read(note),child:const Text('Leída'))))),
 ]));
}
