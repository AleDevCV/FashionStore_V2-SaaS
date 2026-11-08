/**
 * =============================================================================
 * FASHIONSTORE - SERVICIO DE MOVIMIENTOS DE INVENTARIO (CU11)
 * Sistemas de Información II - UAGRM
 * -----------------------------------------------------------------------------
 * Consume /api/movimientos-inventario/. Permite registrar entradas, salidas y
 * traspasos físicos, consultar existencias disponibles en sucursal y listar
 * el historial del kardex con filtros combinados.
 * =============================================================================
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, catchError, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import { traducirErrorApi } from '../utils/api-error';
import {
  FiltrosMovimientos,
  MovimientoInventario,
  MovimientoInventarioCrear,
  TraspasoInventario,
  StockRespuesta,
} from '../models/movimiento.model';

@Injectable({ providedIn: 'root' })
export class MovimientoInventarioService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/api/movimientos-inventario`;

  /**
   * Recupera el historial de movimientos de almacén aplicando filtros opcionales.
   *
   * @param filtros Filtros por sucursal, variante, tipo, fechas y paginación.
   * @returns Observable con la lista de movimientos registrados.
   */
  listar(filtros?: FiltrosMovimientos): Observable<MovimientoInventario[]> {
    let params = new HttpParams();
    if (filtros?.id_sucursal) {
      params = params.set('id_sucursal', filtros.id_sucursal.toString());
    }
    if (filtros?.id_variante_prenda) {
      params = params.set('id_variante_prenda', filtros.id_variante_prenda.toString());
    }
    if (filtros?.tipo) {
      params = params.set('tipo', filtros.tipo);
    }
    if (filtros?.fecha_inicio) {
      params = params.set('fecha_inicio', filtros.fecha_inicio);
    }
    if (filtros?.fecha_fin) {
      params = params.set('fecha_fin', filtros.fecha_fin);
    }
    if (filtros?.skip !== undefined && filtros?.skip !== null) {
      params = params.set('skip', filtros.skip.toString());
    }
    if (filtros?.limit !== undefined && filtros?.limit !== null) {
      params = params.set('limit', filtros.limit.toString());
    }

    return this.http
      .get<MovimientoInventario[]>(`${this.baseUrl}/`, { params })
      .pipe(catchError(traducirErrorApi));
  }

  /**
   * Registra un movimiento físico manual en el inventario.
   * Entrada/Salida conservan su respuesta de movimiento. Traspaso requiere
   * destino/UUID y devuelve ambas patas confirmadas por el servidor.
   *
   * @param datos Sucursal, variante, tipo de movimiento, cantidad y motivo.
   * @returns Observable con el movimiento creado (HTTP 201).
   */
  crear(datos: MovimientoInventarioCrear): Observable<MovimientoInventario | TraspasoInventario> {
    return this.http
      .post<MovimientoInventario | TraspasoInventario>(`${this.baseUrl}/`, datos)
      .pipe(catchError(traducirErrorApi), map(respuesta => {
        if (datos.tipo === 'Traspaso' && (!respuesta || !('movimiento_salida' in respuesta) || !('movimiento_entrada' in respuesta))) {
          throw new Error('El servidor no confirmó los dos movimientos del traspaso. Revisa el historial antes de iniciar otro.');
        }
        return respuesta;
      }));
  }

  /**
   * Consulta las existencias físicas actuales de una variante en una sucursal.
   *
   * @param id_sucursal Identificador de la sucursal.
   * @param id_variante_prenda Identificador de la variante.
   * @returns Observable con `{ id_sucursal, id_variante_prenda, stock }`.
   */
  consultarStock(id_sucursal: number, id_variante_prenda: number, disponible = false): Observable<StockRespuesta> {
    let params = new HttpParams()
      .set('id_sucursal', id_sucursal.toString())
      .set('id_variante_prenda', id_variante_prenda.toString());
    if (disponible) params = params.set('disponible', 'true');

    return this.http
      .get<StockRespuesta>(`${this.baseUrl}/stock`, { params })
      .pipe(catchError(traducirErrorApi));
  }
}
