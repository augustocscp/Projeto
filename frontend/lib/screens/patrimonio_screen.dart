import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../widgets/patrimonio_form_dialog.dart';

const _accent = Color(0xFF009CDF);

class PatrimonioScreen extends StatefulWidget {
  const PatrimonioScreen({super.key});

  @override
  State<PatrimonioScreen> createState() => _PatrimonioScreenState();
}

class _PatrimonioScreenState extends State<PatrimonioScreen> {
  final _buscaController = TextEditingController();
  List<Map<String, dynamic>> _itens = [];
  bool _carregando = true;
  String? _erro;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  @override
  void dispose() {
    _buscaController.dispose();
    super.dispose();
  }

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final resultado = await ApiService.listarPatrimonios(
        busca: _buscaController.text,
      );
      if (!mounted) return;
      setState(() {
        _itens = (resultado['items'] as List<dynamic>)
            .cast<Map<String, dynamic>>();
      });
    } catch (error) {
      if (mounted) setState(() => _erro = error.toString());
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }

  Future<void> _novo() async {
    final criado = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      barrierColor: const Color(0x990B2235),
      builder: (_) => const PatrimonioFormDialog(),
    );
    if (criado == true) await _carregar();
  }

  Future<void> _inativar(Map<String, dynamic> item) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Inativar patrimônio'),
        content: Text('Confirma a inativação de ${item['numero_tombo']}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Inativar'),
          ),
        ],
      ),
    );
    if (confirmar != true) return;
    try {
      await ApiService.inativarPatrimonio(item['id'] as int);
      await _carregar();
    } catch (error) {
      if (mounted) _mostrarErro(error);
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
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _buscaController,
                    onSubmitted: (_) => _carregar(),
                    decoration: const InputDecoration(
                      labelText: 'Buscar por número de tombo',
                      prefixIcon: Icon(Icons.search),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
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
            ),
          ),
          Expanded(child: _conteudo()),
        ],
      ),
    );
  }

  Widget _conteudo() {
    if (_carregando) return const Center(child: CircularProgressIndicator());
    if (_erro != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 40, color: Colors.red),
            const SizedBox(height: 8),
            Text(_erro!),
            TextButton(
              onPressed: _carregar,
              child: const Text('Tentar novamente'),
            ),
          ],
        ),
      );
    }
    if (_itens.isEmpty) {
      return const Center(child: Text('Nenhum patrimônio encontrado.'));
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: SizedBox(
        width: double.infinity,
        child: DataTable(
          headingRowColor: WidgetStateProperty.all(const Color(0xFFEAF3F8)),
          columns: const [
            DataColumn(label: Text('Tombo')),
            DataColumn(label: Text('Descrição')),
            DataColumn(label: Text('Plaqueta')),
            DataColumn(label: Text('Filial')),
            DataColumn(label: Text('Localização')),
            DataColumn(label: Text('Situação')),
            DataColumn(label: Text('Responsável')),
            DataColumn(label: Text('')),
          ],
          rows: _itens.map((item) {
            final ativo = item['ativo'] as bool? ?? false;
            return DataRow(
              cells: [
                DataCell(Text(item['numero_tombo'] as String)),
                DataCell(
                  ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 260),
                    child: Text(
                      item['descricao'] as String,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
                DataCell(Text(item['numero_plaqueta_fisica'] as String)),
                DataCell(Text(item['filial']['nome'] as String)),
                DataCell(Text(item['localizacao']['nome'] as String)),
                DataCell(Text(item['situacao']['nome'] as String)),
                DataCell(Text(item['responsavel']['nome'] as String)),
                DataCell(
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        tooltip: 'Ver detalhes',
                        onPressed: () => _detalhar(item),
                        icon: const Icon(Icons.visibility_outlined),
                      ),
                      IconButton(
                        tooltip: ativo ? 'Inativar' : 'Patrimônio inativo',
                        onPressed: ativo ? () => _inativar(item) : null,
                        icon: Icon(
                          ativo
                              ? Icons.block_outlined
                              : Icons.check_circle_outline,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }
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
