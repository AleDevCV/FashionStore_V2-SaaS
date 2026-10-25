import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:flutter/material.dart';
import 'package:fashionstore_mobile/core/api_client.dart';
import 'package:fashionstore_mobile/core/session_vault.dart';
import 'package:fashionstore_mobile/services/auth_service.dart';
import 'package:fashionstore_mobile/features/login/login_screen.dart';

String jwt(Map<String,dynamic> fields)=>'eyJhbGciOiJIUzI1NiJ9.${base64Url.encode(utf8.encode(jsonEncode({...fields,'exp':DateTime.now().millisecondsSinceEpoch~/1000+3600}))).replaceAll('=','')}.firma-de-prueba';

void main(){
 TestWidgetsFlutterBinding.ensureInitialized();
 setUp((){FlutterSecureStorage.setMockInitialValues({});SessionVault.active=null;ApiClient.empresa='empresa-anterior';});
 test('login solo envia correo y password y resuelve empresa desde token',() async {
  final access=jwt({'account_id':1,'id_usuario':11,'tenant_id':3,'tipo_cuenta':'PERSONAL','rol':'Cajero (POS)','empresa_slug':'atelierandino'});
  await http.runWithClient(() async {
   final auth=AuthService(api:ApiClient(baseUrl:'https://example.test'));
   await auth.login('cajero@example.com','password-de-prueba');
   expect(auth.rol,'Cajero (POS)');expect(ApiClient.empresa,'atelierandino');expect(SessionVault.active,'3:11');
  },()=>MockClient((request)async{
   expect(request.headers.containsKey('X-Empresa')||request.headers.containsKey('x-empresa'),false);
   expect(jsonDecode(request.body),{'correo':'cajero@example.com','password':'password-de-prueba'});
   return http.Response(jsonEncode({'access_token':access}),200);
  }));
 });
 test('cliente global elige tiendas y conserva una sola identidad',()async{
  final global=jwt({'account_id':9,'id_usuario':9,'tenant_id':0,'tipo_cuenta':'CLIENTE','rol':'Cliente'});
  await http.runWithClient(()async{
   final auth=AuthService(api:ApiClient(baseUrl:'https://example.test'));
   await auth.login('cliente@example.com','password-de-prueba');expect(SessionVault.active,isNull);
   await auth.selectStore('tienda-a');expect(SessionVault.active,'1:101');expect(auth.tokenClaims!['account_id'],9);
   await auth.selectStore('tienda-b');expect(SessionVault.active,'2:202');expect(auth.tokenClaims!['account_id'],9);
  },()=>MockClient((request)async{
   if(request.url.path.contains('/login'))return http.Response(jsonEncode({'access_token':global}),200);
   expect(request.headers['Authorization']??request.headers['authorization'],startsWith('Bearer '));
   final store=jsonDecode(request.body)['empresa'];final first=store=='tienda-a';
   return http.Response(jsonEncode({'access_token':jwt({'account_id':9,'id_usuario':first?101:202,'tenant_id':first?1:2,'empresa_slug':store,'tipo_cuenta':'CLIENTE','rol':'Cliente'})}),200);
  }));
 });
 test('recuperacion no transmite empresa ni una sesion anterior',()async{
  await http.runWithClient(()async{
   await ApiClient(baseUrl:'https://example.test',tokenProvider:()=> 'sesion-anterior').post('/api/auth/recuperar-password',body:{'correo':'cliente@example.com'});
  },()=>MockClient((request)async{
   expect(request.headers.keys.any((key)=>key.toLowerCase()=='authorization'||key.toLowerCase()=='x-empresa'),false);
   return http.Response('{}',200);
  }));
 });
 test('cambiar al hostname definitivo conserva la referencia de la sesion anterior',()async{
  final previous='p2_${base64Url.encode(utf8.encode('https://fashionstore-v2.aledevcv.me')).replaceAll('=','')}_';
  FlutterSecureStorage.setMockInitialValues({'${previous}token':'token-anterior','${previous}active':'2:17','${previous}empresa':'demo-b'});
  await SessionVault.initialize();expect(SessionVault.active,'2:17');
  expect(await SessionVault.storage.read(key:SessionVault.key('token')),'token-anterior');
  expect(await SessionVault.storage.read(key:'${previous}active'),'2:17');
 });
 testWidgets('formulario compartido solo solicita correo y contraseña',(tester)async{
  await tester.pumpWidget(const MaterialApp(home:LoginScreen()));
  expect(find.text('Empresa'),findsNothing);expect(find.byType(TextFormField),findsNWidgets(2));
  expect(find.text('Crear una cuenta de cliente'),findsOneWidget);
 });
}
