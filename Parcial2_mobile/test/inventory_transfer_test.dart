import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:fashionstore_mobile/core/api_client.dart';
import 'package:fashionstore_mobile/features/movimientos/models/movimiento_models.dart';
import 'package:fashionstore_mobile/services/movimiento_service.dart';

void main() {
  const oid='00000000-0000-4000-8000-000000000003';
  const transfer=MovimientoCrear(idSucursal:1,idSucursalDestino:2,idVariantePrenda:7,tipo:'Traspaso',cantidad:2,motivo:'Reponer',operationId:oid);
  Map<String,dynamic> leg(int id,int branch,String kind)=>{'id_movimiento':id,'id_sucursal':branch,'id_variante_prenda':7,'tipo':kind,'cantidad':2,'motivo':'Reponer','fecha':'2026-11-07T00:00:00'};
  test('un traspaso incompleto no se serializa como operación válida',(){
    const old=MovimientoCrear(idSucursal:1,idVariantePrenda:7,tipo:'Traspaso',cantidad:2,motivo:'Reponer');
    expect(old.toJson,throwsArgumentError);
  });
  test('el contrato envía destino y conserva UUID al reintentar',()async{
    final bodies=<Map<String,dynamic>>[];
    await http.runWithClient(()async{
      final service=MovimientoService(api:ApiClient(baseUrl:'https://example.test'));
      final first=await service.registrar(transfer);final second=await service.registrar(transfer);
      expect(first.traspaso!.salida.tipo,'Salida');expect(first.traspaso!.entrada.tipo,'Entrada');
      expect(second.traspaso!.operationId,oid);
    },()=>MockClient((request)async{
      bodies.add(jsonDecode(request.body) as Map<String,dynamic>);
      return http.Response(jsonEncode({'tipo':'Traspaso','operation_id':oid,'movimiento_salida':leg(10,1,'Salida'),'movimiento_entrada':leg(11,2,'Entrada')}),201);
    }));
    expect(bodies.length,2);expect(bodies[0],bodies[1]);expect(bodies[0]['id_sucursal_destino'],2);
  });
  test('no interpreta el antiguo falso éxito como traspaso confirmado',()async{
    await http.runWithClient(()async{
      final service=MovimientoService(api:ApiClient(baseUrl:'https://example.test'));
      await expectLater(service.registrar(transfer),throwsFormatException);
    },()=>MockClient((request)async=>http.Response(jsonEncode(leg(10,1,'Traspaso')),201)));
  });
  test('Entrada conserva su payload y respuesta de movimiento',()async{
    const entry=MovimientoCrear(idSucursal:1,idVariantePrenda:7,tipo:'Entrada',cantidad:2,motivo:'Reponer');
    expect(entry.toJson().containsKey('operation_id'),false);
    expect(entry.toJson().containsKey('id_sucursal_destino'),false);
    await http.runWithClient(()async{
      final service=MovimientoService(api:ApiClient(baseUrl:'https://example.test'));
      final result=await service.registrar(entry);expect(result.movimiento!.idMovimiento,10);expect(result.traspaso,isNull);
    },()=>MockClient((request)async=>http.Response(jsonEncode(leg(10,1,'Entrada')),201)));
  });
  test('consulta disponible únicamente cuando el formulario lo solicita',()async{
    await http.runWithClient(()async{
      final service=MovimientoService(api:ApiClient(baseUrl:'https://example.test'));
      expect(await service.consultarStock(idSucursal:1,idVariantePrenda:7,disponible:true),1);
    },()=>MockClient((request)async{
      expect(request.url.queryParameters['disponible'],'true');
      return http.Response('{"id_sucursal":1,"id_variante_prenda":7,"stock":1}',200);
    }));
  });
}
