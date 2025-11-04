from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models_financeiro import (
    CategoriaFinanceira, ContaBancaria, Receita, Despesa, 
    MovimentacaoFinanceira, CobrancaFinanceira, ConfiguracaoFinanceira, 
    TaxaCondominio, HistoricoTaxa, FinanceiroService
)
from app.models import Morador
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func
import json

# Criar blueprint para o módulo financeiro
financeiro_bp = Blueprint('financeiro', __name__, url_prefix='/financeiro')


@financeiro_bp.route('/')
@financeiro_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal do módulo financeiro"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Estatísticas gerais
    total_receitas = db.session.query(func.sum(Receita.valor)).filter(
        Receita.tenant_id == tenant_id,
        Receita.ativo == True,
        Receita.status == 'recebido'
    ).scalar() or 0
    
    total_despesas = db.session.query(func.sum(Despesa.valor)).filter(
        Despesa.tenant_id == tenant_id,
        Despesa.ativo == True,
        Despesa.status == 'pago'
    ).scalar() or 0
    
    saldo_atual = total_receitas - total_despesas
    
    # Receitas do mês atual
    mes_atual = date.today().replace(day=1)
    receitas_mes = db.session.query(func.sum(Receita.valor)).filter(
        Receita.tenant_id == tenant_id,
        Receita.ativo == True,
        Receita.data_recebimento >= mes_atual,
        Receita.status == 'recebido'
    ).scalar() or 0
    
    # Despesas do mês atual
    despesas_mes = db.session.query(func.sum(Despesa.valor)).filter(
        Despesa.tenant_id == tenant_id,
        Despesa.ativo == True,
        Despesa.data_pagamento >= mes_atual,
        Despesa.status == 'pago'
    ).scalar() or 0
    
    # Cobranças pendentes
    cobrancas_pendentes = CobrancaFinanceira.query.filter(
        CobrancaFinanceira.tenant_id == tenant_id,
        CobrancaFinanceira.ativo == True,
        CobrancaFinanceira.status == 'pendente'
    ).count()
    
    # Cobranças atrasadas
    cobrancas_atrasadas = CobrancaFinanceira.query.filter(
        CobrancaFinanceira.tenant_id == tenant_id,
        CobrancaFinanceira.ativo == True,
        CobrancaFinanceira.status == 'atrasado'
    ).count()
    
    # Receitas recentes
    receitas_recentes = Receita.query.filter(
        Receita.tenant_id == tenant_id,
        Receita.ativo == True
    ).order_by(Receita.created_at.desc()).limit(5).all()
    
    # Despesas recentes
    despesas_recentes = Despesa.query.filter(
        Despesa.tenant_id == tenant_id,
        Despesa.ativo == True
    ).order_by(Despesa.created_at.desc()).limit(5).all()
    
    # Gráfico de receitas vs despesas (últimos 6 meses)
    dados_grafico = []
    for i in range(6):
        data_ref = date.today().replace(day=1) - timedelta(days=30*i)
        mes_inicio = data_ref
        mes_fim = (data_ref + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        receitas_periodo = db.session.query(func.sum(Receita.valor)).filter(
            Receita.tenant_id == tenant_id,
            Receita.ativo == True,
            Receita.data_recebimento.between(mes_inicio, mes_fim),
            Receita.status == 'recebido'
        ).scalar() or 0
        
        despesas_periodo = db.session.query(func.sum(Despesa.valor)).filter(
            Despesa.tenant_id == tenant_id,
            Despesa.ativo == True,
            Despesa.data_pagamento.between(mes_inicio, mes_fim),
            Despesa.status == 'pago'
        ).scalar() or 0
        
        dados_grafico.append({
            'mes': data_ref.strftime('%m/%Y'),
            'receitas': float(receitas_periodo),
            'despesas': float(despesas_periodo)
        })
    
    dados_grafico.reverse()
    
    return render_template('financeiro/dashboard.html',
                         title='Dashboard Financeiro',
                         total_receitas=total_receitas,
                         total_despesas=total_despesas,
                         saldo_atual=saldo_atual,
                         receitas_mes=receitas_mes,
                         despesas_mes=despesas_mes,
                         cobrancas_pendentes=cobrancas_pendentes,
                         cobrancas_atrasadas=cobrancas_atrasadas,
                         receitas_recentes=receitas_recentes,
                         despesas_recentes=despesas_recentes,
                         dados_grafico=dados_grafico)

@financeiro_bp.route('/cobranca')
@login_required
def cobranca():
    """Página de cobranças"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Filtros
    status = request.args.get('status', 'todas')
    mes = request.args.get('mes', date.today().strftime('%Y-%m'))
    
    query = CobrancaFinanceira.query.filter(
        CobrancaFinanceira.tenant_id == tenant_id,
        CobrancaFinanceira.ativo == True
    )
    
    if status != 'todas':
        query = query.filter(CobrancaFinanceira.status == status)
    
    if mes:
        mes_date = datetime.strptime(mes, '%Y-%m').date()
        query = query.filter(
            func.extract('year', CobrancaFinanceira.mes_referencia) == mes_date.year,
            func.extract('month', CobrancaFinanceira.mes_referencia) == mes_date.month
        )
    
    cobrancas = query.order_by(CobrancaFinanceira.data_vencimento.desc()).all()
    
    # Moradores para seleção
    moradores = Morador.query.filter(
        Morador.tenant_id == tenant_id
    ).order_by(Morador.bloco, Morador.apartamento).all()
    
    # Estatísticas
    total_cobrancas = len(cobrancas)
    total_valor = sum([c.valor_total for c in cobrancas])
    cobrancas_pagas = len([c for c in cobrancas if c.status == 'pago'])
    cobrancas_pendentes = len([c for c in cobrancas if c.status == 'pendente'])
    cobrancas_atrasadas = len([c for c in cobrancas if c.status == 'atrasado'])
    
    return render_template('financeiro/cobranca.html',
                         title='Cobranças',
                         cobrancas=cobrancas,
                         moradores=moradores,
                         total_cobrancas=total_cobrancas,
                         total_valor=total_valor,
                         cobrancas_pagas=cobrancas_pagas,
                         cobrancas_pendentes=cobrancas_pendentes,
                         cobrancas_atrasadas=cobrancas_atrasadas,
                         status_filtro=status,
                         mes_filtro=mes)

@financeiro_bp.route('/receitas')
@login_required
def receitas():
    """Página de receitas"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Filtros
    categoria_id = request.args.get('categoria_id', type=int)
    status = request.args.get('status', 'todas')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Receita.query.filter(
        Receita.tenant_id == tenant_id,
        Receita.ativo == True
    )
    
    if categoria_id:
        query = query.filter(Receita.categoria_id == categoria_id)
    
    if status != 'todas':
        query = query.filter(Receita.status == status)
    
    if data_inicio:
        query = query.filter(Receita.data_recebimento >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    
    if data_fim:
        query = query.filter(Receita.data_recebimento <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    
    receitas = query.order_by(Receita.data_recebimento.desc()).all()
    
    # Categorias para filtro
    categorias = CategoriaFinanceira.query.filter(
        CategoriaFinanceira.tenant_id == tenant_id,
        CategoriaFinanceira.tipo == 'receita',
        CategoriaFinanceira.ativo == True
    ).all()
    
    # Estatísticas
    total_receitas = len(receitas)
    total_valor = sum([r.valor for r in receitas])
    receitas_recebidas = len([r for r in receitas if r.status == 'recebido'])
    receitas_pendentes = len([r for r in receitas if r.status == 'pendente'])
    
    return render_template('financeiro/receitas.html',
                         title='Receitas',
                         receitas=receitas,
                         categorias=categorias,
                         total_receitas=total_receitas,
                         total_valor=total_valor,
                         receitas_recebidas=receitas_recebidas,
                         receitas_pendentes=receitas_pendentes,
                         categoria_filtro=categoria_id,
                         status_filtro=status,
                         data_inicio_filtro=data_inicio,
                         data_fim_filtro=data_fim)

@financeiro_bp.route('/fluxo_caixa')
@login_required
def fluxo_caixa():
    """Página de fluxo de caixa"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Filtros
    tipo = request.args.get('tipo', 'todas')
    categoria_id = request.args.get('categoria_id', type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = MovimentacaoFinanceira.query.filter(
        MovimentacaoFinanceira.tenant_id == tenant_id
    )
    
    if tipo != 'todas':
        query = query.filter(MovimentacaoFinanceira.tipo == tipo)
    
    if categoria_id:
        query = query.filter(MovimentacaoFinanceira.categoria_id == categoria_id)
    
    if data_inicio:
        query = query.filter(MovimentacaoFinanceira.data_movimentacao >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    
    if data_fim:
        query = query.filter(MovimentacaoFinanceira.data_movimentacao <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    
    movimentacoes = query.order_by(MovimentacaoFinanceira.data_movimentacao.desc()).all()
    
    # Categorias para filtro
    categorias = CategoriaFinanceira.query.filter(
        CategoriaFinanceira.tenant_id == tenant_id,
        CategoriaFinanceira.ativo == True
    ).all()
    
    # Estatísticas
    total_entradas = sum([m.valor for m in movimentacoes if m.tipo == 'entrada'])
    total_saidas = sum([m.valor for m in movimentacoes if m.tipo == 'saida'])
    saldo_atual = total_entradas - total_saidas
    total_movimentacoes = len(movimentacoes)
    
    # Dados para gráfico (últimos 30 dias)
    datas_grafico = []
    entradas_grafico = []
    saidas_grafico = []
    saldo_grafico = []
    
    for i in range(30):
        data = (datetime.now() - timedelta(days=29-i)).date()
        datas_grafico.append(data.strftime('%d/%m'))
        
        mov_dia = [m for m in movimentacoes if m.data_movimentacao == data]
        entradas = sum([m.valor for m in mov_dia if m.tipo == 'entrada'])
        saidas = sum([m.valor for m in mov_dia if m.tipo == 'saida'])
        
        entradas_grafico.append(float(entradas))
        saidas_grafico.append(float(saidas))
        saldo_grafico.append(float(entradas - saidas))
    
    return render_template('financeiro/fluxo_caixa.html',
                         title='Fluxo de Caixa',
                         movimentacoes=movimentacoes,
                         categorias=categorias,
                         total_entradas=total_entradas,
                         total_saidas=total_saidas,
                         saldo_atual=saldo_atual,
                         total_movimentacoes=total_movimentacoes,
                         datas_grafico=datas_grafico,
                         entradas_grafico=entradas_grafico,
                         saidas_grafico=saidas_grafico,
                         saldo_grafico=saldo_grafico,
                         tipo_filtro=tipo,
                         categoria_filtro=categoria_id,
                         data_inicio_filtro=data_inicio,
                         data_fim_filtro=data_fim)

@financeiro_bp.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Simular relatórios gerados
    relatorios_gerados = []
    
    return render_template('financeiro/relatorios.html',
                         title='Relatórios',
                         relatorios_gerados=relatorios_gerados)

@financeiro_bp.route('/configuracoes')
@login_required
def configuracoes():
    """Página de configurações"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Categorias
    categorias_receitas = CategoriaFinanceira.query.filter(
        CategoriaFinanceira.tenant_id == tenant_id,
        CategoriaFinanceira.tipo == 'receita',
        CategoriaFinanceira.ativo == True
    ).all()
    
    categorias_despesas = CategoriaFinanceira.query.filter(
        CategoriaFinanceira.tenant_id == tenant_id,
        CategoriaFinanceira.tipo == 'despesa',
        CategoriaFinanceira.ativo == True
    ).all()
    
    # Contas bancárias
    contas_bancarias = ContaBancaria.query.filter(
        ContaBancaria.tenant_id == tenant_id
    ).all()
    
    # Taxas do condomínio
    taxas_condominio = TaxaCondominio.query.filter(
        TaxaCondominio.tenant_id == tenant_id
    ).order_by(TaxaCondominio.categoria, TaxaCondominio.nome).all()
    
    # Histórico de taxas (últimas 10 alterações)
    historico_taxas = HistoricoTaxa.query.filter(
        HistoricoTaxa.tenant_id == tenant_id
    ).order_by(HistoricoTaxa.created_at.desc()).limit(10).all()
    
    return render_template('financeiro/configuracoes.html',
                         title='Configurações',
                         categorias_receitas=categorias_receitas,
                         categorias_despesas=categorias_despesas,
                         contas_bancarias=contas_bancarias,
                         taxas_condominio=taxas_condominio,
                         historico_taxas=historico_taxas)

@financeiro_bp.route('/despesas')
@login_required
def despesas():
    """Página de despesas"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Filtros
    categoria_id = request.args.get('categoria_id', type=int)
    status = request.args.get('status', 'todas')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Despesa.query.filter(
        Despesa.tenant_id == tenant_id,
        Despesa.ativo == True
    )
    
    if categoria_id:
        query = query.filter(Despesa.categoria_id == categoria_id)
    
    if status != 'todas':
        query = query.filter(Despesa.status == status)
    
    if data_inicio:
        query = query.filter(Despesa.data_pagamento >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    
    if data_fim:
        query = query.filter(Despesa.data_pagamento <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    
    despesas = query.order_by(Despesa.data_pagamento.desc()).all()
    
    # Categorias para filtro
    categorias = CategoriaFinanceira.query.filter(
        CategoriaFinanceira.tenant_id == tenant_id,
        CategoriaFinanceira.tipo == 'despesa',
        CategoriaFinanceira.ativo == True
    ).all()
    
    # Estatísticas
    total_despesas = len(despesas)
    total_valor = sum([d.valor for d in despesas])
    despesas_pagas = len([d for d in despesas if d.status == 'pago'])
    despesas_pendentes = len([d for d in despesas if d.status == 'pendente'])
    
    return render_template('financeiro/despesas.html',
                         title='Despesas',
                         despesas=despesas,
                         categorias=categorias,
                         total_despesas=total_despesas,
                         total_valor=total_valor,
                         despesas_pagas=despesas_pagas,
                         despesas_pendentes=despesas_pendentes,
                         categoria_filtro=categoria_id,
                         status_filtro=status,
                         data_inicio_filtro=data_inicio,
                         data_fim_filtro=data_fim)




# APIs para AJAX
@financeiro_bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API para dados do dashboard"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Implementar lógica para retornar dados em JSON
    return jsonify({
        'status': 'success',
        'data': {
            'saldo_atual': 0,
            'receitas_mes': 0,
            'despesas_mes': 0
        }
    })

# Rotas para gerenciar taxas
@financeiro_bp.route('/api/taxas', methods=['POST'])
@login_required
def criar_taxa():
    """Criar nova taxa"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    try:
        data = request.get_json()
        
        taxa = TaxaCondominio(
            tenant_id=tenant_id,
            nome=data['nome'],
            descricao=data.get('descricao', ''),
            tipo=data['tipo'],
            valor=Decimal(str(data['valor'])),
            categoria=data.get('categoria', 'adicional'),
            ativo=data.get('ativo', True),
            created_by=current_user.id
        )
        
        db.session.add(taxa)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Taxa criada com sucesso!',
            'taxa': {
                'id': taxa.id,
                'nome': taxa.nome,
                'valor_formatado': taxa.valor_formatado,
                'tipo': taxa.tipo,
                'categoria': taxa.categoria
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erro ao criar taxa: {str(e)}'
        }), 400

@financeiro_bp.route('/api/taxas/<int:taxa_id>', methods=['PUT'])
@login_required
def editar_taxa_api(taxa_id):
    """Editar taxa existente"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    try:
        taxa = TaxaCondominio.query.filter_by(
            id=taxa_id, 
            tenant_id=tenant_id
        ).first()
        
        if not taxa:
            return jsonify({
                'status': 'error',
                'message': 'Taxa não encontrada'
            }), 404
        
        data = request.get_json()
        
        # Registrar alterações no histórico
        campos_alterados = []
        if taxa.nome != data['nome']:
            campos_alterados.append(('nome', taxa.nome, data['nome']))
        if taxa.tipo != data['tipo']:
            campos_alterados.append(('tipo', taxa.tipo, data['tipo']))
        if taxa.valor != Decimal(str(data['valor'])):
            campos_alterados.append(('valor', str(taxa.valor), str(data['valor'])))
        if taxa.categoria != data.get('categoria', 'adicional'):
            campos_alterados.append(('categoria', taxa.categoria, data.get('categoria', 'adicional')))
        
        # Atualizar taxa
        taxa.nome = data['nome']
        taxa.descricao = data.get('descricao', '')
        taxa.tipo = data['tipo']
        taxa.valor = Decimal(str(data['valor']))
        taxa.categoria = data.get('categoria', 'adicional')
        taxa.ativo = data.get('ativo', True)
        taxa.updated_at = datetime.utcnow()
        
        # Salvar histórico
        for campo, valor_anterior, valor_novo in campos_alterados:
            historico = HistoricoTaxa(
                tenant_id=tenant_id,
                taxa_id=taxa.id,
                campo_alterado=campo,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                created_by=current_user.id
            )
            db.session.add(historico)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Taxa atualizada com sucesso!',
            'taxa': {
                'id': taxa.id,
                'nome': taxa.nome,
                'valor_formatado': taxa.valor_formatado,
                'tipo': taxa.tipo,
                'categoria': taxa.categoria
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erro ao atualizar taxa: {str(e)}'
        }), 400

@financeiro_bp.route('/api/taxas/<int:taxa_id>', methods=['DELETE'])
@login_required
def excluir_taxa_api(taxa_id):
    """Excluir taxa"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    try:
        taxa = TaxaCondominio.query.filter_by(
            id=taxa_id, 
            tenant_id=tenant_id
        ).first()
        
        if not taxa:
            return jsonify({
                'status': 'error',
                'message': 'Taxa não encontrada'
            }), 404
        
        # Verificar se a taxa está sendo usada em cobranças
        # (implementar verificação se necessário)
        
        db.session.delete(taxa)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Taxa excluída com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erro ao excluir taxa: {str(e)}'
        }), 400

