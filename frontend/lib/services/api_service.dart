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

  static Future<Map<String, dynamic>> getPatrimonioResumo() async {
    final response = await _client.get(Uri.parse('$baseUrl/api/patrimonio/resumo'));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception('Falha ao carregar resumo patrimonial');
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
