/**
 * =============================================================================
 * PRUEBAS DE ATENCIÓN DE RESERVAS EN SUCURSAL Y SERVICIO DE VENTAS (CU12)
 * Sistemas de Información II - UAGRM
 * -----------------------------------------------------------------------------
 * Verifica que las consultas a /api/ventas/reservas-probador no serialicen
 * valores undefined, null ni cadenas vacías en HttpParams (evitando errores
 * HTTP 422 en FastAPI) y cubre los 8 escenarios obligatorios de filtrado,
 * respuesta vacía y manejo de errores de autorización y servidor.
 * =============================================================================
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';

import { ReservasAtencion } from './reservas-atencion';
import { VentaService } from '../../core/services/venta.service';
import { ReservaSucursalItem } from '../../core/models/venta.model';

describe('ReservasAtencion y VentaService — Filtros HttpParams (CU12)', () => {
  let fixture: ComponentFixture<ReservasAtencion>;
  let componente: ReservasAtencion;
  let httpMock: HttpTestingController;
  let ventaService: VentaService;

  const sucursalesMock = [
    {
      id_sucursal: 1,
      nombre: 'Central',
      direccion: 'Av. Principal 100',
      telefono: '33300011',
      estado: 'Activo' as const,
      id_ciudad: 1,
      ciudad: 'Santa Cruz de la Sierra',
    },
    {
      id_sucursal: 2,
      nombre: 'Norte',
      direccion: 'Av. Banzer 400',
      telefono: '33300022',
      estado: 'Activo' as const,
      id_ciudad: 1,
      ciudad: 'Santa Cruz de la Sierra',
    },
  ];

  const reservaMock: ReservaSucursalItem = {
    id_reserva: 105,
    id_cliente: 3,
    cliente_nombre: 'Cliente Demo',
    cliente_telefono: '70000000',
    id_sucursal: 1,
    sucursal_nombre: 'Central',
    fecha_reserva: '2026-11-08T00:00:00Z',
    fecha_limite: '2026-11-08T02:00:00Z',
    estado: 'Pendiente',
    total: 150,
    total_prendas: 1,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReservasAtencion],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(ReservasAtencion);
    componente = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    ventaService = TestBed.inject(VentaService);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function responderCargaInicial(reservas: ReservaSucursalItem[] = [reservaMock]): void {
    fixture.detectChanges();

    const reqSucursales = httpMock.expectOne(
      (r) => r.url.endsWith('/api/sucursales') && r.method === 'GET',
    );
    reqSucursales.flush(sucursalesMock);

    const reqReservas = httpMock.expectOne(
      (r) => r.url.endsWith('/api/ventas/reservas-probador/') && r.method === 'GET',
    );
    expect(reqReservas.request.params.keys()).toEqual([]);
    expect(reqReservas.request.urlWithParams).not.toContain('undefined');
    expect(reqReservas.request.urlWithParams).not.toContain('null');
    reqReservas.flush(reservas);
  }

  it('1. realiza la consulta inicial sin filtros sin enviar id_sucursal=undefined ni estado=undefined', () => {
    responderCargaInicial([reservaMock]);

    expect(componente.cargando()).toBeFalse();
    expect(componente.error()).toBeNull();
    expect(componente.reservas().length).toBe(1);
    expect(componente.reservas()[0].id_reserva).toBe(105);
  });

  it('2. realiza la consulta enviando únicamente id_sucursal cuando se selecciona una sucursal válida', () => {
    responderCargaInicial([reservaMock]);

    const evento = { target: { value: '1' } } as unknown as Event;
    componente.cambiarSucursal(evento);

    const req = httpMock.expectOne(
      (r) => r.url.endsWith('/api/ventas/reservas-probador/') && r.method === 'GET',
    );
    expect(req.request.params.keys()).toEqual(['id_sucursal']);
    expect(req.request.params.get('id_sucursal')).toBe('1');
    expect(req.request.params.has('estado')).toBeFalse();
    expect(req.request.urlWithParams).toBe('/api/ventas/reservas-probador/?id_sucursal=1');
    req.flush([reservaMock]);

    expect(componente.idSucursalSeleccionada()).toBe(1);
    expect(componente.reservas().length).toBe(1);
  });

  it('3. realiza la consulta enviando únicamente estado cuando se selecciona un estado válido', () => {
    responderCargaInicial([reservaMock]);

    componente.cambiarFiltroEstado('Pendiente');

    const req = httpMock.expectOne(
      (r) => r.url.endsWith('/api/ventas/reservas-probador/') && r.method === 'GET',
    );
    expect(req.request.params.keys()).toEqual(['estado']);
    expect(req.request.params.get('estado')).toBe('Pendiente');
    expect(req.request.params.has('id_sucursal')).toBeFalse();
    expect(req.request.urlWithParams).toBe('/api/ventas/reservas-probador/?estado=Pendiente');
    req.flush([reservaMock]);

    expect(componente.filtroEstado()).toBe('Pendiente');
  });

  it('4. envía ambos filtros (id_sucursal y estado) y al volver a «Todos» omite estado conservando la sucursal', () => {
    responderCargaInicial([reservaMock]);

    componente.idSucursalSeleccionada.set(2);
    componente.cambiarFiltroEstado('Preparado');

    const reqAmbos = httpMock.expectOne(
      (r) => r.url.endsWith('/api/ventas/reservas-probador/') && r.method === 'GET',
    );
    expect(reqAmbos.request.params.get('id_sucursal')).toBe('2');
    expect(reqAmbos.request.params.get('estado')).toBe('Preparado');
    expect(reqAmbos.request.urlWithParams).toBe(
      '/api/ventas/reservas-probador/?id_sucursal=2&estado=Preparado',
    );
    reqAmbos.flush([{ ...reservaMock, id_sucursal: 2, estado: 'Preparado' }]);

    // Al seleccionar «Todos», debe recuperar el listado de la sucursal sin enviar estado=Todos ni undefined
    componente.cambiarFiltroEstado('Todos');

    const reqTodos = httpMock.expectOne(
      (r) => r.url.endsWith('/api/ventas/reservas-probador/') && r.method === 'GET',
    );
    expect(reqTodos.request.params.keys()).toEqual(['id_sucursal']);
    expect(reqTodos.request.params.get('id_sucursal')).toBe('2');
    expect(reqTodos.request.params.has('estado')).toBeFalse();
    reqTodos.flush([{ ...reservaMock, id_sucursal: 2 }]);

    // Y VentaService ignora cadenas vacías o nulos directos
    ventaService
      .listarReservasSucursal({ id_sucursal: null, estado: '   ' })
      .subscribe();
    const reqLimpio = httpMock.expectOne(
      (r) => r.url.endsWith('/api/ventas/reservas-probador/') && r.method === 'GET',
    );
    expect(reqLimpio.request.params.keys()).toEqual([]);
    reqLimpio.flush([]);
  });

  it('5. maneja correctamente una respuesta vacía mostrando el estado sin reservas', () => {
    responderCargaInicial([]);
    fixture.detectChanges();

    expect(componente.reservas()).toEqual([]);
    expect(componente.error()).toBeNull();
    const vacioTexto = fixture.nativeElement.querySelector('.atencion-reservas__vacio')?.textContent;
    expect(vacioTexto).toContain('No se encontraron reservas con los filtros seleccionados.');
  });

  it('6. maneja el error 403 cuando un usuario no tiene permiso para consultar reservas', () => {
    fixture.detectChanges();

    httpMock
      .expectOne((r) => r.url.endsWith('/api/sucursales'))
      .flush([]);

    const req = httpMock.expectOne((r) => r.url.endsWith('/api/ventas/reservas-probador/'));
    req.flush(
      { detail: 'No tiene permiso para esta operación.' },
      { status: 403, statusText: 'Forbidden' },
    );

    expect(componente.cargando()).toBeFalse();
    expect(componente.reservas()).toEqual([]);
    expect(componente.error()).toBe('No tiene permiso para esta operación.');
  });

  it('7. maneja el rechazo por sucursal no autorizada preservando el mensaje de aislamiento', () => {
    responderCargaInicial([]);

    const evento = { target: { value: '99' } } as unknown as Event;
    componente.cambiarSucursal(evento);

    const req = httpMock.expectOne((r) => r.url.endsWith('/api/ventas/reservas-probador/'));
    expect(req.request.params.get('id_sucursal')).toBe('99');
    req.flush(
      { detail: 'Sucursal no autorizada para este usuario.' },
      { status: 403, statusText: 'Forbidden' },
    );

    expect(componente.cargando()).toBeFalse();
    expect(componente.error()).toBe('Sucursal no autorizada para este usuario.');
  });

  it('8. maneja errores 500 del servidor informando el fallo sin bloquear la pantalla', () => {
    responderCargaInicial([reservaMock]);

    componente.cambiarFiltroEstado('Atendido');

    const req = httpMock.expectOne((r) => r.url.endsWith('/api/ventas/reservas-probador/'));
    req.flush(
      { detail: 'Error interno al consultar las reservas de sucursal' },
      { status: 500, statusText: 'Internal Server Error' },
    );

    expect(componente.cargando()).toBeFalse();
    expect(componente.error()).toBe('Error interno al consultar las reservas de sucursal');
  });
});
