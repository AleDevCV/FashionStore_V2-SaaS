/**
 * =============================================================================
 * FASHIONSTORE - LAYOUT DEL PANEL ADMINISTRATIVO
 * Sistemas de Información II - UAGRM
 * -----------------------------------------------------------------------------
 * Contenedor base de todas las vistas internas: sidebar de navegación a la
 * izquierda, cabecera superior con los datos de sesión y un área central donde
 * el enrutador inyecta la vista activa.
 *
 * Incluye además el contenedor de notificaciones emergentes, que se renderiza
 * aquí para estar disponible en cualquier sección del panel.
 * =============================================================================
 */

import { Component, computed, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

import { AuthService } from '../core/services/auth.service';
import { NotificacionService } from '../core/services/notificacion.service';
import { ROLES } from '../core/models/auth.model';

/**
 * Opción hija dentro de un submenú desplegable.
 * Representa una pantalla específica dentro de un mismo Caso de Uso ICONIX,
 * sin repetir visualmente el código CU del grupo padre.
 */
export interface SubItemMenu {
  /** Texto visible de la funcionalidad concreta. */
  etiqueta: string;

  /** Ruta destino en el enrutador. */
  ruta: string;

  /** Roles autorizados a ver esta subopción; null para cualquier rol del ámbito. */
  roles: string[] | null;

  /** Ámbitos de cuenta (`tipo_cuenta`) donde esta subopción es válida. */
  ambitos?: Array<'PLATAFORMA' | 'PERSONAL' | 'CLIENTE'>;
}

/** Entrada del menú lateral alineada con los 20 casos de uso ICONIX (CU01–CU20). */
export interface ItemMenu {
  /** Texto visible del enlace directo o del encabezado de grupo desplegable. */
  etiqueta: string;

  /** Caso de uso consolidado (CU01 a CU20) mostrado una sola vez por ítem/grupo. */
  caso: string;

  /** Ruta destino si es un enlace directo; null cuando es un grupo desplegable. */
  ruta: string | null;

  /**
   * Roles autorizados a VER la entrada. Si es null, la ve cualquier usuario
   * del ámbito permitido.
   */
  roles: string[] | null;

  /**
   * Ámbitos de cuenta (`tipo_cuenta`) donde este ítem es válido:
   * - `'PLATAFORMA'`: SuperAdministrador SaaS (gobierno global de empresas y planes).
   * - `'PERSONAL'`: Personal interno de una empresa comercial (Admin, Encargado, Cajero).
   * - `'CLIENTE'`: Comprador final.
   */
  ambitos?: Array<'PLATAFORMA' | 'PERSONAL' | 'CLIENTE'>;

  /**
   * Submenú desplegable de pantallas que pertenecen al mismo caso de uso oficial.
   * Cuando está presente, el identificador `caso` se muestra únicamente en el
   * encabezado del grupo y los hijos listan las funcionalidades concretas.
   */
  hijos?: SubItemMenu[];
}

/** Agrupación funcional del menú lateral según las responsabilidades del actor. */
export interface SeccionMenu {
  titulo: string;
  items: ItemMenu[];
}

@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './layout.html',
  styleUrl: './layout.scss',
})
export class Layout {
  private readonly authService = inject(AuthService);
  private readonly notificacion = inject(NotificacionService);
  private readonly router = inject(Router);

  /** Datos del usuario autenticado, leídos del payload del JWT. */
  readonly usuario = this.authService.usuarioActual;

  /** Avisos emergentes activos. */
  readonly avisos = this.notificacion.avisos;

  /** URL activa del enrutador para identificar grupos con subrutas activas. */
  readonly urlActual = signal<string>(this.router.url || '');

  /**
   * Registro de grupos contraídos manualmente por el usuario (`clave -> true`).
   * Por defecto los grupos se presentan expandidos para facilitar el acceso
   * inmediato y permiten contraerse o expandirse con un clic.
   */
  private readonly gruposContraidos = signal<Record<string, boolean>>({});

  constructor() {
    this.router.events
      .pipe(filter((ev): ev is NavigationEnd => ev instanceof NavigationEnd))
      .subscribe((ev) => {
        const destino = ev.urlAfterRedirects || ev.url;
        this.urlActual.set(destino);
        this.expandirGrupoDeRutaActiva(destino);
      });
  }

