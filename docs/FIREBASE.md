# Configuración pendiente de Firebase

La bandeja persistente funciona sin Firebase. El código Android y el despachador están preparados, pero **no se ha verificado ningún envío push real** porque todavía no existe un proyecto configurado en esta sesión.

1. Crear un proyecto propio en Firebase y registrar Android con el applicationId `com.fashionstore.fashionstore_mobile.p2`. Habilitar Cloud Messaging.
2. Obtener los cuatro valores públicos de configuración del cliente: projectId, apiKey, appId y messagingSenderId. Compilar usando `--dart-define=FIREBASE_PROJECT_ID=...`, `FIREBASE_API_KEY`, `FIREBASE_APP_ID` y `FIREBASE_SENDER_ID`. La cuenta de servicio nunca se incluye en el APK.
3. Guardar el JSON de una cuenta de servicio autorizada para FCM fuera del repositorio. Para Docker **local**, usar `infra/secrets/firebase.json` y `-f compose.firebase.yaml`; el usuario 10001 necesita lectura. En producción **nativa**, guardarlo en `/home/alecv/Parcial2_FashionStore/shared/firebase.json`, con propietario `root:fashionstore-p2` y modo `0640`, configurar esa ruta en `FIREBASE_CREDENTIALS_FILE` de `shared/api.env` y reiniciar exclusivamente `fashionstore-p2-api`. No se utiliza Docker en el servidor.
4. Probar en Android con Google Play Services: iniciar sesión como cliente, permitir avisos y registrar una solicitud. Al aceptar y reservar un reemplazo, comprobar aviso y bandeja con la diferencia pendiente. Probar también aplicación en segundo plano, permiso denegado y cambio de usuario.

El backend conserva resultados de entrega y reintenta con espera creciente. No registra tokens push en logs. El aviso externo omite importes y datos personales; el detalle se obtiene desde la sesión autorizada. La rotación del token móvil reduce la exposición al cambiar de cuenta. Un envío puede repetirse si el proveedor acepta el mensaje y se pierde su respuesta; no se ejecutan operaciones comerciales desde las notificaciones.

Referencias: [cliente Flutter oficial](https://firebase.google.com/docs/cloud-messaging/flutter/get-started), [envío con Admin SDK](https://firebase.google.com/docs/cloud-messaging/send/admin-sdk).
