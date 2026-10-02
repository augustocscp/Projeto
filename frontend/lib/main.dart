import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:url_launcher/url_launcher.dart';

import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'services/api_service.dart';
import 'theme/app_theme.dart';

// Desenvolvimento: altere para false para voltar a exigir login Microsoft.
const bool _ignorarLoginEmDesenvolvimento = true;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('pt_BR');
  runApp(const PatrimonioApp());
}

class PatrimonioApp extends StatefulWidget {
  const PatrimonioApp({super.key});

  @override
  State<PatrimonioApp> createState() => _PatrimonioAppState();
}

class _PatrimonioAppState extends State<PatrimonioApp> {
  bool _autenticado = false;
  bool _carregando = false;
  bool _inicializado = false;

  Map<String, dynamic>? _usuario;

  @override
  void initState() {
    super.initState();
    _verificarSessao();
  }

  Future<void> _verificarSessao() async {
    if (_ignorarLoginEmDesenvolvimento) {
      try {
        final usuario = await ApiService.loginDesenvolvimento();
        setState(() {
          _usuario = usuario;
          _autenticado = true;
          _inicializado = true;
        });
        return;
      } catch (error) {
        debugPrint('Falha ao iniciar sessão de desenvolvimento: $error');
      }
    }

    try {
      final usuario = await ApiService.getCurrentUser();
      setState(() {
        _usuario = usuario;
        _autenticado = usuario != null;
        _inicializado = true;
      });
    } catch (error) {
      debugPrint('Falha ao verificar sessão: $error');
      setState(() {
        _autenticado = false;
        _inicializado = true;
      });
    }
  }

  Future<void> _login() async {
    setState(() {
      _carregando = true;
    });

    final online = await ApiService.checkHealth();

    if (!online) {
      setState(() {
        _carregando = false;
      });

      debugPrint('Backend indisponível. Verifique se o servidor está rodando.');
      return;
    }

    final url = Uri.parse('http://localhost:8000/auth/login');

    final abriu = await launchUrl(url, webOnlyWindowName: '_self');

    setState(() {
      _carregando = false;
    });

    if (!abriu) {
      debugPrint('Não foi possível abrir a tela de login da Microsoft.');
    }
  }

  Future<void> _logout() async {
    if (_ignorarLoginEmDesenvolvimento) {
      return;
    }

    final url = Uri.parse('http://localhost:8000/auth/logout');
    final abriu = await launchUrl(url, webOnlyWindowName: '_self');

    if (abriu) {
      return;
    }

    await ApiService.logout();

    setState(() {
      _usuario = null;
      _autenticado = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sistema Patrimonial',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: !_inicializado || _carregando
          ? const Scaffold(body: Center(child: CircularProgressIndicator()))
          : _autenticado
          ? HomeScreen(usuario: _usuario!, onLogoutPressed: _logout)
          : LoginScreen(onLoginPressed: _login),
    );
  }
}
