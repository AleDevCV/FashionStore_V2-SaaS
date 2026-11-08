/**
 * =============================================================================
 * FASHIONSTORE - GUARDIÁN DE AUTORIZACIÓN POR ROL (RBAC EN EL FRONTEND)
 * -----------------------------------------------------------------------------
 * Impide que un usuario autenticado alcance una sección para la que no tiene
 * privilegios, incluso si escribe la URL directamente en el navegador.
 *
 * IMPORTANTE — ESTE GUARDIÁN NO ES UNA MEDIDA DE SEGURIDAD REAL:
 * el código de Angular vive en el navegador y cualquiera puede manipularlo. La
 * autorización que de verdad protege los datos es la del backend, donde
 * `requiere_rol(["Administrador"])` responde 403 a toda petición no autorizada.
 * Lo que aporta este guardián es EXPERIENCIA DE USUARIO: evita mostrar una
 * pantalla vacía que acabaría fallando con un error del servidor.
 * =============================================================================
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';
import { NotificacionService } from '../services/notificacion.service';

export interface OpcionesRolGuard {
  /**
   * Indica si una cuenta global de tipo PLATAFORMA (SuperAdministrador SaaS)
   * puede acceder a esta ruta. Por defecto es false en los módulos operativos
   * de tienda/empresa, y true únicamente en gobierno SaaS (CU02), auditoría (CU20)
   * y cuenta (CU01).
   */
  permitirPlataforma?: boolean;
}

/**
 * Fábrica de guardianes: construye un `CanActivateFn` restringido a los roles
 * y al ámbito de cuenta indicados.
 *
 * Uso en la tabla de rutas:
 *     { path: 'usuarios', canActivate: [rolGuard(['Administrador'], 'Usuarios y Roles')], ... }
 *
 * @param rolesPermitidos Nombres de rol autorizados, tal como figuran en la
 *                        columna `rol.nombre` de PostgreSQL.
 * @param seccion Nombre de la sección, usado para redactar el aviso de acceso
 *                denegado de forma coherente en cada módulo.
 * @param opciones Reglas adicionales sobre el tipo de cuenta (PLATAFORMA vs PERSONAL/CLIENTE).
 * @returns CanActivateFn que concede o deniega el acceso a la ruta.
 */
export const rolGuard = (
  rolesPermitidos: string[],
  seccion: string = 'esta sección',
  opciones: OpcionesRolGuard = {},
): CanActivateFn => {
  return () => {
    const authService = inject(AuthService);
    const notificacion = inject(NotificacionService);
    const router = inject(Router);

    const usuario = authService.usuarioActual();
    const rol = authService.obtenerRol();
    const esPlataforma = usuario?.tipo_cuenta === 'PLATAFORMA' && !usuario.platform_workspace;

    // Si la cuenta es de gobierno de plataforma SaaS y la ruta pertenece a la
    // operación interna de una empresa comercial, redirigir a /panel/saas.
    if (esPlataforma && !opciones.permitirPlataforma) {
      notificacion.aviso(
        `La sección "${seccion}" pertenece a la operación interna de una empresa comercial.`,
      );
      router.navigate(['/panel/saas']);
      return false;
    }

    // Acceso concedido: el rol de la sesión está en la lista de permitidos.
    if (rol !== null && rolesPermitidos.includes(rol)) {
      return true;
    }

    // Acceso denegado: se avisa al usuario y se lo devuelve a su espacio de
    // trabajo correspondiente sin cerrar su sesión.
    notificacion.aviso(
      `No tiene permisos para acceder a la sección "${seccion}".`,
    );
    if (esPlataforma) {
      router.navigate(['/panel/saas']);
    } else if (rol === 'Cliente' || usuario?.tipo_cuenta === 'CLIENTE') {
      router.navigate(['/tiendas']);
    } else if (rol === 'Cajero (POS)') {
      router.navigate(['/panel/pos']);
    } else {
      router.navigate(['/panel/inicio']);
    }
    return false;
  };
};
