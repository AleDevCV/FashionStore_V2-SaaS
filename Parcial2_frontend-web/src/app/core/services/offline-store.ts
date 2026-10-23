import Dexie,{Table} from 'dexie';
export type LocalState='PENDIENTE'|'ENVIANDO'|'CONFIRMADA'|'RECHAZADA'|'EN_CONFLICTO';
export interface LocalOperation {
 operation_id:string;version:1;tenant_id:number;author_id:number;branch_id:number;device_id:string;kind:'venta'|'reserva';occurred_at:string;lease:string;customer_id:number|null;cash_received:string|null;original_operation:string|null;
 state:LocalState;attempts:number;reason:string;result?:any;accounted:boolean;
}
export class OfflineDatabase extends Dexie {
 products!:Table<any,number>;variants!:Table<any,number>;stocks!:Table<any,[number,number]>;customers!:Table<any,number>;branches!:Table<any,number>;operations!:Table<LocalOperation,string>;details!:Table<any,[string,number]>;meta!:Table<any,string>;
 constructor(namespace:string){super('fashionstore-p2-'+namespace);this.version(1).stores({products:'id_prenda',variants:'id_variante_prenda,id_prenda',customers:'id_cliente',branches:'id_sucursal',operations:'operation_id,state,kind,occurred_at,original_operation',details:'[operation_id+id_variante_prenda],operation_id',meta:'key'});this.version(2).stores({stocks:'[branch_id+id_variante_prenda],branch_id'});}
}
export function cents(value:any):number {
 const text=String(value??0);if(!/^\d+(\.\d{1,2})?$/.test(text))throw new Error('Importe inválido.');
 const [whole,fraction='']=text.split('.');const result=Number(whole)*100+Number(fraction.padEnd(2,'0'));if(!Number.isSafeInteger(result))throw new Error('Importe fuera de rango.');return result;
}
export function priceCents(product:any,variant:any,quantity:number):number {
 const prices=[cents(product.precio_base)];
 if(product.precio_mayorista!=null && quantity>=(product.umbral_mayorista||6))prices.push(cents(product.precio_mayorista));
 const day=new Date().toISOString().slice(0,10);
 if(product.precio_oferta!=null && (!product.oferta_inicio || product.oferta_inicio<=day) && (!product.oferta_fin || product.oferta_fin>=day))prices.push(cents(product.precio_oferta));
 return Math.min(...prices)+cents(variant.precio_adicional);
}
