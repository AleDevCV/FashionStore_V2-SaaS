import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'config.dart';

/// El JWT y la selección de empresa/usuario no se guardan en preferencias planas.
class SessionVault {
  static const storage = FlutterSecureStorage();
  static String key(String name)=>'p2_${base64Url.encode(utf8.encode(apiBaseUrl)).replaceAll('=','')}_$name';
  static String? active;
  static Future<void> initialize() async {
    // Ambos hostnames corresponden al mismo despliegue; no perder la referencia a SQLite al corregir la URL.
    if(apiBaseUrl=='https://fashionstore.aledevcv.me' && await storage.read(key:key('token'))==null){
      final previous='p2_${base64Url.encode(utf8.encode('https://fashionstore-v2.aledevcv.me')).replaceAll('=','')}_';
      for(final name in ['token','active','empresa']){
        final value=await storage.read(key:'$previous$name');
        if(value!=null)await storage.write(key:key(name),value:value);
      }
    }
    active = await storage.read(key: key('active'));
  }
  static Future<void> select(String value) async {
    active = value;
    await storage.write(key: key('active'), value: value);
  }
  static Future<void> clear() async {
    active = null;
    await storage.delete(key: key('active'));
    await storage.delete(key: key('token'));
  }
}
