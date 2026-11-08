/**
 * =============================================================================
 * PRUEBAS DE ALINEACIÓN UI/UX Y NAVEGACIÓN POR ACTOR (CU01–CU20)
 * -----------------------------------------------------------------------------
 * Verifican que el Layout administrativo y el guardián rolGuard diferencien
 * estrictamente los espacios de trabajo según tipo_cuenta (PLATAFORMA,
 * PERSONAL, CLIENTE) y rol jerárquico, utilizando únicamente la numeración
 * oficial consolidada de los 20 casos de uso ICONIX (CU01 a CU20) sin
 * repetir visualmente el mismo código CU en el menú lateral.
 * =============================================================================
 */

import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, provideRouter } from '@angular/router';

import { Layout } from './layout';
import { AuthService } from '../core/services/auth.service';
import { NotificacionService } from '../core/services/notificacion.service';
import { PayloadJwt, ROLES } from '../core/models/auth.model';
import { rolGuard } from '../core/guards/rol.guard';

describe('Layout y rolGuard — Alineación UI/UX y Submenús sin Duplicados (CU01–CU20)', () => {
  let fixture: ComponentFixture<Layout>;
  let componente: Layout;
  const usuarioSignal = signal<PayloadJwt | null>(null);
  let authStub: Partial<AuthService>;
  let notificacionSpy: jasmine.SpyObj<NotificacionService>;

  beforeEach(async () => {
    usuarioSignal.set(null);

    authStub = {
      usuarioActual: usuarioSignal.asReadonly(),
      obtenerRol: () => usuarioSignal()?.rol ?? null,
      logout: jasmine.createSpy('logout'),
    };

    notificacionSpy = jasmine.createSpyObj<NotificacionService>(
      'NotificacionService',
      ['exito', 'error', 'aviso', 'cerrar'],
      { avisos: signal([]).asReadonly() },
    );

    await TestBed.configureTestingModule({
      imports: [Layout],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authStub },
        { provide: NotificacionService, useValue: notificacionSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Layout);
    componente = fixture.componentInstance;
  });

  function obtenerCodigosCuVisiblesEnDom(): string[] {
    const badges: NodeListOf<HTMLElement> =
      fixture.nativeElement.querySelectorAll('.admin__link-caso');
    return Array.from(badges)
      .map((el) => (el.textContent ?? '').trim())
      .filter((t) => t.length > 0);
  }

  it('separa el menú del SuperAdministrador SaaS (PLATAFORMA) de la operación interna de tienda', () => {
    usuarioSignal.set({
      id_usuario: 1,
      tenant_id: 1,
      sub: '1',
      correo: 'plataforma@fashionstore.com',
      nombre: 'Administración Plataforma',
      rol: ROLES.ADMINISTRADOR,
      tipo_cuenta: 'PLATAFORMA',
      exp: 9999999999,
      iat: 1700000000,
    });
    fixture.detectChanges();

    expect(componente.esPlataforma()).toBeTrue();
    expect(componente.etiquetaRolVisible()).toBe('SuperAdministrador SaaS');
    expect(componente.etiquetaEspacioTrabajo()).toContain('Plataforma SaaS');

    const rutas = componente.menu().map((i) => i.ruta);
    expect(rutas).toEqual(['/panel/saas', '/panel/bitacora', '/panel/inicio']);

    const codigosDom = obtenerCodigosCuVisiblesEnDom();
    expect(codigosDom).toEqual(['CU02', 'CU20', 'CU01']);
    expect(new Set(codigosDom).size).toBe(codigosDom.length);

    // Ningún módulo operativo de tienda debe aparecer en el sidebar de plataforma
    expect(rutas).not.toContain('/panel/pagos-control');
    expect(rutas).not.toContain('/panel/pos');
    expect(rutas).not.toContain('/panel/compras');
    expect(rutas).not.toContain('/panel/usuarios');
    expect(rutas).not.toContain('/panel/analitica');
    expect(rutas).not.toContain('/panel/reportes');
    expect(rutas).not.toContain('/offline');
  });

  it('muestra al Administrador de Empresa (PERSONAL) los módulos agrupados en submenús con códigos CU01–CU20 únicos en el sidebar', () => {
    usuarioSignal.set({
      id_usuario: 2,
      tenant_id: 2,
      sub: '2',
      correo: 'admin@demo-a.com',
      nombre: 'Ana Administradora',
      rol: ROLES.ADMINISTRADOR,
      tipo_cuenta: 'PERSONAL',
      empresa_slug: 'demo-a',
      exp: 9999999999,
      iat: 1700000000,
    });
    fixture.detectChanges();

    expect(componente.esPlataforma()).toBeFalse();
    expect(componente.etiquetaRolVisible()).toBe('Administrador de Empresa');
    expect(componente.empresaActivaSlug()).toBe('demo-a');
    expect(componente.seccionesMenu().length).toBe(6);

    // Verifica que en el DOM del sidebar cada código CU aparezca UNA SOLA VEZ (sin duplicados)
    const codigosDom = obtenerCodigosCuVisiblesEnDom();
    expect(codigosDom.length).toBe(18);
    expect(new Set(codigosDom).size).toBe(codigosDom.length);
    for (const codigo of codigosDom) {
      const numero = Number(codigo.replace('CU', ''));
      expect(numero).toBeGreaterThanOrEqual(1);
      expect(numero).toBeLessThanOrEqual(20);
    }
    expect(codigosDom).not.toContain('CU21');
    expect(codigosDom).not.toContain('CU22');
    expect(codigosDom).not.toContain('CU23');
    expect(codigosDom).not.toContain('CU24');
    expect(codigosDom).not.toContain('CU25');

    // Verifica que todas las rutas sigan disponibles y asociadas a su CU oficial
    const porRuta = new Map(componente.menu().map((i) => [i.ruta, i.caso]));
    expect(porRuta.get('/panel/inicio')).toBe('CU01');
    expect(porRuta.get('/panel/saas')).toBe('CU02');
    expect(porRuta.get('/panel/usuarios')).toBe('CU03');
    expect(porRuta.get('/panel/roles-permisos')).toBe('CU03');
    expect(porRuta.get('/panel/sucursales')).toBe('CU04');
    expect(porRuta.get('/panel/clientes')).toBe('CU05');
    expect(porRuta.get('/panel/categorias')).toBe('CU06');
    expect(porRuta.get('/panel/temporadas')).toBe('CU06');
    expect(porRuta.get('/panel/prendas')).toBe('CU06');
    expect(porRuta.get('/panel/proveedores')).toBe('CU07');
    expect(porRuta.get('/panel/compras')).toBe('CU07');
    expect(porRuta.get('/panel/inventario/monitoreo')).toBe('CU08');
    expect(porRuta.get('/panel/ia/asistente-moda')).toBe('CU09');
    expect(porRuta.get('/catalogo')).toBe('CU09');
    expect(porRuta.get('/panel/movimientos-inventario')).toBe('CU10');
    expect(porRuta.get('/panel/pagos-control')).toBe('CU11');
    expect(porRuta.get('/panel/reservas-atencion')).toBe('CU12');
    expect(porRuta.get('/panel/pos')).toBe('CU13');
    expect(porRuta.get('/panel/cambios')).toBe('CU15');
    expect(porRuta.get('/offline')).toBe('CU16');
    expect(porRuta.get('/panel/reportes')).toBe('CU18');
    expect(porRuta.get('/panel/ia/analitica-voz')).toBe('CU18');
    expect(porRuta.get('/panel/dashboard')).toBe('CU19');
    expect(porRuta.get('/panel/analitica')).toBe('CU19');
    expect(porRuta.get('/panel/bitacora')).toBe('CU20');
  });

  it('permite expandir y contraer los submenús desplegables y conserva identificada la página activa', () => {
    usuarioSignal.set({
      id_usuario: 2,
      tenant_id: 2,
      sub: '2',
      correo: 'admin@demo-a.com',
      nombre: 'Ana Administradora',
      rol: ROLES.ADMINISTRADOR,
      tipo_cuenta: 'PERSONAL',
      empresa_slug: 'demo-a',
      exp: 9999999999,
      iat: 1700000000,
    });
    fixture.detectChanges();

    const todosLosGrupos = componente
      .seccionesMenu()
      .flatMap((s) => s.items)
      .filter((i) => i.hijos && i.hijos.length > 0);

    // Deben existir los 6 grupos desplegables: CU19, CU03, CU06, CU07, CU18 y CU09
    expect(todosLosGrupos.map((g) => `${g.caso} — ${g.etiqueta}`)).toEqual([
      'CU19 — Analítica inteligente',
      'CU03 — Personal, roles y permisos',
      'CU06 — Catálogo de prendas',
      'CU07 — Proveedores y compras',
      'CU18 — Reportes comerciales',
      'CU09 — Catálogo y asistencia de compra',
    ]);

    const grupoCu03 = todosLosGrupos.find((g) => g.caso === 'CU03')!;
    expect(grupoCu03.hijos?.map((h) => h.etiqueta)).toEqual([
      'Usuarios y Roles',
      'Roles y Permisos',
    ]);
    expect(componente.estaGrupoAbierto(grupoCu03)).toBeTrue();

    // Verifica que el botón DOM muestre ▼ cuando está expandido y aria-expanded="true"
    const botonesToggle: NodeListOf<HTMLButtonElement> =
      fixture.nativeElement.querySelectorAll('.admin__group-toggle');
    expect(botonesToggle.length).toBe(6);
    expect(botonesToggle[0].getAttribute('aria-expanded')).toBe('true');
    expect(botonesToggle[0].querySelector('.admin__group-chevron')?.textContent?.trim()).toBe('▼');

    // Las opciones hijas en el DOM no deben contener badges .admin__link-caso repetidos
    const sublinksCu03: NodeListOf<HTMLElement> = fixture.nativeElement.querySelectorAll(
      '.admin__sublink .admin__link-caso',
    );
    expect(sublinksCu03.length).toBe(0);

    // Contraer el grupo haciendo clic real en su botón de encabezado
    botonesToggle[1].click();
    fixture.detectChanges();
    expect(componente.estaGrupoAbierto(grupoCu03)).toBeFalse();
    expect(botonesToggle[1].getAttribute('aria-expanded')).toBe('false');
    expect(botonesToggle[1].querySelector('.admin__group-chevron')?.textContent?.trim()).toBe('▶');

    // Si la URL activa pasa a ser /panel/roles-permisos, el grupo identifica su hijo activo
    componente.urlActual.set('/panel/roles-permisos');
    expect(componente.tieneHijoActivo(grupoCu03)).toBeTrue();

    // Volver a expandir el grupo CU03 con clic
    botonesToggle[1].click();
    fixture.detectChanges();
    expect(componente.estaGrupoAbierto(grupoCu03)).toBeTrue();
    expect(botonesToggle[1].getAttribute('aria-expanded')).toBe('true');
    expect(botonesToggle[1].querySelector('.admin__group-chevron')?.textContent?.trim()).toBe('▼');
  });

  it('habilita al Cajero (POS) sus vistas operativas (CU01, CU05, CU08, CU09, CU11, CU12, CU13, CU15, CU16) sin duplicar códigos CU', () => {
    usuarioSignal.set({
      id_usuario: 4,
      tenant_id: 2,
      sub: '4',
      correo: 'cajero@demo-a.com',
      nombre: 'Carlos Cajero',
      rol: ROLES.CAJERO,
      tipo_cuenta: 'PERSONAL',
      empresa_slug: 'demo-a',
      exp: 9999999999,
      iat: 1700000000,
    });
    fixture.detectChanges();

    const rutas = componente.menu().map((i) => i.ruta);
    expect(rutas).toContain('/panel/pos');
    expect(rutas).toContain('/panel/reservas-atencion');
    expect(rutas).toContain('/panel/pagos-control');
    expect(rutas).toContain('/panel/clientes');
    expect(rutas).toContain('/panel/cambios');
    expect(rutas).toContain('/panel/inventario/monitoreo');
    expect(rutas).toContain('/offline');

    expect(rutas).not.toContain('/panel/saas');
    expect(rutas).not.toContain('/panel/usuarios');
    expect(rutas).not.toContain('/panel/roles-permisos');
    expect(rutas).not.toContain('/panel/reportes');
    expect(rutas).not.toContain('/panel/analitica');
    expect(rutas).not.toContain('/panel/compras');

    const codigosDom = obtenerCodigosCuVisiblesEnDom();
    expect(new Set(codigosDom).size).toBe(codigosDom.length);
  });

  it('restringe al Encargado de Sucursal las vistas de gobierno de plataforma y usuarios/roles de empresa sin duplicar códigos CU', () => {
    usuarioSignal.set({
      id_usuario: 3,
      tenant_id: 2,
      sub: '3',
      correo: 'encargado@demo-a.com',
      nombre: 'Elena Encargada',
      rol: ROLES.ENCARGADO,
      tipo_cuenta: 'PERSONAL',
      empresa_slug: 'demo-a',
      exp: 9999999999,
      iat: 1700000000,
    });
    fixture.detectChanges();

    const rutas = componente.menu().map((i) => i.ruta);
    expect(rutas).toContain('/panel/dashboard');
    expect(rutas).toContain('/panel/reportes');
    expect(rutas).toContain('/panel/analitica');
    expect(rutas).toContain('/panel/movimientos-inventario');
    expect(rutas).not.toContain('/panel/saas');
    expect(rutas).not.toContain('/panel/usuarios');
    expect(rutas).not.toContain('/panel/roles-permisos');
    expect(rutas).not.toContain('/panel/sucursales');
    expect(rutas).not.toContain('/panel/bitacora');

    const codigosDom = obtenerCodigosCuVisiblesEnDom();
    expect(new Set(codigosDom).size).toBe(codigosDom.length);
  });

  it('muestra al Cliente únicamente opciones de su cuenta, pedidos, cambios y catálogo sin duplicar códigos CU', () => {
    usuarioSignal.set({
      id_usuario: 9,
      tenant_id: 0,
      sub: '9',
      correo: 'cliente@correo.com',
      nombre: 'Claudia Cliente',
      rol: ROLES.CLIENTE,
      tipo_cuenta: 'CLIENTE',
      exp: 9999999999,
      iat: 1700000000,
    });
    fixture.detectChanges();

    const rutas = componente.menu().map((i) => i.ruta);
    expect(rutas).toEqual([
      '/panel/clientes',
      '/mi-cuenta/pedidos',
      '/panel/cambios',
      '/offline',
      '/panel/ia/asistente-moda',
      '/catalogo',
      '/tiendas',
    ]);

    const codigosDom = obtenerCodigosCuVisiblesEnDom();
    expect(codigosDom).toEqual(['CU05', 'CU14', 'CU15', 'CU16', 'CU09', 'CU01']);
    expect(new Set(codigosDom).size).toBe(codigosDom.length);
  });

  it('rolGuard redirige al SuperAdministrador SaaS (PLATAFORMA) a /panel/saas si intenta abrir /panel/pagos-control', () => {
    const router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);

    usuarioSignal.set({
      id_usuario: 1,
      tenant_id: 1,
      sub: '1',
      correo: 'plataforma@fashionstore.com',
      nombre: 'Administración Plataforma',
      rol: ROLES.ADMINISTRADOR,
      tipo_cuenta: 'PLATAFORMA',
      exp: 9999999999,
      iat: 1700000000,
    });

    const guard = rolGuard(
      [ROLES.ADMINISTRADOR, ROLES.ENCARGADO, ROLES.CAJERO],
      'Pagos y entregas',
    );
    const resultado = TestBed.runInInjectionContext(() =>
      guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );

    expect(resultado).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/panel/saas']);
    expect(notificacionSpy.aviso).toHaveBeenCalled();
  });

  it('rolGuard permite al SuperAdministrador SaaS (PLATAFORMA) acceder a /panel/saas cuando permitirPlataforma es true', () => {
    usuarioSignal.set({
      id_usuario: 1,
      tenant_id: 1,
      sub: '1',
      correo: 'plataforma@fashionstore.com',
      nombre: 'Administración Plataforma',
      rol: ROLES.ADMINISTRADOR,
      tipo_cuenta: 'PLATAFORMA',
      exp: 9999999999,
      iat: 1700000000,
    });

    const guard = rolGuard([ROLES.ADMINISTRADOR], 'Empresas, Planes y Suscripciones', {
      permitirPlataforma: true,
    });
    const resultado = TestBed.runInInjectionContext(() =>
      guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );

    expect(resultado).toBeTrue();
  });
});
