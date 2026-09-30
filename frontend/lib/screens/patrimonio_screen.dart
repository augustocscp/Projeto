import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../services/api_service.dart';
import '../widgets/patrimonio_form_dialog.dart';

const _accent = Color(0xFF009CDF);

class PatrimonioScreen extends StatefulWidget {
  const PatrimonioScreen({super.key});

  @override
  State<PatrimonioScreen> createState() => _PatrimonioScreenState();
}

class _PatrimonioScreenState extends State<PatrimonioScreen> {
  final _plaquetaController = TextEditingController();
  final _descricaoController = TextEditingController();
  List<Map<String, dynamic>> _itens = [];
  List<Map<String, dynamic>> _departamentos = [];
  List<Map<String, dynamic>> _situacoes = [];
  List<Map<String, dynamic>> _responsaveis = [];
  List<Map<String, dynamic>> _categorias = [];
  Map<String, dynamic> _indicadores = {};
  int? _departamentoId;
  int? _situacaoId;
  int? _responsavelId;
  int? _categoriaId;
  int _pagina = 1;
  int _paginas = 0;
  int _total = 0;
  static const _tamanhoPagina = 10;
  bool _carregando = true;
  String? _erro;

  @override
  void initState() {
    super.initState();
    _inicializar();
  }

  @override
  void dispose() {
    _plaquetaController.dispose();
    _descricaoController.dispose();
    super.dispose();
  }

