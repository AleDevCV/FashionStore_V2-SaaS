/**
 * =============================================================================
 * FASHIONSTORE - GUARDIANES DE RUTA (CU01)
 * -----------------------------------------------------------------------------
 * Protegen la navegación del panel administrativo: impiden que un visitante sin
 * sesión válida alcance las vistas internas y, a la inversa, evitan que un
 * usuario ya autenticado vuelva a la pantalla de login.
 * =============================================================================
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { AuthService } from '../services/auth.service';

/**
 * Permite el acceso únicamente si existe un token JWT vigente.
 *
 * @param ruta Instantánea de la ruta solicitada (no se usa por ahora).
 * @param estado Estado del router; su `url` se conserva para volver a la
 *               página pedida después de iniciar sesión.
 * @returns true si la sesión es válida; si no, redirige a /login y devuelve false.
 */
export const authGuard: CanActivateFn = (ruta, estado) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Se comprueba la expiración además de la existencia del token: un JWT
  // caducado en el localStorage no debe dar acceso.
  if (authService.estaAutenticado() && !authService.tokenExpirado()) {
    return true;
  }

  // Sesión inexistente o vencida: se limpia y se envía al login guardando la
  // URL de destino en `returnUrl` para redirigir tras autenticarse.
  authService.logout();
  router.navigate(['/login'], { queryParams: { returnUrl: estado.url } });
  return false;
};

/**
 * Impide que un usuario con sesión activa vuelva a ver la pantalla de login.
 *
 * @returns true si NO hay sesión (puede ver el login); si ya está autenticado,
 *          lo redirige al panel y devuelve false.
 */
export const invitadoGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.estaAutenticado() && !authService.tokenExpirado()) {
    router.navigate([authService.obtenerRol()==='Cliente' ? '/tiendas' : authService.usuarioActual()?.tipo_cuenta==='PLATAFORMA' ? '/panel/saas' : authService.obtenerRol()==='Cajero (POS)' ? '/panel/pos' : '/panel']);
    return false;
  }

  return true;
};

/** Vincula el cliente autenticado a la tienda de la navegación, nunca desde el login. */
export const tiendaGuard: CanActivateFn = async (ruta) => {
  const auth=inject(AuthService); const router=inject(Router);
  const user=auth.usuarioActual();
  const empresa=ruta.queryParamMap.get('empresa') || (user?.tenant_id ? user.empresa_slug : null);
  if (user?.tipo_cuenta==='CLIENTE' && empresa && empresa!==user.empresa_slug) {
    try { await firstValueFrom(auth.seleccionarTienda(empresa)); }
    catch { return router.parseUrl('/tiendas'); }
  }
  if (user?.tipo_cuenta==='CLIENTE' && !empresa) return router.parseUrl('/tiendas');
  if (empresa) localStorage.setItem('fashionstore_p2_empresa',empresa);
  return true;
};
