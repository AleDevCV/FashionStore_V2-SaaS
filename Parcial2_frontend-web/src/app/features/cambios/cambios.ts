import { Component,inject,signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

@Component({standalone:true,selector:'app-cambios',imports:[CommonModule,FormsModule],template:`
<main class="changes"><p class="eyebrow">FASHIONSTORE / ATENCIÓN</p><h1>Cambios y devoluciones</h1>
<p>Solicita un cambio dentro de siete días de la entrega. Conserva la prenda sin uso para su inspección.</p>
@if(message()){<p role="status" class="notice">{{message()}}</p>}
<section><h2>Nueva solicitud</h2><form (ngSubmit)="request()">
<label>Compra y prenda<select name="eligible" [(ngModel)]="selected" required><option [ngValue]="null">Selecciona una compra entregada</option>@for(item of eligible();track item.id_venta+'-'+item.id_variante_prenda){<option [ngValue]="item">Venta {{item.id_venta}} · {{item.nombre}} · {{item.talla}} / {{item.color}} · Bs {{item.precio_unitario}}</option>}</select></label>
<label>Unidades<input type="number" name="quantity" min="1" [max]="selected?.cantidad || 1" [(ngModel)]="quantity" required></label>
<label>Motivo<textarea name="reason" [(ngModel)]="reason" minlength="4" maxlength="1000" required></textarea></label>
<button [disabled]="busy() || !selected">Registrar solicitud</button></form></section>
<section><div class="heading"><h2>Seguimiento</h2><button class="quiet" (click)="load()">Actualizar</button></div>
@for(item of changes();track item.id_cambio){<article><div class="heading"><h3>Solicitud {{item.id_cambio}}</h3><span class="status">{{item.estado}}</span></div>
<p>{{item.motivo}}</p><dl><div><dt>Crédito original</dt><dd>Bs {{item.credito}}</dd></div><div><dt>Diferencia</dt><dd>{{item.diferencia===null ? 'A definir' : 'Bs '+item.diferencia}}</dd></div><div><dt>Recepción</dt><dd>{{item.recibido_at ? (item.recibido_at | date:'short') : 'Pendiente'}}</dd></div></dl>
<div class="actions">
@if(staff() && item.estado==='Solicitado'){<button (click)="action(item,'recibir',{aceptada:true})" [disabled]="busy()">Registrar prenda recibida y aceptada</button><button class="quiet" (click)="action(item,'recibir',{aceptada:false})">Rechazar tras inspección</button>}
@if(staff() && item.estado==='Recibido'){<button (click)="choose(item)">Seleccionar reemplazo</button>}
@if(item.estado==='PagoPendiente'){<button (click)="pay(item)">Pagar diferencia</button>}
@if(staff() && item.estado==='ReembolsoPendiente'){<button (click)="refundItem=item">Registrar restitución</button>}
@if(staff() && item.estado==='Listo'){<button (click)="action(item,'entregar')">Confirmar entrega del reemplazo</button>}
@if(!['Entregado','Reembolsado','Rechazado','Cancelado'].includes(item.estado)){<button class="quiet" (click)="action(item,'cancelar')">Cancelar solicitud</button>}
</div></article>}@empty{<p>No hay solicitudes registradas en esta cuenta.</p>}</section>
@if(replacementItem){<section><h2>Reemplazo de solicitud {{replacementItem.id_cambio}}</h2><label>Prenda disponible<select [(ngModel)]="replacementVariant"><option [ngValue]="0">Selecciona una variante</option>@for(option of options();track option.id_variante_prenda){<option [ngValue]="option.id_variante_prenda">{{option.nombre}} · {{option.talla}} / {{option.color}} · {{option.stock}} disponibles</option>}</select></label><p>El servidor calcula el precio y la diferencia antes del cobro.</p><button (click)="replace()" [disabled]="busy() || !replacementVariant">Reservar reemplazo y calcular diferencia</button><button class="quiet" (click)="replacementItem=null">Cerrar</button></section>}
@if(refundItem){<section><h2>Restitución de solicitud {{refundItem.id_cambio}}</h2><p>Para efectivo, QR o transferencia registra la restitución por el medio original. Para tarjeta el servidor solicita la devolución sandbox a la pasarela.</p><label><input type="checkbox" [(ngModel)]="refundConfirmed"> Confirmo que se restituyó por el medio original cuando es un movimiento manual.</label><label>Referencia de caja o transferencia<input [(ngModel)]="refundReference" maxlength="100"></label><button (click)="refund()" [disabled]="busy()">Procesar y registrar devolución</button><button class="quiet" (click)="refundItem=null">Cerrar</button></section>}
<section><h2>Notificaciones</h2>@for(note of notifications();track note.id_notificacion){<article><strong>{{note.titulo}}</strong><p>{{note.mensaje}}</p><small>{{note.created_at | date:'short'}}</small>@if(!note.leida){<button class="quiet" (click)="read(note)">Marcar leída</button>}</article>}@empty{<p>No hay avisos pendientes.</p>}</section>
</main>`,styles:[`:host{display:block}.changes{max-width:1100px;margin:auto;padding:40px 24px;background:#faf9f4;min-height:100vh;color:#243a2d}h1,h2,h3{font-family:Georgia,serif;font-weight:400}h1{font-size:44px;margin:14px 0}.eyebrow{font-size:11px;letter-spacing:2px}section{padding:25px;background:white;border:1px solid #d6ded6;border-radius:8px;margin:24px 0}.heading,.actions{display:flex;gap:12px;justify-content:space-between;align-items:center;flex-wrap:wrap}.actions{justify-content:flex-start}article{border-top:1px solid #e3e7df;padding:22px 0}form{display:grid;gap:18px}label{display:grid;gap:8px;font-size:14px}input,select,textarea{font:inherit;padding:12px;border:1px solid #a9b6ab;border-radius:4px;max-width:100%;box-sizing:border-box}input[type=checkbox]{width:20px;height:20px}button{padding:11px 18px;background:#204d36;color:white;border:0;border-radius:4px;cursor:pointer;margin-top:8px}button:disabled{opacity:.5;cursor:wait}.quiet{background:#edf0e8;color:#243a2d}.notice{padding:16px;border-left:4px solid #8c733b;background:#f2eddf}.status{background:#eef1e8;padding:8px 14px;border-radius:20px}dl{display:flex;gap:40px;flex-wrap:wrap}dt{font-size:12px;color:#647164}dd{margin:8px 0}button,input,select,textarea{outline-offset:4px}@media(max-width:600px){h1{font-size:32px}section{padding:18px}}`]})
export class Cambios {
 private http=inject(HttpClient);private base=environment.apiUrl+'/api';
 changes=signal<any[]>([]);eligible=signal<any[]>([]);notifications=signal<any[]>([]);options=signal<any[]>([]);message=signal('');busy=signal(false);staff=signal(false);
 selected:any=null;quantity=1;reason='';replacementItem:any=null;replacementVariant=0;refundItem:any=null;refundConfirmed=false;refundReference='';
 constructor(){this.load();this.http.get<any>(this.base+'/contexto').subscribe({next:x=>this.staff.set(['Administrador','Encargado de Sucursal','Cajero (POS)'].includes(x.usuario.rol)),error:e=>this.fail(e)});}
 private fail(e:any){this.message.set(typeof e.error?.detail==='string'?e.error.detail:'No fue posible completar la operación.');this.busy.set(false);}
 load(){this.http.get<any[]>(this.base+'/cambios').subscribe({next:x=>this.changes.set(x),error:e=>this.fail(e)});this.http.get<any[]>(this.base+'/cambios/elegibles').subscribe({next:x=>this.eligible.set(x),error:e=>this.fail(e)});this.http.get<any[]>(this.base+'/notificaciones').subscribe({next:x=>this.notifications.set(x),error:e=>this.fail(e)});}
 async request(){if(!this.selected)return;this.busy.set(true);try{await firstValueFrom(this.http.post(this.base+'/cambios',{id_venta:this.selected.id_venta,id_variante_prenda:this.selected.id_variante_prenda,cantidad:this.quantity,motivo:this.reason}));this.reason='';this.message.set('Solicitud registrada para inspección.');this.load();}catch(e){this.fail(e);}finally{this.busy.set(false);}}
 async action(item:any,name:string,body:any={}){this.busy.set(true);try{await firstValueFrom(this.http.post(this.base+'/cambios/'+item.id_cambio+'/'+name,body));this.message.set('Estado actualizado.');this.load();}catch(e){this.fail(e);}finally{this.busy.set(false);}}
 async choose(item:any){try{this.options.set(await firstValueFrom(this.http.get<any[]>(this.base+'/cambios/reemplazos/'+item.id_sucursal)));this.replacementItem=item;this.replacementVariant=0;}catch(e){this.fail(e);}}
 async replace(){this.busy.set(true);try{await firstValueFrom(this.http.put(this.base+'/cambios/'+this.replacementItem.id_cambio+'/reemplazo',{id_variante_prenda:this.replacementVariant}));this.replacementItem=null;this.load();}catch(e){this.fail(e);}finally{this.busy.set(false);}}
 async pay(item:any){this.busy.set(true);try{const response=await firstValueFrom(this.http.post<any>(this.base+'/cambios/'+item.id_cambio+'/pago',{}));location.assign(response.url_pago);}catch(e){this.fail(e);}finally{this.busy.set(false);}}
 async refund(){await this.action(this.refundItem,'reembolsar',{confirmar_restitucion:this.refundConfirmed,referencia:this.refundReference});this.refundItem=null;this.refundConfirmed=false;this.refundReference='';}
 read(note:any){this.http.patch(this.base+'/notificaciones/'+note.id_notificacion+'/leida',{}).subscribe({next:()=>this.load(),error:e=>this.fail(e)});}
}