# Rotas para cobranças em lote
@financeiro_bp.route('/api/cobrancas/lote', methods=['POST'])
@login_required
def gerar_cobrancas_lote():
    """Gerar cobranças em lote para todos os apartamentos"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    try:
        data = request.get_json()
        
        # Validar dados
        if not data.get('mes_referencia') or not data.get('valor_condominio'):
            return jsonify({
                'status': 'error',
                'message': 'Mês de referência e valor são obrigatórios'
            }), 400
        
        # Criar lote
        lote = CobrancaLote(
            tenant_id=tenant_id,
            mes_referencia=datetime.strptime(data['mes_referencia'], '%Y-%m').date(),
            valor_condominio=Decimal(str(data['valor_condominio'])),
            data_vencimento=datetime.strptime(data['mes_referencia'], '%Y-%m').replace(day=data.get('dia_vencimento', 10)).date(),
            created_by=current_user.id
        )
        
        db.session.add(lote)
        db.session.flush()  # Para obter o ID do lote
        
        # Buscar moradores
        query = Morador.query.filter(Morador.tenant_id == tenant_id)
        
        # Filtrar apenas titulares se solicitado
        if data.get('apenas_titulares'):
            query = query.filter(Morador.eh_titular == True)
        
        # Se não for todos os apartamentos, filtrar pelos selecionados
        if not data.get('todos_apartamentos') and data.get('apartamentos_selecionados'):
            apartamentos_ids = [apto['id'] for apto in data['apartamentos_selecionados']]
            query = query.filter(Morador.id.in_(apartamentos_ids))
        
        moradores = query.all()
        lote.total_apartamentos = len(moradores)
        
        # Gerar cobranças
        cobrancas_criadas = 0
        erros = 0
        
        for morador in moradores:
            try:
                # Verificar se já existe cobrança para este mês
                cobranca_existente = CobrancaFinanceira.query.filter(
                    CobrancaFinanceira.tenant_id == tenant_id,
                    CobrancaFinanceira.morador_id == morador.id,
                    CobrancaFinanceira.mes_referencia == lote.mes_referencia
                ).first()
                
                if cobranca_existente:
                    erros += 1
                    continue
                
                # Calcular valores
                valor_condominio = Decimal(str(data['valor_condominio']))
                valor_extra = Decimal(str(data.get('valor_extra', 0)))
                valor_total = valor_condominio + valor_extra
                
                # Criar cobrança
                cobranca = CobrancaFinanceira(
                    tenant_id=tenant_id,
                    morador_id=morador.id,
                    bloco=morador.bloco,
                    apartamento=morador.apartamento,
                    mes_referencia=lote.mes_referencia,
                    valor_condominio=valor_condominio,
                    valor_extra=valor_extra,
                    valor_total=valor_total,
                    data_vencimento=lote.data_vencimento,
                    observacoes=data.get('observacoes', ''),
                    created_by=current_user.id
                )
                
                db.session.add(cobranca)
                cobrancas_criadas += 1
                
            except Exception as e:
                erros += 1
                print(f"Erro ao criar cobrança para morador {morador.id}: {str(e)}")
        
        # Atualizar lote
        lote.total_gerado = cobrancas_criadas
        lote.total_erros = erros
        lote.status = 'concluido' if erros == 0 else 'concluido_com_erros'
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Cobranças geradas com sucesso! {cobrancas_criadas} criadas, {erros} erros.',
            'lote_id': lote.id,
            'total_gerado': cobrancas_criadas,
            'total_erros': erros
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erro ao gerar cobranças: {str(e)}'
        }), 400

@financeiro_bp.route('/api/moradores')
@login_required
def api_moradores():
    """API para listar moradores para seleção"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    moradores = Morador.query.filter(
        Morador.tenant_id == tenant_id
    ).order_by(Morador.bloco, Morador.apartamento).all()
    
    return jsonify({
        'status': 'success',
        'moradores': [{
            'id': m.id,
            'nome': m.nome_completo,
            'bloco': m.bloco,
            'apartamento': m.apartamento,
            'email': m.email,
            'titular': m.eh_titular,
            'apartamento_completo': f"{m.bloco}/{m.apartamento}"
        } for m in moradores]
    })

@financeiro_bp.route('/api/grafico-receitas-despesas')
@login_required
def api_grafico_receitas_despesas():
    """API para gráfico de receitas vs despesas"""
    tenant_id = getattr(current_user, 'tenant_id', 1)
    
    # Implementar lógica para retornar dados do gráfico
    return jsonify({
        'status': 'success',
        'data': []
    })
