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
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../core/services/auth.service';
import { NotificacionService } from '../core/services/notificacion.service';
import { ROLES } from '../core/models/auth.model';

import { USE_CASE_PACKAGES } from './use-case-navigation';

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

  readonly posicionPaquete = signal({ top: 0, left: 0 });
  readonly paqueteFijado = signal<string | null>(null);
  readonly paqueteBajoPuntero = signal<string | null>(null);
  readonly paqueteAbierto = computed(() => this.paqueteBajoPuntero() ?? this.paqueteFijado());

  readonly paquetes = computed(() => {
    const usuario = this.usuario();
    if (!usuario) return [];
    const plataforma = usuario.tipo_cuenta === 'PLATAFORMA';
    const cliente = usuario.tipo_cuenta === 'CLIENTE' || usuario.rol === ROLES.CLIENTE;
    return USE_CASE_PACKAGES.map(paquete => ({
      ...paquete,
      cases: paquete.cases.map(caso => ({
        ...caso,
        actions: (caso.links ?? []).filter(link => {
          if (link.roles && !link.roles.includes(usuario.rol)) return false;
          if (link.audience === 'staff') return !plataforma && !cliente;
          if (link.audience === 'client') return cliente;
          if (link.audience === 'store') return !plataforma;
          return true;
        }),
      })).filter(caso => plataforma || caso.id === 'CU01' || caso.actions.length > 0),
    })).filter(paquete => paquete.cases.length > 0);
  });

  previsualizarPaquete(id: string, event: PointerEvent): void {
    if (event.pointerType !== 'mouse') return;
    const trigger = (event.currentTarget as HTMLElement).querySelector('button');
    if (!trigger) return;
    this.ubicarPaquete(trigger);
    if (this.paqueteFijado() !== id) this.paqueteFijado.set(null);
    this.paqueteBajoPuntero.set(id);
  }

  private ubicarPaquete(trigger: HTMLButtonElement): void {
    const { top, right } = trigger.getBoundingClientRect();
    this.posicionPaquete.set({ top, left: right - 1 });
  }

  retirarPrevisualizacion(event: PointerEvent): void {
    if (event.pointerType !== 'mouse') return;
    const grupo = event.currentTarget as HTMLElement;
    if (this.paqueteBajoPuntero() && grupo.contains(document.activeElement) &&
        document.activeElement !== grupo.firstElementChild) {
      this.paqueteFijado.set(this.paqueteBajoPuntero());
    }
    this.paqueteBajoPuntero.set(null);
  }

  alternarPaquete(id: string, trigger: HTMLButtonElement): void {
    this.ubicarPaquete(trigger);
    this.paqueteBajoPuntero.set(null);
    this.paqueteFijado.update(actual => actual === id ? null : id);
  }

  cerrarPaquete(trigger: HTMLButtonElement, event: Event): void {
    event.stopPropagation();
    this.paqueteBajoPuntero.set(null);
    this.paqueteFijado.set(null);
    trigger.focus();
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
