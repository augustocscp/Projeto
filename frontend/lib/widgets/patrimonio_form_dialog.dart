import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

import '../services/api_service.dart';

const _accent = Color(0xFF009CDF);
const _ink = Color(0xFF17364D);
const _muted = Color(0xFF6E8290);
const _situacoesNovoCadastro = {'Em Uso', 'Disponível'};
const _destinacoesNovoCadastro = {
  'Operacional',
  'Administrativo',
  'Almoxarifado',
  'Reserva Técnica',
};
const _destinacoesPorSituacao = {
  'Em Uso': {'Operacional', 'Administrativo'},
  'Disponível': {'Reserva Técnica', 'Almoxarifado'},
};

String _formatarDataContabil(Object? value) {
  if (value == null) return 'Não informado';
  final texto = value.toString().trim();
  final data = DateTime.tryParse(texto);
  return data == null ? texto : DateFormat('dd/MM/yyyy').format(data);
}

String _formatarMoeda(Object? value) {
  if (value == null) return 'Não informado';
  final numero = value is num
      ? value
      : num.tryParse(value.toString().trim().replaceAll(',', '.'));
  if (numero == null) return value.toString();
  return NumberFormat.currency(
    locale: 'pt_BR',
    symbol: 'R\$',
    decimalDigits: 2,
  ).format(numero);
}

class PatrimonioFormDialog extends StatefulWidget {
  final Map<String, dynamic>? patrimonio;

  const PatrimonioFormDialog({super.key, this.patrimonio});

  @override
  State<PatrimonioFormDialog> createState() => _PatrimonioFormDialogState();
}

class _PatrimonioFormDialogState extends State<PatrimonioFormDialog> {
  static const _stepLabels = [
    'Identificação',
    'Localização',
    'Responsabilidade',
    'Contabilidade',
    'Controle',
  ];
  static const _stepIcons = [
    Icons.inventory_2_outlined,
    Icons.location_on_outlined,
    Icons.badge_outlined,
    Icons.account_balance_outlined,
    Icons.fact_check_outlined,
  ];

  final _formKeys = List.generate(5, (_) => GlobalKey<FormState>());
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
  bool consultandoProtheus = false;
  bool consultandoResponsavel = false;
  String? erro;
  int etapaAtual = 0;
  int maiorEtapaLiberada = 0;
  Map<String, dynamic>? dadosContabeis;
  Map<String, dynamic>? responsavelConsultado;
  String? codigoReConsultado;

  bool get _editando => widget.patrimonio != null;

  DateTime get _dataMinimaGarantia {
    final cadastro = DateTime.tryParse(
      widget.patrimonio?['criado_em']?.toString() ?? '',
    )?.toLocal();
    final referencia = cadastro ?? DateTime.now();
    return DateTime(referencia.year, referencia.month, referencia.day);
  }