  /** Indica si la sesión activa corresponde al SuperAdministrador SaaS (PLATAFORMA). */
  readonly esPlataforma = computed(() => this.usuario()?.tipo_cuenta === 'PLATAFORMA');

  /** Identificador (slug) de la empresa activa cuando pertenece a una tienda comercial. */
  readonly empresaActivaSlug = computed(() => {
    if (this.esPlataforma()) {
      return null;
    }
    return this.usuario()?.empresa_slug ?? null;
  });

  /** Subtítulo del logotipo en el sidebar según el espacio de trabajo. */
  readonly etiquetaSubtituloSidebar = computed(() => {
    const u = this.usuario();
    if (!u) return 'Panel administrativo';
    if (u.tipo_cuenta === 'PLATAFORMA') return 'Gobierno Plataforma SaaS';
    if (u.rol === ROLES.CLIENTE || u.tipo_cuenta === 'CLIENTE') return 'Espacio del Cliente';
    if (u.rol === ROLES.CAJERO) return 'Terminal y Atención';
    if (u.rol === ROLES.ENCARGADO) return 'Gestión de Sucursal';
    return 'Administración de Empresa';
  });

  /** Etiqueta contextual superior en la barra del espacio de trabajo. */
  readonly etiquetaEspacioTrabajo = computed(() => {
    const u = this.usuario();
    if (!u) return 'Sistema de gestión';
    if (u.tipo_cuenta === 'PLATAFORMA') {
      return 'Administración de Plataforma SaaS · Multi-Empresa';
    }
    if (u.rol === ROLES.CLIENTE || u.tipo_cuenta === 'CLIENTE') {
      return 'Portal del Cliente';
    }
    if (u.rol === ROLES.CAJERO) {
      return 'Operación de Tienda y Terminal POS';
    }
    if (u.rol === ROLES.ENCARGADO) {
      return 'Supervisión Operativa de Sucursal';
    }
    return 'Panel de Administración de Empresa';
  });

  /** Nombre del rol contextualizado para distinguir SuperAdmin SaaS de Admin de Empresa. */
  readonly etiquetaRolVisible = computed(() => {
    const u = this.usuario();
    if (!u) return '';
    if (u.tipo_cuenta === 'PLATAFORMA') {
      return 'SuperAdministrador SaaS';
    }
    if (u.rol === ROLES.ADMINISTRADOR) {
      return 'Administrador de Empresa';
    }
    return u.rol;
  });

