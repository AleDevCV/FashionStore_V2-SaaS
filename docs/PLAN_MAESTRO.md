# FashionStore SaaS Parcial 2

## Mandato y secuencia

Evolucionar el primer parcial conservando Angular, Flutter, FastAPI y PostgreSQL. Primero se redactan los aspectos generales, requisitos, reglas y las 38 fichas de casos de uso; después se implementan los CU en orden; finalmente se verifican los diagramas técnicos contra el código mediante Graphify y análisis de símbolos. La indicación docente de modelos previos al código se registra como una diferencia metodológica aceptada por el equipo; no se declarará cumplida anticipadamente.

La aplicación anterior es una fuente de reutilización, no evidencia de pruebas ejecutadas sobre P2. Cada capacidad requiere trazabilidad y comprobación en la nueva base multitenant.

## Decisiones confirmadas

- Dos integrantes con 4 a 6 horas diarias por persona.
- Repositorio de respaldo: https://github.com/AleDevCV/FashionStore_V2-SaaS.git. Las subidas son manuales. No ejecutar push ni escrituras equivalentes mediante API.
- Producción separada en `/home/alecv/Parcial2_FashionStore`; subdominio previsto `fashionstore-v2.aledevcv.me`.
- SSH LAN `alecv@192.168.1.100`, alternativo `alecv@alecv`.
- Datos de demostración nuevos; migración del P1 ensayada sobre copia.
- Cambios dentro de siete días, prenda sin uso y una vez por unidad; diferencia positiva cobrada y diferencia negativa devuelta íntegramente.
- Dos planes configurables: Básico con dos sucursales, Profesional con diez; reportes generativos exclusivos de Profesional.
- Contratación administrativa sin facturación SaaS recurrente.
- Mantener la aplicación que ya ocupa el servidor. Puerto P2: 127.0.0.1:2468, solicitado por el usuario el 23 de octubre. Túnel Cloudflare independiente FashionStore_Parcial2, servicio fashionstore-p2-tunnel.
- Actualización del 23 de octubre de 2026: producción **nativa, sin Docker**, por instrucción del usuario. Docker Compose se conserva exclusivamente para desarrollo y pruebas locales.
- En producción se reutilizan PostgreSQL 17 y Nginx ya instalados. P2 tiene base `fashionstore_p2`, propietario `fashionstore_p2_owner`, rol limitado `fashionstore_p2_app`, usuario Linux `fashionstore-p2`, un entorno virtual por versión y servicio `fashionstore-p2-api`. No se instala otro PostgreSQL ni se modifica el clúster global.
- Angular se compila localmente y se transfiere como archivos estáticos. Python instala ruedas compatibles en el entorno virtual nativo de Python 3.13; no se entrena ML en el servidor. Límites iniciales de la API: 3 conexiones, un proceso, MemoryHigh 384 MiB y MemoryMax 512 MiB. Su viabilidad requiere medición real.

## Entregas y objetivos

| Fecha de Bolivia | Objetivo |
|---|---|
| 22 a 24 octubre 2026 | Capítulos I y II, fichas, prototipos y contratos |
| 25 octubre | Primera presentación y entorno reproducible |
| 26 octubre | CU 01 a 05 |
| 27 octubre | CU 06 a 12 |
| 28 octubre | CU 13 a 18 |
| 29 octubre | CU 19 a 23 |
| 30 octubre | CU 24 y 25 |
| 31 octubre | CU 26 a 28 |
| 1 noviembre | CU 29 a 31 y segunda presentación |
| 2 noviembre | CU 32 y 33 |
| 3 noviembre | CU 34 y 35 |
| 4 noviembre | CU 36 y 37 |
| 5 noviembre | CU 38 y regresión |
| 6 a 8 noviembre | Diagramas técnicos, documento final, despliegue y tercera presentación |
| 9 noviembre | Ensayo, restauración y congelación |
| 10 noviembre 07:00 | Defensa |

Carga objetivo: 206 horas-persona. El calendario es una referencia de organización, no evidencia de trabajo completado. El PDF no establece una hora de cierre de las presentaciones dominicales.

## Condiciones de cierre

Cada CU requiere ficha, comportamiento implementado, prueba pertinente, evidencia verificable y trazabilidad. Las fases del tablero son pendiente, especificado, implementado, probado y documentado. Ninguna captura o resultado de P1 acredita por sí mismo el funcionamiento de P2.

La entrega final contiene Word/PDF, fuentes, APK, migraciones, Docker para uso local, configuración nativa de producción, diagramas editables, inventario de métodos, pruebas y manuales. La accesibilidad pública se comprueba desde otra red; SSH no sustituye esa comprobación. El procedimiento vigente de producción es `docs/DESPLIEGUE_NATIVO.md`; sustituye cualquier propuesta anterior de desplegar contenedores o transferir imágenes Docker al servidor.
