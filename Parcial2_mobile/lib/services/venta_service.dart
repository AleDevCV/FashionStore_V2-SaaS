import '../core/api_client.dart';
import '../core/config.dart';
import '../core/models/venta_models.dart';
import 'auth_service.dart';
import 'carrito_service.dart';

/// Servicio de ventas, pagos y facturación para el cliente móvil (CU15, CU20, CU21).
class VentaService {
  final ApiClient _api;

  VentaService({ApiClient? api})
      : _api = api ??
            ApiClient(
              baseUrl: apiBaseUrl,
              tokenProvider: () => AuthService.instance.token,
            );

  /// Obtiene los datos de la ficha del cliente autenticado desde la sesión (/api/clientes/me).
  Future<Map<String, dynamic>?> obtenerClientePropio() async {
    try {
      final res = await _api.get('/api/clientes/me');
      return res as Map<String, dynamic>?;
    } catch (_) {
      return null;
    }
  }

  /// Crea una reserva que bloquea el stock de los productos (CU15).
  Future<ReservaRespuesta> crearReserva(ReservaPeticion peticion) async {
    final body=peticion.toJson();final quote=await cotizar(peticion.idSucursal,peticion.items.map((i)=>{'id_variante_prenda':i.idVariantePrenda,'cantidad':i.cantidad}).toList());
    body['items']=(quote['items'] as List).map((i)=>{'id_variante_prenda':i['id_variante_prenda'],'cantidad':i['cantidad'],'precio_unitario':i['precio_unitario']}).toList();
    CarritoService.instance.actualizarPrecios(quote['items']);
    final res = await _api.post('/api/ventas/reserva', body: body);
    return ReservaRespuesta.fromJson(res as Map<String, dynamic>);
  }
  Future<Map<String,dynamic>> cotizar(int branch,List<Map<String,dynamic>> items) async=>Map<String,dynamic>.from(await _api.post('/api/ventas/cotizar',body:{'id_sucursal':branch,'items':items}));
  Future<Map<String,dynamic>> estadoPago(int id) async=>Map<String,dynamic>.from(await _api.get('/api/ventas/reserva/$id/estado-pago'));

  /// Genera un código QR boliviano de pago (CU20).
  Future<QRGenerarRespuesta> generarQR(QRGenerarPeticion peticion) async {
    final res = await _api.post('/api/pagos/qr/generar', body: peticion.toJson());
    return QRGenerarRespuesta.fromJson(res as Map<String, dynamic>);
  }

  /// Crea una sesión de pago en Stripe Checkout (CU20).
  Future<StripeCheckoutRespuesta> crearSesionStripe({
    required int idReserva,
    required int idCliente,
    required String nitCi,
    required String razonSocial,
  }) async {
    final res = await _api.post(
      '/api/pagos/stripe/crear-sesion',
      body: {
        'id_reserva': idReserva,
        'id_cliente': idCliente,
        'url_exito': 'https://fashionstore.aledevcv.me/pago/exitoso',
        'url_cancelacion': 'https://fashionstore.aledevcv.me/pago/cancelado',
        'nit_ci': nitCi,
        'razon_social': razonSocial,
        'enviar_email': false,
      },
    );
    return StripeCheckoutRespuesta.fromJson(res as Map<String, dynamic>);
  }

  /// Confirma el pago QR y consolida la venta descontando el stock (CU20).
  Future<Map<String, dynamic>> confirmarQR(QRConfirmarPeticion peticion) async {
    final res = await _api.post('/api/pagos/qr/confirmar', body: peticion.toJson());
    return res as Map<String, dynamic>;
  }

  /// Genera el comprobante fiscal PDF con QR (CU21).
  Future<ComprobanteRespuesta> generarComprobante({
    required int idVenta,
    required String nitCi,
    required String razonSocial,
    bool enviarEmail = true,
  }) async {
    final res = await _api.post(
      '/api/comprobantes/generar',
      body: {
        'id_venta': idVenta,
        'nit_ci': nitCi,
        'razon_social': razonSocial,
        'enviar_email': enviarEmail,
      },
    );
    return ComprobanteRespuesta.fromJson(res as Map<String, dynamic>);
  }

  /// Consulta el comprobante de una venta (CU21).
  Future<ComprobanteRespuesta> obtenerComprobante(int idVenta) async {
    final res = await _api.get('/api/comprobantes/venta/$idVenta');
    return ComprobanteRespuesta.fromJson(res as Map<String, dynamic>);
  }

  // ── RESERVAS DE PROBADOR FÍSICO (CU16) ────────────────────────────────────

  /// Crea una reserva de prendas para probar físicamente en una sucursal.
  Future<TicketReservaRespuesta> crearReservaProbador(ReservaProbadorPeticion peticion) async {
    final res = await _api.post('/api/ventas/reservas-probador', body: peticion.toJson());
    return TicketReservaRespuesta.fromJson(res as Map<String, dynamic>);
  }

  /// Obtiene los datos del ticket con QR dinámico por código o ID.
  Future<TicketReservaRespuesta> obtenerTicketReserva(String codigoOId) async {
    final res = await _api.get('/api/ventas/reservas-probador/$codigoOId');
    return TicketReservaRespuesta.fromJson(res as Map<String, dynamic>);
  }

  /// Lista el historial de reservas de probador del cliente.
  Future<List<ReservaRespuesta>> listarMisReservas(int idCliente) async {
    final res = await _api.get('/api/ventas/mis-reservas/$idCliente');
    final lista = res as List<dynamic>? ?? [];
    return lista.map((e) => ReservaRespuesta.fromJson(e as Map<String, dynamic>)).toList();
  }
}

