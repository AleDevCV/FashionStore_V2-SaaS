import { TestBed } from '@angular/core/testing';
import { provideHttpClient,withInterceptors } from '@angular/common/http';
import { OfflineService } from './offline.service';
import { OfflineDatabase,LocalOperation } from './offline-store';
import runtimeFixture from '../../../a5-runtime-fixture';

describe('A5 HTTP real: Angular IndexedDB FastAPI PostgreSQL tmpfs',()=>{
 let fixture:any,service:OfflineService,db:OfflineDatabase;const requests:number[]=[];let original:any[];
 function configure(){
  TestBed.configureTestingModule({providers:[provideHttpClient(withInterceptors([(req,next)=>{
   if(req.url.startsWith('/a5-api/')){requests.push(req.params.getAll('operation_ids')?.length||0);return next(req.clone({setHeaders:{Authorization:fixture.header.Authorization}}));}return next(req);
  }]))]});
 }
 beforeAll(async()=>{
  fixture=runtimeFixture;
  localStorage.setItem('fashionstore_p2_active',fixture.namespace);
  configure();
  service=TestBed.inject(OfflineService);spyOn<any>(service,'schedule').and.stub();(service as any).base='/a5-api/api';await service.open();
  db=new OfflineDatabase(fixture.namespace);await db.open();
  for(const snapshot of fixture.before){
   await db.branches.put(snapshot.branch);
   for(const row of snapshot.products){await db.products.put({...row});await db.variants.put({...row});await db.stocks.put({branch_id:snapshot.branch.id_sucursal,id_variante_prenda:row.id_variante_prenda,stock:row.stock});}
   await db.customers.bulkPut(snapshot.customers);
  }
  await db.meta.put({key:'snapshot',value:fixture.before[0]});service.snapshot.set(fixture.before[0]);
  for(let i=0;i<fixture.operations.length;i++){
   const {items,...wire}=fixture.operations[i];const result=fixture.results[i];
   await db.operations.add({...wire,state:result.state,attempts:1,result,reason:result.reason||'',accounted:false} as LocalOperation);
   await db.details.bulkAdd(items.map((line:any)=>({...line,operation_id:wire.operation_id})));
  }
  original=(await db.operations.toArray()).map(({state,accounted,result,reason,...wire})=>wire);
 });
 afterAll(async()=>{db.close();localStorage.removeItem('fashionstore_p2_active');await service.open();TestBed.resetTestingModule();});
 it('125 UUID reales en 3 lotes contabilizan 75 sin afectar los 2 de otra sucursal',async()=>{
  await service.download(fixture.before[0].branch.id_sucursal);
  expect(service.message()).toContain('3/3');expect(requests).toEqual([50,50,25]);
  expect((await db.operations.toArray()).filter(r=>r.accounted).length).toBe(75);expect(service.catalog()[0].available).toBe(900);
  expect((await db.operations.toArray()).filter(r=>r.branch_id===fixture.before[1].branch.id_sucursal).every(r=>!r.accounted)).toBeTrue();
 });
 it('otra sucursal, reapertura y reintento conservan 127 cabeceras y 127 detalles',async()=>{
  (service as any).db.close();TestBed.resetTestingModule();configure();service=TestBed.inject(OfflineService);spyOn<any>(service,'schedule').and.stub();(service as any).base='/a5-api/api';await service.open();
  await service.download(fixture.before[1].branch.id_sucursal);expect(service.catalog()[0].available).toBe(998);
  (service as any).db.close();TestBed.resetTestingModule();configure();service=TestBed.inject(OfflineService);spyOn<any>(service,'schedule').and.stub();(service as any).base='/a5-api/api';await service.open();
  await service.download(fixture.before[0].branch.id_sucursal);
  expect(service.catalog()[0].available).toBe(900);expect(await db.operations.count()).toBe(127);expect(await db.details.count()).toBe(127);
  expect((await db.operations.toArray()).map(({state,accounted,result,reason,...wire})=>wire)).toEqual(original);
  expect((await db.operations.toArray()).filter(r=>r.accounted).length).toBe(77);
  localStorage.setItem('fashionstore_p2_active',fixture.other_company.namespace);await service.open();expect(service.operations()).toEqual([]);expect(service.snapshot()).toBeNull();
 });
});