  Future<void> _inicializar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final resultados = await Future.wait<dynamic>([
        ApiService.listarPatrimonios(pagina: 1, tamanho: _tamanhoPagina),
        ApiService.getPatrimonioResumo(),
        ApiService.listarDepartamentos(),
        ApiService.listarSituacoes(),
        ApiService.listarResponsaveis(),
        ApiService.listarCategorias(),
      ]);
      if (!mounted) return;
      setState(() {
        _aplicarResultado(resultados[0] as Map<String, dynamic>);
        _indicadores =
            (resultados[1] as Map<String, dynamic>)['indicadores']
                as Map<String, dynamic>;
        _departamentos = resultados[2] as List<Map<String, dynamic>>;
        _situacoes = resultados[3] as List<Map<String, dynamic>>;
        _responsaveis = resultados[4] as List<Map<String, dynamic>>;
        _categorias = resultados[5] as List<Map<String, dynamic>>;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _erro = error.toString().replaceFirst('Exception: ', '');
        });
      }
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }

  void _aplicarResultado(Map<String, dynamic> resultado) {
    _itens = (resultado['items'] as List<dynamic>).cast<Map<String, dynamic>>();
    _pagina = resultado['page'] as int;
    _paginas = resultado['pages'] as int;
    _total = resultado['total'] as int;
  }

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final resultados = await Future.wait([
        ApiService.listarPatrimonios(
          pagina: _pagina,
          tamanho: _tamanhoPagina,
          numeroPlaqueta: _plaquetaController.text,
          descricao: _descricaoController.text,
          departamentoId: _departamentoId,
          situacaoId: _situacaoId,
          responsavelId: _responsavelId,
          categoriaId: _categoriaId,
        ),
        ApiService.getPatrimonioResumo(),
      ]);
      if (!mounted) return;
      setState(() {
        _aplicarResultado(resultados[0]);
        _indicadores = resultados[1]['indicadores'] as Map<String, dynamic>;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _erro = error.toString().replaceFirst('Exception: ', '');
        });
      }
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }

  void _pesquisar() {
    _pagina = 1;
    _carregar();
  }

  void _limparFiltros() {
    setState(() {
      _plaquetaController.clear();
      _descricaoController.clear();
      _departamentoId = null;
      _situacaoId = null;
      _responsavelId = null;
      _categoriaId = null;
      _pagina = 1;
    });
    _carregar();
  }

  void _irParaPagina(int pagina) {
    if (pagina < 1 || pagina > _paginas || pagina == _pagina) return;
    _pagina = pagina;
    _carregar();
  }

  Future<void> _novo() async {
    final criado = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      barrierColor: const Color(0x990B2235),
      builder: (_) => const PatrimonioFormDialog(),
    );
    if (criado == true) {
      _pagina = 1;
      await _carregar();
    }
  }

  Future<void> _editar(Map<String, dynamic> item) async {
    final atualizado = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      barrierColor: const Color(0x990B2235),
      builder: (_) => PatrimonioFormDialog(patrimonio: item),
    );
    if (atualizado == true) {
      await _carregar();
    }
  }

  Future<void> _detalhar(Map<String, dynamic> item) async {
    try {
      final resultados = await Future.wait([
        ApiService.consultarPatrimonio(item['id'] as int),
        ApiService.consultarHistorico(item['id'] as int),
      ]);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (_) => _PatrimonioDetailDialog(
          patrimonio: resultados[0],
          historico: resultados[1],
        ),
      );
    } catch (error) {
      if (mounted) _mostrarErro(error);
    }
  }

  void _mostrarErro(Object error) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(error.toString().replaceFirst('Exception: ', ''))),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: const Color(0xFFF7F9FB),
      child: Column(
        children: [
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(20, 14, 20, 12),
            child: LayoutBuilder(
              builder: (context, constraints) {
                const titulo = Text(
                  'Patrimônios cadastrados',
                  style: TextStyle(
                    color: Color(0xFF17364D),
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                );
                final acoes = Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton.filledTonal(
                      tooltip: 'Atualizar',
                      onPressed: _carregar,
                      icon: const Icon(Icons.refresh),
                    ),
                    const SizedBox(width: 12),
                    FilledButton.icon(
                      onPressed: _novo,
                      icon: const Icon(Icons.add),
                      label: const Text('Novo patrimônio'),
                    ),
                  ],
                );
                if (constraints.maxWidth < 520) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [titulo, const SizedBox(height: 10), acoes],
                  );
                }
                return Row(
                  children: [
                    Expanded(child: titulo),
                    acoes,
                  ],
                );
              },
            ),
          ),
          Expanded(child: _corpo()),
        ],
      ),
    );
  }

  Widget _corpo() {
    if (_carregando && _indicadores.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_erro != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 40, color: Colors.red),
            const SizedBox(height: 8),
            Text(_erro!),
            TextButton(
              onPressed: _inicializar,
              child: const Text('Tentar novamente'),
            ),
          ],
        ),
      );
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _painelFiltros(),
          const SizedBox(height: 18),
          _painelIndicadores(),
          const SizedBox(height: 18),
          _tabela(),
        ],
      ),
    );
  }

  Widget _painelFiltros() => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: Colors.white,
      border: Border.all(color: const Color(0xFFDCE5EB)),
      borderRadius: BorderRadius.circular(6),
    ),
    child: LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        if (width >= 1180) {
          final primeiraLinha = (width - 32) / 3;
          final segundaLinha = (width - 444) / 3;
          return Column(
            children: [
              Row(
                children: [
                  _campoBusca(
                    controller: _plaquetaController,
                    label: 'Código de plaqueta',
                    hint: 'Digite o código...',
                    width: primeiraLinha,
                  ),
                  const SizedBox(width: 16),
                  _campoBusca(
                    controller: _descricaoController,
                    label: 'Descrição',
                    hint: 'Digite a descrição...',
                    width: primeiraLinha,
                  ),
                  const SizedBox(width: 16),
                  _filtroDropdown(
                    label: 'Departamento',
                    value: _departamentoId,
                    items: _departamentos,
                    onChanged: (value) =>
                        setState(() => _departamentoId = value),
                    width: primeiraLinha,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  _filtroDropdown(
                    label: 'Situação',
                    value: _situacaoId,
                    items: _situacoes,
                    onChanged: (value) => setState(() => _situacaoId = value),
                    width: segundaLinha,
                  ),
                  const SizedBox(width: 16),
                  _filtroDropdown(
                    label: 'Usuário',
                    value: _responsavelId,
                    items: _responsaveis,
                    onChanged: (value) =>
                        setState(() => _responsavelId = value),
                    width: segundaLinha,
                  ),
                  const SizedBox(width: 16),
                  _filtroDropdown(
                    label: 'Categoria',
                    value: _categoriaId,
                    items: _categorias,
                    onChanged: (value) => setState(() => _categoriaId = value),
                    width: segundaLinha,
                  ),
                  const SizedBox(width: 16),
                  _botaoPesquisar(),
                  const SizedBox(width: 16),
                  _botaoLimpar(),
                ],
              ),
            ],
          );
        }
        final campo = width >= 1180
            ? (width - 32) / 3
            : width >= 680
            ? (width - 16) / 2
            : width;
        return Wrap(
          spacing: 16,
          runSpacing: 16,
          crossAxisAlignment: WrapCrossAlignment.end,
          children: [
            _campoBusca(
              controller: _plaquetaController,
              label: 'Código de plaqueta',
              hint: 'Digite o código...',
              width: campo,
            ),
            _campoBusca(
              controller: _descricaoController,
              label: 'Descrição',
              hint: 'Digite a descrição...',
              width: campo,
            ),
            _filtroDropdown(
              label: 'Departamento',
              value: _departamentoId,
              items: _departamentos,
              onChanged: (value) => setState(() => _departamentoId = value),
              width: campo,
            ),
            _filtroDropdown(
              label: 'Situação',
              value: _situacaoId,
              items: _situacoes,
              onChanged: (value) => setState(() => _situacaoId = value),
              width: campo,
            ),
            _filtroDropdown(
              label: 'Usuário',
              value: _responsavelId,
              items: _responsaveis,
              onChanged: (value) => setState(() => _responsavelId = value),
              width: campo,
            ),
            _filtroDropdown(
              label: 'Categoria',
              value: _categoriaId,
              items: _categorias,
              onChanged: (value) => setState(() => _categoriaId = value),
              width: campo,
            ),
            _botaoPesquisar(),
            _botaoLimpar(),
          ],
        );
      },
    ),
  );

  Widget _botaoPesquisar() => SizedBox(
    width: 190,
    height: 48,
    child: FilledButton.icon(
      onPressed: _carregando ? null : _pesquisar,
      icon: const Icon(Icons.search),
      label: const Text('Pesquisar'),
    ),
  );

  Widget _botaoLimpar() => SizedBox(
    width: 190,
    height: 48,
    child: OutlinedButton.icon(
      onPressed: _carregando ? null : _limparFiltros,
      icon: const Icon(Icons.filter_alt_off_outlined),
      label: const Text('Limpar filtros'),
    ),
  );

  Widget _campoBusca({
    required TextEditingController controller,
    required String label,
    required String hint,
    required double width,
  }) => SizedBox(
    width: width,
    child: TextField(
      controller: controller,
      onSubmitted: (_) => _pesquisar(),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: const Icon(Icons.search),
      ),
    ),
  );

  Widget _filtroDropdown({
    required String label,
    required int? value,
    required List<Map<String, dynamic>> items,
    required ValueChanged<int?> onChanged,
    required double width,
  }) => SizedBox(
    width: width,
    child: DropdownButtonFormField<int>(
      key: ValueKey('$label:$value'),
      initialValue: value,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: [
        const DropdownMenuItem<int>(value: null, child: Text('Todos')),
        ...items.map(
          (item) => DropdownMenuItem<int>(
            value: item['id'] as int,
            child: Text(
              item['nome'] as String,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
      ],
      onChanged: onChanged,
    ),
  );

  Widget _painelIndicadores() => LayoutBuilder(
    builder: (context, constraints) {
      final width = constraints.maxWidth;
      final cardWidth = width >= 1050
          ? (width - 54) / 4
          : width >= 560
          ? (width - 18) / 2
          : width;
      final dados = [
        _KpiData(
          'Total de patrimônios',
          _indicadores['bensCadastrados'],
          Icons.storage_outlined,
          const Color(0xFF1976D2),
        ),
        _KpiData(
          'Ativos',
          _indicadores['bensAtivos'],
          Icons.check_circle_outline,
          const Color(0xFF1C9B55),
        ),
        _KpiData(
          'Baixados',
          _indicadores['bensBaixados'],
          Icons.arrow_circle_down_outlined,
          const Color(0xFFE39A16),
        ),
        _KpiData(
          'Inativos',
          _indicadores['bensInativos'],
          Icons.block_outlined,
          const Color(0xFF667985),
        ),
      ];
      return Wrap(
        spacing: 18,
        runSpacing: 18,
        children: dados
            .map((item) => SizedBox(width: cardWidth, child: _KpiCard(item)))
            .toList(),
      );
    },
  );

  Widget _tabela() => Container(
    decoration: BoxDecoration(
      color: Colors.white,
      border: Border.all(color: const Color(0xFFDCE5EB)),
      borderRadius: BorderRadius.circular(6),
    ),
    clipBehavior: Clip.antiAlias,
    child: Column(
      children: [
        if (_carregando) const LinearProgressIndicator(minHeight: 2),
        LayoutBuilder(
          builder: (context, constraints) => SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: ConstrainedBox(
              constraints: BoxConstraints(minWidth: constraints.maxWidth),
              child: DataTable(
                columnSpacing: 18,
                horizontalMargin: 14,
                headingRowColor: WidgetStateProperty.all(
                  const Color(0xFFEAF3F8),
                ),
                headingTextStyle: const TextStyle(
                  color: Color(0xFF1478B8),
                  fontWeight: FontWeight.w700,
                ),
                headingRowHeight: 48,
                dataRowMinHeight: 50,
                dataRowMaxHeight: 54,
                columns: const [
                  DataColumn(label: Text('Nº do Patrimônio')),
                  DataColumn(label: Text('Cód. Protheus')),
                  DataColumn(label: Text('Cód. do Item')),
                  DataColumn(label: Text('Nº da Plaqueta')),
                  DataColumn(label: Text('Categoria')),
                  DataColumn(label: Text('Filial')),
                  DataColumn(label: Text('Localização')),
                  DataColumn(label: Text('Situação')),
                  DataColumn(label: Text('Ações')),
                ],
                rows: _itens.map(_linhaTabela).toList(),
              ),
            ),
          ),
        ),
        if (_itens.isEmpty && !_carregando)
          const Padding(
            padding: EdgeInsets.all(32),
            child: Text('Nenhum patrimônio encontrado.'),
          ),
        const Divider(height: 1),
        _paginacao(),
      ],
    ),
  );

  DataRow _linhaTabela(Map<String, dynamic> item) {
    return DataRow(
      cells: [
        DataCell(Text(_texto(item['numero_tombo']))),
        DataCell(Text(_texto(item['codigo_protheus']))),
        DataCell(Text(_texto(item['numero_item']))),
        DataCell(Text(_texto(item['numero_plaqueta_fisica']))),
        DataCell(Text(_nomeReferencia(item['categoria']))),
        DataCell(Text(_nomeReferencia(item['filial']))),
        DataCell(Text(_nomeReferencia(item['localizacao']))),
        DataCell(Text(_nomeReferencia(item['situacao']))),
        DataCell(
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                tooltip: 'Visualizar',
                onPressed: () => _detalhar(item),
                icon: const Icon(Icons.visibility_outlined),
                visualDensity: VisualDensity.compact,
                constraints: const BoxConstraints.tightFor(
                  width: 36,
                  height: 36,
                ),
              ),
              IconButton(
                tooltip: 'Editar',
                onPressed: () => _editar(item),
                icon: const Icon(Icons.edit_outlined),
                visualDensity: VisualDensity.compact,
                constraints: const BoxConstraints.tightFor(
                  width: 36,
                  height: 36,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _paginacao() {
    final inicio = _total == 0 ? 0 : ((_pagina - 1) * _tamanhoPagina) + 1;
    final fim = math.min(_pagina * _tamanhoPagina, _total);
    final controles = Wrap(
      spacing: 8,
      runSpacing: 8,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        OutlinedButton.icon(
          onPressed: _pagina > 1 && !_carregando
              ? () => _irParaPagina(_pagina - 1)
              : null,
          icon: const Icon(Icons.chevron_left),
          label: const Text('Anterior'),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 6),
          child: Text(
            _paginas == 0 ? '0 de 0' : '$_pagina de $_paginas',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ),
        FilledButton.tonalIcon(
          onPressed: _pagina < _paginas && !_carregando
              ? () => _irParaPagina(_pagina + 1)
              : null,
          iconAlignment: IconAlignment.end,
          icon: const Icon(Icons.chevron_right),
          label: const Text('Próximo'),
        ),
      ],
    );
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        runAlignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 16,
        runSpacing: 10,
        children: [Text('$inicio–$fim de $_total registros'), controles],
      ),
    );
  }

  String _texto(Object? valor) => valor?.toString() ?? '-';

  String _nomeReferencia(Object? valor) {
    if (valor is Map<String, dynamic>) return _texto(valor['nome']);
    return '-';
  }
}

class _KpiData {
  final String label;
  final Object? value;
  final IconData icon;
  final Color color;

  const _KpiData(this.label, this.value, this.icon, this.color);
}

class _KpiCard extends StatelessWidget {
  final _KpiData data;

  const _KpiCard(this.data);

  @override
  Widget build(BuildContext context) => Container(
    height: 116,
    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
    decoration: BoxDecoration(
      color: Colors.white,
      border: Border.all(color: const Color(0xFFDCE5EB)),
      borderRadius: BorderRadius.circular(6),
    ),
    child: Row(
      children: [
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: data.color.withValues(alpha: 0.11),
            shape: BoxShape.circle,
          ),
          child: Icon(data.icon, color: data.color, size: 29),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                data.label,
                style: const TextStyle(
                  color: Color(0xFF526875),
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                NumberFormat.decimalPattern('pt_BR').format(data.value ?? 0),
                style: TextStyle(
                  color: data.color,
                  fontSize: 26,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _PatrimonioDetailDialog extends StatelessWidget {
  final Map<String, dynamic> patrimonio;
  final Map<String, dynamic> historico;

  const _PatrimonioDetailDialog({
    required this.patrimonio,
    required this.historico,
  });

  Widget _linha(String label, Object? value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 190,
          child: Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ),
        Expanded(child: SelectableText(value?.toString() ?? '-')),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) {
    final contabil = patrimonio['contabil'] as Map<String, dynamic>?;
    final responsavel = patrimonio['responsavel'] as Map<String, dynamic>?;
    final eventos = <dynamic>[
      ...(historico['contabil'] as List<dynamic>? ?? []),
      ...(historico['controle_patrimonial'] as List<dynamic>? ?? []),
      ...(historico['sistema'] as List<dynamic>? ?? []),
    ];
    return Dialog(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 880, maxHeight: 760),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 18, 12, 12),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      patrimonio['numero_tombo'] as String,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Fechar',
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const _SectionTitle('Identificação'),
                    _linha('Código Protheus', patrimonio['codigo_protheus']),
                    _linha('Nº do Item', patrimonio['numero_item']),
                    _linha('Descrição', patrimonio['descricao']),
                    _linha('Número de Série', patrimonio['numero_serie']),
                    _linha('Responsável', responsavel?['nome']),
                    const _SectionTitle('Contabilidade'),
                    if (contabil == null)
                      const Text('Nenhum snapshot contábil disponível.')
                    else ...[
                      _linha('Nota Fiscal', contabil['numero_nota_fiscal']),
                      _linha('Série', contabil['serie_nota_fiscal']),
                      _linha('Valor de Aquisição', contabil['valor_aquisicao']),
                      _linha(
                        'Depreciação Acumulada',
                        contabil['depreciacao_acumulada'],
                      ),
                      _linha('Valor Atual', contabil['valor_atual']),
                      _linha('Conta Contábil', contabil['conta_contabil']),
                      _linha('Centro de Custo', contabil['centro_custo']),
                      _linha('Última consulta', contabil['consultado_em']),
                    ],
                    const _SectionTitle('Histórico'),
                    _linha('Eventos registrados', eventos.length),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PatrimonioFormDialog extends StatefulWidget {
  const _PatrimonioFormDialog();

  @override
  State<_PatrimonioFormDialog> createState() => _PatrimonioFormDialogState();
}

class _PatrimonioFormDialogState extends State<_PatrimonioFormDialog> {
  final _formKey = GlobalKey<FormState>();
  final _controllers = <String, TextEditingController>{
    for (final field in [
      'codigo_protheus',
      'numero_item',
      'codigo_sap',
      'numero_plaqueta_fisica',
      'descricao',
      'marca',
      'modelo',
      'fabricante',
      'numero_serie',
      'codigo_re',
      'numero_patrimonio_anterior',
      'observacao',
    ])
      field: TextEditingController(),
  };

  List<Map<String, dynamic>> categorias = [];
  List<Map<String, dynamic>> estados = [];
  List<Map<String, dynamic>> situacoes = [];
  List<Map<String, dynamic>> destinacoes = [];
  List<Map<String, dynamic>> empresas = [];
  List<Map<String, dynamic>> filiais = [];
  List<Map<String, dynamic>> departamentos = [];
  List<Map<String, dynamic>> localizacoes = [];
  int? categoriaId;
  int? estadoId;
  int? situacaoId;
  int? destinacaoId;
  int? empresaId;
  int? filialId;
  int? departamentoId;
  int? localizacaoId;
  String cidadeSelecionada = '';
  bool possuiGarantia = false;
  DateTime? garantia;
  bool carregando = true;
  bool salvando = false;
  String? erro;

  @override
  void initState() {
    super.initState();
    _carregarCatalogos();
  }

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _carregarCatalogos() async {
    try {
      final resultados = await Future.wait([
        ApiService.listarCategorias(),
        ApiService.listarEstadosConservacao(),
        ApiService.listarSituacoes(),
        ApiService.listarDestinacoes(),
        ApiService.listarEmpresas(),
        ApiService.listarDepartamentos(),
      ]);
      if (!mounted) return;
      setState(() {
        categorias = resultados[0];
        estados = resultados[1];
        situacoes = resultados[2];
        destinacoes = resultados[3];
        empresas = resultados[4];
        departamentos = resultados[5];
        carregando = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          erro = error.toString();
          carregando = false;
        });
      }
    }
  }

  Future<void> _selecionarEmpresa(int? id) async {
    setState(() {
      empresaId = id;
      filialId = null;
      cidadeSelecionada = '';
      localizacaoId = null;
      filiais = [];
      localizacoes = [];
    });
    if (id == null) return;
    final dados = await ApiService.listarFiliais(id);
    if (mounted) setState(() => filiais = dados);
  }

  Future<void> _atualizarLocalizacoes() async {
    setState(() {
      localizacaoId = null;
      localizacoes = [];
    });
    if (filialId == null || departamentoId == null) return;
    final dados = await ApiService.listarLocalizacoes(
      filialId!,
      departamentoId!,
    );
    if (mounted) setState(() => localizacoes = dados);
  }

  String? _obrigatorio(dynamic value) =>
      value == null || value.toString().trim().isEmpty
      ? 'Campo obrigatório'
      : null;

  Widget _texto(
    String field,
    String label, {
    bool required = false,
    int lines = 1,
  }) {
    return SizedBox(
      width: lines > 1 ? 560 : 270,
      child: TextFormField(
        controller: _controllers[field],
        maxLines: lines,
        validator: required ? _obrigatorio : null,
        decoration: InputDecoration(labelText: label),
      ),
    );
  }

  Widget _dropdown(
    String label,
    List<Map<String, dynamic>> items,
    int? value,
    ValueChanged<int?> onChanged,
  ) {
    return SizedBox(
      width: 270,
      child: DropdownButtonFormField<int>(
        initialValue: value,
        isExpanded: true,
        validator: _obrigatorio,
        decoration: InputDecoration(labelText: label),
        items: items
            .map(
              (item) => DropdownMenuItem<int>(
                value: item['id'] as int,
                child: Text(
                  item['nome'] as String,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            )
            .toList(),
        onChanged: onChanged,
      ),
    );
  }

  Future<void> _consultarProtheus() async {
    final codigo = _controllers['codigo_protheus']!.text.trim();
    final item = _controllers['numero_item']!.text.trim();
    if (codigo.isEmpty || item.isEmpty) {
      setState(() => erro = 'Informe o Código Protheus e o Nº do Item.');
      return;
    }
    try {
      final cadastral = await ApiService.consultarProtheusCadastral(
        codigo,
        item,
      );
      final resposta = await ApiService.consultarProtheusContabil(codigo, item);
      if (!mounted) return;
      final dados = cadastral['dados'] as Map<String, dynamic>?;
      if (dados != null) {
        _controllers['descricao']!.text = dados['descricao'] as String? ?? '';
        _controllers['modelo']!.text = dados['modelo'] as String? ?? '';
        _controllers['fabricante']!.text = dados['fabricante'] as String? ?? '';
      }
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Dados contábeis do Protheus'),
          content: SizedBox(
            width: 680,
            child: SingleChildScrollView(
              child: SelectableText(
                const JsonEncoder.withIndent('  ').convert(resposta),
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Fechar'),
            ),
          ],
        ),
      );
    } catch (error) {
      if (mounted) setState(() => erro = error.toString());
    }
  }

  Future<void> _selecionarGarantia() async {
    final data = await showDatePicker(
      context: context,
      firstDate: DateTime(1990),
      lastDate: DateTime(2100),
      initialDate: garantia ?? DateTime.now(),
    );
    if (data != null) {
      setState(() => garantia = data);
    }
  }

  String _date(DateTime value) =>
      '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';

  Future<void> _salvar() async {
    if (!_formKey.currentState!.validate()) return;
    if (possuiGarantia && garantia == null) {
      setState(() => erro = 'Informe a data de fim da garantia.');
      return;
    }
    setState(() {
      salvando = true;
      erro = null;
    });
    String? opcional(String field) {
      final value = _controllers[field]!.text.trim();
      return value.isEmpty ? null : value;
    }

    try {
      await ApiService.criarPatrimonio({
        'codigo_protheus': opcional('codigo_protheus'),
        'numero_item': _controllers['numero_item']!.text.trim(),
        'codigo_sap': opcional('codigo_sap'),
        'numero_plaqueta_fisica': _controllers['numero_plaqueta_fisica']!.text
            .trim(),
        'descricao': _controllers['descricao']!.text.trim(),
        'categoria_id': categoriaId,
        'marca': opcional('marca'),
        'modelo': opcional('modelo'),
        'fabricante': opcional('fabricante'),
        'numero_serie': opcional('numero_serie'),
        'possui_garantia': possuiGarantia,
        'data_fim_garantia': garantia == null ? null : _date(garantia!),
        'empresa_id': empresaId,
        'filial_id': filialId,
        'departamento_id': departamentoId,
        'localizacao_id': localizacaoId,
        'codigo_re': _controllers['codigo_re']!.text.trim(),
        'estado_conservacao_id': estadoId,
        'situacao_id': situacaoId,
        'destinacao_id': destinacaoId,
        'observacao': opcional('observacao'),
        'numero_patrimonio_anterior': opcional('numero_patrimonio_anterior'),
      });
      if (mounted) {
        Navigator.pop(context, true);
      }
    } catch (error) {
      if (mounted) {
        setState(() => erro = error.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 920, maxHeight: 760),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 20, 12, 12),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Novo patrimônio',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Fechar',
                    onPressed: salvando ? null : () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: carregando
                  ? const Center(child: CircularProgressIndicator())
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(24),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (erro != null)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 16),
                                child: Text(
                                  erro!,
                                  style: const TextStyle(color: Colors.red),
                                ),
                              ),
                            if (categorias.isEmpty)
                              const Padding(
                                padding: EdgeInsets.only(bottom: 16),
                                child: Text(
                                  'Nenhuma categoria patrimonial ativa foi cadastrada.',
                                  style: TextStyle(color: Colors.orange),
                                ),
                              ),
                            const _SectionTitle('Identificação'),
                            Wrap(
                              spacing: 16,
                              runSpacing: 16,
                              children: [
                                _texto(
                                  'numero_plaqueta_fisica',
                                  'Plaqueta física',
                                  required: true,
                                ),
                                _texto(
                                  'numero_patrimonio_anterior',
                                  'Patrimônio anterior',
                                ),
                                SizedBox(
                                  width: 270,
                                  child: TextFormField(
                                    controller: _controllers['codigo_protheus'],
                                    validator: _obrigatorio,
                                    decoration: InputDecoration(
                                      labelText: 'Código Protheus *',
                                      suffixIcon: IconButton(
                                        tooltip: 'Consultar BigQuery',
                                        onPressed: _consultarProtheus,
                                        icon: const Icon(Icons.cloud_outlined),
                                      ),
                                    ),
                                  ),
                                ),
                                _texto(
                                  'numero_item',
                                  'Nº do Item *',
                                  required: true,
                                ),
                                _texto('codigo_sap', 'Código SAP'),
                                _texto(
                                  'descricao',
                                  'Descrição',
                                  required: true,
                                  lines: 2,
                                ),
                              ],
                            ),
                            const _SectionTitle('Dados cadastrais'),
                            Wrap(
                              spacing: 16,
                              runSpacing: 16,
                              children: [
                                _dropdown(
                                  'Categoria',
                                  categorias,
                                  categoriaId,
                                  (id) => setState(() => categoriaId = id),
                                ),
                                _texto('marca', 'Marca'),
                                _texto('modelo', 'Modelo'),
                                _texto('fabricante', 'Fabricante'),
                                _texto(
                                  'numero_serie',
                                  'Número de Série *',
                                  required: true,
                                ),
                                SizedBox(
                                  width: 270,
                                  child: SwitchListTile(
                                    contentPadding: EdgeInsets.zero,
                                    title: const Text('Possui Garantia? *'),
                                    value: possuiGarantia,
                                    onChanged: (value) => setState(() {
                                      possuiGarantia = value;
                                      if (!value) garantia = null;
                                    }),
                                  ),
                                ),
                                _DateButton(
                                  label: 'Fim da garantia',
                                  value: garantia,
                                  onPressed: possuiGarantia
                                      ? _selecionarGarantia
                                      : null,
                                ),
                              ],
                            ),
                            const _SectionTitle(
                              'Localização e responsabilidade',
                            ),
                            Wrap(
                              spacing: 16,
                              runSpacing: 16,
                              children: [
                                _dropdown(
                                  'Empresa',
                                  empresas,
                                  empresaId,
                                  _selecionarEmpresa,
                                ),
                                _dropdown('Filial', filiais, filialId, (id) {
                                  setState(() {
                                    filialId = id;
                                    final filial = filiais.firstWhere(
                                      (item) => item['id'] == id,
                                      orElse: () => <String, dynamic>{},
                                    );
                                    final cidade =
                                        filial['cidade']
                                            as Map<String, dynamic>?;
                                    cidadeSelecionada = cidade == null
                                        ? ''
                                        : '${cidade['nome']} - ${cidade['uf']}';
                                  });
                                  _atualizarLocalizacoes();
                                }),
                                SizedBox(
                                  width: 270,
                                  child: InputDecorator(
                                    decoration: const InputDecoration(
                                      labelText: 'Cidade',
                                    ),
                                    child: Text(
                                      cidadeSelecionada.isEmpty
                                          ? 'Selecione uma filial'
                                          : cidadeSelecionada,
                                    ),
                                  ),
                                ),
                                _dropdown(
                                  'Departamento',
                                  departamentos,
                                  departamentoId,
                                  (id) {
                                    setState(() => departamentoId = id);
                                    _atualizarLocalizacoes();
                                  },
                                ),
                                _dropdown(
                                  'Localização',
                                  localizacoes,
                                  localizacaoId,
                                  (id) => setState(() => localizacaoId = id),
                                ),
                                _texto(
                                  'codigo_re',
                                  'RE do Responsável *',
                                  required: true,
                                ),
                              ],
                            ),
                            const _SectionTitle('Controle patrimonial'),
                            Wrap(
                              spacing: 16,
                              runSpacing: 16,
                              children: [
                                _dropdown(
                                  'Estado de conservação',
                                  estados,
                                  estadoId,
                                  (id) => setState(() => estadoId = id),
                                ),
                                _dropdown(
                                  'Situação',
                                  situacoes,
                                  situacaoId,
                                  (id) => setState(() => situacaoId = id),
                                ),
                                _dropdown(
                                  'Destinação',
                                  destinacoes,
                                  destinacaoId,
                                  (id) => setState(() => destinacaoId = id),
                                ),
                                _texto('observacao', 'Observação', lines: 3),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
            ),
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: salvando ? null : () => Navigator.pop(context),
                    child: const Text('Cancelar'),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    onPressed: salvando ? null : _salvar,
                    icon: salvando
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.save_outlined),
                    label: const Text('Salvar patrimônio'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;

  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 20, bottom: 12),
    child: Text(
      text,
      style: const TextStyle(color: _accent, fontWeight: FontWeight.w700),
    ),
  );
}

class _DateButton extends StatelessWidget {
  final String label;
  final DateTime? value;
  final VoidCallback? onPressed;

  const _DateButton({
    required this.label,
    required this.value,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) => SizedBox(
    width: 270,
    height: 56,
    child: OutlinedButton.icon(
      onPressed: onPressed,
      icon: const Icon(Icons.calendar_today_outlined, size: 18),
      label: Text(
        value == null
            ? label
            : '$label: ${value!.day}/${value!.month}/${value!.year}',
      ),
    ),
  );
}
