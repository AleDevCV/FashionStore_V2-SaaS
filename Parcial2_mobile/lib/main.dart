import 'package:flutter/material.dart';

import 'app.dart';
import 'services/auth_service.dart';
import 'core/push_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AuthService().restore();
  await PushService.initialize();
  if(AuthService().autenticado)await PushService.register(()=>AuthService().token);
  runApp(const FashionStoreApp());
}
