import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { CategoriaService } from '../../core/services/categoria.service';
import { GeografiaService } from '../../core/services/geografia.service';
import { InventarioService } from '../../core/services/inventario.service';
import { TemporadaService } from '../../core/services/temporada.service';
import { InventarioMonitoreo } from './inventario-monitoreo';

describe('Monitoreo de disponibilidad CU08', () => {
  it('distingue la retención y muestra su liberación sin alterar el físico', () => {
    let retenido = 3;
    TestBed.configureTestingModule({
      imports: [InventarioMonitoreo],
      providers: [
        provideRouter([]),
        { provide: GeografiaService, useValue: { listarSucursales: () => of([]) } },
        { provide: CategoriaService, useValue: { listar: () => of([]) } },
        { provide: TemporadaService, useValue: { listar: () => of([]) } },
        { provide: InventarioService, useValue: {
          obtenerResumen: () => of(null),
          monitorear: () => of([{
            id_sucursal: 1, sucursal: 'Central', id_prenda: 1, prenda_nombre: 'Camisa',
            id_variante_prenda: 1, sku_variante: 'C1', stock: 5, stock_fisico: 5,
            stock_retenido: retenido, stock_disponible: 5 - retenido,
          }]),
        } },
      ],
    });
    const fixture = TestBed.createComponent(InventarioMonitoreo);
    fixture.detectChanges();
    const table = fixture.nativeElement as HTMLElement;
    const cells = () => Array.from(table.querySelectorAll('tbody tr td')).map(td => td.textContent?.trim());
    expect(cells().slice(5, 9)).toEqual(['5', '3', '2', 'Bajo stock']);
    retenido = 0;
    fixture.componentInstance.cargarDatos();
    fixture.detectChanges();
    expect(cells().slice(5, 9)).toEqual(['5', '0', '5', 'Óptimo']);
  });
});
