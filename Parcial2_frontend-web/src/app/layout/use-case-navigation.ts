import { ROLES } from '../core/models/auth.model';

type Audience = 'all' | 'staff' | 'store' | 'client';
export interface CaseLink {
  label: string;
  path: string;
  audience?: Audience;
  roles?: readonly string[];
  scope?: 'global' | 'empresa' | 'cliente' | 'actual';
  query?: Record<string, string>;
  platformOnly?: boolean;
}

interface UseCase {
  id: string;
  title: string;
  links?: readonly CaseLink[];
  requires?: string;
}

interface Package {
  id: string;
  title: string;
  cases: readonly UseCase[];
}

const admin = [ROLES.ADMINISTRADOR];
const managers = [...admin, ROLES.ENCARGADO];
const counter = [...managers, ROLES.CAJERO];

export const USE_CASE_PACKAGES: readonly Package[] = [
  { id: 'P1', title: 'Administración SaaS y control de acceso', cases: [
    { id: 'CU01', title: 'Gestionar acceso y cuenta', links: [
      { label: 'Datos de la sesión y cuenta', path: '/panel/inicio', scope: 'actual' },
      { label: 'Recuperar acceso por correo', path: '/panel/recuperar-acceso', scope: 'actual', platformOnly: true },
    ] },
    { id: 'CU02', title: 'Administrar empresas, planes y suscripciones', requires: 'Administración', links: [
      { label: 'Empresas, planes y suscripciones', path: '/panel/saas', roles: admin },
      { label: 'Consultar contrato de una empresa', path: '/panel/saas', scope: 'empresa', platformOnly: true },
    ] },
    { id: 'CU03', title: 'Administrar personal, roles y permisos', requires: 'Administrador de empresa', links: [
      { label: 'Personal y roles asignados', path: '/panel/usuarios', audience: 'staff', roles: admin },
      { label: 'Matriz de roles y permisos', path: '/panel/roles-permisos', audience: 'staff', roles: admin },
    ] },
    { id: 'CU04', title: 'Gestionar ciudades y sucursales', requires: 'Administrador de empresa', links: [
      { label: 'Ciudades y sucursales', path: '/panel/sucursales', audience: 'staff', roles: admin },
    ] },
  ] },
  { id: 'P2', title: 'Catálogo, abastecimiento y movimientos de inventario', cases: [
    { id: 'CU06', title: 'Administrar catálogo de prendas', requires: 'Cuenta de empresa', links: [
      { label: 'Prendas y variantes', path: '/panel/prendas', audience: 'staff', roles: managers },
      { label: 'Categorías', path: '/panel/categorias', audience: 'staff', roles: managers },
      { label: 'Temporadas y colecciones', path: '/panel/temporadas', audience: 'staff', roles: managers },
    ] },
    { id: 'CU07', title: 'Gestionar proveedores, compras y recepciones', requires: 'Cuenta de empresa', links: [
      { label: 'Proveedores', path: '/panel/proveedores', audience: 'staff', roles: managers },
      { label: 'Compras y recepciones', path: '/panel/compras', audience: 'staff', roles: managers },
    ] },
    { id: 'CU10', title: 'Registrar movimientos de inventario', requires: 'Cuenta de empresa', links: [
      { label: 'Movimientos y traspasos', path: '/panel/movimientos-inventario', audience: 'staff', roles: managers },
    ] },
  ] },
  { id: 'P3', title: 'Atención al cliente y reservas', cases: [
    { id: 'CU05', title: 'Gestionar fichas de clientes', requires: 'Cuenta de empresa o cliente', links: [
      { label: 'Fichas de clientes', path: '/panel/clientes', audience: 'store', roles: [...counter, ROLES.CLIENTE] },
      { label: 'Consultar la ficha como comprador', path: '/panel/clientes', scope: 'cliente', platformOnly: true },
    ] },
    { id: 'CU09', title: 'Explorar catálogo y asistencia de compra', links: [
      { label: 'Elegir tienda', path: '/tiendas', audience: 'store', scope: 'actual' },
      { label: 'Vitrina del catálogo', path: '/catalogo', audience: 'store', scope: 'cliente' },
      { label: 'Asistente de moda', path: '/panel/ia/asistente-moda', audience: 'store' },
    ] },
    { id: 'CU12', title: 'Gestionar reservas de prendas', requires: 'Cuenta de empresa o cliente', links: [
      { label: 'Atención de reservas', path: '/panel/reservas-atencion', audience: 'staff', roles: counter },
      { label: 'Reservar desde el carrito', path: '/checkout', audience: 'client', query: { flujo: 'reserva' } },
    ] },
  ] },
  { id: 'P4', title: 'Ventas, pagos y posventa', cases: [
    { id: 'CU11', title: 'Realizar compra y pago en línea', requires: 'Cuenta de empresa o cliente', links: [
      { label: 'Carrito y pago en línea', path: '/checkout', audience: 'client' },
      { label: 'Conciliación de pagos y entregas', path: '/panel/pagos-control', audience: 'staff', roles: counter },
    ] },
    { id: 'CU13', title: 'Registrar venta presencial', requires: 'Cuenta de empresa', links: [
      { label: 'Terminal de caja', path: '/panel/pos', audience: 'staff', roles: counter },
    ] },
    { id: 'CU14', title: 'Obtener comprobantes de compra', requires: 'Cuenta de empresa o cliente', links: [
      { label: 'Consultar y descargar comprobantes de la empresa', path: '/panel/comprobantes', audience: 'staff', roles: counter },
      { label: 'Descargar comprobantes de mis pedidos', path: '/mi-cuenta/pedidos', audience: 'client' },
    ] },
    { id: 'CU15', title: 'Gestionar cambios y reembolsos', requires: 'Cuenta de empresa o cliente', links: [
      { label: 'Cambios y devoluciones', path: '/panel/cambios', audience: 'store' },
      { label: 'Solicitudes y seguimiento como comprador', path: '/panel/cambios', scope: 'cliente', platformOnly: true },
    ] },
  ] },
  { id: 'P5', title: 'Disponibilidad y continuidad operativa', cases: [
    { id: 'CU08', title: 'Consultar inventario y disponibilidad', requires: 'Cuenta de empresa', links: [
      { label: 'Monitoreo de inventario', path: '/panel/inventario/monitoreo', audience: 'staff', roles: counter },
    ] },
    { id: 'CU16', title: 'Registrar y consultar operaciones offline', requires: 'Cuenta de empresa o cliente', links: [
      { label: 'Catálogo local y operaciones guardadas', path: '/panel/operacion-local', audience: 'store' },
    ] },
    { id: 'CU17', title: 'Sincronizar operaciones y resolver conflictos', requires: 'Cuenta de empresa o cliente', links: [
      { label: 'Sincronizar y revisar operaciones locales', path: '/panel/sincronizacion', audience: 'store' },
    ] },
  ] },
  { id: 'P6', title: 'Reportes, analítica y auditoría', cases: [
    { id: 'CU18', title: 'Obtener reportes comerciales', requires: 'Cuenta de empresa', links: [
      { label: 'Reportes comerciales', path: '/panel/reportes', audience: 'staff', roles: managers },
      { label: 'Consultas por voz', path: '/panel/ia/analitica-voz', audience: 'staff', roles: managers },
    ] },
    { id: 'CU19', title: 'Preparar y consultar analítica inteligente', requires: 'Cuenta de empresa', links: [
      { label: 'Panel de indicadores', path: '/panel/dashboard', audience: 'staff', roles: managers },
      { label: 'Analítica y aprendizaje automático', path: '/panel/analitica', audience: 'staff', roles: managers },
    ] },
    { id: 'CU20', title: 'Consultar auditoría y trazabilidad', requires: 'Administración', links: [
      { label: 'Bitácora de auditoría', path: '/panel/bitacora', roles: managers },
      { label: 'Auditoría de una empresa', path: '/panel/bitacora', scope: 'empresa', platformOnly: true },
    ] },
  ] },
];
