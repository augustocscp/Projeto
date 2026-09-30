import 'dart:convert';

import 'package:http/http.dart' as http;

import 'http_client.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000';
  static final http.Client _client = createHttpClient();

  static Future<Map<String, dynamic>?> getCurrentUser() async {
    final response = await _client.get(Uri.parse('$baseUrl/auth/me'));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    if (response.statusCode == 401) {
      return null;
    }

    throw Exception('Falha ao carregar usuário');
  }

  static Future<Map<String, dynamic>> loginDesenvolvimento() async {
    final response = await _client.post(Uri.parse('$baseUrl/auth/dev-login'));
    if (response.statusCode != 200) throw Exception(_errorMessage(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getPatrimonioResumo() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/patrimonio/resumo'),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception('Falha ao carregar resumo patrimonial');
  }

  static String _errorMessage(http.Response response) {
    try {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      final detail = decoded['detail'];
      if (detail is Map<String, dynamic>) {
        return detail['mensagem'] as String? ?? 'Falha na operação';
      }
      if (detail is String) return detail;
    } catch (_) {}
    return 'Falha na operação (${response.statusCode})';
  }

  static Map<String, dynamic> _protheusResponse(http.Response response) {
    if (response.statusCode != 200) throw Exception(_errorMessage(response));

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    if (decoded['integracao_ativa'] == false) {
      throw Exception(
        'A integração com o Protheus está desativada no backend.',
      );
    }
    if (decoded['encontrado'] == false || decoded['dados'] == null) {
      throw Exception('Nenhum dado foi encontrado no Protheus.');
    }
    return decoded;
  }

  static Future<List<Map<String, dynamic>>> _getList(
    String path, [
    Map<String, String>? query,
  ]) async {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: query);
    final response = await _client.get(uri);
    if (response.statusCode != 200) throw Exception(_errorMessage(response));
    final items = jsonDecode(response.body) as List<dynamic>;
    return items.cast<Map<String, dynamic>>();
  }

  static Future<Map<String, dynamic>> listarPatrimonios({
    int pagina = 1,
    int tamanho = 10,
    String? numeroPlaqueta,
    String? descricao,
    int? departamentoId,
    int? situacaoId,
    int? responsavelId,
    int? categoriaId,
  }) async {
    final query = <String, String>{'pagina': '$pagina', 'tamanho': '$tamanho'};
    if (numeroPlaqueta != null && numeroPlaqueta.trim().isNotEmpty) {
      query['numero_plaqueta_fisica'] = numeroPlaqueta.trim();
    }
    if (descricao != null && descricao.trim().isNotEmpty) {
      query['descricao'] = descricao.trim();
    }
    if (departamentoId != null) query['departamento_id'] = '$departamentoId';
    if (situacaoId != null) query['situacao_id'] = '$situacaoId';
    if (responsavelId != null) query['responsavel_id'] = '$responsavelId';
    if (categoriaId != null) query['categoria_id'] = '$categoriaId';
    final response = await _client.get(
      Uri.parse('$baseUrl/api/patrimonios').replace(queryParameters: query),
    );
    if (response.statusCode != 200) throw Exception(_errorMessage(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> consultarPatrimonio(int id) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/patrimonios/$id'),
    );
    if (response.statusCode != 200) throw Exception(_errorMessage(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> consultarHistorico(int id) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/patrimonios/$id/historico'),
    );
    if (response.statusCode != 200) throw Exception(_errorMessage(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<List<Map<String, dynamic>>> listarCategorias() =>
      _getList('/api/categorias-patrimoniais');

  static Future<List<Map<String, dynamic>>> listarEstadosConservacao() =>
      _getList('/api/estados-conservacao');

  static Future<List<Map<String, dynamic>>> listarSituacoes() =>
      _getList('/api/situacoes-patrimoniais');

  static Future<List<Map<String, dynamic>>> listarDestinacoes() =>
      _getList('/api/destinacoes-patrimoniais');

  static Future<List<Map<String, dynamic>>> listarEmpresas() =>
      _getList('/api/empresas');

  static Future<List<Map<String, dynamic>>> listarFiliais(
    int empresaId, [
    int? departamentoId,
  ]) => _getList('/api/filiais', {
    'empresa_id': '$empresaId',
    if (departamentoId != null) 'departamento_id': '$departamentoId',
  });

  static Future<List<Map<String, dynamic>>> listarDepartamentos([
    int? empresaId,
  ]) => _getList('/api/departamentos', {
    if (empresaId != null) 'empresa_id': '$empresaId',
  });

  static Future<List<Map<String, dynamic>>> listarResponsaveis() =>
      _getList('/api/responsaveis');

  static Future<List<Map<String, dynamic>>> listarLocalizacoes(
    int filialId,
    int departamentoId,
  ) => _getList('/api/localizacoes', {
    'filial_id': '$filialId',
    'departamento_id': '$departamentoId',
  });

  static Future<Map<String, dynamic>> criarPatrimonio(
    Map<String, dynamic> payload,
  ) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/patrimonios'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    if (response.statusCode != 201) throw Exception(_errorMessage(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> consultarProtheusCadastral(
    String codigo,
    String numeroItem,
  ) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/patrimonios/protheus-cadastral').replace(
        queryParameters: {'codigo_protheus': codigo, 'numero_item': numeroItem},
      ),
    );
    return _protheusResponse(response);
  }

  static Future<bool> patrimonioProtheusItemJaCadastrado(
    String codigo,
    String numeroItem,
  ) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/patrimonios/verificar-duplicidade').replace(
        queryParameters: {'codigo_protheus': codigo, 'numero_item': numeroItem},
      ),
    );
    if (response.statusCode != 200) throw Exception(_errorMessage(response));
    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    return decoded['duplicado'] == true;
  }

  static Future<Map<String, dynamic>> consultarProtheusContabil(
    String codigo,
    String numeroItem,
  ) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/patrimonios/protheus-contabil').replace(
        queryParameters: {'codigo_protheus': codigo, 'numero_item': numeroItem},
      ),
    );
    return _protheusResponse(response);
  }

  static Future<Map<String, dynamic>> consultarResponsavel(
    String codigoRe,
  ) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/responsaveis/protheus')
          .replace(queryParameters: {'codigo_re': codigoRe}),
    );
    return _protheusResponse(response);
  }

  static Future<void> inativarPatrimonio(int patrimonioId) async {
    final response = await _client.patch(
      Uri.parse('$baseUrl/api/patrimonios/$patrimonioId/inativar'),
    );
    if (response.statusCode != 200) throw Exception(_errorMessage(response));
  }

  static Future<void> logout() async {
    await _client.post(Uri.parse('$baseUrl/auth/logout'));
  }

  static Future<bool> checkHealth() async {
    try {
      final response = await _client.get(Uri.parse('$baseUrl/health'));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
