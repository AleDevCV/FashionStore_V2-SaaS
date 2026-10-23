import 'dart:async';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'api_client.dart';
import 'config.dart';

/// Configuración pública del cliente. La cuenta de servicio vive solo en el servidor.
class PushService {
  static const project=String.fromEnvironment('FIREBASE_PROJECT_ID');
  static const options=FirebaseOptions(apiKey:String.fromEnvironment('FIREBASE_API_KEY'),appId:String.fromEnvironment('FIREBASE_APP_ID'),messagingSenderId:String.fromEnvironment('FIREBASE_SENDER_ID'),projectId:project);
  static final message=ValueNotifier<String>('Firebase pendiente de configurar. La bandeja de notificaciones sigue disponible.');
  static bool enabled=false;
  static String? _deviceToken;
  static String? Function()? _session;
  static StreamSubscription<String>? _refresh;
  static Future<void> initialize() async {
    if(project.isEmpty)return;
    try{await Firebase.initializeApp(options:options);enabled=true;FirebaseMessaging.onBackgroundMessage(backgroundPush);FirebaseMessaging.onMessage.listen((event){message.value=event.notification?.title??'Hay novedades en sus solicitudes.';});message.value='Notificaciones disponibles.';}catch(_){message.value='No se pudo inicializar Firebase; consulte la bandeja.';}
  }
  static Future<void> register(String? Function() session) async {
    if(!enabled)return;_session=session;
    try{
      final permission=await FirebaseMessaging.instance.requestPermission();
      if(permission.authorizationStatus==AuthorizationStatus.denied){message.value='Push desactivado por permiso del dispositivo. Puede usar la bandeja.';return;}
      // Rotar el token al cambiar de cuenta impide reutilizar el registro anterior.
      await FirebaseMessaging.instance.unregister();
      await _refresh?.cancel();_refresh=FirebaseMessaging.instance.onRegistered.listen((token){unawaited(_save(token));});
      await FirebaseMessaging.instance.register();
    }catch(_){message.value='Registro push pendiente; consulte la bandeja de notificaciones.';}
  }
  static Future<void> _save(String value) async {
    if(_session?.call()==null)return;
    try{await ApiClient(baseUrl:apiBaseUrl,tokenProvider:_session).post('/api/dispositivos/push',body:{'token':value});_deviceToken=value;message.value='Dispositivo registrado para avisos.';}catch(_){message.value='No se pudo registrar push; la bandeja permanece disponible.';}
  }
  static Future<void> unregister(String? oldSession) async {
    final device=_deviceToken;_deviceToken=null;_session=null;await _refresh?.cancel();_refresh=null;
    if(device!=null && oldSession!=null){try{await ApiClient(baseUrl:apiBaseUrl,tokenProvider:()=>oldSession).delete('/api/dispositivos/push',body:{'token':device});}catch(_){/* Rotación posterior del token y mensajes sin datos privados. */}}
    if(enabled){try{await FirebaseMessaging.instance.unregister();}catch(_){}}
  }
}

@pragma('vm:entry-point')
Future<void> backgroundPush(RemoteMessage message) async {
  if(PushService.project.isNotEmpty && Firebase.apps.isEmpty)await Firebase.initializeApp(options:PushService.options);
  // No se confirman pagos ni se alteran operaciones comerciales desde un push.
}
