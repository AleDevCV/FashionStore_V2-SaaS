/**
 * =============================================================================
 * FASHIONSTORE - SERVICIO DE VENTAS (CU15)
 * =============================================================================
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable,switchMap,tap } from 'rxjs';
import {CarritoService} from './carrito.service';
import { environment } from '../../../environments/environment';
import {
  ReservaPeticion,
  ReservaProbadorCrear,
  ReservaProbadorEstadoActualizar,
  ReservaRespuesta,
  ReservaSucursalItem,
  TicketReservaRespuesta,
  VentaConfirmarPeticion,
  VentaDetalladaRespuesta,
  VentaRespuesta,
} from '../models/venta.model';

@Injectable({ providedIn: 'root' })
export class VentaService {
  private readonly http = inject(HttpClient);
  private readonly cart=inject(CarritoService);
  private readonly base = `${environment.apiUrl}/api/ventas`;

  crearReserva(datos: ReservaPeticion): Observable<ReservaRespuesta> {
    return this.http.post<any>(`${this.base}/cotizar`,{id_sucursal:datos.id_sucursal,items:datos.items.map(({id_variante_prenda,cantidad})=>({id_variante_prenda,cantidad}))}).pipe(tap(q=>this.cart.actualizarPrecios(q.items)),switchMap(q=>this.http.post<ReservaRespuesta>(`${this.base}/reserva`,{...datos,items:q.items.map(({id_variante_prenda,cantidad,precio_unitario}:any)=>({id_variante_prenda,cantidad,precio_unitario}))})));
  }
  estadoPago(id:number):Observable<any>{return this.http.get(`${this.base}/reserva/${id}/estado-pago`);}

  obtenerReserva(id: number): Observable<ReservaRespuesta> {
    return this.http.get<ReservaRespuesta>(`${this.base}/reserva/${id}`);
  }

  misReservas(id_cliente: number): Observable<ReservaRespuesta[]> {
    return this.http.get<ReservaRespuesta[]>(`${this.base}/mis-reservas/${id_cliente}`);
  }

  confirmarVenta(datos: VentaConfirmarPeticion): Observable<VentaDetalladaRespuesta> {
    return this.http.post<VentaDetalladaRespuesta>(`${this.base}/confirmar`, datos);
  }

  misPedidos(id_cliente: number): Observable<VentaRespuesta[]> {
    return this.http.get<VentaRespuesta[]>(`${this.base}/mis-pedidos/${id_cliente}`);
  }

  obtenerVenta(id: number): Observable<VentaDetalladaRespuesta> {
    return this.http.get<VentaDetalladaRespuesta>(`${this.base}/${id}`);
  }

  listarVentas(params?: { id_cliente?: number | null; id_sucursal?: number | null; skip?: number | null; limit?: number | null }): Observable<VentaRespuesta[]> {
    return this.http.get<VentaRespuesta[]>(`${this.base}/`, {
      params: this.construirParametros(params),
    });
  }

  // ── RESERVAS DE PROBADOR Y ATENCIÓN EN SUCURSAL (CU16, CU17) ────────────────

  crearReservaProbador(datos: ReservaProbadorCrear): Observable<TicketReservaRespuesta> {
    return this.http.post<TicketReservaRespuesta>(`${this.base}/reservas-probador`, datos);
  }

  obtenerTicketReserva(codigoOId: string | number): Observable<TicketReservaRespuesta> {
    return this.http.get<TicketReservaRespuesta>(`${this.base}/reservas-probador/${codigoOId}`);
  }

  listarReservasSucursal(params?: { id_sucursal?: number | null; estado?: string | null; skip?: number | null; limit?: number | null }): Observable<ReservaSucursalItem[]> {
    return this.http.get<ReservaSucursalItem[]>(`${this.base}/reservas-probador/`, {
      params: this.construirParametros(params),
    });
  }

  actualizarEstadoReservaProbador(idReserva: number, datos: ReservaProbadorEstadoActualizar): Observable<TicketReservaRespuesta> {
    return this.http.patch<TicketReservaRespuesta>(`${this.base}/reservas-probador/${idReserva}/estado`, datos);
  }

  private construirParametros(
    params?: Record<string, string | number | null | undefined>,
  ): HttpParams {
    let httpParams = new HttpParams();
    if (!params) {
      return httpParams;
    }
    for (const [clave, valor] of Object.entries(params)) {
      if (valor === undefined || valor === null) {
        continue;
      }
      if (typeof valor === 'number') {
        if (!Number.isNaN(valor)) {
          httpParams = httpParams.set(clave, valor.toString());
        }
        continue;
      }
      const texto = valor.trim();
      if (texto.length > 0 && texto !== 'Todos') {
        httpParams = httpParams.set(clave, texto);
      }
    }
    return httpParams;
  }
}

