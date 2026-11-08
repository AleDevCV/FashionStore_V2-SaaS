import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController,provideHttpClientTesting } from '@angular/common/http/testing';
import { OfflineService } from './offline.service';
import { OfflineDatabase,LocalOperation } from './offline-store';

describe('A5 reconciliación IndexedDB real',()=>{
 let service:OfflineService,db:OfflineDatabase,http:HttpTestingController;
 let namespace='90007:90011',sequence=0;let states:Map<string,string>,requests:string[][];
 let stock:number,failAt:number|null,hook:((request:number)=>Promise<void>)|null,wrongBranch:boolean;
 const id=(i:number)=>'00000000-0000-4000-8000-'+String(i).padStart(12,'0');
 const snapshot=(branch:number,stock:number)=>({tenant_id:90007,author_id:Number(namespace.split(':')[1]),branch:{id_sucursal:branch,nombre:'A5 '+branch},lease:'isolated-only',lease_expires:Date.now()/1000+3600,can_sell:true,products:[{id_prenda:1,id_variante_prenda:1,nombre:'Test',precio_base:'50.00',precio_adicional:'0.00',stock}],customers:[],operation_results:[]});
 beforeEach(async()=>{
  namespace='90007:'+(90011+sequence++);localStorage.setItem('fashionstore_p2_active',namespace);
  TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting()]});
  service=TestBed.inject(OfflineService);spyOn<any>(service,'schedule').and.stub();http=TestBed.inject(HttpTestingController);
  await service.open();db=new OfflineDatabase(namespace);await db.open();states=new Map();requests=[];stock=999;failAt=null;hook=null;wrongBranch=false;
  const value=snapshot(1,1000);await db.meta.put({key:'snapshot',value});
  await db.products.put({id_prenda:1,precio_base:'50.00'});await db.variants.put({id_variante_prenda:1,id_prenda:1,precio_adicional:'0.00'});
  await db.stocks.bulkPut([{branch_id:1,id_variante_prenda:1,stock:1000},{branch_id:2,id_variante_prenda:1,stock:1000}]);service.snapshot.set(value);
 });
 afterEach(async()=>{
  http.verify();db.close();localStorage.removeItem('fashionstore_p2_active');await service.open();
  // Each case uses a distinct synthetic account; no database/operation is cleared.
  TestBed.resetTestingModule();
 });
 async function seed(count:number,foreignPrefix=false){
  const rows:LocalOperation[]=[];
  for(let i=1;i<=count;i++){
   const state=i===count?'CONFIRMADA':i%2===0?'EN_CONFLICTO':'RECHAZADA';states.set(id(i),state);
   rows.push({operation_id:id(i),version:1,tenant_id:90007,author_id:Number(namespace.split(':')[1]),branch_id:foreignPrefix&&i<count?2:1,device_id:id(999),kind:'venta',occurred_at:new Date(Date.UTC(2026,0,1)+i*1000).toISOString(),lease:'isolated-only',customer_id:null,cash_received:'50.00',original_operation:null,state,attempts:0,reason:'',accounted:false});
  }
  await db.operations.bulkAdd(rows);await db.details.bulkAdd(rows.map(op=>({operation_id:op.operation_id,id_variante_prenda:1,cantidad:1,precio_unitario:'50.00'})));
 }
 async function download(wrongIdentity=false,offline=false,duplicate=false){
  let done=false;const completion=service.download(1).finally(()=>done=true);
  for(let i=0;i<500&&!done;i++){
   await new Promise(r=>setTimeout(r,10));
   for(const req of http.match(r=>r.url.endsWith('/api/offline/catalogo'))){
    const ids=req.request.params.getAll('operation_ids')||[];requests.push(ids);expect(ids.length).toBeLessThanOrEqual(50);
    if(hook)await hook(requests.length);
    if(offline||requests.length===failAt){req.flush({detail:'Controlled A5 connection interruption'},{status:503,statusText:'Service Unavailable'});continue;}
    const value:any=snapshot(wrongBranch?2:1,stock);if(wrongIdentity)value.tenant_id=99999;
    value.operation_results=ids.filter(op=>states.has(op)).map(op=>({operation_id:op,state:states.get(op),server_id:states.get(op)==='CONFIRMADA'?77:null}));
    if(duplicate)value.operation_results=[...value.operation_results,...value.operation_results];req.flush(value);
   }
  }
  await completion;
 }
 async function verify(count:number,rounds=1,foreignPrefix=false){
  await seed(count,foreignPrefix);const before=(await db.operations.toArray()).map(({state,accounted,result,reason,...rest})=>rest);
  for(let i=0;i<rounds;i++)await download();
  const tail=(await db.operations.get(id(count)))!;const available=service.catalog()[0].available;const expected=999-(foreignPrefix?0:Math.floor((count-1)/2));
  console.log('A5_REPRO:'+JSON.stringify({client:'Angular native IndexedDB',queue:count,rounds,other_branch_prefix:foreignPrefix,requested_unique:new Set(requests.flat()).size,HTTP_requests:requests.length,tail_state:tail.state,tail_accounted:tail.accounted,available,expected}));
  expect((await db.operations.toArray()).map(({state,accounted,result,reason,...rest})=>rest)).toEqual(before);expect(await db.details.count()).toBe(count);
  expect(tail.accounted).withContext('Confirmed operation after terminal prefix must be reconciled').toBeTrue();expect(available).toBe(expected);
 }
 for(const count of [1,49,50,51,125])it('cola '+count+': resultado confirmado posterior',async()=>verify(count));
 it('tres descargas no quedan en el mismo prefijo de 50',async()=>verify(51,3));
 it('otra sucursal no bloquea el lote de la sucursal solicitada',async()=>verify(51,1,true));
 it('sin resultado conserva PENDIENTE y ENVIANDO',async()=>{
  await seed(2);states.clear();await db.operations.update(id(1),{state:'PENDIENTE'});await db.operations.update(id(2),{state:'ENVIANDO'});
  await download();expect((await db.operations.toArray()).map(r=>r.state)).toEqual(['PENDIENTE','ENVIANDO']);expect((await db.operations.toArray()).every(r=>!r.accounted)).toBeTrue();
 });
 it('otra empresa en la respuesta no cambia catálogo ni operación',async()=>{
  await seed(1);const before=(await db.meta.get('snapshot')).value;await download(true);
  expect((await db.meta.get('snapshot')).value).toEqual(before);expect((await db.operations.get(id(1)))!.accounted).toBeFalse();
 });
 it('reapertura de IndexedDB no perpetúa bloqueo posterior a 50',async()=>{
  await seed(51);await download();db.close();(service as any).db.close();
  service=TestBed.runInInjectionContext(()=>new OfflineService());spyOn<any>(service,'schedule').and.stub();
  await service.open();db=new OfflineDatabase(namespace);await db.open();
  await download();expect(await db.operations.count()).toBe(51);expect((await db.operations.get(id(51)))!.accounted).toBeTrue();
 });
 it('respuesta duplicada y descargas repetidas no duplican descuento',async()=>{
  await seed(1);await download(false,false,true);await download(false,false,true);
  expect(await db.operations.count()).toBe(1);expect(await db.details.count()).toBe(1);expect(service.catalog()[0].available).toBe(999);
 });
 it('conexión interrumpida conserva cola y al reconectar progresa 125',async()=>{
  await seed(125);const before=await db.operations.toArray();const cache=(await db.meta.get('snapshot')).value;
  await download(false,true);expect(await db.operations.toArray()).toEqual(before);expect((await db.meta.get('snapshot')).value).toEqual(cache);
  await download();expect(await db.operations.count()).toBe(125);expect((await db.operations.get(id(125)))!.accounted).toBeTrue();
 });
 it('pendiente solo cambia a confirmada con respuesta explícita',async()=>{
  await seed(1);await db.operations.update(id(1),{state:'PENDIENTE'});await download();
  const op=(await db.operations.get(id(1)))!;expect(op.state).toBe('CONFIRMADA');expect(op.accounted).toBeTrue();
 });
 it('una revisión local solo resuelve el original al confirmar en el servidor', async () => {
  await seed(1);
  await db.operations.update(id(1), { state: 'EN_CONFLICTO' });
  await db.branches.put(snapshot(1, 1000).branch);
  await db.meta.put({ key: 'device', value: id(999) });
  states.set(id(1), 'EN_CONFLICTO');
  await service.refresh();
  const revise = () => service.capture('venta', null, [{ variantId: 1, quantity: 1 }], '50.00', id(1));
  const first = await revise();
  expect((await db.operations.get(id(1)))?.result?.resolved).toBeFalsy();
  await expectAsync(revise()).toBeRejectedWithError('El original no admite otra revisión.');
  states.set(first, 'EN_CONFLICTO');
  await download();
  expect((await db.operations.get(id(1)))?.result?.resolved).toBeFalsy();
  const next = await revise();
  states.set(next, 'CONFIRMADA');
  await download();
  expect((await db.operations.get(id(1)))?.result?.resolved).toBeTrue();
  expect((await db.operations.get(id(1)))?.result?.revision).toBe(next);
  expect(await db.operations.count()).toBe(3);
 });
 it('sin candidatos renueva catálogo con una petición vacía',async()=>{
  await download();expect(requests).toEqual([[]]);expect((await db.meta.get('snapshot')).value.branch.id_sucursal).toBe(1);
 });
 it('125 UUID se recorren una vez en lotes 50 50 25',async()=>{
  await seed(125);await download();expect(requests.map(r=>r.length)).toEqual([50,50,25]);expect(new Set(requests.flat()).size).toBe(125);expect(service.message()).toContain('3/3');expect(await db.details.count()).toBe(125);
 });
 async function allConfirmed(){await seed(125);for(const key of states.keys())states.set(key,'CONFIRMADA');stock=875;await db.operations.toCollection().modify({state:'PENDIENTE'});}
 it('fallo del segundo lote conserva 50 y reintenta 75',async()=>{
  await allConfirmed();failAt=2;await download();expect((await db.operations.toArray()).filter(r=>r.accounted).length).toBe(50);expect(service.message()).toContain('parcial (1/3');expect(await db.meta.get('sync_lock')).toBeUndefined();expect(service.busy()).toBeFalse();
  failAt=null;requests=[];await download();expect(requests.map(r=>r.length)).toEqual([50,25]);expect((await db.operations.toArray()).every(r=>r.accounted)).toBeTrue();expect(service.catalog()[0].available).toBe(875);
 });
 it('fallo del tercer lote conserva 100 y reintenta 25',async()=>{
  await allConfirmed();failAt=3;await download();expect((await db.operations.toArray()).filter(r=>r.accounted).length).toBe(100);expect(service.message()).toContain('parcial (2/3');
  failAt=null;requests=[];await download();expect(requests.map(r=>r.length)).toEqual([25]);expect(service.catalog()[0].available).toBe(875);
 });
 it('rollback IndexedDB del segundo lote no deja medias confirmaciones',async()=>{
  await allConfirmed();const table=(service as any).db.operations;const original=table.update.bind(table);const update=spyOn(table,'update').and.callFake(((key:any,changes:any)=>key===id(75)?Promise.reject(new Error('Controlled A5 rollback')):original(key,changes)) as any);
  await download();expect((await db.operations.toArray()).filter(r=>r.accounted).length).toBe(50);expect((await db.operations.toArray()).filter(r=>r.result).length).toBe(50);expect(service.message()).toContain('parcial (1/3');
  update.and.callThrough();await download();expect((await db.operations.toArray()).every(r=>r.accounted)).toBeTrue();
 });
 it('UUID ausente al final de 125 conserva PENDIENTE',async()=>{
  await seed(125);states.delete(id(125));await db.operations.update(id(125),{state:'PENDIENTE'});await download();expect(requests.length).toBe(3);const tail=(await db.operations.get(id(125)))!;expect(tail.state).toBe('PENDIENTE');expect(tail.accounted).toBeFalse();
 });
 it('sucursal distinta en respuesta no modifica datos',async()=>{
  await seed(1);wrongBranch=true;const before=(await db.meta.get('snapshot')).value;await download();expect((await db.meta.get('snapshot')).value).toEqual(before);expect((await db.operations.get(id(1)))!.accounted).toBeFalse();
 });
 it('cambio de sesión durante respuesta no mezcla datos ni retiene bloqueo',async()=>{
  await seed(1);const before=(await db.meta.get('snapshot')).value;hook=async()=>{localStorage.setItem('fashionstore_p2_active','80000:80001');};
  await download();expect((await db.meta.get('snapshot')).value).toEqual(before);expect((await db.operations.get(id(1)))!.accounted).toBeFalse();expect(await db.meta.get('sync_lock')).toBeUndefined();localStorage.setItem('fashionstore_p2_active',namespace);
 });
 it('bloqueo ajeno impide HTTP sin borrar la cola',async()=>{
  await seed(1);await db.meta.put({key:'sync_lock',owner:'other-a5',expiresAt:Date.now()+60000});await download();expect(requests).toEqual([]);expect(await db.operations.count()).toBe(1);expect((await db.meta.get('sync_lock')).owner).toBe('other-a5');
 });
});
