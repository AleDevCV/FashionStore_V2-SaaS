import { Injectable,inject,signal } from '@angular/core';
import { HttpClient,HttpParams } from '@angular/common/http';
import { firstValueFrom,timeout } from 'rxjs';
import { environment } from '../../../environments/environment';
import { OfflineDatabase,LocalOperation,cents,priceCents } from './offline-store';
import { commerceSession } from './commerce-session';

@Injectable({providedIn:'root'})
export class OfflineService {
 private http=inject(HttpClient);private base=environment.apiUrl+'/api';private db:OfflineDatabase|null=null;private namespace='';
 readonly snapshot=signal<any>(null);readonly catalog=signal<any[]>([]);readonly customers=signal<any[]>([]);readonly operations=signal<LocalOperation[]>([]);readonly busy=signal(false);readonly message=signal('');
 private tab=crypto.randomUUID();private timer:ReturnType<typeof setTimeout>|null=null;private failures=0;
 constructor(){window.addEventListener('online',()=>this.schedule());window.addEventListener('fashionstore-session',()=>void this.open().catch(e=>this.message.set(this.error(e))));window.addEventListener('storage',e=>{if(e.key==='fashionstore_p2_active')void this.open().catch(e=>this.message.set(this.error(e)));});}
 async open(){
  const active=commerceSession()||'';
  if(!/^\d+:\d+$/.test(active)){this.db?.close();this.db=null;this.namespace='';this.snapshot.set(null);this.catalog.set([]);this.customers.set([]);this.operations.set([]);return;}
  if(this.namespace!==active){this.db?.close();this.snapshot.set(null);this.catalog.set([]);this.customers.set([]);this.operations.set([]);this.message.set('');this.db=new OfflineDatabase(active);this.namespace=active;}
  await this.db!.open();
  const lock=await this.db!.meta.get('sync_lock');
  if(!lock || lock.expiresAt<Date.now())await this.db!.operations.where('state').equals('ENVIANDO').modify({state:'PENDIENTE'});
  this.snapshot.set((await this.db!.meta.get('snapshot'))?.value||null);await this.refresh();this.schedule();
 }
 private current(){if(!this.db || this.namespace!==commerceSession())throw new Error('Inicia sesión en la empresa correcta.');return this.db;}
 get validLease(){const value=this.snapshot();return !!value && value.lease_expires*1000>Date.now();}
 async refresh(){
  const db=this.current();const products=new Map((await db.products.toArray()).map(p=>[p.id_prenda,p]));const rows=await db.operations.toArray();
  const branch=this.snapshot()?.branch.id_sucursal;
  const active=new Set(rows.filter(o=>o.state==='PENDIENTE'||o.state==='ENVIANDO'||o.state==='CONFIRMADA').map(o=>o.original_operation));
  const unresolved=new Set(rows.filter(o=>!o.result?.resolved).map(o=>o.operation_id));
  const unaccounted=rows.filter(o=>o.branch_id===branch && !o.accounted && o.state!=='RECHAZADA' && !o.result?.resolved
    && !active.has(o.operation_id)
    && !(o.state==='EN_CONFLICTO' && o.original_operation && unresolved.has(o.original_operation)));
  const quantities=new Map<number,number>();
  for(const op of unaccounted){for(const line of await db.details.where('operation_id').equals(op.operation_id).toArray())quantities.set(line.id_variante_prenda,(quantities.get(line.id_variante_prenda)||0)+line.cantidad);}
  const variants=new Map((await db.variants.toArray()).map(v=>[v.id_variante_prenda,v]));
  this.catalog.set((await db.stocks.where('branch_id').equals(branch||0).toArray()).map(s=>({...variants.get(s.id_variante_prenda),product:products.get(variants.get(s.id_variante_prenda)?.id_prenda),available:Math.max(0,s.stock-(quantities.get(s.id_variante_prenda)||0))})).filter(v=>v.product));
  this.customers.set(await db.customers.toArray());this.operations.set(rows.sort((a,b)=>b.occurred_at.localeCompare(a.occurred_at)));
 }
 private async locked(action:()=>Promise<void>){
  const db=this.current();let acquired=false;
  await db.transaction('rw',db.meta,async()=>{const lock=await db.meta.get('sync_lock');if(!lock || lock.owner===this.tab || lock.expiresAt<Date.now()){await db.meta.put({key:'sync_lock',owner:this.tab,expiresAt:Date.now()+60000});acquired=true;}});
  if(!acquired)return;
  try{await action();}finally{await db.transaction('rw',db.meta,async()=>{const lock=await db.meta.get('sync_lock');if(lock?.owner===this.tab)await db.meta.delete('sync_lock');});}
 }
 async download(branchId:number){
  if(this.busy())return;this.busy.set(true);this.message.set('Descargando catálogo autorizado…');
  let completed=0,total=0;
  try{
   const db=this.current(),profile=this.namespace;
   // Lista finita: rechazos y conflictos no necesitan cambiar accounted para avanzar.
   const ids=(await db.operations.toArray()).filter(o=>!o.accounted && o.branch_id===branchId).map(o=>o.operation_id);
   const batches:string[][]=[];for(let offset=0;offset<ids.length;offset+=50)batches.push(ids.slice(offset,offset+50));
   if(!batches.length)batches.push([]);total=batches.length;
   for(const batch of batches){
    let applied=false;
    if(this.current()!==db || this.namespace!==profile)throw new Error('La sesión cambió durante la reconciliación.');
    // El bloqueo existente protege una petición y su transacción, no toda la cola.
    await this.locked(async()=>{
     if(this.current()!==db || this.namespace!==profile)throw new Error('La sesión cambió durante la reconciliación.');
     let params=new HttpParams().set('branch_id',branchId);for(const id of batch)params=params.append('operation_ids',id);
     const snapshot=await firstValueFrom(this.http.get<any>(this.base+'/offline/catalogo',{params}).pipe(timeout(20000)));
     if(this.current()!==db || this.namespace!==profile || snapshot.tenant_id+':'+snapshot.author_id!==profile || snapshot.branch?.id_sucursal!==branchId)throw new Error('El catálogo no corresponde a la cuenta y sucursal solicitadas.');
     await db.transaction('rw',[db.products,db.variants,db.stocks,db.branches,db.customers,db.meta,db.operations],async()=>{
    await db.stocks.where('branch_id').equals(branchId).delete();
    // Se conservan variantes antiguas para mantener referencias de operaciones pendientes.
    for(const row of snapshot.products){const {id_variante_prenda,id_prenda,sku_variante,talla,color,precio_adicional,stock,...product}=row;await db.products.put({id_prenda,...product});await db.variants.put({id_variante_prenda,id_prenda,sku_variante,talla,color,precio_adicional});await db.stocks.put({branch_id:branchId,id_variante_prenda,stock});}
    await db.branches.put(snapshot.branch);await db.customers.bulkPut(snapshot.customers);
    for(const result of snapshot.operation_results||[]){
     const op=await db.operations.get(result.operation_id);
     if(op)await this.applyResult(db,op,result,op.accounted||(result.state==='CONFIRMADA' && op.branch_id===branchId));
    }
    await db.meta.put({key:'snapshot',value:snapshot});if(!await db.meta.get('device'))await db.meta.put({key:'device',value:crypto.randomUUID()});
     });
     completed++;applied=true;
     if(this.current()!==db || this.namespace!==profile)throw new Error('La sesión cambió durante la reconciliación.');
     this.snapshot.set(snapshot);await this.refresh();
    });
    if(!applied)throw new Error('Otra operación está usando la cola. Reintenta la descarga.');
   }
   this.message.set(`Catálogo guardado. Reconciliación completada (${completed}/${total} lotes). Las operaciones se conservan.`);
  }catch(e:any){this.message.set((completed?`Reconciliación parcial (${completed}/${total} lotes guardados). `:'')+this.error(e));}finally{this.busy.set(false);}
 }
 async capture(kind:'venta'|'reserva',customerId:number|null,entries:{variantId:number;quantity:number}[],cash:any,original:string|null=null){
  const db=this.current(),snapshot=this.snapshot();if(!this.validLease)throw new Error('La autorización offline venció; conecta para renovarla.');
  if(kind==='venta' && !snapshot.can_sell)throw new Error('Esta cuenta no puede registrar ventas offline.');
  if(!entries.length || new Set(entries.map(e=>e.variantId)).size!==entries.length)throw new Error('Selecciona variantes únicas.');
  const products=new Map((await db.products.toArray()).map(p=>[p.id_prenda,p]));const variants=new Map((await db.variants.toArray()).map(v=>[v.id_variante_prenda,v]));const quantities=new Map<number,number>();
  for(const entry of entries){const v=variants.get(entry.variantId);if(!v || !Number.isInteger(entry.quantity) || entry.quantity<1)throw new Error('Revisa los detalles de la operación.');quantities.set(v.id_prenda,(quantities.get(v.id_prenda)||0)+entry.quantity);}
  const oldLines=original?await this.details(original):[];
  const operation_id=crypto.randomUUID();const lines=entries.map(entry=>{const v=variants.get(entry.variantId)!;const price=priceCents(products.get(v.id_prenda),v,quantities.get(v.id_prenda)!);const known=this.catalog().find(x=>x.id_variante_prenda===entry.variantId);const credit=oldLines.find(x=>x.id_variante_prenda===entry.variantId)?.cantidad||0;if(entry.quantity>(known?.available||0)+credit)throw new Error('La cantidad supera la disponibilidad local estimada.');return {operation_id,id_variante_prenda:entry.variantId,cantidad:entry.quantity,precio_unitario:(price/100).toFixed(2)};});
  const total=lines.reduce((sum,line)=>sum+cents(line.precio_unitario)*line.cantidad,0);
  if(kind==='venta' && cents(cash)<total)throw new Error('El efectivo recibido no cubre el total conocido.');
  if(kind==='reserva' && !customerId)throw new Error('Selecciona un cliente previamente descargado.');
  const header:LocalOperation={operation_id,version:1,tenant_id:snapshot.tenant_id,author_id:snapshot.author_id,branch_id:snapshot.branch.id_sucursal,device_id:(await db.meta.get('device')).value,kind,occurred_at:new Date().toISOString(),lease:snapshot.lease,customer_id:customerId||null,cash_received:kind==='venta'?(cents(cash)/100).toFixed(2):null,original_operation:original,state:'PENDIENTE',attempts:0,reason:'',accounted:false};
  await db.transaction('rw',[db.operations,db.details,db.variants,db.customers,db.branches],async()=>{
   if(!await db.branches.get(header.branch_id))throw new Error('Sucursal local no disponible.');
   if(customerId && !await db.customers.get(customerId))throw new Error('Cliente local no disponible.');
   for(const line of lines)if(!await db.variants.get(line.id_variante_prenda))throw new Error('Variante local no disponible.');
   if(original){
    const old=await db.operations.get(original);
    const pending=await db.operations.where('original_operation').equals(original)
      .and(op=>op.state==='PENDIENTE'||op.state==='ENVIANDO').first();
    if(!old || old.original_operation || !['RECHAZADA','EN_CONFLICTO'].includes(old.state) || old.result?.resolved || pending)throw new Error('El original no admite otra revisión.');
   }
   await db.operations.add(header);await db.details.bulkAdd(lines);
  });
  await this.refresh();this.message.set('Registrado en este dispositivo. Pendiente de validación central.');this.schedule();return operation_id;
 }
 async details(operationId:string){return this.current().details.where('operation_id').equals(operationId).toArray();}
 async branchName(branchId:number){return (await this.current().branches.get(branchId))?.nombre ?? String(branchId);}
 private async applyResult(db:OfflineDatabase,op:LocalOperation,result:any,accounted=op.accounted){
  if(result.state==='CONFIRMADA' && op.original_operation){
   const original=await db.operations.get(op.original_operation);
   if(original)await db.operations.update(original.operation_id,{result:{...original.result,resolved:true,revision:op.operation_id}});
  }
  const savedResult=op.result?.resolved && result.resolved===undefined
    ? {...result,resolved:true,revision:op.result.revision} : result;
  await db.operations.update(op.operation_id,{state:result.state,result:savedResult,reason:result.reason||'',accounted});
 }
 async compensate(op:LocalOperation,reason:string,amount:string){const result=await firstValueFrom(this.http.post<any>(this.base+'/conflictos/'+op.operation_id+'/compensar',{motivo:reason,compensacion:amount}));await this.current().operations.update(op.operation_id,{result:{...op.result,resolved:result.resuelto},reason});await this.refresh();}
 async sync(){
  if(this.busy() || !navigator.onLine)return;const token=localStorage.getItem(environment.claveTokenJwt);if(!token)return;
  this.busy.set(true);
  try{await this.locked(async()=>{
   const db=this.current();const rows=await db.operations.where('state').equals('PENDIENTE').limit(20).toArray();if(!rows.length)return;
   const wire=[];
   for(const op of rows){const {state,attempts,reason,result,accounted,...data}=op;wire.push({...data,items:(await this.details(op.operation_id)).map(({operation_id,...line})=>line)});}
   await db.operations.bulkPut(rows.map(o=>({...o,state:'ENVIANDO' as const,attempts:o.attempts+1})));
   try{
    const response=await firstValueFrom(this.http.post<any>(this.base+'/sincronizacion/lote',{operations:wire}).pipe(timeout(30000)));
    await db.transaction('rw',db.operations,async()=>{
     for(const op of rows){
      const result=response.results?.find((r:any)=>r.operation_id===op.operation_id);
      if(result)await this.applyResult(db,op,result);
      else await db.operations.update(op.operation_id,{state:'PENDIENTE',reason:'El servidor no devolvió confirmación para esta operación.'});
     }
    });
    this.failures=0;this.message.set('Resultados de sincronización guardados. Las operaciones se conservan.');
   }catch(e:any){await db.operations.bulkPut(rows.map(o=>({...o,state:'PENDIENTE' as const,attempts:o.attempts+1,reason:this.error(e)})));throw e;}
  });await this.refresh();}catch(e:any){this.failures++;this.message.set(this.error(e));}finally{this.busy.set(false);this.schedule();}
 }
 private schedule(){if(this.timer)clearTimeout(this.timer);if(!this.db || !navigator.onLine)return;this.timer=setTimeout(()=>void this.sync(),Math.min(60000,5000*2**Math.min(this.failures,4)));}
 async exportPending(){const db=this.current();const operations=[];for(const op of await db.operations.toArray()){if(op.state==='CONFIRMADA')continue;const {state,attempts,reason,result,accounted,...data}=op;operations.push({...data,items:(await this.details(op.operation_id)).map(({operation_id,...line})=>line)});}return JSON.stringify({operations},null,2);}
 private error(e:any){return typeof e.error?.detail==='string'?e.error.detail:(e.message||'Error de comunicación. Las operaciones siguen guardadas.');}
}
