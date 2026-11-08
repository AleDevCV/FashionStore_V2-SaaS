import { HttpClient } from '@angular/common/http';
import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from '../../core/services/auth.service';
import { CaseLink, USE_CASE_PACKAGES } from '../../layout/use-case-navigation';

interface Tienda {
  id_empresa: number;
  slug: string;
  nombre: string;
}

const descripcion: Record<string, string> = {
  CU01: 'Consulta tu sesión, revisa el contexto de acceso o solicita recuperar la contraseña.',
  CU02: 'Registra empresas y sus administradores iniciales. Configura planes, vigencias y cupos.',
  CU03: 'Gestiona al personal, sus sucursales y los permisos efectivos de cada rol.',
  CU04: 'Organiza ciudades y sucursales. Las altas y reactivaciones comprueban el cupo del plan.',
  CU05: 'Busca fichas comerciales y consulta su historial dentro de la empresa.',
  CU06: 'Edita la estructura del catálogo, variantes, precios y ofertas de prendas.',
  CU07: 'Mantén proveedores y registra compras con su recepción y entrada de inventario.',
  CU08: 'Consulta existencias físicas, unidades reservadas y disponibilidad por sucursal.',
  CU09: 'Explora la vitrina, sus filtros, variantes y vestidor. Consulta también el asistente de moda.',
  CU10: 'Registra entradas, salidas, ajustes y traspasos con motivo y trazabilidad.',
  CU11: 'Revisa el carrito y el pago en línea. Consulta los pagos y entregas desde la operación de tienda.',
  CU12: 'Solicita una reserva desde el carrito o atiende su preparación, entrega y cancelación.',
  CU13: 'Abre la caja, arma el ticket y registra el cobro de contado y el vuelto.',
  CU14: 'Busca comprobantes de ventas confirmadas y descarga el PDF autorizado.',
  CU15: 'Atiende cambios, recepción de prendas, reemplazos y diferencias o reembolsos.',
  CU16: 'Descarga el catálogo de una sucursal y guarda operaciones provisionales en el dispositivo.',
  CU17: 'Sincroniza los pendientes y revisa rechazos, conflictos y compensaciones.',
  CU18: 'Consulta reportes convencionales o generativos y revisa la consulta por voz.',
  CU19: 'Consulta indicadores, predicciones de demanda y segmentos con los modelos evaluados.',
  CU20: 'Revisa los eventos de plataforma o la bitácora operativa de una empresa.',
};

@Component({
  selector: 'app-casos-plataforma',
  templateUrl: './casos-plataforma.html',
  styleUrl: './casos-plataforma.scss',
})
export class CasosPlataforma {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);
  private readonly params = toSignal(this.route.paramMap, { requireSync: true });
  private readonly query = toSignal(this.route.queryParamMap, { requireSync: true });

  readonly paquete = computed(() => USE_CASE_PACKAGES.find(p => p.cases.some(c => c.id === this.params().get('id'))));
  readonly caso = computed(() => this.paquete()?.cases.find(c => c.id === this.params().get('id')));
  readonly resumen = computed(() => descripcion[this.caso()?.id ?? '']);
  readonly accionElegida = computed(() => (this.caso()?.links ?? [])[Number(this.query().get('accion')) - 1]);
  readonly tiendas = signal<Tienda[]>([]);
  readonly empresa = signal(this.auth.usuarioActual()?.platform_workspace
    ? this.auth.usuarioActual()?.empresa_slug ?? ''
    : sessionStorage.getItem('fashionstore_platform_workspace') ?? '');
  readonly ocupado = signal(false);
  readonly error = signal('');

  constructor() {
    this.http.get<Tienda[]>(environment.apiUrl + '/api/tiendas').subscribe({
      next: tiendas => this.tiendas.set(tiendas),
      error: () => this.error.set('No se pudo cargar la lista de empresas activas.'),
    });
    effect(() => {
      const accion = this.accionElegida();
      untracked(() => {
        if (accion && (!this.requiereEmpresa(accion) || this.empresa())) void this.abrir(accion);
      });
    });
  }

  private ambito(accion: CaseLink): NonNullable<CaseLink['scope']> {
    return accion.scope ?? (accion.audience === 'client' ? 'cliente' : accion.audience ? 'empresa' : 'global');
  }

  requiereEmpresa(accion: CaseLink): boolean {
    const ambito = this.ambito(accion);
    return ambito === 'empresa' || ambito === 'cliente';
  }

  elegirEmpresa(slug: string): void {
    this.empresa.set(slug);
    sessionStorage.setItem('fashionstore_platform_workspace', slug);
    this.error.set('');
  }

  async abrir(accion: CaseLink): Promise<void> {
    if (this.ocupado()) return;
    const ambito = this.ambito(accion);
    const slug = this.empresa();
    if (this.requiereEmpresa(accion) && !slug) {
      this.error.set('Elige una empresa para abrir esta interfaz.');
      return;
    }
    this.ocupado.set(true);
    this.error.set('');
    try {
      const usuario = this.auth.usuarioActual();
      if (ambito === 'global' && usuario?.platform_workspace) {
        await firstValueFrom(this.auth.abrirAmbitoPlataforma(null));
      } else if ((ambito === 'empresa' || ambito === 'cliente') &&
        (!usuario?.platform_workspace || usuario.empresa_slug !== slug ||
          (usuario.rol === 'Cliente') !== (ambito === 'cliente'))) {
        await firstValueFrom(this.auth.abrirAmbitoPlataforma(slug, ambito));
      }
      const queryParams = accion.path === '/catalogo' ? { empresa: slug } : accion.query;
      if (!await this.router.navigate([accion.path], { queryParams })) {
        this.error.set('No se pudo abrir la interfaz solicitada.');
      }
    } catch (error: unknown) {
      const detalle = (error as { error?: { detail?: unknown } }).error?.detail;
      this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo abrir el ámbito de la empresa.');
    } finally {
      this.ocupado.set(false);
    }
  }
}
