/**
 * =============================================================================
 * FASHIONSTORE - MODAL DE REGISTRO DE MOVIMIENTOS DE INVENTARIO (CU11)
 * Sistemas de Información II - UAGRM
 * -----------------------------------------------------------------------------
 * Formulario para registrar operaciones de Entrada, Salida y Traspaso.
 * Consulta de forma reactiva el stock disponible en la sucursal seleccionada
 * y previene proactivamente transacciones de salida que excedan las existencias.
 * =============================================================================
 */

import { Component, OnInit, inject, output, signal } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { MovimientoInventarioService } from '../../../core/services/movimiento-inventario.service';
import { GeografiaService } from '../../../core/services/geografia.service';
import { PrendaService } from '../../../core/services/prenda.service';
import { Sucursal } from '../../../core/models/catalogo.model';
import { MovimientoInventarioCrear, TipoMovimiento } from '../../../core/models/movimiento.model';

export interface OpcionVariante {
  id_variante_prenda: number;
  sku_variante: string;
  nombre_prenda: string;
  talla: string;
  color: string;
  etiqueta: string;
}

@Component({
  selector: 'app-movimiento-modal',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './movimiento-modal.html',
  styleUrl: './movimiento-modal.scss',
})
export class MovimientoModal implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly movimientoService = inject(MovimientoInventarioService);
  private readonly geografiaService = inject(GeografiaService);
  private readonly prendaService = inject(PrendaService);

  // ---------------------------------------------------------------------------
  // SALIDAS
  // ---------------------------------------------------------------------------

  readonly cerrado = output<void>();
  readonly guardado = output<string>();

  // ---------------------------------------------------------------------------
  // ESTADO REACTIVO
  // ---------------------------------------------------------------------------

  readonly cargando = signal(false);
  readonly cargandoOpciones = signal(true);
  readonly mensajeError = signal<string | null>(null);

  readonly sucursales = signal<Sucursal[]>([]);
  readonly variantes = signal<OpcionVariante[]>([]);

  /** Stock físico actual de la variante en la sucursal seleccionada */
  readonly stockActual = signal<number | null>(null);
  readonly consultandoStock = signal(false);

  formulario!: FormGroup;
  private operationId: string | null = null;

  // ---------------------------------------------------------------------------
  // CICLO DE VIDA
  // ---------------------------------------------------------------------------

  ngOnInit(): void {
    this.formulario = this.fb.group({
      id_sucursal: [null, [Validators.required]],
      id_sucursal_destino: [null],
      id_variante_prenda: [null, [Validators.required]],
      tipo: ['Entrada' as TipoMovimiento, [Validators.required]],
      cantidad: [1, [Validators.required, Validators.min(1), Validators.pattern(/^\d+$/)]],
      motivo: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(255)]],
    });

    this.cargarListasAuxiliares();
  }

  private cargarListasAuxiliares(): void {
    this.cargandoOpciones.set(true);

    this.geografiaService.listarSucursales().subscribe({
      next: (sucursales) => {
        this.sucursales.set(sucursales);
        if (sucursales.length > 0 && !this.formulario.value.id_sucursal) {
          this.formulario.patchValue({ id_sucursal: sucursales[0].id_sucursal });
        }
        this.verificarConsultaStock();
      },
      error: () => {},
    });

    this.prendaService.listar().subscribe({
      next: (prendas) => {
        const opciones: OpcionVariante[] = [];
        for (const p of prendas) {
          if (p.variantes && p.variantes.length > 0) {
            for (const v of p.variantes) {
              const talla = v.talla || 'Sin talla';
              const color = v.color || 'Sin color';
              opciones.push({
                id_variante_prenda: v.id_variante_prenda,
                sku_variante: v.sku_variante,
                nombre_prenda: p.nombre,
                talla,
                color,
                etiqueta: `${v.sku_variante} — ${p.nombre} (${talla} / ${color})`,
              });
            }
          }
        }
        this.variantes.set(opciones);
        if (opciones.length > 0 && !this.formulario.value.id_variante_prenda) {
          this.formulario.patchValue({ id_variante_prenda: opciones[0].id_variante_prenda });
        }
        this.cargandoOpciones.set(false);
        this.verificarConsultaStock();
      },
      error: () => {
        this.cargandoOpciones.set(false);
      },
    });
  }

  // ---------------------------------------------------------------------------
  // VERIFICACIÓN DE STOCK EN TIEMPO REAL
  // ---------------------------------------------------------------------------

  alCambiarSucursal(): void {
    if (Number(this.formulario.value.id_sucursal_destino) === Number(this.formulario.value.id_sucursal)) {
      this.formulario.controls['id_sucursal_destino'].setValue(null);
    }
    this.verificarConsultaStock();
  }

  get esTraspaso(): boolean { return this.formulario?.value?.tipo === 'Traspaso'; }

  get sucursalesDestino(): Sucursal[] {
    return this.sucursales().filter(s => s.id_sucursal !== Number(this.formulario.value.id_sucursal));
  }

  alCambiarTipo(): void {
    const destino = this.formulario.controls['id_sucursal_destino'];
    destino.setValidators(this.esTraspaso ? [Validators.required, Validators.min(1)] : []);
    destino.updateValueAndValidity();
    this.verificarConsultaStock();
  }

  alCambiarVariante(): void {
    this.verificarConsultaStock();
  }

  private verificarConsultaStock(): void {
    const idSucursal = Number(this.formulario?.value?.id_sucursal);
    const idVariante = Number(this.formulario?.value?.id_variante_prenda);

    if (idSucursal && idVariante) {
      this.consultandoStock.set(true);
      this.movimientoService.consultarStock(idSucursal, idVariante, this.esTraspaso).subscribe({
        next: (res) => {
          this.stockActual.set(res.stock);
          this.consultandoStock.set(false);
        },
        error: () => {
          this.stockActual.set(0);
          this.consultandoStock.set(false);
        },
      });
    } else {
      this.stockActual.set(null);
    }
  }

  get esSalidaOTraspaso(): boolean {
    const tipo = this.formulario?.value?.tipo;
    return tipo === 'Salida' || tipo === 'Traspaso';
  }

  get stockInsuficiente(): boolean {
    if (!this.esSalidaOTraspaso) return false;
    const stock = this.stockActual();
    if (stock === null) return false;
    const cantidad = Number(this.formulario?.value?.cantidad || 0);
    return cantidad > stock;
  }

  get bloqueadoPorStock(): boolean {
    // Un reintento puede recuperar un traspaso ya confirmado con saldo actual diferente.
    return this.stockInsuficiente && (!this.esTraspaso || this.operationId === null);
  }

  campoInvalido(nombreCampo: string): boolean {
    const control = this.formulario.controls[nombreCampo];
    return control.invalid && (control.touched || control.dirty);
  }

  // ---------------------------------------------------------------------------
  // ACCIONES
  // ---------------------------------------------------------------------------

  cerrar(): void {
    if (!this.cargando()) {
      this.cerrado.emit();
    }
  }

  guardar(): void {
    if (this.cargando()) return;
    if (this.formulario.invalid || this.bloqueadoPorStock) {
      this.formulario.markAllAsTouched();
      return;
    }
    if (this.esTraspaso && !navigator.onLine) {
      this.mensajeError.set('El traspaso requiere conexión. No se guardará como operación offline.');
      return;
    }
    if (this.esTraspaso && Number(this.formulario.value.id_sucursal_destino) === Number(this.formulario.value.id_sucursal)) {
      this.mensajeError.set('Selecciona una sucursal de destino distinta del origen.');
      return;
    }

    this.cargando.set(true);
    this.mensajeError.set(null);

    const v = this.formulario.value;
    const cuerpo: MovimientoInventarioCrear = {
      id_sucursal: Number(v.id_sucursal),
      id_variante_prenda: Number(v.id_variante_prenda),
      tipo: v.tipo as TipoMovimiento,
      cantidad: Number(v.cantidad),
      motivo: v.motivo.trim(),
    };
    if (this.esTraspaso) {
      this.operationId ??= crypto.randomUUID();
      cuerpo.id_sucursal_destino = Number(v.id_sucursal_destino);
      cuerpo.operation_id = this.operationId;
    }

    this.movimientoService.crear(cuerpo).subscribe({
      next: (creado) => {
        this.cargando.set(false);
        this.guardado.emit('movimiento_salida' in creado
          ? `Traspaso confirmado: ${creado.movimiento_salida.sucursal_nombre || 'Origen'} → ${creado.movimiento_entrada.sucursal_nombre || 'Destino'} (${creado.cantidad} un.).`
          : `Movimiento de ${creado.tipo} (${creado.cantidad} un.) registrado exitosamente.`);
      },
      error: (error: Error) => {
        this.cargando.set(false);
        this.mensajeError.set(error.message + (this.esTraspaso
          ? ' Reintenta sin cambiar los datos. Antes de iniciar otro traspaso, revisa el historial.' : ''));
      },
    });
  }
}
