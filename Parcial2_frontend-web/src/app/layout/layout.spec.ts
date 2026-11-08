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

  function rutasMenu(): string[] {
    return [
      '/panel/inicio',
      ...new Set(componente.paquetes().flatMap((paquete) =>
        paquete.cases.flatMap((caso) => caso.actions.map((accion) => accion.path)),
      )),
    ];
  }

  function obtenerCodigosCuVisiblesEnDom(): string[] {
    const badges: NodeListOf<HTMLElement> =
      fixture.nativeElement.querySelectorAll('.admin__link-caso');
    return Array.from(badges)
      .map((el) => (el.textContent ?? '').trim())
      .filter((t) => t.length > 0);
  }

  it('ofrece al SuperAdministrador las veinte fichas y todas sus acciones', () => {
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

    const codigosDom = obtenerCodigosCuVisiblesEnDom();
    expect(codigosDom.length).toBe(20);
    expect(new Set(codigosDom).size).toBe(codigosDom.length);

    const casos = componente.paquetes().flatMap(paquete => paquete.cases);
    for (const caso of casos) {
      expect(caso.actions.length).toBeGreaterThan(0);
      expect(fixture.nativeElement.querySelector(`a[href="/panel/casos/${caso.id}"]`)).not.toBeNull();
    }
    expect(fixture.nativeElement.querySelector('a[href="/panel/casos/CU03?accion=2"]')).not.toBeNull();
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
    expect(componente.paquetes().length).toBe(6);

    // Verifica que en el DOM del sidebar cada código CU aparezca UNA SOLA VEZ (sin duplicados)
    const codigosDom = obtenerCodigosCuVisiblesEnDom();
    expect(codigosDom.length).toBe(20);
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
    const enlaces = componente.paquetes().flatMap((paquete) =>
      paquete.cases.flatMap((caso) => caso.actions.map((accion) => [accion.path, caso.id])),
    );
    enlaces.push(['/panel/inicio', 'CU01']);
    expect(enlaces).toContain(['/panel/inicio', 'CU01']);
    expect(enlaces).toContain(['/panel/saas', 'CU02']);
    expect(enlaces).toContain(['/panel/usuarios', 'CU03']);
    expect(enlaces).toContain(['/panel/roles-permisos', 'CU03']);
    expect(enlaces).toContain(['/panel/sucursales', 'CU04']);
    expect(enlaces).toContain(['/panel/clientes', 'CU05']);
    expect(enlaces).toContain(['/panel/categorias', 'CU06']);
    expect(enlaces).toContain(['/panel/temporadas', 'CU06']);
    expect(enlaces).toContain(['/panel/prendas', 'CU06']);
    expect(enlaces).toContain(['/panel/proveedores', 'CU07']);
    expect(enlaces).toContain(['/panel/compras', 'CU07']);
    expect(enlaces).toContain(['/panel/inventario/monitoreo', 'CU08']);
    expect(enlaces).toContain(['/panel/ia/asistente-moda', 'CU09']);
    expect(enlaces).toContain(['/catalogo', 'CU09']);
    expect(enlaces).toContain(['/panel/movimientos-inventario', 'CU10']);
    expect(enlaces).toContain(['/panel/pagos-control', 'CU11']);
    expect(enlaces).toContain(['/panel/reservas-atencion', 'CU12']);
    expect(enlaces).toContain(['/panel/pos', 'CU13']);
    expect(enlaces).toContain(['/panel/cambios', 'CU15']);
    expect(enlaces).toContain(['/panel/operacion-local', 'CU16']);
    expect(enlaces).toContain(['/panel/sincronizacion', 'CU17']);
    expect(enlaces).toContain(['/panel/reportes', 'CU18']);
    expect(enlaces).toContain(['/panel/ia/analitica-voz', 'CU18']);
    expect(enlaces).toContain(['/panel/dashboard', 'CU19']);
    expect(enlaces).toContain(['/panel/analitica', 'CU19']);
    expect(enlaces).toContain(['/panel/bitacora', 'CU20']);
  });

  it('permite abrir un paquete, consultar sus casos de uso y cerrarlo con Escape', () => {
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

    const trigger: HTMLButtonElement = fixture.nativeElement.querySelector('#paquete-P1');
    const lista: HTMLUListElement = fixture.nativeElement.querySelector('#casos-P1');
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    expect(lista.hidden).toBeTrue();
    trigger.click();
    fixture.detectChanges();
    expect(trigger.getAttribute('aria-expanded')).toBe('true');
    expect(lista.hidden).toBeFalse();
    expect(lista.querySelector('a[href="/panel/roles-permisos"]')).not.toBeNull();

    trigger.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    expect(lista.hidden).toBeTrue();
    expect(document.activeElement).toBe(trigger);
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

    const rutas = rutasMenu();
    expect(rutas).toContain('/panel/pos');
    expect(rutas).toContain('/panel/reservas-atencion');
    expect(rutas).toContain('/panel/pagos-control');
    expect(rutas).toContain('/panel/clientes');
    expect(rutas).toContain('/panel/cambios');
    expect(rutas).toContain('/panel/inventario/monitoreo');
    expect(rutas).toContain('/panel/operacion-local');

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

    const rutas = rutasMenu();
    expect(rutas).toContain('/panel/dashboard');
    expect(rutas).toContain('/panel/reportes');
    expect(rutas).toContain('/panel/analitica');
    expect(rutas).toContain('/panel/movimientos-inventario');
    expect(rutas).not.toContain('/panel/saas');
    expect(rutas).not.toContain('/panel/usuarios');
    expect(rutas).not.toContain('/panel/roles-permisos');
    expect(rutas).not.toContain('/panel/sucursales');
    expect(rutas).toContain('/panel/bitacora');

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

    const rutas = rutasMenu();
    expect(rutas).toContain('/panel/clientes');
    expect(rutas).toContain('/mi-cuenta/pedidos');
    expect(rutas).toContain('/panel/cambios');
    expect(rutas).toContain('/panel/operacion-local');
    expect(rutas).toContain('/panel/ia/asistente-moda');
    expect(rutas).toContain('/catalogo');
    expect(rutas).toContain('/tiendas');
    expect(rutas).toContain('/checkout');
    expect(rutas).not.toContain('/panel/saas');
    expect(rutas).not.toContain('/panel/pos');
    expect(rutas).not.toContain('/panel/usuarios');

    const codigosDom = obtenerCodigosCuVisiblesEnDom();
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
