/**
 * =============================================================================
 * FASHIONSTORE - TABLA DE RUTAS DE LA APLICACIÃ“N
 * -----------------------------------------------------------------------------
 * Todas las vistas se cargan de forma diferida (`loadComponent`) para que el
 * paquete inicial que descarga el navegador sea lo mÃ¡s liviano posible (RNF02).
 *
 * Estructura:
 *   /login              -> pantalla de acceso (CU01)
 *   /panel              -> layout administrativo, protegido por authGuard
 *     /panel/inicio     -> bienvenida
 *     /panel/usuarios   -> gestiÃ³n de usuarios y roles (CU02), solo Administrador
 * =============================================================================
 */

import { Routes } from '@angular/router';

import { authGuard, invitadoGuard, tiendaGuard } from './core/guards/auth.guard';
import { rolGuard } from './core/guards/rol.guard';
import { ROLES } from './core/models/auth.model';

export const routes: Routes = [
  {path:'tiendas',title:'Tiendas · FashionStore',loadComponent:()=>import('./features/tiendas/tiendas').then(m=>m.Tiendas)},
  {path:'offline',title:'Operación sin conexión · FashionStore',loadComponent:()=>import('./features/offline/offline').then(m=>m.Offline)},
  {path: 'cambios', canActivate: [authGuard], title: 'Cambios y devoluciones', loadComponent: () => import('./features/cambios/cambios').then(m => m.Cambios)},
    {
      path: 'probador-mobile/:id',
      loadComponent: () => import('./features/probador-mobile').then(m => m.ProbadorMobile)
    },
  {
    // Ruta por defecto: envÃ­a al login, que a su vez redirige al panel si ya
    // existe una sesiÃ³n activa (gracias a invitadoGuard).
    path: '',
    pathMatch: 'full',
    redirectTo: 'login',
  },
  {
    // CU01 - Pantalla de inicio de sesiÃ³n
    path: 'login',
    canActivate: [invitadoGuard],
    title: 'Iniciar sesiÃ³n Â· FashionStore',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    // CU04 - Solicitud de recuperaciÃ³n de contraseÃ±a ("OlvidÃ© mi contraseÃ±a")
    path: 'recuperar-password',
    canActivate: [invitadoGuard],
    title: 'Recuperar contraseÃ±a Â· FashionStore',
    loadComponent: () =>
      import('./features/auth/recuperar-password/recuperar-password').then(
        (m) => m.RecuperarPassword,
      ),
  },
  {
    // CU04 - Restablecimiento de contraseÃ±a mediante token temporal
    path: 'restablecer-password',
    canActivate: [invitadoGuard],
    title: 'Restablecer contraseÃ±a Â· FashionStore',
    loadComponent: () =>
      import('./features/auth/restablecer-password/restablecer-password').then(
        (m) => m.RestablecerPassword,
      ),
  },
  {
    // CU05 / CU01 - Registro de nuevo cliente (auto-registro pÃºblico)
    path: 'registro',
    canActivate: [invitadoGuard],
    title: 'Crear cuenta Â· FashionStore',
    loadComponent: () => import('./features/auth/registro/registro').then((m) => m.Registro),
  },
  {
    // Alias de conveniencia para la ruta de registro
    path: 'registro-cliente',
    redirectTo: 'registro',
  },
  {
    // CU01 / CU14 - Inicio de sesiÃ³n exclusivo para clientes
    path: 'login-cliente',
    canActivate: [invitadoGuard],
    title: 'Iniciar sesiÃ³n Â· FashionStore Clientes',
    loadComponent: () =>
      import('./features/auth/login-cliente/login-cliente').then((m) => m.LoginCliente),
  },
  {
    // Alias alternativo para inicio de sesiÃ³n de clientes
    path: 'cliente-login',
    redirectTo: 'login-cliente',
  },
  {
    // Layout administrativo: sidebar + cabecera. Todas sus rutas hijas quedan
    // protegidas por authGuard, que exige un token JWT vigente.
    path: 'panel',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/layout').then((m) => m.Layout),
    children: [
      {
        // CU11 / CU12 / CU14 - Conciliación de pagos y entregas pendientes (exclusivo personal de tienda)
        path: 'pagos-control',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
            'Pagos y entregas',
          ),
        ],
        title: 'Pagos y entregas · FashionStore',
        loadComponent: () =>
          import('./features/pagos-control/pagos-control').then((m) => m.PagosControl),
      },
      {
        // CU19 - Analítica avanzada y modelos de Machine Learning (empresa comercial)
        path: 'analitica',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
            'Analítica y Machine Learning',
          ),
        ],
        title: 'Analítica y Machine Learning · FashionStore',
        loadComponent: () => import('./features/analitica/analitica').then((m) => m.Analitica),
      },
      {
        // CU18 - Reportes comerciales convencionales y generativos con IA
        path: 'reportes',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
            'Reportes Comerciales',
          ),
        ],
        title: 'Reportes Comerciales · FashionStore',
        loadComponent: () => import('./features/reportes/reportes').then((m) => m.Reportes),
      },
      {
        // CU15 - Gestión de cambios, devoluciones y notificaciones
        path: 'cambios',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO, ROLES.CLIENTE],
            'Cambios y devoluciones',
          ),
        ],
        title: 'Cambios y devoluciones · FashionStore',
        loadComponent: () => import('./features/cambios/cambios').then((m) => m.Cambios),
      },
      {
        // CU02 - Administración de empresas, planes y suscripciones (SuperAdmin SaaS y Admin de Empresa)
        path: 'saas',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR],
            'Empresas, Planes y Suscripciones',
            { permitirPlataforma: true },
          ),
        ],
        title: 'Empresas y suscripción · FashionStore',
        loadComponent: () => import('./features/saas/saas').then((m) => m.Saas),
      },
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard',
      },
      {
        // CU01 - Resumen de sesión verificada y contexto de cuenta
        path: 'inicio',
        title: 'Sesión y Cuenta · FashionStore',
        loadComponent: () => import('./features/panel/panel').then((m) => m.Panel),
      },
      {
        // CU19 - Dashboard de Indicadores y KPIs Gerenciales
        path: 'dashboard',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Dashboard Gerencial')],
        title: 'Dashboard de Indicadores y KPIs · FashionStore',
        loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard),
      },
      {
        path: 'kpis',
        redirectTo: 'dashboard',
      },
      {
        // CU20 - Bitácora de Auditoría del Sistema (Trazabilidad Forense)
        path: 'bitacora',
        canActivate: [
          rolGuard([ROLES.ADMINISTRADOR], 'Bitácora de Auditoría', {
            permitirPlataforma: true,
          }),
        ],
        title: 'Bitácora de Auditoría · FashionStore',
        loadComponent: () => import('./features/bitacora/bitacora').then((m) => m.Bitacora),
      },
      {
        // CU03 - Administrar usuarios y asignar roles (exclusivo Administrador de Empresa)
        path: 'usuarios',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR], 'Usuarios y Roles')],
        title: 'Usuarios y Roles · FashionStore',
        loadComponent: () => import('./features/usuarios/usuarios').then((m) => m.Usuarios),
      },
      {
        // CU03 - Matriz de Roles y Permisos (RBAC granular, exclusivo Administrador de Empresa)
        path: 'roles-permisos',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR], 'Roles y Permisos')],
        title: 'Roles y Permisos · FashionStore',
        loadComponent: () =>
          import('./features/admin/roles-permisos/roles-permisos').then((m) => m.RolesPermisos),
      },
      {
        // CU05 - Gestión administrativa de clientes y autogestión de ficha propia
        path: 'clientes',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO, ROLES.CLIENTE],
            'Fichas de Clientes',
          ),
        ],
        title: 'Clientes · FashionStore',
        loadComponent: () => import('./features/clientes/clientes').then((m) => m.Clientes),
      },
      {
        // CU04 - Ciudades y sucursales (exclusivo Administrador de Empresa)
        path: 'sucursales',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR], 'Ciudades y Sucursales')],
        title: 'Ciudades y Sucursales · FashionStore',
        loadComponent: () => import('./features/sucursales/sucursales').then((m) => m.Sucursales),
      },
      {
        // CU06 - Categorías del catálogo comercial
        path: 'categorias',
        canActivate: [
          rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Categorías de Prendas'),
        ],
        title: 'Categorías · FashionStore',
        loadComponent: () => import('./features/categorias/categorias').then((m) => m.Categorias),
      },
      {
        // CU06 - Prendas, variantes y precios del catálogo comercial
        path: 'prendas',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Prendas del Catálogo')],
        title: 'Prendas · FashionStore',
        loadComponent: () => import('./features/prendas/prendas').then((m) => m.Prendas),
      },
      {
        // CU06 - Gestión de Temporadas y Colecciones
        path: 'temporadas',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Temporadas')],
        title: 'Temporadas y Colecciones · FashionStore',
        loadComponent: () => import('./features/temporadas/temporadas').then((m) => m.Temporadas),
      },
      {
        // CU08 - Consultar inventario y disponibilidad por sucursal
        path: 'inventario/monitoreo',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
            'Inventario y Disponibilidad',
          ),
        ],
        title: 'Inventario y Disponibilidad · FashionStore',
        loadComponent: () =>
          import('./features/inventario-monitoreo/inventario-monitoreo').then(
            (m) => m.InventarioMonitoreo,
          ),
      },
      {
        // CU08 - Alias alternativo
        path: 'monitoreo-inventario',
        redirectTo: 'inventario/monitoreo',
      },
      {
        // CU07 - Directorio de Proveedores
        path: 'proveedores',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Proveedores')],
        title: 'Proveedores · FashionStore',
        loadComponent: () =>
          import('./features/proveedores/proveedores').then((m) => m.Proveedores),
      },
      {
        // CU10 - Registrar movimientos y traspasos de inventario
        path: 'movimientos-inventario',
        canActivate: [
          rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Movimientos de Inventario'),
        ],
        title: 'Movimientos de Inventario · FashionStore',
        loadComponent: () =>
          import('./features/inventario-movimientos/movimientos').then((m) => m.Movimientos),
      },
      {
        // CU10 - Alias alternativo para concordancia exacta de URLs
        path: 'inventario/movimientos',
        redirectTo: 'movimientos-inventario',
      },
      {
        // CU07 - Historial de Compras
        path: 'compras',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Compras')],
        title: 'Compras · FashionStore',
        loadComponent: () => import('./features/compras/compras').then((m) => m.Compras),
      },
      {
        // CU07 - Formulario de Adquisición Transaccional
        path: 'compras/nueva',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Registro de Compras')],
        title: 'Nueva Compra · FashionStore',
        loadComponent: () =>
          import('./features/compras/compra-nueva/compra-nueva').then((m) => m.CompraNueva),
      },
      {
        // CU09 - Asistente y Recomendador Virtual de Moda con IA (Gemini)
        path: 'ia/asistente-moda',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO, ROLES.CLIENTE],
            'Asistente de Moda IA',
          ),
        ],
        title: 'Asistente de Moda IA · FashionStore',
        loadComponent: () =>
          import('./features/ia/asistente-moda/asistente-moda').then((m) => m.AsistenteModa),
      },
      {
        // CU09 - Alias de ruta
        path: 'ia/recomendador',
        redirectTo: 'ia/asistente-moda',
      },
      {
        // CU18 - Consultas Analíticas Ejecutivas por Voz con IA
        path: 'ia/analitica-voz',
        canActivate: [rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO], 'Analítica por Voz')],
        title: 'Analítica por Voz · FashionStore',
        loadComponent: () =>
          import('./features/ia/analitica-voz/analitica-voz').then((m) => m.AnaliticaVoz),
      },
      {
        // CU12 - Atención de Reservas en Sucursal y Probadores Físicos
        path: 'reservas-atencion',
        canActivate: [
          rolGuard(
            [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
            'Atención de Reservas',
          ),
        ],
        title: 'Atención de Reservas · FashionStore',
        loadComponent: () =>
          import('./features/reservas-atencion/reservas-atencion').then((m) => m.ReservasAtencion),
      },
      {
        path: 'reservas',
        redirectTo: 'reservas-atencion',
      },
      {
        // CU13 - Terminal POS de Ventas Presenciales y Caja
        path: 'pos',
        canActivate: [
          rolGuard([ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO], 'Terminal POS'),
        ],
        title: 'Terminal POS · FashionStore',
        loadComponent: () => import('./features/pos/pos').then((m) => m.Pos),
      },
      {
        path: 'caja',
        redirectTo: 'pos',
      },
    ],
  },
  {
    // CU14 - CatÃ¡logo pÃºblico. Vive FUERA del layout administrativo y sin
    // guardiÃ¡n de sesiÃ³n: un visitante puede explorar la vitrina antes de
    // autenticarse. El endpoint /api/catalogo no exige token.
    path: 'catalogo',
    canActivate: [tiendaGuard],
    title: 'CatÃ¡logo Â· FashionStore',
    loadComponent: () => import('./features/catalogo/catalogo').then((m) => m.Catalogo),
  },
  {
    // CU15 - Checkout Digital (carrito â†’ reserva â†’ pago â†’ comprobante)
    path: 'checkout',
    title: 'Checkout Â· FashionStore',
    loadComponent: () => import('./features/checkout/checkout').then((m) => m.Checkout),
  },
  {
    // CU20 - Retorno exitoso de Stripe
    path: 'pago/exitoso',
    title: 'Pago Confirmado Â· FashionStore',
    loadComponent: () =>
      import('./features/pago/pago-exitoso/pago-exitoso').then((m) => m.PagoExitoso),
  },
  {
    // CU20 - Retorno cancelado de Stripe
    path: 'pago/cancelado',
    title: 'Pago Cancelado Â· FashionStore',
    loadComponent: () =>
      import('./features/pago/pago-cancelado/pago-cancelado').then((m) => m.PagoCancelado),
  },
  {
    // CU15 - Historial de pedidos del cliente
    path: 'mi-cuenta/pedidos',
    canActivate:[authGuard],
    title: 'Mis Pedidos Â· FashionStore',
    loadComponent: () =>
      import('./features/cliente/mis-pedidos/mis-pedidos').then((m) => m.MisPedidos),
  },
  {
    // Cualquier ruta desconocida vuelve al inicio.
    path: '**',
    redirectTo: '',
  },
];