  List<Map<String, dynamic>> get _destinacoesDisponiveis {
    final situacaoSelecionada = situacoes
        .where((item) => item['id'] == situacaoId)
        .firstOrNull;
    final nomesPermitidos =
        _destinacoesPorSituacao[situacaoSelecionada?['nome']];
    if (nomesPermitidos == null) return _editando ? destinacoes : [];
    return destinacoes
        .where((item) => nomesPermitidos.contains(item['nome']))
        .toList();
  }

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
      final patrimonio = widget.patrimonio;
      final empresaInicial = _referenciaId(patrimonio?['empresa']);
      final departamentoInicial = _referenciaId(patrimonio?['departamento']);
      final filialInicial = _referenciaId(patrimonio?['filial']);
      final resultados = await Future.wait([
        ApiService.listarCategorias(),
        ApiService.listarEstadosConservacao(),
        ApiService.listarSituacoes(),
        ApiService.listarDestinacoes(),
        ApiService.listarEmpresas(),
        empresaInicial == null
            ? Future.value(<Map<String, dynamic>>[])
            : ApiService.listarDepartamentos(empresaInicial),
        empresaInicial == null || departamentoInicial == null
            ? Future.value(<Map<String, dynamic>>[])
            : ApiService.listarFiliais(empresaInicial, departamentoInicial),
        filialInicial == null || departamentoInicial == null
            ? Future.value(<Map<String, dynamic>>[])
            : ApiService.listarLocalizacoes(filialInicial, departamentoInicial),
      ]);
      if (!mounted) return;
      setState(() {
        categorias = resultados[0];
        estados = resultados[1];
        situacoes = _editando
            ? resultados[2]
            : resultados[2]
                  .where(
                    (item) => _situacoesNovoCadastro.contains(item['nome']),
                  )
                  .toList();
        destinacoes = _editando
            ? resultados[3]
            : resultados[3]
                  .where(
                    (item) => _destinacoesNovoCadastro.contains(item['nome']),
                  )
                  .toList();
        empresas = resultados[4];
        departamentos = resultados[5];
        filiais = resultados[6];
        localizacoes = resultados[7];
        if (patrimonio != null) _preencherPatrimonio(patrimonio);
        carregando = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        erro = error.toString().replaceFirst('Exception: ', '');
        carregando = false;
      });
    }
  }

  int? _referenciaId(Object? referencia) {
    if (referencia is! Map<String, dynamic>) return null;
    return referencia['id'] as int?;
  }

  void _preencherPatrimonio(Map<String, dynamic> patrimonio) {
    const campos = [
      'codigo_protheus',
      'numero_item',
      'codigo_sap',
      'numero_plaqueta_fisica',
      'descricao',
      'marca',
      'modelo',
      'fabricante',
      'numero_serie',
      'observacao',
    ];
    for (final campo in campos) {
      _controllers[campo]!.text = patrimonio[campo]?.toString() ?? '';
    }

    final responsavel = patrimonio['responsavel'] as Map<String, dynamic>?;
    final codigoRe = responsavel?['codigo']?.toString() ?? '';
    _controllers['codigo_re']!.text = codigoRe;
    categoriaId = _referenciaId(patrimonio['categoria']);
    estadoId = _referenciaId(patrimonio['estado_conservacao']);
    situacaoId = _referenciaId(patrimonio['situacao']);
    destinacaoId = _referenciaId(patrimonio['destinacao']);
    empresaId = _referenciaId(patrimonio['empresa']);
    departamentoId = _referenciaId(patrimonio['departamento']);
    filialId = _referenciaId(patrimonio['filial']);
    localizacaoId = _referenciaId(patrimonio['localizacao']);
    final cidade = patrimonio['cidade'] as Map<String, dynamic>?;
    cidadeSelecionada = cidade?['nome']?.toString() ?? '';
    possuiGarantia = patrimonio['possui_garantia'] == true;
    garantia = DateTime.tryParse(
      patrimonio['data_fim_garantia']?.toString() ?? '',
    );
    dadosContabeis = patrimonio['contabil'] as Map<String, dynamic>?;
    responsavelConsultado = responsavel;
    codigoReConsultado = codigoRe;
  }

  Future<void> _selecionarEmpresa(int? id) async {
    setState(() {
      empresaId = id;
      departamentoId = null;
      filialId = null;
      cidadeSelecionada = '';
      localizacaoId = null;
      departamentos = [];
      filiais = [];
      localizacoes = [];
    });
    if (id == null) return;
    try {
      final dados = await ApiService.listarDepartamentos(id);
      if (mounted) setState(() => departamentos = dados);
    } catch (error) {
      if (mounted) {
        setState(() => erro = error.toString().replaceFirst('Exception: ', ''));
      }
    }
  }

  void _selecionarSituacao(int? id) {
    setState(() {
      situacaoId = id;
      destinacaoId = null;
    });
  }

  Future<void> _selecionarDepartamento(int? id) async {
    setState(() {
      departamentoId = id;
      filialId = null;
      cidadeSelecionada = '';
      localizacaoId = null;
      filiais = [];
      localizacoes = [];
    });
    if (empresaId == null || id == null) return;
    try {
      final dados = await ApiService.listarFiliais(empresaId!, id);
      if (mounted) setState(() => filiais = dados);
    } catch (error) {
      if (mounted) {
        setState(() => erro = error.toString().replaceFirst('Exception: ', ''));
      }
    }
  }

  Future<void> _atualizarLocalizacoes() async {
    setState(() {
      localizacaoId = null;
      localizacoes = [];
    });
    if (filialId == null || departamentoId == null) return;
    try {
      final dados = await ApiService.listarLocalizacoes(
        filialId!,
        departamentoId!,
      );
      if (mounted) setState(() => localizacoes = dados);
    } catch (error) {
      if (mounted) {
        setState(() => erro = error.toString().replaceFirst('Exception: ', ''));
      }
    }
  }

  String? _obrigatorio(dynamic value) {
    if (value == null || value.toString().trim().isEmpty) {
      return 'Campo obrigatório';
    }
    return null;
  }

  String? _normalizarIdentificador(String field, String nome, int tamanho) {
    final informado = _controllers[field]!.text.trim();
    if (informado.isEmpty ||
        informado.length > tamanho ||
        !RegExp(r'^[A-Za-z0-9]+$').hasMatch(informado)) {
      setState(() {
        erro = 'Informe $nome com até $tamanho letras ou números.';
      });
      return null;
    }

    final normalizado = informado.toUpperCase().padLeft(tamanho, '0');
    _controllers[field]!.value = TextEditingValue(
      text: normalizado,
      selection: TextSelection.collapsed(offset: normalizado.length),
    );
    return normalizado;
  }

  String? _normalizarCodigoProtheus() =>
      _normalizarIdentificador('codigo_protheus', 'o Código Protheus', 10);

  Future<void> _consultarProtheus() async {
    final codigo = _normalizarCodigoProtheus();
    if (codigo == null) return;

    final item = _normalizarIdentificador('numero_item', 'o Nº do Item', 4);
    if (item == null) return;
    setState(() {
      consultandoProtheus = true;
      erro = null;
    });
    try {
      final original = widget.patrimonio;
      final mesmosIdentificadores =
          original != null &&
          original['codigo_protheus']?.toString().toUpperCase() == codigo &&
          original['numero_item']?.toString().toUpperCase() == item;
      final duplicado = mesmosIdentificadores
          ? false
          : await ApiService.patrimonioProtheusItemJaCadastrado(codigo, item);
      if (duplicado) {
        throw Exception(
          'Este Código Protheus e Nº do Item já estão cadastrados.',
        );
      }
      final resultados = await Future.wait([
        ApiService.consultarProtheusCadastral(codigo, item),
        ApiService.consultarProtheusContabil(codigo, item),
      ]);
      if (!mounted) return;
      final cadastral = resultados[0]['dados'] as Map<String, dynamic>?;
      final contabil = resultados[1]['dados'] as Map<String, dynamic>?;
      setState(() {
        dadosContabeis = contabil;
        if (cadastral != null) {
          _controllers['descricao']!.text =
              cadastral['descricao']?.toString() ?? '';
          _controllers['modelo']!.text = cadastral['modelo']?.toString() ?? '';
          _controllers['fabricante']!.text =
              cadastral['fabricante']?.toString() ?? '';
        }
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Dados do Protheus atualizados.')),
      );
    } catch (error) {
      if (mounted) {
        setState(() => erro = error.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => consultandoProtheus = false);
    }
  }

  Future<void> _consultarResponsavel() async {
    final codigo = _normalizarIdentificador('codigo_re', 'o RE', 5);
    if (codigo == null) return;
    setState(() {
      consultandoResponsavel = true;
      responsavelConsultado = null;
      codigoReConsultado = null;
      erro = null;
    });
    try {
      final resposta = await ApiService.consultarResponsavel(codigo);
      if (!mounted) return;
      setState(() {
        responsavelConsultado =
            (resposta['dados'] as Map<String, dynamic>?) ?? resposta;
        codigoReConsultado = codigo;
      });
    } catch (error) {
      if (mounted) {
        setState(() => erro = error.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => consultandoResponsavel = false);
    }
  }

  Future<void> _selecionarGarantia() async {
    final dataMinima = _dataMinimaGarantia;
    final dataInicial = garantia == null || garantia!.isBefore(dataMinima)
        ? dataMinima
        : garantia!;
    final data = await showDatePicker(
      context: context,
      firstDate: dataMinima,
      lastDate: DateTime(2100),
      initialDate: dataInicial,
    );
    if (data != null) setState(() => garantia = data);
  }

  String _date(DateTime value) =>
      '${value.year.toString().padLeft(4, '0')}-'
      '${value.month.toString().padLeft(2, '0')}-'
      '${value.day.toString().padLeft(2, '0')}';

  bool _validarEtapa() {
    final valido = _formKeys[etapaAtual].currentState?.validate() ?? true;
    if (!valido) return false;
    if (etapaAtual == 0 && possuiGarantia && garantia == null) {
      setState(() => erro = 'Informe a data de fim da garantia.');
      return false;
    }
    if (etapaAtual == 0 &&
        garantia != null &&
        garantia!.isBefore(_dataMinimaGarantia)) {
      setState(() {
        erro = 'A data de fim da garantia não pode ser anterior à data do cadastro.';
      });
      return false;
    }
    if (etapaAtual == 2 &&
        codigoReConsultado != _controllers['codigo_re']!.text.trim()) {
      setState(() {
        erro = 'Consulte o RE informado antes de continuar.';
      });
      return false;
    }
    setState(() => erro = null);
    return true;
  }

  void _avancar() {
    if (!_validarEtapa()) return;
    if (etapaAtual == _stepLabels.length - 1) {
      _salvar();
      return;
    }
    setState(() {
      etapaAtual += 1;
      if (etapaAtual > maiorEtapaLiberada) {
        maiorEtapaLiberada = etapaAtual;
      }
    });
  }

  void _irParaEtapa(int index) {
    if (index > maiorEtapaLiberada || index == etapaAtual) return;
    if (index > etapaAtual && !_validarEtapa()) return;
    setState(() {
      etapaAtual = index;
      erro = null;
    });
  }

  Future<void> _salvar() async {
    if (!_validarEtapa()) return;
    setState(() {
      salvando = true;
      erro = null;
    });

    String? opcional(String field) {
      final value = _controllers[field]!.text.trim();
      return value.isEmpty ? null : value;
    }

    try {
      final codigoProtheus = _normalizarCodigoProtheus();
      final numeroItem = _normalizarIdentificador(
        'numero_item',
        'o Nº do Item',
        4,
      );
      final numeroPlaqueta = _normalizarIdentificador(
        'numero_plaqueta_fisica',
        'o Nº da Plaqueta Física',
        10,
      );
      final codigoRe = _normalizarIdentificador('codigo_re', 'o RE', 5);
      if (codigoProtheus == null ||
          numeroItem == null ||
          numeroPlaqueta == null ||
          codigoRe == null) {
        return;
      }
      final payload = <String, dynamic>{
        'codigo_protheus': codigoProtheus,
        'numero_item': numeroItem,
        'codigo_sap': opcional('codigo_sap'),
        'numero_plaqueta_fisica': numeroPlaqueta,
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
        'codigo_re': codigoRe,
        'estado_conservacao_id': estadoId,
        'situacao_id': situacaoId,
        'destinacao_id': destinacaoId,
        'observacao': opcional('observacao'),
      };
      if (_editando) {
        await ApiService.atualizarPatrimonio(
          widget.patrimonio!['id'] as int,
          payload,
        );
      } else {
        await ApiService.criarPatrimonio(payload);
      }
      if (mounted) Navigator.pop(context, true);
    } catch (error) {
      if (mounted) {
        setState(() => erro = error.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  double _larguraCampo(double width) {
    if (width >= 900) return (width - 32) / 3;
    if (width >= 600) return (width - 16) / 2;
    return width;
  }

  Widget _texto(
    String field,
    String label, {
    bool required = false,
    int lines = 1,
    required double width,
    bool readOnly = false,
    List<TextInputFormatter>? inputFormatters,
    TextInputType? keyboardType,
    ValueChanged<String>? onChanged,
  }) {
    return SizedBox(
      width: width,
      child: TextFormField(
        controller: _controllers[field],
        maxLines: lines,
        readOnly: readOnly,
        inputFormatters: inputFormatters,
        keyboardType: keyboardType,
        onChanged: onChanged,
        validator: required ? _obrigatorio : null,
        decoration: InputDecoration(
          labelText: label,
          filled: readOnly,
          fillColor: readOnly ? const Color(0xFFF4F7F9) : null,
        ),
      ),
    );
  }

  Widget _dropdown(
    String label,
    List<Map<String, dynamic>> items,
    int? value,
    ValueChanged<int?> onChanged, {
    required double width,
    bool enabled = true,
  }) {
    return SizedBox(
      width: width,
      child: DropdownButtonFormField<int>(
        key: ValueKey(
          '$label:$value:${items.map((item) => item['id']).join(',')}',
        ),
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
        onChanged: enabled ? onChanged : null,
      ),
    );
  }

  Widget _cabecalhoEtapa(String titulo, String descricao) => Padding(
    padding: const EdgeInsets.only(bottom: 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          titulo,
          style: const TextStyle(
            color: _ink,
            fontSize: 20,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 6),
        Text(descricao, style: const TextStyle(color: _muted)),
      ],
    ),
  );

  Widget _identificacao(double width) {
    final campo = _larguraCampo(width);
    return Form(
      key: _formKeys[0],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _cabecalhoEtapa(
            'Identificação do patrimônio',
            'Informe os códigos de origem e os dados cadastrais do bem.',
          ),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              _texto(
                'codigo_protheus',
                'Código Protheus *',
                required: true,
                width: campo,
                keyboardType: TextInputType.text,
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9]')),
                  LengthLimitingTextInputFormatter(10),
                ],
              ),
              _texto(
                'numero_item',
                'Nº do Item *',
                required: true,
                width: campo,
                keyboardType: TextInputType.text,
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9]')),
                  LengthLimitingTextInputFormatter(4),
                ],
              ),
              SizedBox(
                width: campo,
                height: 56,
                child: FilledButton.tonalIcon(
                  onPressed: consultandoProtheus ? null : _consultarProtheus,
                  icon: consultandoProtheus
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.cloud_sync_outlined),
                  label: const Text('Consultar Protheus'),
                ),
              ),
              _texto(
                'numero_plaqueta_fisica',
                'Nº da Plaqueta Física *',
                required: true,
                width: campo,
                keyboardType: TextInputType.text,
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9]')),
                  LengthLimitingTextInputFormatter(10),
                ],
              ),
              _texto('codigo_sap', 'Código SAP', width: campo),
              _texto('numero_serie', 'Número de Série', width: campo),
              _texto(
                'descricao',
                'Descrição *',
                required: true,
                width: width,
                lines: 2,
                readOnly: true,
              ),
            ],
          ),
          const _SectionTitle('Características'),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              _dropdown(
                'Categoria *',
                categorias,
                categoriaId,
                (id) => setState(() => categoriaId = id),
                width: campo,
              ),
              _texto('marca', 'Marca', width: campo),
              _texto('modelo', 'Modelo', width: campo, readOnly: true),
              _texto('fabricante', 'Fabricante', width: campo, readOnly: true),
              SizedBox(
                width: campo,
                height: 56,
                child: SwitchListTile.adaptive(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12),
                  title: const Text('Possui garantia? *'),
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
                width: campo,
                onPressed: possuiGarantia ? _selecionarGarantia : null,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _localizacao(double width) {
    final campo = _larguraCampo(width);
    return Form(
      key: _formKeys[1],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _cabecalhoEtapa(
            'Localização do bem',
            'Defina a unidade e o vínculo interno onde o patrimônio ficará alocado.',
          ),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              _dropdown(
                'Empresa *',
                empresas,
                empresaId,
                _selecionarEmpresa,
                width: campo,
              ),
              _dropdown(
                'Departamento interno *',
                departamentos,
                departamentoId,
                _selecionarDepartamento,
                width: campo,
                enabled: empresaId != null,
              ),
              _dropdown(
                'Filial *',
                filiais,
                filialId,
                (id) {
                  setState(() {
                    filialId = id;
                    final filial = filiais.firstWhere(
                      (item) => item['id'] == id,
                      orElse: () => <String, dynamic>{},
                    );
                    final cidade = filial['cidade'] as Map<String, dynamic>?;
                    cidadeSelecionada = cidade == null
                        ? ''
                        : '${cidade['nome']} - ${cidade['uf']}';
                  });
                  _atualizarLocalizacoes();
                },
                width: campo,
                enabled: departamentoId != null,
              ),
              SizedBox(
                width: campo,
                child: InputDecorator(
                  decoration: const InputDecoration(labelText: 'Cidade'),
                  child: Text(
                    cidadeSelecionada.isEmpty
                        ? 'Preenchida pela filial'
                        : cidadeSelecionada,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
              _dropdown(
                'Localização *',
                localizacoes,
                localizacaoId,
                (id) => setState(() => localizacaoId = id),
                width: campo,
                enabled: filialId != null,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _responsabilidade(double width) {
    final campo = _larguraCampo(width);
    final responsavel = responsavelConsultado;
    return Form(
      key: _formKeys[2],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _cabecalhoEtapa(
            'Responsabilidade',
            'Consulte o RE para confirmar o responsável vinculado ao patrimônio.',
          ),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              _texto(
                'codigo_re',
                'RE do Responsável *',
                required: true,
                width: campo,
                keyboardType: TextInputType.text,
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9]')),
                  LengthLimitingTextInputFormatter(5),
                ],
                onChanged: (_) {
                  if (codigoReConsultado == null &&
                      responsavelConsultado == null) {
                    return;
                  }
                  setState(() {
                    codigoReConsultado = null;
                    responsavelConsultado = null;
                  });
                },
              ),
              SizedBox(
                width: campo,
                height: 56,
                child: FilledButton.tonalIcon(
                  onPressed: consultandoResponsavel
                      ? null
                      : _consultarResponsavel,
                  icon: consultandoResponsavel
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.person_search_outlined),
                  label: const Text('Validar responsável'),
                ),
              ),
            ],
          ),
          if (responsavel != null) ...[
            const SizedBox(height: 24),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F8FC),
                border: Border.all(color: const Color(0xFFC9E6F2)),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Wrap(
                spacing: 32,
                runSpacing: 18,
                children: [
                  _InfoValue('Nome', responsavel['nome']),
                  _InfoValue('Cargo', responsavel['cargo']),
                  _InfoValue(
                    'Departamento externo',
                    responsavel['departamento_externo'],
                  ),
                  _InfoValue(
                    'Gestor responsável',
                    responsavel['gestor_responsavel'],
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _contabilidade(double width) {
    final dados = dadosContabeis;
    return Form(
      key: _formKeys[3],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _cabecalhoEtapa(
            'Dados contábeis',
            'Informações somente para leitura, obtidas do Protheus pelo código e item.',
          ),
          if (dados == null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFFF6F8FA),
                border: Border.all(color: const Color(0xFFDCE4EA)),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Column(
                children: [
                  const Icon(
                    Icons.cloud_off_outlined,
                    size: 38,
                    color: Color(0xFF78909C),
                  ),
                  const SizedBox(height: 10),
                  const Text('Nenhum dado contábil consultado nesta sessão.'),
                  const SizedBox(height: 14),
                  OutlinedButton.icon(
                    onPressed: consultandoProtheus ? null : _consultarProtheus,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Consultar agora'),
                  ),
                ],
              ),
            )
          else
            Wrap(
              spacing: 32,
              runSpacing: 22,
              children: [
                _InfoValue('Nº Nota Fiscal', dados['numero_nota_fiscal']),
                _InfoValue('Série', dados['serie_nota_fiscal']),
                _InfoValue(
                  'Data da Nota',
                  _formatarDataContabil(dados['data_nota_fiscal']),
                ),
                _InfoValue('Fornecedor', dados['fornecedor']),
                _InfoValue(
                  'Valor de Aquisição',
                  _formatarMoeda(dados['valor_aquisicao']),
                ),
                _InfoValue('ICMS', _formatarMoeda(dados['icms'])),
                _InfoValue('% Depreciação', dados['percentual_depreciacao']),
                _InfoValue(
                  'Depreciação Mensal',
                  _formatarMoeda(dados['depreciacao_mensal']),
                ),
                _InfoValue(
                  'Depreciação Acumulada',
                  _formatarMoeda(dados['depreciacao_acumulada']),
                ),
                _InfoValue('Valor Atual', _formatarMoeda(dados['valor_atual'])),
                _InfoValue('Conta Contábil', dados['conta_contabil']),
                _InfoValue('Centro de Custo', dados['centro_custo']),
              ],
            ),
        ],
      ),
    );
  }

  Widget _controle(double width) {
    final campo = _larguraCampo(width);
    return Form(
      key: _formKeys[4],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _cabecalhoEtapa(
            'Controle patrimonial',
            'Conclua o cadastro com a condição, situação e destinação do bem.',
          ),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              _dropdown(
                'Estado de conservação *',
                estados,
                estadoId,
                (id) => setState(() => estadoId = id),
                width: campo,
              ),
              _dropdown(
                'Situação *',
                situacoes,
                situacaoId,
                _selecionarSituacao,
                width: campo,
              ),
              _dropdown(
                'Destinação *',
                _destinacoesDisponiveis,
                destinacaoId,
                (id) => setState(() => destinacaoId = id),
                width: campo,
                enabled: situacaoId != null,
              ),
              _texto('observacao', 'Observação', width: width, lines: 4),
            ],
          ),
        ],
      ),
    );
  }

  Widget _conteudoEtapa(double width) {
    switch (etapaAtual) {
      case 0:
        return _identificacao(width);
      case 1:
        return _localizacao(width);
      case 2:
        return _responsabilidade(width);
      case 3:
        return _contabilidade(width);
      default:
        return _controle(width);
    }
  }

  Widget _barraEtapas() => Container(
    color: Colors.white,
    padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 18),
    child: SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(_stepLabels.length, (index) {
          final ativa = index == etapaAtual;
          final concluida = index < etapaAtual;
          final liberada = index <= maiorEtapaLiberada;
          return Row(
            children: [
              InkWell(
                borderRadius: BorderRadius.circular(6),
                onTap: liberada ? () => _irParaEtapa(index) : null,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: ativa || concluida
                              ? _accent
                              : const Color(0xFFE8EEF2),
                          shape: BoxShape.circle,
                        ),
                        child: concluida
                            ? const Icon(
                                Icons.check,
                                color: Colors.white,
                                size: 18,
                              )
                            : Text(
                                '${index + 1}',
                                style: TextStyle(
                                  color: ativa ? Colors.white : _muted,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                      ),
                      const SizedBox(width: 9),
                      Text(
                        _stepLabels[index],
                        style: TextStyle(
                          color: ativa ? _ink : _muted,
                          fontWeight: ativa ? FontWeight.w700 : FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (index < _stepLabels.length - 1)
                Container(
                  width: 46,
                  height: 1,
                  margin: const EdgeInsets.symmetric(horizontal: 14),
                  color: concluida ? _accent : const Color(0xFFD9E2E8),
                ),
            ],
          );
        }),
      ),
    ),
  );

  Widget _resumoProgresso() => Container(
    width: 250,
    color: const Color(0xFFF7FAFC),
    padding: const EdgeInsets.all(24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Progresso do cadastro',
          style: TextStyle(color: _ink, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 10),
        LinearProgressIndicator(
          value: (etapaAtual + 1) / _stepLabels.length,
          minHeight: 6,
          borderRadius: BorderRadius.circular(3),
          backgroundColor: const Color(0xFFDCE6EC),
        ),
        const SizedBox(height: 24),
        for (var index = 0; index < _stepLabels.length; index++)
          Padding(
            padding: const EdgeInsets.only(bottom: 18),
            child: Row(
              children: [
                Icon(
                  index < etapaAtual ? Icons.check_circle : _stepIcons[index],
                  size: 20,
                  color: index <= etapaAtual
                      ? _accent
                      : const Color(0xFF9AAAB4),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _stepLabels[index],
                    style: TextStyle(
                      color: index == etapaAtual ? _ink : _muted,
                      fontWeight: index == etapaAtual
                          ? FontWeight.w700
                          : FontWeight.w400,
                    ),
                  ),
                ),
              ],
            ),
          ),
        const Spacer(),
        Text(
          'Etapa ${etapaAtual + 1} de ${_stepLabels.length}',
          style: const TextStyle(color: _muted, fontSize: 12),
        ),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 1240, maxHeight: 860),
        decoration: BoxDecoration(
          color: const Color(0xFFF2F6F9),
          borderRadius: BorderRadius.circular(8),
          boxShadow: const [
            BoxShadow(
              color: Color(0x33000000),
              blurRadius: 28,
              offset: Offset(0, 12),
            ),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          children: [
            Container(
              color: Colors.white,
              padding: const EdgeInsets.fromLTRB(28, 20, 16, 18),
              child: Row(
                children: [
                  const Icon(
                    Icons.inventory_2_outlined,
                    color: _accent,
                    size: 28,
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _editando ? 'Editar patrimônio' : 'Novo patrimônio',
                          style: const TextStyle(
                            color: _ink,
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          _editando
                              ? 'Atualize os dados e vínculos do bem selecionado.'
                              : 'Cadastre e vincule um novo bem ao controle patrimonial.',
                          style: const TextStyle(color: _muted),
                        ),
                      ],
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
            const Divider(height: 1, color: Color(0xFFE2E9EE)),
            _barraEtapas(),
            const Divider(height: 1, color: Color(0xFFE2E9EE)),
            Expanded(
              child: carregando
                  ? const Center(child: CircularProgressIndicator())
                  : LayoutBuilder(
                      builder: (context, constraints) {
                        final mostraResumo = constraints.maxWidth >= 980;
                        return Row(
                          children: [
                            Expanded(
                              child: Container(
                                color: Colors.white,
                                child: SingleChildScrollView(
                                  padding: const EdgeInsets.all(28),
                                  child: LayoutBuilder(
                                    builder: (context, inner) => Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        if (erro != null) _ErrorBanner(erro!),
                                        if (categorias.isEmpty)
                                          const Padding(
                                            padding: EdgeInsets.only(
                                              bottom: 16,
                                            ),
                                            child: Text(
                                              'Nenhuma categoria patrimonial ativa foi cadastrada.',
                                              style: TextStyle(
                                                color: Colors.orange,
                                              ),
                                            ),
                                          ),
                                        _conteudoEtapa(inner.maxWidth),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            if (mostraResumo) ...[
                              const VerticalDivider(width: 1),
                              _resumoProgresso(),
                            ],
                          ],
                        );
                      },
                    ),
            ),
            const Divider(height: 1, color: Color(0xFFE2E9EE)),
            Container(
              color: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
              child: Row(
                children: [
                  TextButton(
                    onPressed: salvando ? null : () => Navigator.pop(context),
                    child: const Text('Cancelar'),
                  ),
                  const Spacer(),
                  if (etapaAtual > 0) ...[
                    OutlinedButton.icon(
                      onPressed: salvando
                          ? null
                          : () => setState(() => etapaAtual -= 1),
                      icon: const Icon(Icons.arrow_back),
                      label: const Text('Anterior'),
                    ),
                    const SizedBox(width: 12),
                  ],
                  FilledButton.icon(
                    onPressed: salvando ? null : _avancar,
                    icon: salvando
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Icon(
                            etapaAtual == _stepLabels.length - 1
                                ? Icons.save_outlined
                                : Icons.arrow_forward,
                          ),
                    label: Text(
                      etapaAtual == _stepLabels.length - 1
                          ? (_editando
                                ? 'Salvar alterações'
                                : 'Salvar patrimônio')
                          : 'Próxima etapa',
                    ),
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
    padding: const EdgeInsets.only(top: 24, bottom: 12),
    child: Text(
      text,
      style: const TextStyle(color: _accent, fontWeight: FontWeight.w700),
    ),
  );
}

class _DateButton extends StatelessWidget {
  final String label;
  final DateTime? value;
  final double width;
  final VoidCallback? onPressed;

  const _DateButton({
    required this.label,
    required this.value,
    required this.width,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) => SizedBox(
    width: width,
    height: 56,
    child: OutlinedButton.icon(
      onPressed: onPressed,
      icon: const Icon(Icons.calendar_today_outlined, size: 18),
      label: Text(
        value == null
            ? label
            : '$label: ${value!.day}/${value!.month}/${value!.year}',
        overflow: TextOverflow.ellipsis,
      ),
    ),
  );
}

class _InfoValue extends StatelessWidget {
  final String label;
  final Object? value;

  const _InfoValue(this.label, this.value);

  @override
  Widget build(BuildContext context) => SizedBox(
    width: 190,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: _muted, fontSize: 12)),
        const SizedBox(height: 4),
        Text(
          value?.toString().trim().isNotEmpty == true
              ? '$value'
              : 'Não informado',
          style: const TextStyle(color: _ink, fontWeight: FontWeight.w600),
        ),
      ],
    ),
  );
}

class _ErrorBanner extends StatelessWidget {
  final String message;

  const _ErrorBanner(this.message);

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 20),
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: const Color(0xFFFFF2F1),
      border: Border.all(color: const Color(0xFFF1C9C5)),
      borderRadius: BorderRadius.circular(6),
    ),
    child: Row(
      children: [
        const Icon(Icons.error_outline, color: Color(0xFFB74235)),
        const SizedBox(width: 10),
        Expanded(child: Text(message)),
      ],
    ),
  );
}
