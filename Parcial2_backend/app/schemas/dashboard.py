"""
=============================================================================
FASHIONSTORE - ESQUEMAS DEL DASHBOARD GERENCIAL Y KPIS (CU24)
Sistemas de Información II - UAGRM
-----------------------------------------------------------------------------
Modelos Pydantic para validar y serializar los datos analíticos del panel
ejecutivo: resumen financiero, conversión de probadores, rendimiento
multisucursal, top de ventas y salud de existencias.
=============================================================================
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class KPISummary(BaseModel):
    """Métricas ejecutivas agregadas en tiempo real."""

    model_config = ConfigDict(from_attributes=True)

    ingresos_totales: float = Field(..., description="Suma acumulada de ventas presenciales y online (Bs)")
    total_ventas: int = Field(..., description="Número total de transacciones completadas")
    ticket_promedio: float = Field(..., description="Monto promedio por transacción (Bs)")
    total_reservas: int = Field(..., description="Total de solicitudes de prueba en probadores (CU16)")
    reservas_atendidas: int = Field(..., description="Reservas convertidas en mostrador (CU17/CU19)")
    tasa_conversion_reservas: float = Field(..., description="Porcentaje de efectividad probador -> venta (%)")
    stock_total_piezas: int = Field(..., description="Total de prendas físicas en toda la cadena")
    valor_inventario_estimado: float = Field(..., description="Valoración financiera del stock a precio de venta (Bs)")


class VentaPorPeriodo(BaseModel):
    """Serie cronológica para gráficos de tendencia diaria."""

    model_config = ConfigDict(from_attributes=True)

    fecha: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    total_ingresos: float = Field(..., description="Ingresos facturados en la fecha (Bs)")
    cantidad_ventas: int = Field(..., description="Número de ventas registradas")


class DistribucionCanal(BaseModel):
    """Proporción de ingresos y transacciones por canal de venta."""

    model_config = ConfigDict(from_attributes=True)

    canal: str = Field(..., description="Canal de venta: Presencial u Online")
    total_ingresos: float = Field(..., description="Ingresos generados por el canal (Bs)")
    cantidad_ventas: int = Field(..., description="Transacciones generadas por el canal")
    porcentaje: float = Field(..., description="Participación porcentual en ventas (%)")


class DistribucionMetodoPago(BaseModel):
    """Distribución de pagos según el instrumento utilizado."""

    model_config = ConfigDict(from_attributes=True)

    metodo_pago: str = Field(..., description="Efectivo, Tarjeta, QR Dinámico, Stripe, etc.")
    total_ingresos: float = Field(..., description="Monto recaudado (Bs)")
    cantidad_ventas: int = Field(..., description="Número de pagos con este método")
    porcentaje: float = Field(..., description="Participación en el total (%)")


class SucursalReservaRendimiento(BaseModel):
    """Métricas de tráfico omnicanal y uso de probadores por sucursal física."""

    model_config = ConfigDict(from_attributes=True)

    id_sucursal: int
    sucursal: str = Field(..., description="Nombre de la sucursal física")
    ciudad: Optional[str] = None
    total_reservas: int = Field(..., description="Total de reservas solicitadas para esta tienda")
    atendidas: int = Field(..., description="Reservas atendidas/completadas")
    pendientes: int = Field(..., description="Reservas pendientes o en probador")
    canceladas: int = Field(..., description="Reservas no asistidas o liberadas")
    tasa_efectividad: float = Field(..., description="Porcentaje de atención exitosa (%)")


class TopPrendaVendida(BaseModel):
    """Ranking de prendas con mayor demanda."""

    model_config = ConfigDict(from_attributes=True)

    id_prenda: int
    nombre: str = Field(..., description="Denominación de la prenda")
    categoria: Optional[str] = None
    unidades_vendidas: int = Field(..., description="Total de unidades físicas vendidas")
    total_ingresos: float = Field(..., description="Ingresos brutos generados (Bs)")
    url_imagen: Optional[str] = None


class EstadoInventarioSucursal(BaseModel):
    """Diagnóstico del estado de existencias por sucursal."""

    model_config = ConfigDict(from_attributes=True)

    id_sucursal: int
    sucursal: str
    total_stock: int = Field(..., description="Piezas disponibles en la tienda")
    variantes_agotadas: int = Field(..., description="Variantes con stock = 0")
    variantes_bajo_stock: int = Field(..., description="Variantes con stock entre 1 y 4 unidades")
    variantes_optimas: int = Field(..., description="Variantes con stock >= 5 unidades")


class DashboardKPIsRespuesta(BaseModel):
    """Carga útil consolidada del Dashboard Gerencial."""

    model_config = ConfigDict(from_attributes=True)

    resumen: KPISummary
    ventas_recientes: List[VentaPorPeriodo]
    canales: List[DistribucionCanal]
    metodos_pago: List[DistribucionMetodoPago]
    rendimiento_sucursales: List[SucursalReservaRendimiento]
    top_prendas: List[TopPrendaVendida]
    inventario_sucursales: List[EstadoInventarioSucursal]
