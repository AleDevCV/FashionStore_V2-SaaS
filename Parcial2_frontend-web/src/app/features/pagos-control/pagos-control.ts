import {Component,OnInit,inject,signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HttpClient} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {environment} from '../../../environments/environment';
@Component({standalone:true,selector:'app-pagos-control',imports:[CommonModule,FormsModule],template:`
<main><p class="eyebrow">Caja y entrega</p><h1>Conciliación y pedidos pendientes.</h1><p>Verifica el cobro antes de confirmar un QR. La entrega de una venta pagada se registra cuando se entrega físicamente la prenda.</p>@if(message()){<p class="message" role="status">{{message()}}</p>}
<section><h2>Pagos pendientes de atención</h2><button class="secondary" (click)="load()">Actualizar</button>@for(p of payments();track p.id_pago){<article><h3>{{p.pasarela}} · Reserva {{p.id_reserva}} · Bs {{p.monto}}</h3><p>{{p.estado_pago}} · {{p.transaccion_id}} · Vence {{p.vence|date:'short'}}</p>@if(p.pasarela==='QR Bolivia'&&p.estado_pago==='Pendiente'){<label><input type="checkbox" [(ngModel)]="verified[p.id_pago]">He comprobado el cobro correspondiente a esta referencia e importe</label><button [disabled]="!verified[p.id_pago]||busy()" (click)="confirm(p)">Registrar confirmación de caja</button>}@if(p.estado_pago==='RequiereResolucion'){<p>El cobro fue recibido y no pudo convertirse en venta. Requiere restitución íntegra.</p><button [disabled]="busy()" (click)="refund(p)">Solicitar devolución por Stripe</button>}</article>}@empty{<p>No hay pagos que requieran atención.</p>}</section>
<section class="result"><h2>Entregas de ventas pagadas</h2>@for(s of deliveries();track s.id_venta){<article><h3>Venta {{s.id_venta}} · {{s.cliente}}</h3><p>{{s.sucursal}} · Bs {{s.total}} · {{s.fecha_venta|date:'short'}}</p><label><input type="checkbox" [(ngModel)]="handed[s.id_venta]">He entregado físicamente las prendas del pedido</label><button [disabled]="!handed[s.id_venta]||busy()" (click)="deliver(s)">Registrar entrega</button></article>}@empty{<p>No hay entregas pendientes.</p>}</section></main>
`,styleUrls:['../reportes/reportes.scss'],styles:[`article{padding:20px 0;border-top:1px solid #d4ded4}label{flex-direction:row;align-items:center}input[type=checkbox]{width:auto}`]})
export class PagosControl implements OnInit {
 private http=inject(HttpClient);private base=environment.apiUrl+'/api';payments=signal<any[]>([]);deliveries=signal<any[]>([]);message=signal('');busy=signal(false);verified:Record<number,boolean>={};handed:Record<number,boolean>={};
 ngOnInit(){this.load();}
 async load(){try{const [p,d]=await Promise.all([firstValueFrom(this.http.get<any[]>(this.base+'/pagos/pendientes')),firstValueFrom(this.http.get<any[]>(this.base+'/ventas/entregas/pendientes'))]);this.payments.set(p);this.deliveries.set(d);}catch(e:any){this.message.set(e.error?.detail||'No se pudo consultar la atención pendiente.');}}
 async confirm(p:any){if(!this.verified[p.id_pago])return;await this.action('/pagos/qr/confirmar',{referencia:p.transaccion_id,id_reserva:p.id_reserva,id_cliente:p.id_cliente,id_sucursal:p.id_sucursal});}
 async refund(p:any){await this.action('/pagos/intentos/'+p.id_pago+'/reembolsar',{});}
 async deliver(s:any){if(this.handed[s.id_venta])await this.action('/ventas/'+s.id_venta+'/entregar',{});}
 private async action(path:string,body:any){this.busy.set(true);try{await firstValueFrom(this.http.post(this.base+path,body));this.message.set('Operación registrada.');await this.load();}catch(e:any){this.message.set(e.error?.detail||'No se pudo completar. El registro permanece pendiente.');}finally{this.busy.set(false);}}
}
