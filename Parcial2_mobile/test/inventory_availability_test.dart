import 'package:fashionstore_mobile/features/inventario_monitoreo/models/inventario_monitoreo_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('CU08 desglosa stock físico, retenido y disponible por sucursal', () {
    VarianteAgrupadaInventario monitoring(int retained) {
      final item = MonitoreoItem.fromJson({
        'id_prenda': 1,
        'id_variante_prenda': 7,
        'id_sucursal': 2,
        'stock': 5,
        'stock_fisico': 5,
        'stock_retenido': retained,
        'stock_disponible': 5 - retained,
      });
      return VarianteAgrupadaInventario.agrupar([item]).single;
    }

    final reserved = monitoring(3);
    expect(reserved.stockTotal, 2);
    expect(reserved.estadoStock, 'Bajo');
    expect(reserved.desgloseSucursales.single.stockFisico, 5);
    expect(reserved.desgloseSucursales.single.stockRetenido, 3);
    expect(reserved.desgloseSucursales.single.stock, 2);

    final canceled = monitoring(0);
    expect(canceled.stockTotal, 5);
    expect(canceled.estadoStock, 'Optimo');
    expect(canceled.desgloseSucursales.single.stockRetenido, 0);
  });
}