  /**
   * Catálogo estructurado de secciones, grupos desplegables y enlaces directos
   * alineado con los 20 Casos de Uso consolidados del Segundo Examen Parcial
   * (CU01–CU20), sin duplicar identificadores CU dentro de un mismo perfil.
   */
  private readonly catalogoSecciones: SeccionMenu[] = [
    {
      titulo: 'Gobierno Plataforma SaaS',
      items: [
        {
          etiqueta: 'Empresas, Planes y Suscripciones',
          caso: 'CU02',
          ruta: '/panel/saas',
          roles: [ROLES.ADMINISTRADOR],
          ambitos: ['PLATAFORMA'],
        },
        {
          etiqueta: 'Bitácora de Plataforma',
          caso: 'CU20',
          ruta: '/panel/bitacora',
          roles: [ROLES.ADMINISTRADOR],
          ambitos: ['PLATAFORMA'],
        },
        {
          etiqueta: 'Sesión y Cuenta',
          caso: 'CU01',
          ruta: '/panel/inicio',
          roles: [ROLES.ADMINISTRADOR],
          ambitos: ['PLATAFORMA'],
        },
      ],
    },
    {
      titulo: 'Resumen y Analítica',
      items: [
        {
          etiqueta: 'Analítica inteligente',
          caso: 'CU19',
          ruta: null,
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
          ambitos: ['PERSONAL'],
          hijos: [
            {
              etiqueta: 'Dashboard de indicadores',
              ruta: '/panel/dashboard',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
            {
              etiqueta: 'Analítica y Machine Learning',
              ruta: '/panel/analitica',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
          ],
        },
        {
          etiqueta: 'Sesión y Cuenta',
          caso: 'CU01',
          ruta: '/panel/inicio',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
      ],
    },
    {
      titulo: 'Organización y Suscripción',
      items: [
        {
          etiqueta: 'Empresa y Suscripción',
          caso: 'CU02',
          ruta: '/panel/saas',
          roles: [ROLES.ADMINISTRADOR],
          ambitos: ['PERSONAL'],
        },
        {
          etiqueta: 'Personal, roles y permisos',
          caso: 'CU03',
          ruta: null,
          roles: [ROLES.ADMINISTRADOR],
          ambitos: ['PERSONAL'],
          hijos: [
            {
              etiqueta: 'Usuarios y Roles',
              ruta: '/panel/usuarios',
              roles: [ROLES.ADMINISTRADOR],
              ambitos: ['PERSONAL'],
            },
            {
              etiqueta: 'Roles y Permisos',
              ruta: '/panel/roles-permisos',
              roles: [ROLES.ADMINISTRADOR],
              ambitos: ['PERSONAL'],
            },
          ],
        },
        {
          etiqueta: 'Ciudades y Sucursales',
          caso: 'CU04',
          ruta: '/panel/sucursales',
          roles: [ROLES.ADMINISTRADOR],
          ambitos: ['PERSONAL'],
        },
      ],
    },
    {
      titulo: 'Catálogo Comercial',
      items: [
        {
          etiqueta: 'Catálogo de prendas',
          caso: 'CU06',
          ruta: null,
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
          ambitos: ['PERSONAL'],
          hijos: [
            {
              etiqueta: 'Categorías',
              ruta: '/panel/categorias',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
            {
              etiqueta: 'Temporadas y Colecciones',
              ruta: '/panel/temporadas',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
            {
              etiqueta: 'Prendas y Variantes',
              ruta: '/panel/prendas',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
          ],
        },
      ],
    },
    {
      titulo: 'Compras e Inventario',
      items: [
        {
          etiqueta: 'Proveedores y compras',
          caso: 'CU07',
          ruta: null,
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
          ambitos: ['PERSONAL'],
          hijos: [
            {
              etiqueta: 'Proveedores',
              ruta: '/panel/proveedores',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
            {
              etiqueta: 'Compras y Recepciones',
              ruta: '/panel/compras',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
          ],
        },
        {
          etiqueta: 'Inventario y Disponibilidad',
          caso: 'CU08',
          ruta: '/panel/inventario/monitoreo',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
        {
          etiqueta: 'Movimientos y Traspasos',
          caso: 'CU10',
          ruta: '/panel/movimientos-inventario',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
          ambitos: ['PERSONAL'],
        },
      ],
    },
    {
      titulo: 'Ventas, Caja y Postventa',
      items: [
        {
          etiqueta: 'Terminal POS (Caja)',
          caso: 'CU13',
          ruta: '/panel/pos',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
        {
          etiqueta: 'Atención de Reservas',
          caso: 'CU12',
          ruta: '/panel/reservas-atencion',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
        {
          etiqueta: 'Pagos y Entregas',
          caso: 'CU11',
          ruta: '/panel/pagos-control',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
        {
          etiqueta: 'Clientes',
          caso: 'CU05',
          ruta: '/panel/clientes',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
        {
          etiqueta: 'Cambios y Devoluciones',
          caso: 'CU15',
          ruta: '/panel/cambios',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
        {
          etiqueta: 'Operación sin Conexión',
          caso: 'CU16',
          ruta: '/offline',
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
        },
      ],
    },
    {
      titulo: 'Reportes, IA y Auditoría',
      items: [
        {
          etiqueta: 'Reportes comerciales',
          caso: 'CU18',
          ruta: null,
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
          ambitos: ['PERSONAL'],
          hijos: [
            {
              etiqueta: 'Reportes Comerciales e IA',
              ruta: '/panel/reportes',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
            {
              etiqueta: 'Analítica por Voz IA',
              ruta: '/panel/ia/analitica-voz',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO],
              ambitos: ['PERSONAL'],
            },
          ],
        },
        {
          etiqueta: 'Catálogo y asistencia de compra',
          caso: 'CU09',
          ruta: null,
          roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
          ambitos: ['PERSONAL'],
          hijos: [
            {
              etiqueta: 'Asistente de Moda IA',
              ruta: '/panel/ia/asistente-moda',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
              ambitos: ['PERSONAL'],
            },
            {
              etiqueta: 'Vitrina del Catálogo',
              ruta: '/catalogo',
              roles: [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
              ambitos: ['PERSONAL'],
            },
          ],
        },
        {
          etiqueta: 'Bitácora de Auditoría',
          caso: 'CU20',
          ruta: '/panel/bitacora',
          roles: [ROLES.ADMINISTRADOR],
          ambitos: ['PERSONAL'],
        },
      ],
    },
    {
      titulo: 'Mi Cuenta y Compras',
      items: [
        {
          etiqueta: 'Mi Ficha de Cliente',
          caso: 'CU05',
          ruta: '/panel/clientes',
          roles: [ROLES.CLIENTE],
          ambitos: ['CLIENTE'],
        },
        {
          etiqueta: 'Mis Pedidos y Comprobantes',
          caso: 'CU14',
          ruta: '/mi-cuenta/pedidos',
          roles: [ROLES.CLIENTE],
          ambitos: ['CLIENTE'],
        },
        {
          etiqueta: 'Cambios y Devoluciones',
          caso: 'CU15',
          ruta: '/panel/cambios',
          roles: [ROLES.CLIENTE],
          ambitos: ['CLIENTE'],
        },
        {
          etiqueta: 'Reserva sin Conexión',
          caso: 'CU16',
          ruta: '/offline',
          roles: [ROLES.CLIENTE],
          ambitos: ['CLIENTE'],
        },
        {
          etiqueta: 'Catálogo y asistencia de compra',
          caso: 'CU09',
          ruta: null,
          roles: [ROLES.CLIENTE],
          ambitos: ['CLIENTE'],
          hijos: [
            {
              etiqueta: 'Asistente de Moda IA',
              ruta: '/panel/ia/asistente-moda',
              roles: [ROLES.CLIENTE],
              ambitos: ['CLIENTE'],
            },
            {
              etiqueta: 'Vitrina del Catálogo',
              ruta: '/catalogo',
              roles: [ROLES.CLIENTE],
              ambitos: ['CLIENTE'],
            },
          ],
        },
        {
          etiqueta: 'Explorar Tiendas',
          caso: 'CU01',
          ruta: '/tiendas',
          roles: [ROLES.CLIENTE],
          ambitos: ['CLIENTE'],
        },
      ],
    },
  ];

  /**
   * Resuelve el ámbito efectivo de la sesión (`PLATAFORMA`, `CLIENTE` o `PERSONAL`).
   */
  private obtenerAmbitoActual(): 'PLATAFORMA' | 'PERSONAL' | 'CLIENTE' {
    const u = this.usuario();
    if (!u) return 'PERSONAL';
    if (u.tipo_cuenta === 'PLATAFORMA') return 'PLATAFORMA';
    if (u.tipo_cuenta === 'CLIENTE' || u.rol === ROLES.CLIENTE) return 'CLIENTE';
    return 'PERSONAL';
  }

  /**
   * Verifica si una entrada o subentrada está permitida para el ámbito y rol activos.
   */
  private esEntradaPermitida(
    entrada: { roles: string[] | null; ambitos?: Array<'PLATAFORMA' | 'PERSONAL' | 'CLIENTE'> },
    rol: string | null,
    ambito: 'PLATAFORMA' | 'PERSONAL' | 'CLIENTE',
  ): boolean {
    if (entrada.ambitos && !entrada.ambitos.includes(ambito)) {
      return false;
    }
    if (entrada.roles === null) {
      return true;
    }
    return rol !== null && entrada.roles.includes(rol);
  }

  /**
   * Secciones del menú filtradas según el tipo de cuenta (`tipo_cuenta`) y el
   * rol jerárquico (`rol`) del usuario autenticado.
   */
  readonly seccionesMenu = computed<SeccionMenu[]>(() => {
    const rol = this.usuario()?.rol ?? null;
    const ambito = this.obtenerAmbitoActual();

    return this.catalogoSecciones
      .map((seccion) => ({
        titulo: seccion.titulo,
        items: seccion.items
          .filter((item) => this.esEntradaPermitida(item, rol, ambito))
          .map((item) => {
            if (!item.hijos) {
              return item;
            }
            const hijosVisibles = item.hijos.filter((hijo) =>
              this.esEntradaPermitida(hijo, rol, ambito),
            );
            return {
              ...item,
              hijos: hijosVisibles,
            };
          })
          .filter((item) => !item.hijos || item.hijos.length > 0),
      }))
      .filter((seccion) => seccion.items.length > 0);
  });

  /**
   * Lista plana de todas las hojas navegables visibles para la sesión activa.
   * Cada subopción hereda el código `caso` de su grupo padre para facilitar
   * la trazabilidad programática de rutas por Caso de Uso ICONIX.
   */
  readonly menu = computed<ItemMenu[]>(() =>
    this.seccionesMenu().flatMap((seccion) =>
      seccion.items.flatMap((item) => {
        if (item.hijos && item.hijos.length > 0) {
          return item.hijos.map((hijo) => ({
            etiqueta: hijo.etiqueta,
            caso: item.caso,
            ruta: hijo.ruta,
            roles: hijo.roles,
            ambitos: hijo.ambitos,
          }));
        }
        return [item];
      }),
    ),
  );

  /**
   * Construye la clave única de un grupo desplegable.
   */
  claveGrupo(item: ItemMenu): string {
    return `${item.caso}:${item.etiqueta}`;
  }

  /**
   * Indica si un grupo desplegable se encuentra expandido.
   */
  estaGrupoAbierto(item: ItemMenu): boolean {
    const clave = this.claveGrupo(item);
    return !this.gruposContraidos()[clave];
  }

  /**
   * Expande o contrae un grupo desplegable del menú lateral.
   */
  alternarGrupo(item: ItemMenu): void {
    const clave = this.claveGrupo(item);
    this.gruposContraidos.update((actual) => ({
      ...actual,
      [clave]: !actual[clave],
    }));
  }

  /**
   * Determina si una ruta específica coincide con la URL activa del enrutador.
   */
  esRutaActiva(ruta: string | null): boolean {
    if (!ruta) return false;
    const actual = (this.urlActual() || this.router.url || '').split('?')[0].split('#')[0];
    return actual === ruta || actual.startsWith(`${ruta}/`);
  }

  /**
   * Determina si alguna de las opciones hijas de un grupo desplegable está activa.
   */
  tieneHijoActivo(item: ItemMenu): boolean {
    if (!item.hijos || item.hijos.length === 0) {
      return false;
    }
    return item.hijos.some((hijo) => this.esRutaActiva(hijo.ruta));
  }

  /**
   * Si el usuario navega hacia una subruta perteneciente a un grupo que estaba
   * contraído, lo expande automáticamente para mantener visible la ubicación.
   */
  private expandirGrupoDeRutaActiva(urlDestino: string): void {
    const limpia = urlDestino.split('?')[0].split('#')[0];
    for (const seccion of this.seccionesMenu()) {
      for (const item of seccion.items) {
        if (
          item.hijos &&
          item.hijos.some((h) => limpia === h.ruta || limpia.startsWith(`${h.ruta}/`))
        ) {
          const clave = this.claveGrupo(item);
          if (this.gruposContraidos()[clave]) {
            this.gruposContraidos.update((actual) => ({
              ...actual,
              [clave]: false,
            }));
          }
        }
      }
    }
  }

  /** Iniciales del usuario, mostradas en el distintivo circular de la cabecera. */
  readonly iniciales = computed(() => {
    const nombre = this.usuario()?.nombre ?? '';
    return nombre
      .split(' ')
      .filter((parte) => parte.length > 0)
      .slice(0, 2)
      .map((parte) => parte[0].toUpperCase())
      .join('');
  });

  /**
   * Cierra la sesión y devuelve al usuario a la pantalla de acceso.
   * Corresponde al paso 10 del flujo principal del CU01.
   *
   * @returns void
   */
  cerrarSesion(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  /**
   * Retira manualmente un aviso emergente.
   *
   * @param id Identificador del aviso.
   * @returns void
   */
  cerrarAviso(id: number): void {
    this.notificacion.cerrar(id);
  }
}
