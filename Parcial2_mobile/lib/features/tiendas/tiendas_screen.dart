import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../core/config.dart';
import '../../core/theme.dart';
import '../../services/auth_service.dart';
import '../catalogo/catalogo_screen.dart';
import '../login/login_screen.dart';

/// La tienda se elige después de autenticar al cliente, sin cambiar su cuenta.
class TiendasScreen extends StatefulWidget {
 const TiendasScreen({super.key});
 @override State<TiendasScreen> createState()=>_TiendasScreenState();
}
class _TiendasScreenState extends State<TiendasScreen> {
 final auth=AuthService();List<dynamic> stores=[],purchases=[];bool loading=true,busy=false;String message='';
 ApiClient get api=>ApiClient(baseUrl:apiBaseUrl,tokenProvider:()=>auth.token);
 @override void initState(){super.initState();load();}
 Future<void> load() async {
  try{final data=await api.get('/api/tiendas');final history=auth.rol=='Cliente'?await api.get('/api/cuenta/compras'):<dynamic>[];
   if(mounted)setState((){stores=List<dynamic>.from(data);purchases=List<dynamic>.from(history);});
  }catch(e){if(mounted)setState(()=>message=e.toString());}finally{if(mounted)setState(()=>loading=false);}
 }
 Future<void> enter(Map<String,dynamic> store) async {
  if(busy)return;setState(()=>busy=true);
  try{if(auth.rol=='Cliente'){await auth.selectStore(store['slug']);}else{ApiClient.empresa=store['slug'];}
   if(mounted)await Navigator.of(context).push(MaterialPageRoute(builder:(_)=>const CatalogoScreen()));
   if(mounted)await load();
  }catch(e){if(mounted)setState(()=>message=e.toString());}finally{if(mounted)setState(()=>busy=false);}
 }
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('FashionStore / Tiendas'),actions:[if(auth.autenticado)IconButton(tooltip:'Cerrar sesión',icon:const Icon(Icons.logout),onPressed:(){auth.logout();Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder:(_)=>const LoginScreen()),(_)=>false);})]),body:RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(24),children:[
  const Text('Tu cuenta. Todas las tiendas.',style:TextStyle(fontFamily:'Georgia',fontSize:30,color:fsInk)),const SizedBox(height:12),
  Text(auth.autenticado?'Bienvenido, ${auth.nombreUsuario}. Elige una colección.':'Explora las tiendas y accede cuando quieras comprar.'),const SizedBox(height:24),
  if(loading||busy)const LinearProgressIndicator(),if(message.isNotEmpty)Padding(padding:const EdgeInsets.symmetric(vertical:16),child:Text(message)),
  for(final store in stores)Card(child:Padding(padding:const EdgeInsets.all(20),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(store['nombre'],style:const TextStyle(fontSize:24)),const SizedBox(height:8),const Text('Prendas y disponibilidad en sus sucursales.'),const SizedBox(height:12),FilledButton(onPressed:busy?null:()=>enter(Map<String,dynamic>.from(store)),child:const Text('Explorar tienda'))]))),
  if(auth.rol=='Cliente')...[const SizedBox(height:28),const Text('Tus compras entre tiendas',style:TextStyle(fontSize:24)),
   if(purchases.isEmpty)const Padding(padding:EdgeInsets.symmetric(vertical:16),child:Text('Todavía no tienes compras registradas.')),
   for(final sale in purchases)ListTile(title:Text('${sale['tienda']} · Compra #${sale['id_venta']}'),subtitle:Text('${sale['fecha_venta']}'),trailing:Text('Bs ${sale['total']}'))],
  if(!auth.autenticado)TextButton(onPressed:()=>Navigator.of(context).push(MaterialPageRoute(builder:(_)=>const LoginScreen())),child:const Text('Iniciar sesión')),
 ])));
}

/// La administración SaaS completa está en web; móvil identifica correctamente su ámbito.
class PlataformaScreen extends StatefulWidget {
 const PlataformaScreen({super.key});
 @override State<PlataformaScreen> createState()=>_PlataformaScreenState();
}
class _PlataformaScreenState extends State<PlataformaScreen>{
 List<dynamic> companies=[];String error='';
 @override void initState(){super.initState();load();}
 Future<void> load() async{try{final data=await ApiClient(baseUrl:apiBaseUrl,tokenProvider:()=>AuthService().token).get('/api/empresas');if(mounted)setState(()=>companies=List<dynamic>.from(data));}catch(e){if(mounted)setState(()=>error=e.toString());}}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Administración SaaS'),actions:[IconButton(tooltip:'Cerrar sesión',onPressed:(){AuthService().logout();Navigator.of(context).pushReplacement(MaterialPageRoute(builder:(_)=>const LoginScreen()));},icon:const Icon(Icons.logout))]),body:ListView(padding:const EdgeInsets.all(24),children:[const Text('Superadministrador',style:TextStyle(fontSize:28)),const Text('Gestiona planes y suscripciones desde $webBaseUrl/panel/saas.'),if(error.isNotEmpty)Text(error),for(final company in companies)ListTile(title:Text(company['nombre']),subtitle:Text(company['slug']),trailing:Text(company['activa']?'Activa':'Suspendida'))]));
}
