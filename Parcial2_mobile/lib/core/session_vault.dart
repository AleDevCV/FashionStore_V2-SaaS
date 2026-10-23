import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'config.dart';

/// El JWT y la selección de empresa/usuario no se guardan en preferencias planas.
class SessionVault {
  static const storage = FlutterSecureStorage();
  static String key(String name)=>'p2_${base64Url.encode(utf8.encode(apiBaseUrl)).replaceAll('=','')}_$name';
  static String? active;
  static Future<void> initialize() async {
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
