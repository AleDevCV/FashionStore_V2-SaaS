import {Component,inject,signal,OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {HttpClient} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {OfflineService} from '../../core/services/offline.service';
import {LocalOperation,cents,priceCents} from '../../core/services/offline-store';
import {environment} from '../../../environments/environment';

@Component({selector:'app-offline',standalone:true,imports:[CommonModule,FormsModule,RouterLink],templateUrl:'./offline.html',styleUrl:'./offline.scss'})
export class Offline implements OnInit {
 readonly store=inject(OfflineService);private http=inject(HttpClient);
 branches=signal<any[]>([]);branchId=0;kind:'venta'|'reserva'='venta';customerId:number|null=null;cash='0';filter='';cart:Record<number,number>={};revision:string|null=null;error=signal('');online=signal(navigator.onLine);
 async ngOnInit(){window.addEventListener('online',()=>this.online.set(true));window.addEventListener('offline',()=>this.online.set(false));try{await this.store.open();this.branchId=this.store.snapshot()?.branch.id_sucursal||0;if(localStorage.getItem(environment.claveTokenJwt)){const ctx=await firstValueFrom(this.http.get<any>(environment.apiUrl+'/api/contexto'));this.branches.set(ctx.sucursales||[]);}}catch(e:any){this.error.set(e.message||'No se pudo abrir el almacenamiento.');}}
 get visible(){const q=this.filter.toLocaleLowerCase();return this.store.catalog().filter(p=>(p.product.nombre+' '+p.sku_variante+' '+p.color+' '+p.talla).toLocaleLowerCase().includes(q));}
 get entries(){return Object.entries(this.cart).filter(([,qty])=>qty>0).map(([id,quantity])=>({variantId:Number(id),quantity}));}
 price(row:any){const qty=this.entries.filter(e=>this.store.catalog().find(v=>v.id_variante_prenda===e.variantId)?.id_prenda===row.id_prenda).reduce((sum,e)=>sum+e.quantity,0);return priceCents(row.product,row,qty)/100;}
 get total(){return this.entries.reduce((sum,e)=>{const row=this.store.catalog().find(v=>v.id_variante_prenda===e.variantId);return sum+(row?Math.round(this.price(row)*100)*e.quantity:0);},0)/100;}
 async save(){this.error.set('');try{await this.store.capture(this.kind,this.customerId,this.entries,this.cash,this.revision);this.cart={};this.revision=null;this.cash='0';}catch(e:any){this.error.set(e.message);}}
 async download(){this.error.set('');try{await this.store.download(Number(this.branchId));}catch(e:any){this.error.set(e.message);}}
 async revise(op:LocalOperation){this.error.set('');if(this.store.snapshot()?.branch.id_sucursal!==op.branch_id){this.error.set('Actualiza primero el catálogo de la sucursal original.');return;}this.revision=op.operation_id;this.kind=op.kind;this.customerId=op.customer_id;this.cash=op.cash_received||'0';this.cart={};for(const line of await this.store.details(op.operation_id))this.cart[line.id_variante_prenda]=line.cantidad;this.store.message.set('Revisa las cantidades y los precios actuales. Se conservará el original y se creará otra operación.');}
 async compensate(op:LocalOperation){const motivo=prompt('Describe la resolución y la devolución física del efectivo, si corresponde (mínimo 6 caracteres):');if(!motivo)return;const amount=prompt('Importe devuelto de contado (0 si no corresponde):','0');if(amount===null)return;try{cents(amount);await this.store.compensate(op,motivo,amount);}catch(e:any){this.error.set(e.error?.detail||e.message);}}
 async export(){const blob=new Blob([await this.store.exportPending()],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='operaciones-pendientes.json';a.click();URL.revokeObjectURL(a.href);}
}
