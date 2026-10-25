import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../core/config.dart';
import '../../services/auth_service.dart';
import '../tiendas/tiendas_screen.dart';

class RegistroScreen extends StatefulWidget {
 const RegistroScreen({super.key});
 @override State<RegistroScreen> createState()=>_RegistroScreenState();
}
class _RegistroScreenState extends State<RegistroScreen>{
 final form=GlobalKey<FormState>();final fields={for(final name in ['nombre','apellido','ci','correo','password'])name:TextEditingController()};bool busy=false;String error='';
 Future<void> register() async{
  if(busy||!(form.currentState?.validate()??false))return;setState(()=>busy=true);
  try{final body={for(final e in fields.entries)e.key:e.key=='password'?e.value.text:e.value.text.trim()};
   final result=await ApiClient(baseUrl:apiBaseUrl).post('/api/auth/registro',body:body);
   await AuthService().acceptToken(result['access_token']);
   if(mounted)Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder:(_)=>const TiendasScreen()),(_)=>false);
  }catch(e){if(mounted)setState(()=>error=e.toString());}finally{if(mounted)setState(()=>busy=false);}
 }
 @override void dispose(){for(final field in fields.values){field.dispose();}super.dispose();}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Crear cuenta')),body:Form(key:form,child:ListView(padding:const EdgeInsets.all(24),children:[
  const Text('Una cuenta para todas las tiendas.',style:TextStyle(fontSize:28)),const SizedBox(height:20),
  for(final item in {'nombre':'Nombre','apellido':'Apellido','ci':'Documento de identidad','correo':'Correo electrónico','password':'Contraseña'}.entries)Padding(padding:const EdgeInsets.only(bottom:16),child:TextFormField(controller:fields[item.key],obscureText:item.key=='password',keyboardType:item.key=='correo'?TextInputType.emailAddress:TextInputType.text,decoration:InputDecoration(labelText:item.value),validator:(value){if(value==null||value.trim().isEmpty)return 'Completa este campo.';if(item.key=='correo'&&!value.contains('@'))return 'Escribe un correo válido.';if(item.key=='password'&&value.length<6)return 'Usa al menos seis caracteres.';if(item.key=='ci'&&value.length<4)return 'Escribe al menos cuatro caracteres.';return null;})),
  if(error.isNotEmpty)Text(error),FilledButton(onPressed:busy?null:register,child:Text(busy?'Creando cuenta…':'Crear mi cuenta')),
 ])));
}
