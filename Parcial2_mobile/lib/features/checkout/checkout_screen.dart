import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:open_filex/open_filex.dart';
import '../../core/api_client.dart';
import '../../core/config.dart';
import '../../core/models/venta_models.dart';
import '../../services/auth_service.dart';
import '../../services/carrito_service.dart';
import '../../services/venta_service.dart';
import 'stripe_webview_screen.dart';

/// El retorno de Stripe solo dispara una consulta; la confirmación viene del servidor.
class CheckoutScreen extends StatefulWidget {
 const CheckoutScreen({super.key});
 @override State<CheckoutScreen> createState()=>_CheckoutScreenState();
}
class _CheckoutScreenState extends State<CheckoutScreen> {
 final service=VentaService();final cart=CarritoService.instance;
 final api=ApiClient(baseUrl:apiBaseUrl,tokenProvider:()=>AuthService().token);
 final nit=TextEditingController(),name=TextEditingController();
 List<dynamic> branches=[];int? branch,customer;Map<String,dynamic>? quote,status;ReservaRespuesta? reservation;QRGenerarRespuesta? qr;ComprobanteRespuesta? receipt;
 bool busy=false,checking=false;String message='';Timer? timer;
 @override void initState(){super.initState();load();}
 Future<void> load() async {
  try{final values=await Future.wait([api.get('/api/contexto'),api.get('/api/clientes/me')]);if(!mounted)return;setState((){branches=values[0]['sucursales'];branch=branches.isEmpty?null:branches.first['id_sucursal'];customer=values[1]['id_cliente'];nit.text=values[1]['ci']??'';name.text=values[1]['nombre_completo']??'';});}catch(e){if(mounted)setState(()=>message='Inicie sesión con una cuenta de cliente de esta empresa. $e');}
 }
 Future<void> review() async {
  if(branch==null||customer==null||cart.estaVacio)return;setState(()=>busy=true);
  try{final value=await service.cotizar(branch!,cart.items.map((i)=>{'id_variante_prenda':i.idVariantePrenda,'cantidad':i.cantidad}).toList());cart.actualizarPrecios(value['items']);if(mounted)setState((){quote=value;message='Precios actuales por cantidad y oferta. Revise el total antes de reservar y pagar.';});}catch(e){message=e.toString();}finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> pay(bool card) async {
  if(busy||quote==null||customer==null||branch==null)return;
  if(nit.text.isEmpty||name.text.trim().length<2){setState(()=>message='Complete la identificación y el nombre del comprobante.');return;}
  setState(()=>busy=true);
  try{
   reservation??=await service.crearReserva(ReservaPeticion(idCliente:customer!,idSucursal:branch!,items:cart.items.map((i)=>DetalleReservaItem(idVariantePrenda:i.idVariantePrenda,cantidad:i.cantidad,precioUnitario:i.precioUnitario)).toList()));
   if(card){final session=await service.crearSesionStripe(idReserva:reservation!.idReserva,idCliente:customer!,nitCi:nit.text,razonSocial:name.text);if(!mounted)return;await Navigator.of(context).push(MaterialPageRoute(builder:(_)=>StripeWebviewScreen(checkoutUrl:session.urlPago)));}
   else{qr=await service.generarQR(QRGenerarPeticion(idReserva:reservation!.idReserva,idCliente:customer!,monto:reservation!.total,concepto:'Pedido ${reservation!.idReserva}'));}
   message='Reserva registrada. Esperando confirmación central del pago.';timer?.cancel();timer=Timer.periodic(const Duration(seconds:4),(_)=>check());await check();
  }catch(e){message=e.toString();}finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> check() async {
  if(reservation==null||status?['pagada']==true||checking)return;checking=true;
  try{final value=await service.estadoPago(reservation!.idReserva);if(!mounted)return;setState(()=>status=value);
   if(value['pagada']==true){timer?.cancel();cart.limpiarComprados(value['venta']['items']);message='Pago confirmado por el servidor. La entrega física se registra por separado.';
    try{receipt=await service.generarComprobante(idVenta:value['venta']['id_venta'],nitCi:nit.text,razonSocial:name.text,enviarEmail:false);}catch(_){message+=' El comprobante puede solicitarse desde el pedido.';}
   }else{message='Estado central: ${value['estado']}. La reserva se conserva.';}
   if(mounted)setState((){});
  }catch(e){if(mounted)setState(()=>message=e.toString());}finally{checking=false;}
 }
 Future<void> openReceipt() async {
  final value=receipt;if(value==null)return;try{final path=Uri.parse(value.urlPdf??'').path;if(!path.startsWith('/api/comprobantes/'))throw StateError('Ruta no autorizada.');final response=await api.download(path);final dir=await getTemporaryDirectory();final file=File('${dir.path}/${value.numeroComprobante}.pdf');await file.writeAsBytes(response.bodyBytes,flush:true);await OpenFilex.open(file.path);}catch(e){if(mounted)setState(()=>message=e.toString());}
 }
 Future<void> cancel() async{if(reservation==null)return;try{await api.post('/api/ventas/reserva/${reservation!.idReserva}/cancelar',body:{});timer?.cancel();if(mounted)setState((){reservation=null;qr=null;quote=null;message='Reserva cancelada. El carrito permanece disponible.';});}catch(e){if(mounted)setState(()=>message=e.toString());}}
 @override void dispose(){timer?.cancel();nit.dispose();name.dispose();super.dispose();}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Revisar y pagar pedido')),body:ListView(padding:const EdgeInsets.all(20),children:[
  const Text('Tu pedido',style:TextStyle(fontSize:28)),...cart.items.map((i)=>ListTile(title:Text(i.prendaNombre),subtitle:Text('${i.talla} · ${i.color} · ${i.cantidad} unidades'),trailing:Text('Bs ${i.subtotal.toStringAsFixed(2)}'))),
  if(reservation==null)...[DropdownButtonFormField<int>(initialValue:branch,decoration:const InputDecoration(labelText:'Sucursal de entrega'),items:branches.map((b)=>DropdownMenuItem<int>(value:b['id_sucursal'],child:Text(b['nombre']))).toList(),onChanged:(v)=>setState((){branch=v;quote=null;})),TextField(controller:nit,decoration:const InputDecoration(labelText:'Identificación del comprobante')),TextField(controller:name,decoration:const InputDecoration(labelText:'Nombre del comprobante')),OutlinedButton(onPressed:busy?null:review,child:const Text('Revisar disponibilidad y precios'))],
  if(quote!=null)Text('Total actual: Bs ${quote!['total']}',style:const TextStyle(fontSize:25)),if(reservation!=null)Text('Reserva ${reservation!.idReserva} · Total Bs ${reservation!.total.toStringAsFixed(2)}'),
  if(status?['pagada']!=true&&quote!=null)...[FilledButton(onPressed:busy?null:()=>pay(true),child:const Text('Pagar con Stripe de prueba')),OutlinedButton(onPressed:busy?null:()=>pay(false),child:const Text('Generar QR de demostración'))],
  if(qr!=null)...[Image.memory(base64Decode(qr!.qrBase64),height:230),Text('Referencia: ${qr!.referencia}'),const Text('QR de demostración; requiere verificación por el personal. No es una integración bancaria automática.')],
  if(reservation!=null&&status?['pagada']!=true)Wrap(children:[TextButton(onPressed:check,child:const Text('Consultar confirmación')),TextButton(onPressed:busy?null:cancel,child:const Text('Cancelar reserva sin pago'))]),
  if(status?['pagada']==true)Text('Venta central ${status!['venta']['id_venta']} · Entrega: ${status!['entregada']==true?'registrada':'pendiente'}'),
  if(receipt!=null)FilledButton(onPressed:openReceipt,child:const Text('Descargar comprobante autorizado')),
  if(busy)const LinearProgressIndicator(),if(message.isNotEmpty)Padding(padding:const EdgeInsets.symmetric(vertical:20),child:Text(message)),
 ]));
}
