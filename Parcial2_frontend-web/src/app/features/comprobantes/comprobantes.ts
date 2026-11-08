import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';
import { DescargaService } from '../../core/services/descarga.service';

interface Comprobante {
  numero_comprobante: string;
  id_venta: number;
  fecha_emision: string;
  total: number;
}

@Component({
  selector: 'app-comprobantes',
  imports: [DatePipe, DecimalPipe, FormsModule],
  template: `
    <section>
      <p>CU14 · Documentos de venta</p>
      <h1>Comprobantes de compra</h1>
      <form (ngSubmit)="cargar()">
        <label for="buscar-comprobante">Número de comprobante o ID de venta</label>
        <input id="buscar-comprobante" name="busqueda" [(ngModel)]="busqueda" maxlength="50">
        <button type="submit" [disabled]="cargando()">Buscar</button>
      </form>
      @if (cargando()) { <p role="status">Cargando comprobantes…</p> }
      @else if (error()) { <p role="alert">{{ error() }}</p> }
      @else if (!comprobantes().length) { <p>No se encontraron comprobantes para esta empresa.</p> }
      @else {
        <div class="tabla">
          <table>
            <thead><tr><th scope="col">Número</th><th scope="col">Venta</th><th scope="col">Emisión</th><th scope="col">Total</th><th scope="col">Documento</th></tr></thead>
            <tbody>
              @for (item of comprobantes(); track item.numero_comprobante) {
                <tr><td>{{ item.numero_comprobante }}</td><td>{{ item.id_venta }}</td>
                  <td>{{ item.fecha_emision | date:'dd/MM/yyyy' }}</td>
                  <td>Bs {{ item.total | number:'1.2-2' }}</td>
                  <td><button type="button" (click)="descargar(item)" [attr.aria-label]="'Descargar PDF ' + item.numero_comprobante">Descargar PDF</button></td></tr>
              }
            </tbody>
          </table>
        </div>
      }
    </section>
  `,
  styles: [`
    section { max-width: 68rem; margin: auto; padding: 2rem; color: #213b2f; }
    h1 { font: normal clamp(2rem, 5vw, 3rem) Georgia, serif; }
    form { display: flex; flex-wrap: wrap; align-items: center; gap: .75rem; margin: 1.5rem 0; }
    input, button { font: inherit; padding: .6rem .85rem; border: 1px solid #657e69; }
    button { color: white; background: #294c37; cursor: pointer; }
    .tabla { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: .75rem; border-bottom: 1px solid #cbd3c8; }
  `],
})
export class Comprobantes {
  private readonly http = inject(HttpClient);
  private readonly descarga = inject(DescargaService);
  readonly comprobantes = signal<Comprobante[]>([]);
  readonly cargando = signal(false);
  readonly error = signal('');
  busqueda = '';

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set('');
    this.http.get<Comprobante[]>(environment.apiUrl + '/api/comprobantes', {
      params: { busqueda: this.busqueda.trim() },
    }).subscribe({
      next: items => { this.comprobantes.set(items); this.cargando.set(false); },
      error: () => { this.error.set('No se pudieron consultar los comprobantes.'); this.cargando.set(false); },
    });
  }

  descargar(item: Comprobante): void {
    this.descarga.abrir('/api/comprobantes/' + encodeURIComponent(item.numero_comprobante) + '/pdf');
  }
}
