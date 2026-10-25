# FashionStore SaaS — Parcial 2

Angular, Flutter y FastAPI con PostgreSQL compartido y aislamiento por empresa. Proyecto en implementación: consultar la trazabilidad y las evidencias para distinguir código, pruebas y pendientes.

- Local: Docker Compose para API, web y PostgreSQL. Usar `compose.yaml` junto con `compose.local.yaml`; este último publica la base únicamente en `127.0.0.1:55433` e incluye Mailpit de desarrollo.
- Pruebas: `compose.test.yaml` contiene PostgreSQL 17 efímero exclusivo en `127.0.0.1:55432`. `scripts/test_database.py` reinicia solamente esa base.
- Producción: **nativa, sin Docker**, con PostgreSQL 17 y Nginx existentes, Python 3.13 en entorno virtual y systemd. Procedimiento en [DESPLIEGUE_NATIVO.md](docs/DESPLIEGUE_NATIVO.md).
- Flutter se compila localmente y se instala en Android; el servidor no compila el APK.

La configuración privada se mantiene fuera de Git. `.env.example` corresponde al desarrollo local. `scripts/generate_native_config.py` genera archivos privados independientes para producción, sin reutilizar las claves JWT ni las contraseñas de la base local.

No ejecutar `git push` ni publicar mediante API: las subidas a GitHub son manuales por indicación del equipo. La transferencia SSH al servidor es independiente de GitHub.

Acceso actualizado: [ACCESO_GLOBAL.md](docs/ACCESO_GLOBAL.md). Correo y contraseña para todos los roles; cliente con una identidad para todas las tiendas y datos comerciales aislados. Producción: https://fashionstore.aledevcv.me. Las cuentas demo y sus claves están en el archivo privado ignorado `infra/secrets/native/acceso-demo.txt`.
