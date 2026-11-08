/**
 * =============================================================================
 * FASHIONSTORE - PRUEBAS UNITARIAS: PROBADOR VIRTUAL IA (A6)
 * Componente: ProbadorIa (Decart AI Realtime WebRTC)
 * =============================================================================
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';

import { ProbadorIa } from './probador-ia';
import { IaService } from '../../../core/services/ia.service';
import { PrendaCatalogo } from '../../../core/models/catalogo.model';

describe('ProbadorIa Component (A6 Decart AI Realtime)', () => {
  let component: ProbadorIa;
  let fixture: ComponentFixture<ProbadorIa>;
  let mockIaService: jasmine.SpyObj<IaService>;
  let mockTrack: jasmine.SpyObj<MediaStreamTrack>;
  let mockMediaStream: MediaStream;
  let mockSession: {
    disconnect: jasmine.Spy;
    on: jasmine.Spy;
  };
  let eventCallbacks: Record<string, ((...args: unknown[]) => void)[]>;

  const mockPrenda: PrendaCatalogo = {
    id_prenda: 12,
    sku: 'VEST-GALA-01',
    nombre: 'Vestido Gala Seda Champagne',
    descripcion: 'Vestido largo de fiesta en satén de seda pura.',
    precio_base: 850.0,
    id_categoria: 1,
    categoria: 'Vestidos',
    genero: 'Femenino',
    marca: 'Atelier FashionStore',
    url_imagen: 'https://example.com/vestido-champagne.png',
    stock_total: 10,
    variantes: [
      {
        id_variante_prenda: 45,
        id_talla: 1,
        talla: 'S',
        id_color: 1,
        color: 'Champagne',
        codigo_hex: '#F7E7CE',
        precio: 850.0,
        stock_total: 4,
        disponibilidad: [
          {
            id_sucursal: 1,
            sucursal: 'Sucursal Central',
            direccion: 'Av. Monseñor Rivero 240',
            ciudad: 'Santa Cruz',
            stock: 4,
          },
        ],
      },
    ],
  };

  beforeEach(async () => {
    mockTrack = jasmine.createSpyObj<MediaStreamTrack>('MediaStreamTrack', ['stop']);
    mockMediaStream = new MediaStream();
    spyOn(mockMediaStream, 'getTracks').and.returnValue([mockTrack]);

    eventCallbacks = {};
    mockSession = {
      disconnect: jasmine.createSpy('disconnect'),
      on: jasmine.createSpy('on').and.callFake((event: string, cb: (...args: unknown[]) => void) => {
        if (!eventCallbacks[event]) {
          eventCallbacks[event] = [];
        }
        eventCallbacks[event].push(cb);
      }),
    };

    mockIaService = jasmine.createSpyObj<IaService>('IaService', ['obtenerRealtimeToken']);
    mockIaService.obtenerRealtimeToken.and.returnValue(
      of({ apiKey: 'mock-decart-token-primary', expiresAt: Date.now() + 3600000, usandoRespaldo: false }),
    );

    if (!navigator.mediaDevices) {
      (navigator as any).mediaDevices = {};
    }
    spyOn(navigator.mediaDevices, 'getUserMedia').and.returnValue(Promise.resolve(mockMediaStream));

    await TestBed.configureTestingModule({
      imports: [ProbadorIa],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: IaService, useValue: mockIaService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProbadorIa);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('prenda', mockPrenda);
    fixture.detectChanges();

    if (component.localVideo?.nativeElement) {
      Object.defineProperty(component.localVideo.nativeElement, 'readyState', {
        value: 2,
        configurable: true,
        writable: true,
      });
    }
  });

  afterEach(() => {
    component?.ngOnDestroy();
  });

  it('se inicializa en estado desconectado con señales limpias e input de prenda asignado', () => {
    expect(component).toBeTruthy();
    expect(component.conectado()).toBeFalse();
    expect(component.conectando()).toBeFalse();
    expect(component.error()).toBeNull();
    expect(component.prenda().id_prenda).toBe(12);
    expect(component.prenda().nombre).toBe('Vestido Gala Seda Champagne');
  });

  it('cerrar() detiene los tracks de MediaStream, desconecta la sesión y emite evento cerrado', () => {
    let eventoEmitido = false;
    component.cerrado.subscribe(() => {
      eventoEmitido = true;
    });

    (component as any).localStream = mockMediaStream;
    (component as any).rtClient = mockSession;

    component.cerrar();

    expect(mockTrack.stop).toHaveBeenCalled();
    expect(mockSession.disconnect).toHaveBeenCalled();
    expect(eventoEmitido).toBeTrue();
  });

  it('ngOnDestroy() invoca la limpieza y desconexión completa de recursos', () => {
    spyOn(component, 'cerrar').and.callThrough();
    component.ngOnDestroy();
    expect(component.cerrar).toHaveBeenCalled();
  });

  it('iniciarExperiencia() gestiona error cuando getUserMedia falla (permiso de cámara denegado)', async () => {
    (navigator.mediaDevices.getUserMedia as jasmine.Spy).and.returnValue(
      Promise.reject(new Error('Permission denied')),
    );

    await component.iniciarExperiencia();

    expect(component.conectado()).toBeFalse();
    expect(component.conectando()).toBeFalse();
    expect(component.error()).toBe('Permission denied');
  });

  it('iniciarExperiencia() gestiona error cuando la conexión falla', async () => {
    spyOn(component as any, 'conectar').and.returnValue(
      Promise.reject(new Error('Fallo al inicializar sesión WebRTC')),
    );

    await component.iniciarExperiencia();

    expect(component.conectado()).toBeFalse();
    expect(component.conectando()).toBeFalse();
    expect(component.error()).toBe('Fallo al inicializar sesión WebRTC');
  });

  it('iniciarExperiencia() conecta exitosamente la sesión WebRTC y actualiza señales', async () => {
    spyOn(component as any, 'conectar').and.callFake(async () => {
      (component as any).rtClient = mockSession;
    });

    await component.iniciarExperiencia();

    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
    expect((component as any).conectar).toHaveBeenCalledWith(false);
    expect(component.conectado()).toBeTrue();
    expect(component.conectando()).toBeFalse();
    expect(component.error()).toBeNull();
  });

  it('activa respaldo automáticamente cuando iniciarExperiencia detecta error de créditos (402/insufficient_credits)', async () => {
    let llamadas = 0;
    spyOn(component as any, 'conectar').and.callFake(async (useBackup: boolean) => {
      llamadas++;
      if (!useBackup) {
        const errorCreditos = { status: 402, message: 'insufficient_credits' };
        throw errorCreditos;
      }
      (component as any).rtClient = mockSession;
    });

    await component.iniciarExperiencia();

    expect(llamadas).toBe(2);
    expect((component as any).conectar).toHaveBeenCalledWith(false);
    expect((component as any).conectar).toHaveBeenCalledWith(true);
    expect(component.conectado()).toBeTrue();
    expect(component.conectando()).toBeFalse();
    expect(component.error()).toBeNull();
  });

  it('sesión activa activa respaldo al recibir evento sessionEnded con reason insufficient_credits', async () => {
    let llamadaRespaldo = false;
    spyOn(component as any, 'conectar').and.callFake(async (useBackup: boolean) => {
      if (useBackup) {
        llamadaRespaldo = true;
      }
      (component as any).rtClient = mockSession;
      mockSession.on('sessionEnded', ({ reason }: { reason: string }) => {
        if (reason === 'insufficient_credits') {
          void (component as any).activarRespaldo();
        }
      });
    });

    await component.iniciarExperiencia();
    expect(component.conectado()).toBeTrue();

    // Simular sessionEnded con insufficient_credits
    const sessionEndedCallbacks = eventCallbacks['sessionEnded'] || [];
    expect(sessionEndedCallbacks.length).toBeGreaterThan(0);

    sessionEndedCallbacks[0]({ reason: 'insufficient_credits' });
    fixture.detectChanges();

    expect((component as any).conectar).toHaveBeenCalledWith(true);
    expect(llamadaRespaldo).toBeTrue();
  });

  it('sesión activa gestiona desconexión inesperada informando indisponibilidad temporal', async () => {
    spyOn(component as any, 'conectar').and.callFake(async () => {
      (component as any).rtClient = mockSession;
      mockSession.on('sessionEnded', ({ reason }: { reason: string }) => {
        if (reason !== 'insufficient_credits' && !(component as any).finalizado) {
          component.conectado.set(false);
          component.error.set('El probador IA no está disponible temporalmente.');
        }
      });
    });

    await component.iniciarExperiencia();
    expect(component.conectado()).toBeTrue();

    const sessionEndedCallbacks = eventCallbacks['sessionEnded'] || [];
    expect(sessionEndedCallbacks.length).toBeGreaterThan(0);

    sessionEndedCallbacks[0]({ reason: 'server_closed' });
    fixture.detectChanges();

    expect(component.conectado()).toBeFalse();
    expect(component.error()).toBe('El probador IA no está disponible temporalmente.');
  });
});
