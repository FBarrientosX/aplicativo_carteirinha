# Exemplo de como modificar rotas para usar o sistema multi-tenant

from flask import g, request, jsonify, render_template
from app.middleware import require_tenant, get_current_tenant_id
from app.models import Morador, Usuario

# ANTES (versão original)
def listar_moradores_original():
    """Versão original - lista TODOS os moradores do sistema"""
    moradores = Morador.query.all()
    return render_template('moradores/listar.html', moradores=moradores)


# DEPOIS (versão multi-tenant)
@require_tenant
def listar_moradores_tenant():
    """Versão multi-tenant - lista apenas moradores do tenant atual"""
    # Método 1: Usar g.tenant_id diretamente
    tenant_id = g.tenant_id
    moradores = Morador.query.filter_by(tenant_id=tenant_id).all()
    
    # Método 2: Usar helper function
    # tenant_id = get_current_tenant_id()
    # moradores = Morador.query.filter_by(tenant_id=tenant_id).all()
    
    # Método 3: Usar TenantMixin (quando implementado)
    # moradores = Morador.query_for_tenant().all()
    
    return render_template('moradores/listar.html', moradores=moradores)


# EXEMPLO: Criar novo morador com tenant automático
@require_tenant
def criar_morador_tenant():
    """Criar morador no tenant atual"""
    
    # Verificar se tenant pode adicionar mais moradores
    if not g.tenant.pode_adicionar_morador():
        return jsonify({
            'erro': f'Limite de moradores excedido ({g.tenant.plano_atual.limite_moradores})'
        }), 403
    
    # Dados do formulário
    dados = request.get_json()
    
    # Criar morador automaticamente no tenant atual
    morador = Morador(
        nome_completo=dados['nome_completo'],
        bloco=dados['bloco'],
        apartamento=dados['apartamento'],
        email=dados['email'],
        celular=dados['celular'],
        tenant_id=g.tenant_id  # Definir automaticamente
    )
    
    db.session.add(morador)
    db.session.commit()
    
    return jsonify({'sucesso': True, 'morador_id': morador.id})


# EXEMPLO: Dashboard com dados filtrados por tenant
@require_tenant  
def dashboard_tenant():
    """Dashboard com estatísticas do tenant atual"""
    
    tenant_id = g.tenant_id
    
    # Estatísticas filtradas por tenant
    stats = {
        'total_moradores': Morador.query.filter_by(tenant_id=tenant_id).count(),
        'carteirinhas_ativas': Morador.query.filter_by(
            tenant_id=tenant_id,
            carteirinha_ativa=True
        ).count(),
        'carteirinhas_vencidas': Morador.query.filter_by(tenant_id=tenant_id).filter(
            Morador.data_vencimento < datetime.now().date()
        ).count()
    }
    
    # Informações do tenant
    tenant_info = {
        'nome': g.tenant.nome,
        'plano': g.tenant.plano_atual.nome,
        'vencimento': g.tenant.data_vencimento,
        'dias_restantes': g.tenant.dias_para_vencer
    }
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         tenant=tenant_info)


# EXEMPLO: API com autenticação por tenant
from functools import wraps

