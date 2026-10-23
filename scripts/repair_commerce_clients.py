from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(relative,fn):
 p=ROOT/relative;p.write_text(fn(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
def checkout(s):
 s=s.replace("import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';","import { FormBuilder, ReactiveFormsModule, FormsModule, Validators } from '@angular/forms';\nimport {HttpClient} from '@angular/common/http';\nimport {environment} from '../../../environments/environment';")
 s=s.replace('imports: [CommonModule, ReactiveFormsModule]','imports: [CommonModule, ReactiveFormsModule,FormsModule]')
 s=s.replace('  readonly ID_SUCURSAL = 1;',"  ID_SUCURSAL=0;\n  branches=signal<any[]>([]);\n  private http=inject(HttpClient);")
 s=s.replace('  ngOnInit(): void {',"  ngOnInit(): void {\n    this.http.get<any>(environment.apiUrl+'/api/contexto').subscribe({next:ctx=>{this.branches.set(ctx.sucursales);this.ID_SUCURSAL=ctx.sucursales[0]?.id_sucursal||0;},error:()=>this.error.set('Inicie sesión como cliente para elegir una sucursal.')});")
 start=s.index('      const idCliente = await this._obtenerIdCliente();',s.index('  async confirmarPagoQR()'));end=s.index('      this.venta_confirmada.set',start)
 s=s[:start]+'''      const status=await this.venta.estadoPago(reservaActual.id_reserva).toPromise();
      if(!status.pagada){this.error.set('Pago pendiente de confirmación por el personal autorizado. Estado: '+status.estado);return;}
      const ventaRes=status.venta;
'''+s[end:]
 s=s.replace('    enviar_email: [true]','    enviar_email: [false]')
 return s
edit('Parcial2_frontend-web/src/app/features/checkout/checkout.ts',checkout)
edit('Parcial2_frontend-web/src/app/features/checkout/checkout.html',lambda s:s.replace('<h2 class="checkout-card__titulo">🛍️ Resumen del pedido</h2>','<h2 class="checkout-card__titulo">Resumen del pedido</h2><label>Sucursal de entrega<select [(ngModel)]="ID_SUCURSAL">@for(b of branches();track b.id_sucursal){<option [ngValue]="b.id_sucursal">{{b.nombre}}</option>}</select></label>').replace('✅ Confirmar pago QR','Consultar confirmación').replace('Escanea este código QR para pagar','QR de demostración para validación en caja').replace('⏱ Válido por 15 minutos. Una vez pagado, haz clic en "Confirmar pago".','Válido por 15 minutos. El personal registra la verificación del cobro; este QR de demostración no se integra con una entidad bancaria.'))
def success(s):
 start=s.index('  verificarPago(): void {');end=s.index('  ngOnDestroy(): void {',start)
 s=s[:start]+'''  verificarPago(): void {
    const id=this.idReserva();if(!id)return;let attempts=0;
    const check=()=>this.ventaService.estadoPago(id).subscribe({next:async status=>{
      if(status.pagada){this.estado.set('exito');clearInterval(this.pollInterval);this.venta_confirmada.set(status.venta);this.carritoService.limpiarComprados(status.venta.items);try{this.comprobante_generado.set(await this.comprobanteService.obtenerPorVenta(status.venta.id_venta).toPromise()||null);}catch{}}
      else if(++attempts>=15){this.estado.set('error');clearInterval(this.pollInterval);}
    },error:()=>{this.estado.set('error');clearInterval(this.pollInterval);}});
    this.pollInterval=setInterval(check,2000);check();
  }

'''+s[end:]
 s=s.replace('/mi-cuenta/reservas','/mi-cuenta/pedidos')
 return s
edit('Parcial2_frontend-web/src/app/features/pago/pago-exitoso/pago-exitoso.ts',success)
def orders(s):
 s="import {ClienteService} from '../../../core/services/cliente.service';\nimport {switchMap} from 'rxjs';\n"+s
 s=s.replace("{{ pedido.total.toFixed(2) }}","{{ pedido.total | number:'1.2-2' }}")
 s=s.replace('    const idCliente = this._idCliente();\n    this.ventaSvc.misPedidos(idCliente).subscribe({',"    this.clienteService.obtenerPropio().pipe(switchMap(c=>this.ventaSvc.misPedidos(c.id_cliente))).subscribe({")
 s=s.replace('export class MisPedidos implements OnInit {','export class MisPedidos implements OnInit {\n  private clienteService=inject(ClienteService);')
 start=s.index('  private _idCliente(): number {');s=s[:start]+'}\n';return s
edit('Parcial2_frontend-web/src/app/features/cliente/mis-pedidos/mis-pedidos.ts',orders)
def auth(s):
 marker='      localStorage.setItem(this.claveToken, token);'
 s=s.replace(marker,"      const key=`fashionstore_p2_cart_${usuario.tenant_id}:${usuario.id_usuario}`;\n      const publicKey='fashionstore_p2_cart_public_'+(localStorage.getItem('fashionstore_p2_empresa')||'demo-a');\n      if(!localStorage.getItem('fashionstore_p2_active')&&!localStorage.getItem(key)&&localStorage.getItem(publicKey)){localStorage.setItem(key,localStorage.getItem(publicKey)!);localStorage.removeItem(publicKey);}\n"+marker,1);return s
edit('Parcial2_frontend-web/src/app/core/services/auth.service.ts',auth)
edit('Parcial2_frontend-web/src/app/core/empresa-selector.ts',lambda s:s.replace("localStorage.setItem('fashionstore_p2_empresa',value);","localStorage.setItem('fashionstore_p2_empresa',value);window.dispatchEvent(new Event('fashionstore-session'));") )
def pos(s):
 s="import {firstValueFrom} from 'rxjs';\n"+s
 s=s.replace('  confirmarVenta(): void {','  async confirmarVenta(): Promise<void> {')
 marker='    this.posService.procesarVenta(payload).subscribe({'
 s=s.replace(marker,'''    if(!payload.id_reserva){
      try{const quote=await firstValueFrom(this.posService.cotizar(payload));
        const changes=quote.items.some((line:any)=>Number(payload.items.find(x=>x.id_variante_prenda===line.id_variante_prenda)?.precio_unitario)!==Number(line.precio_unitario));
        if(changes){this.itemsCarrito.update(rows=>rows.map(row=>({...row,precio_unitario:Number(quote.items.find((line:any)=>line.id_variante_prenda===row.variante.id_variante_prenda).precio_unitario)})));this.procesandoVenta.set(false);this.errorCobro.set('Los precios se actualizaron por cantidad u oferta. Revise el total y confirme nuevamente el cobro.');return;}
      }catch(e:any){this.procesandoVenta.set(false);this.errorCobro.set(e.error?.detail||'No se pudo cotizar la venta.');return;}
    }
'''+marker)
 start=s.index('      const urlCompleta =',s.index('    verComprobantePDF'));end=s.index('\n    }',start);s=s[:start]+"      this.descarga.abrir(url);"+s[end:]
 if 'private readonly descarga' not in s:s=s.replace('export class Pos implements OnInit {','export class Pos implements OnInit {\n  private readonly descarga=inject(DescargaService);')
 return s
edit('Parcial2_frontend-web/src/app/features/pos/pos.ts',pos)
edit('Parcial2_frontend-web/src/app/core/services/pos.service.ts',lambda s:s.replace('  procesarVenta(datos:',"  cotizar(datos:POSVentaCrear):Observable<any>{return this.http.post(environment.apiUrl+'/api/ventas/cotizar',{id_sucursal:datos.id_sucursal,items:datos.items.map(({id_variante_prenda,cantidad})=>({id_variante_prenda,cantidad}))});}\n\n  procesarVenta(datos:"))
