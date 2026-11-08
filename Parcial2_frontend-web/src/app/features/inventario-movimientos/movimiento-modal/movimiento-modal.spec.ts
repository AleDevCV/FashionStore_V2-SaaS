import { TestBed } from '@angular/core/testing';
import { of, Subject, throwError } from 'rxjs';
import { MovimientoModal } from './movimiento-modal';
import { MovimientoInventarioService } from '../../../core/services/movimiento-inventario.service';
import { GeografiaService } from '../../../core/services/geografia.service';
import { PrendaService } from '../../../core/services/prenda.service';

describe('A3 formulario de traspaso online', () => {
  let service: jasmine.SpyObj<MovimientoInventarioService>;
  beforeEach(async () => {
    service = jasmine.createSpyObj('Movimientos', ['consultarStock', 'crear']);
    service.consultarStock.and.returnValue(of({id_sucursal:1,id_variante_prenda:7,stock:5}));
    await TestBed.configureTestingModule({imports:[MovimientoModal],providers:[
      {provide:MovimientoInventarioService,useValue:service},
      {provide:GeografiaService,useValue:{listarSucursales:()=>of([{id_sucursal:1,nombre:'Origen'},{id_sucursal:2,nombre:'Destino'}])}},
      {provide:PrendaService,useValue:{listar:()=>of([{variantes:[{id_variante_prenda:7,sku_variante:'SKU',talla:'M',color:'Azul'}]}])}},
    ]}).compileComponents();
  });
  function form() {
    const fixture=TestBed.createComponent(MovimientoModal);fixture.detectChanges();
    const component=fixture.componentInstance;
    component.formulario.patchValue({tipo:'Traspaso',cantidad:2,motivo:'Reponer sucursal'});
    component.alCambiarTipo();
    return {fixture,component};
  }
  it('exige destino explícito y no permite usar el origen como destino',()=>{
    const {fixture,component}=form();fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('#campo-destino')).not.toBeNull();
    component.guardar();expect(service.crear).not.toHaveBeenCalled();
    component.formulario.patchValue({id_sucursal_destino:1});
    component.guardar();expect(service.crear).not.toHaveBeenCalled();
    expect(service.consultarStock).toHaveBeenCalledWith(1,7,true);
  });
  it('conserva UUID en reintentos aun si el saldo actual ya cambió',()=>{
    const {component}=form();component.formulario.patchValue({id_sucursal_destino:2});
    service.crear.and.returnValue(throwError(()=>new Error('Sin respuesta de red')));
    component.guardar();const first=service.crear.calls.mostRecent().args[0];
    expect(first.operation_id).toMatch(/^[0-9a-f-]{36}$/);
    expect(first.id_sucursal_destino).toBe(2);
    component.stockActual.set(0);component.guardar();
    const retry=service.crear.calls.mostRecent().args[0];
    expect(service.crear).toHaveBeenCalledTimes(2);
    expect(retry).toEqual(first);
  });
  it('no envía doble solicitud mientras espera confirmación',()=>{
    const {component}=form();component.formulario.patchValue({id_sucursal_destino:2});
    service.crear.and.returnValue(new Subject<never>());component.guardar();component.guardar();
    expect(service.crear).toHaveBeenCalledTimes(1);
  });
  it('impide encolar o enviar un traspaso sin conexión',()=>{
    const {component}=form();component.formulario.patchValue({id_sucursal_destino:2});
    spyOnProperty(navigator,'onLine','get').and.returnValue(false);
    component.guardar();expect(service.crear).not.toHaveBeenCalled();
    expect(component.mensajeError()).toContain('requiere conexión');
  });
});
