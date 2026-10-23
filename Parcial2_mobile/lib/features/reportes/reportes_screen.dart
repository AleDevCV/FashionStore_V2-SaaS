import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:open_filex/open_filex.dart';
import 'package:speech_to_text/speech_to_text.dart';
import '../../core/api_client.dart';
import '../../core/config.dart';
import '../../services/auth_service.dart';

class ReportesScreen extends StatefulWidget {
 const ReportesScreen({super.key});
 @override State<ReportesScreen> createState()=>_ReportesScreenState();
}
class _ReportesScreenState extends State<ReportesScreen> {
 final api=ApiClient(baseUrl:apiBaseUrl,tokenProvider:()=>AuthService().token);
 final text=TextEditingController();final speech=SpeechToText();
 Map<String,dynamic> types={},filters={'tipo':'ventas_sucursal','desde':DateTime.now().subtract(const Duration(days:30)).toIso8601String().substring(0,10),'hasta':DateTime.now().toIso8601String().substring(0,10),'sucursal':null,'agrupacion':'dia','umbral':5,'limite':100};
 List<dynamic> branches=[];Map<String,dynamic>? report;bool pro=false,busy=false,listening=false;String message='';
 @override void initState(){super.initState();load();}
 Future<void> load() async{try{final ctx=await api.get('/api/contexto');final values=Map<String,dynamic>.from(await api.get('/api/reportes/tipos'));if(!mounted)return;setState((){types=values;branches=ctx['sucursales'];pro=ctx['suscripcion']?['reportes_ia']==true&&ctx['suscripcion']?['vigente']==true;});}catch(e){if(mounted)setState(()=>message=e.toString());}}
 Future<void> run(bool generative) async {
  if(busy)return;setState((){busy=true;report=null;message='Consultando datos autorizados…';});
  try{final response=await api.post('/api/reportes/${generative?'generativo':'convencional'}',body:generative?{'texto':text.text}:filters);if(!mounted)return;setState((){report=generative?response['reporte']:Map<String,dynamic>.from(response);message=generative?response['intencion']['mensaje']:'Reporte generado.';});}catch(e){if(mounted)setState(()=>message=e.toString());}finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> dictate() async {
  if(listening){await speech.stop();if(mounted)setState(()=>listening=false);return;}
  final available=await speech.initialize(onError:(_){if(mounted)setState((){message='No se pudo transcribir. Puede escribir su solicitud.';listening=false;});},onStatus:(status){if(mounted&&status=='done')setState(()=>listening=false);});
  if(!available){if(mounted)setState(()=>message='Dictado no disponible. Escriba la solicitud.');return;}
  if(mounted)setState(()=>listening=true);
  await speech.listen(onResult:(r){if(mounted)setState(()=>text.text=r.recognizedWords);},listenOptions:SpeechListenOptions(localeId:'es_BO',listenFor:const Duration(seconds:30)));
 }
 Future<void> download(String format) async {
  try{final id=report!['id'];final response=await api.download('/api/reportes/$id/exportar/$format');final directory=await getTemporaryDirectory();final file=File('${directory.path}/reporte-$id.$format');await file.writeAsBytes(response.bodyBytes,flush:true);final result=await OpenFilex.open(file.path);if(mounted)setState(()=>message=result.type==ResultType.done?'Archivo descargado y abierto.':'Archivo guardado: ${result.message}');}catch(e){if(mounted)setState(()=>message=e.toString());}
 }
 @override void dispose(){speech.cancel();text.dispose();super.dispose();}
 @override Widget build(BuildContext context){final r=report;return Scaffold(appBar:AppBar(title:const Text('Reportes de la empresa')),body:ListView(padding:const EdgeInsets.all(20),children:[
  const Text('Reportes con datos actuales',style:TextStyle(fontSize:26)),const Text('Los filtros convencionales están disponibles en ambos planes. El asistente requiere Profesional vigente.'),
  if(types.isNotEmpty)DropdownButtonFormField<String>(initialValue:filters['tipo'],decoration:const InputDecoration(labelText:'Tipo'),isExpanded:true,items:types.entries.map((e)=>DropdownMenuItem(value:e.key,child:Text(e.value))).toList(),onChanged:(v)=>setState(()=>filters['tipo']=v)),
  TextFormField(initialValue:filters['desde'],decoration:const InputDecoration(labelText:'Desde (AAAA-MM-DD)'),onChanged:(v)=>filters['desde']=v),TextFormField(initialValue:filters['hasta'],decoration:const InputDecoration(labelText:'Hasta (AAAA-MM-DD)'),onChanged:(v)=>filters['hasta']=v),
  DropdownButtonFormField<int>(initialValue:filters['sucursal'],decoration:const InputDecoration(labelText:'Sucursal'),items:[const DropdownMenuItem<int>(value:null,child:Text('Todas las autorizadas')),...branches.map((b)=>DropdownMenuItem<int>(value:b['id_sucursal'],child:Text(b['nombre'])))],onChanged:(v)=>setState(()=>filters['sucursal']=v)),
  if(filters['tipo']=='evolucion_ventas')DropdownButtonFormField<String>(initialValue:filters['agrupacion'],decoration:const InputDecoration(labelText:'Agrupar por'),items:const[DropdownMenuItem(value:'dia',child:Text('Día')),DropdownMenuItem(value:'semana',child:Text('Semana')),DropdownMenuItem(value:'mes',child:Text('Mes'))],onChanged:(v)=>filters['agrupacion']=v),
  if(filters['tipo']=='stock_bajo')TextFormField(initialValue:'${filters['umbral']}',decoration:const InputDecoration(labelText:'Disponibilidad máxima'),keyboardType:TextInputType.number,onChanged:(v)=>filters['umbral']=int.tryParse(v)??5),
  FilledButton(onPressed:busy?null:()=>run(false),child:const Text('Generar reporte')),
  const SizedBox(height:28),const Text('Asistente generativo',style:TextStyle(fontSize:24)),TextField(controller:text,maxLines:4,maxLength:2000,decoration:const InputDecoration(labelText:'Solicitud o transcripción editable',hintText:'Productos más vendidos este mes')),
  Wrap(spacing:10,children:[OutlinedButton.icon(onPressed:!pro||busy?null:dictate,icon:Icon(listening?Icons.stop:Icons.mic),label:Text(listening?'Detener':'Dictar')),FilledButton(onPressed:!pro||busy?null:()=>run(true),child:const Text('Interpretar y consultar'))]),
  const Text('Revise el texto antes de enviarlo. El dictado puede utilizar el servicio de voz del dispositivo.'),if(!pro)const Text('Asistente bloqueado: requiere Profesional vigente.'),
  if(busy)const LinearProgressIndicator(),if(message.isNotEmpty)Padding(padding:const EdgeInsets.symmetric(vertical:16),child:Text(message)),
  if(r!=null)...[Text(r['titulo'],style:const TextStyle(fontSize:25)),Text('${r['filtros']['desde']} — ${r['filtros']['hasta']}'),if((r['ventas_demostracion']??0)>0)Text('Incluye ${r['ventas_demostracion']} ventas de demostración identificadas.'),
   if((r['filas'] as List).isEmpty)const Text('No hay registros para los filtros seleccionados.') else SingleChildScrollView(scrollDirection:Axis.horizontal,child:DataTable(columns:(r['columnas'] as List).map((c)=>DataColumn(label:Text(c.toString().replaceAll('_',' ')))).toList(),rows:(r['filas'] as List).map((row)=>DataRow(cells:(r['columnas'] as List).map((c)=>DataCell(Text('${row[c]}'))).toList())).toList())),
   Wrap(spacing:10,children:[OutlinedButton(onPressed:()=>download('pdf'),child:const Text('Descargar PDF')),OutlinedButton(onPressed:()=>download('xlsx'),child:const Text('Descargar Excel'))]),Text(r['nota']),
  ]
 ]));}
}
