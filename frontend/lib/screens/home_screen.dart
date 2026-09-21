import 'package:flutter/material.dart';

const _menuBackground = Color(0xFFECF1F5);
const _menuTextColor = Color(0xFF009CDF);

enum _ModuloSistema {
  inicio('Início', Icons.home_outlined),
  cadastroGeral('Cadastro geral', Icons.folder_outlined),
  cadastroVeicular('Cadastro veicular', Icons.directions_car_outlined),
  auditoria('Auditoria', Icons.fact_check_outlined),
  logs('Log do sistema', Icons.receipt_long_outlined);

  const _ModuloSistema(this.label, this.icon);

  final String label;
  final IconData icon;
}

class HomeScreen extends StatefulWidget {
  final Map<String, dynamic> usuario;
  final VoidCallback onLogoutPressed;

  const HomeScreen({
    super.key,
    required this.usuario,
    required this.onLogoutPressed,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  _ModuloSistema _moduloSelecionado = _ModuloSistema.inicio;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          _SidebarMenu(
            moduloSelecionado: _moduloSelecionado,
            onModuloSelecionado: (modulo) {
              setState(() {
                _moduloSelecionado = modulo;
              });
            },
          ),
          Expanded(
            child: Column(
              children: [
                _TopHeader(
                  titulo: _moduloSelecionado.label,
                  usuario: widget.usuario,
                  onLogoutPressed: widget.onLogoutPressed,
                ),
                Expanded(
                  child: _ModuleContent(
                    modulo: _moduloSelecionado,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TopHeader extends StatelessWidget {
  final String titulo;
  final Map<String, dynamic> usuario;
  final VoidCallback onLogoutPressed;

  const _TopHeader({
    required this.titulo,
    required this.usuario,
    required this.onLogoutPressed,
  });

  @override
  Widget build(BuildContext context) {
    final nome = usuario['nome'] as String? ?? 'Usuário';
    final email = usuario['email'] as String? ?? '';

    return Container(
      width: double.infinity,
      color: _menuBackground,
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
      child: Row(
        children: [
          Expanded(
            child: Text(
              titulo,
              style: const TextStyle(
                color: _menuTextColor,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                nome,
                style: const TextStyle(
                  color: _menuTextColor,
                  fontWeight: FontWeight.w600,
                ),
              ),
              if (email.isNotEmpty)
                Text(
                  email,
                  style: TextStyle(
                    color: _menuTextColor.withOpacity(0.72),
                    fontSize: 12,
                  ),
                ),
            ],
          ),
          const SizedBox(width: 16),
          IconButton(
            tooltip: 'Sair',
            onPressed: onLogoutPressed,
            icon: const Icon(Icons.logout, color: _menuTextColor),
          ),
        ],
      ),
    );
  }
}

class _SidebarMenu extends StatelessWidget {
  final _ModuloSistema moduloSelecionado;
  final ValueChanged<_ModuloSistema> onModuloSelecionado;

  const _SidebarMenu({
    required this.moduloSelecionado,
    required this.onModuloSelecionado,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 236,
      color: _menuBackground,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: _menuTextColor,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.inventory_2_outlined,
                    size: 22,
                    color: _menuBackground,
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'Patrimonio',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: _menuBackground,
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          for (final modulo in _ModuloSistema.values)
            _MenuItem(
              icon: modulo.icon,
              label: modulo.label,
              selected: modulo == moduloSelecionado,
              onTap: () => onModuloSelecionado(modulo),
            ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 9),
              decoration: BoxDecoration(
                color: _menuTextColor,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Flexible(
                    child: Text(
                      'Desenvolvido por',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: _menuBackground,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Image.asset(
                    'assets/images/Icon_gipe_2.png',
                    width: 64,
                    height: 26,
                    fit: BoxFit.contain,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MenuItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _MenuItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      selected: selected,
      selectedTileColor: _menuTextColor.withOpacity(0.1),
      leading: Icon(icon, color: _menuTextColor),
      title: Text(
        label,
        style: TextStyle(
          color: _menuTextColor,
          fontWeight: selected ? FontWeight.w700 : FontWeight.w400,
        ),
      ),
      onTap: onTap,
    );
  }
}

class _ModuleContent extends StatelessWidget {
  final _ModuloSistema modulo;

  const _ModuleContent({
    required this.modulo,
  });

  @override
  Widget build(BuildContext context) {
    return switch (modulo) {
      _ModuloSistema.inicio => const _InicioModule(),
      _ModuloSistema.cadastroGeral => const _PlaceholderModule(
          icon: Icons.folder_outlined,
          titulo: 'Cadastro geral',
          descricao: 'Estrutura inicial para cadastro, consulta e manutenção dos bens patrimoniais.',
        ),
      _ModuloSistema.cadastroVeicular => const _PlaceholderModule(
          icon: Icons.directions_car_outlined,
          titulo: 'Cadastro veicular',
          descricao: 'Base preparada para registrar frota, documentos, vínculo patrimonial e status operacional.',
        ),
      _ModuloSistema.auditoria => const _PlaceholderModule(
          icon: Icons.fact_check_outlined,
          titulo: 'Auditoria',
          descricao: 'Área reservada para conferências, divergências, inventários e aprovações.',
        ),
      _ModuloSistema.logs => const _PlaceholderModule(
          icon: Icons.receipt_long_outlined,
          titulo: 'Log do sistema',
          descricao: 'Histórico protegido para rastrear acessos, alterações e eventos importantes.',
        ),
    };
  }
}

class _InicioModule extends StatelessWidget {
  const _InicioModule();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: double.infinity,
          color: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 22),
          child: const Column(
            children: [
              Text(
                'Bem-vindo ao Sistema Patrimonial',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Color(0xFF222222),
                  fontSize: 30,
                  fontWeight: FontWeight.w700,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Controle, acompanhamento e auditoria dos bens da empresa',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Color(0xFF222222),
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image.asset(
                  'assets/images/urbi_mobilidade.png',
                  width: 360,
                  fit: BoxFit.contain,
                ),
                const SizedBox(height: 8),
                const Text(
                  'Selecione uma opção no menu lateral para começar.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: _menuTextColor,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _PlaceholderModule extends StatelessWidget {
  final IconData icon;
  final String titulo;
  final String descricao;

  const _PlaceholderModule({
    required this.icon,
    required this.titulo,
    required this.descricao,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 72, color: Colors.grey),
            const SizedBox(height: 16),
            Text(
              titulo,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Text(
                descricao,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