def api_require_tenant(f):
    """Decorator para APIs que precisam de tenant"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se tenant existe
        if not hasattr(g, 'tenant') or not g.tenant:
            return jsonify({'erro': 'Tenant não encontrado'}), 404
        
        # Verificar se plano permite API
        if not g.tenant.plano_atual.tem_funcionalidade('api_access'):
            return jsonify({'erro': 'API não disponível no seu plano'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@api_require_tenant
def api_moradores():
    """API para listar moradores do tenant"""
    tenant_id = g.tenant_id
    moradores = Morador.query.filter_by(tenant_id=tenant_id).all()
    
    return jsonify([{
        'id': m.id,
        'nome': m.nome_completo,
        'bloco': m.bloco,
        'apartamento': m.apartamento,
        'status': m.status_carteirinha
    } for m in moradores])


# EXEMPLO: Filtros avançados com tenant
@require_tenant
def buscar_moradores():
    """Busca moradores com filtros (apenas do tenant atual)"""
    
    # Começar com query filtrada por tenant
    query = Morador.query.filter_by(tenant_id=g.tenant_id)
    
    # Aplicar filtros adicionais
    if request.args.get('bloco'):
        query = query.filter_by(bloco=request.args.get('bloco'))
    
    if request.args.get('status'):
        status = request.args.get('status')
        if status == 'ativo':
            query = query.filter_by(carteirinha_ativa=True)
        elif status == 'vencido':
            query = query.filter(Morador.data_vencimento < datetime.now().date())
    
    if request.args.get('nome'):
        nome = f"%{request.args.get('nome')}%"
        query = query.filter(Morador.nome_completo.ilike(nome))
    
    moradores = query.all()
    
    return render_template('moradores/listar.html', moradores=moradores)


# EXEMPLO: Configurações por tenant
@require_tenant
def get_configuracao_tenant(categoria, chave, default=None):
    """Helper para buscar configuração do tenant atual"""
    from app.models import ConfiguracaoTenant
    
    return ConfiguracaoTenant.get_valor(
        tenant_id=g.tenant_id,
        categoria=categoria,
        chave=chave,
        default=default
    )


@require_tenant
def notificacoes_settings():
    """Página de configurações de notificações do tenant"""
    
    # Buscar configurações específicas do tenant
    config = {
        'enviar_30_dias': get_configuracao_tenant('notificacoes', 'enviar_30_dias', True),
        'enviar_vencimento': get_configuracao_tenant('notificacoes', 'enviar_vencimento', True),
        'email_remetente': get_configuracao_tenant('email', 'remetente_padrao', ''),
        'servidor_smtp': get_configuracao_tenant('email', 'servidor_smtp', 'smtp.gmail.com')
    }
    
    return render_template('configuracoes/notificacoes.html', config=config)


# EXEMPLO: Logs de auditoria por tenant  
@require_tenant
def log_acao(acao, tabela=None, registro_id=None, detalhes=None):
    """Helper para registrar ações no log de auditoria"""
    from app.models import LogAuditoria
    from flask_login import current_user
    
    log = LogAuditoria(
        usuario_id=current_user.id if current_user.is_authenticated else None,
        tenant_id=g.tenant_id,  # Importante: associar ao tenant
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        detalhes=detalhes,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    db.session.add(log)
    db.session.commit()


# EXEMPLO: Relatórios por tenant
@require_tenant
def relatorio_moradores():
    """Relatório de moradores do tenant atual"""
    
    tenant_id = g.tenant_id
    
    # Query base filtrada por tenant
    moradores = Morador.query.filter_by(tenant_id=tenant_id)
    
    # Estatísticas
    total = moradores.count()
    ativos = moradores.filter_by(carteirinha_ativa=True).count()
    vencidos = moradores.filter(
        Morador.data_vencimento < datetime.now().date()
    ).count()
    
    # Agrupamento por bloco
    from sqlalchemy import func
    por_bloco = db.session.query(
        Morador.bloco,
        func.count(Morador.id).label('total')
    ).filter_by(tenant_id=tenant_id).group_by(Morador.bloco).all()
    
    dados = {
        'total': total,
        'ativos': ativos, 
        'vencidos': vencidos,
        'por_bloco': {bloco: total for bloco, total in por_bloco},
        'tenant': g.tenant.nome
    }
    
    return render_template('relatorios/moradores.html', dados=dados)


# RESUMO DE MUDANÇAS NECESSÁRIAS:
"""
1. Adicionar @require_tenant em rotas protegidas
2. Filtrar queries por tenant_id (g.tenant_id)
3. Verificar limites do plano antes de criar registros
4. Usar configurações específicas do tenant
5. Logs de auditoria com tenant_id
6. APIs verificam funcionalidades do plano
7. Relatórios filtrados por tenant
""" 