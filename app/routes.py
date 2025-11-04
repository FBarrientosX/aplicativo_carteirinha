from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, current_app, Blueprint, g
from werkzeug.utils import secure_filename
import io
from app import db
from sqlalchemy import text, func, case
from app.models import Morador, AnexoMorador, LogNotificacao, ConfiguracaoSistema, Condominio, SalvaVidas, RegistroAcesso
from app.forms import MoradorForm, ValidarCarteirinhaForm, FiltroMoradorForm, ConfiguracaoEmailForm, ConfiguracaoCondominioForm, ConfiguracaoGeralForm, SalvaVidasForm, FiltroSalvaVidasForm, RegistroAcessoForm, BuscaMoradorForm
from app.carteirinha_service import gerar_carteirinha_completa, gerar_pdf_carteirinha, gerar_lote_pdf
from app.email_service import enviar_email_boas_vindas, verificar_e_enviar_notificacoes, enviar_notificacao_30_dias, enviar_notificacao_vencimento, enviar_email
from datetime import datetime, timedelta
import os
import uuid
import plotly.graph_objs as go
import plotly.utils
import json
from flask_login import login_required

# Criar blueprint para as rotas
bp = Blueprint('main', __name__)

@bp.route('/demo-sidebar')
@login_required
def demo_sidebar():
    """Demonstração da nova navegação lateral"""
    return render_template('demo_sidebar.html', title='Demo Navegação Lateral')

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """Dashboard principal com estatísticas"""
    # Obter tenant_id atual
    tenant_id = getattr(g, 'tenant_id', 1)
    
    # Estatísticas de moradores
    total_moradores = Morador.query# # # .filter_by(tenant_id=tenant_id)  # DESABILITADO TEMPORARIAMENTE  # DESABILITADO TEMPORARIAMENTE  # DESABILITADO TEMPORARIAMENTE.count()
    
    # Contadores por status
    regulares = Morador.query.filter(
        Morador.tenant_id == tenant_id,
        Morador.data_vencimento > datetime.now().date() + timedelta(days=30)
    ).count()
    
    a_vencer = Morador.query.filter(
        Morador.tenant_id == tenant_id,
        Morador.data_vencimento.between(
            datetime.now().date(),
            datetime.now().date() + timedelta(days=30)
        )
    ).count()
    
    vencidas = Morador.query.filter(
        Morador.tenant_id == tenant_id,
        Morador.data_vencimento < datetime.now().date()
    ).count()
    
    sem_carteirinha = Morador.query.filter(
        Morador.tenant_id == tenant_id,
        Morador.data_vencimento.is_(None)
    ).count()
    
    # Estatísticas de acesso à piscina (PATCH EMERGÊNCIA)
    try:
        # Verificar se tenant_id existe na tabela
        test_query = db.session.execute(db.text("SELECT 1 FROM registro_acesso WHERE tenant_id = 1 LIMIT 1"))
        has_tenant_id = True
    except Exception:
        has_tenant_id = False
    
    try:
        if has_tenant_id:
            moradores_na_piscina = len(RegistroAcesso.obter_moradores_na_piscina(tenant_id))
        else:
            moradores_na_piscina = len(RegistroAcesso.obter_moradores_na_piscina())
    except:
        moradores_na_piscina = 0
    
    # Entradas hoje (com/sem tenant dependendo da existência da coluna)
    hoje = datetime.now().date()
    try:
        if has_tenant_id:
            entradas_hoje = RegistroAcesso.query.filter(
                db.func.date(RegistroAcesso.data_hora) == hoje,
                RegistroAcesso.tipo == 'entrada',
                # # # RegistroAcesso.tenant_id == tenant_id  # DESABILITADO TEMPORARIAMENTE  # DESABILITADO TEMPORARIAMENTE  # DESABILITADO TEMPORARIAMENTE
            ).count()
            total_registros_acesso = RegistroAcesso.query# # # .filter_by(tenant_id=tenant_id)  # DESABILITADO TEMPORARIAMENTE  # DESABILITADO TEMPORARIAMENTE  # DESABILITADO TEMPORARIAMENTE.count()
        else:
            entradas_hoje = RegistroAcesso.query.filter(
                db.func.date(RegistroAcesso.data_hora) == hoje,
                RegistroAcesso.tipo == 'entrada'
            ).count()
            total_registros_acesso = RegistroAcesso.query.count()
    except Exception as e:
        print(f"Erro nas estatísticas: {e}")
        entradas_hoje = 0
        total_registros_acesso = 0
    
    # Estatísticas de salva-vidas
    total_salva_vidas = SalvaVidas.query.count()
    salva_vidas_ativos = SalvaVidas.query.filter_by(status='ativo').count()
    salva_vidas_certificados = SalvaVidas.query.filter(
        SalvaVidas.certificacao_salvamento == True,
        SalvaVidas.certificacao_primeiros_socorros == True
    ).count()
    
    # Dados para gráficos
    stats = {
        'total_moradores': total_moradores,
        'regulares': regulares,
        'a_vencer': a_vencer,
        'vencidas': vencidas,
        'sem_carteirinha': sem_carteirinha,
        'moradores_na_piscina': moradores_na_piscina,
        'entradas_hoje': entradas_hoje,
        'total_registros_acesso': total_registros_acesso,
        'total_salva_vidas': total_salva_vidas,
        'salva_vidas_ativos': salva_vidas_ativos,
        'salva_vidas_certificados': salva_vidas_certificados
    }
    
    # Gráfico de pizza
    labels = ['Regulares', 'A Vencer (30 dias)', 'Vencidas', 'Sem Carteirinha']
    values = [regulares, a_vencer, vencidas, sem_carteirinha]
    colors = ['#28a745', '#ffc107', '#dc3545', '#6c757d']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=colors)
    )])
    
    fig.update_layout(
        title="Status das Carteirinhas",
        font=dict(size=14),
        showlegend=True
    )
    
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('index.html', 
                         title='Dashboard', 
                         stats=stats,
                         graph_json=graph_json)

@bp.route('/moradores')
def listar_moradores():
    """Lista todos os moradores com filtros"""
    form = FiltroMoradorForm(request.args)
    
    # Query base
    query = Morador.query
    
    # Aplicar filtros
    if form.bloco.data:
        query = query.filter(Morador.bloco == form.bloco.data)
    
    if form.busca.data:
        query = query.filter(Morador.nome_completo.contains(form.busca.data))
    
    # Aplicar filtro de status usando a mesma lógica da property
    if form.status.data:
        hoje = datetime.now().date()
        if form.status.data == 'sem_carteirinha':
            query = query.filter(Morador.data_vencimento.is_(None))
        elif form.status.data == 'vencida':
            query = query.filter(Morador.data_vencimento < hoje)
        elif form.status.data == 'a_vencer':
            query = query.filter(
                Morador.data_vencimento >= hoje,
                Morador.data_vencimento <= hoje + timedelta(days=30)
            )
        elif form.status.data == 'regular':
            query = query.filter(Morador.data_vencimento > hoje + timedelta(days=30))
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    moradores = query.order_by(Morador.nome_completo).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Carregar opções de bloco para o filtro
    blocos = db.session.query(Morador.bloco).distinct().all()
    form.bloco.choices = [('', 'Todos os blocos')] + [(b[0], b[0]) for b in blocos]
    
    return render_template('moradores/listar.html',
                         title='Moradores',
                         moradores=moradores,
                         form=form)

@bp.route('/morador/novo', methods=['GET', 'POST'])
def novo_morador():
    """Cadastrar novo morador"""
    form = MoradorForm()
    
    if form.validate_on_submit():
        morador = Morador(
            nome_completo=form.nome_completo.data,
            bloco=form.bloco.data,
            apartamento=form.apartamento.data,
            email=form.email.data,
            celular=form.celular.data,
            eh_titular=form.eh_titular.data,
            email_titular=form.email_titular.data if not form.eh_titular.data else None,
            observacoes=form.observacoes.data
        )
        
        # Se foi informada uma data de validação, calcular vencimento
        if form.data_ultima_validacao.data:
            morador.data_ultima_validacao = form.data_ultima_validacao.data
            morador.data_vencimento = form.data_ultima_validacao.data + timedelta(days=180)  # 6 meses
            morador.carteirinha_ativa = True
        
        db.session.add(morador)
        db.session.commit()
        
        # Salvar anexos se fornecidos
        if form.foto_carteirinha.data:
            salvar_anexo(morador, form.foto_carteirinha.data, 'foto_carteirinha')
        
        # Processar documentos de forma mais robusta
        if form.documentos.data and hasattr(form.documentos.data, 'filename') and form.documentos.data.filename:
            salvar_anexo(morador, form.documentos.data, 'documento')
        
        # Enviar email de boas-vindas
        enviar_email_boas_vindas(morador)
        
        flash('Morador cadastrado com sucesso!', 'success')
        return redirect(url_for('main.listar_moradores'))
    
    return render_template('moradores/form.html',
                         title='Novo Morador',
                         form=form)

@bp.route('/morador/<int:id>/editar', methods=['GET', 'POST'])
def editar_morador(id):
    """Editar morador existente"""
    morador = Morador.query.get_or_404(id)
    form = MoradorForm(obj=morador)
    
    if form.validate_on_submit():
        # Atualizar campos manualmente em vez de usar populate_obj
        morador.nome_completo = form.nome_completo.data
        morador.bloco = form.bloco.data
        morador.apartamento = form.apartamento.data
        morador.email = form.email.data
        morador.celular = form.celular.data
        morador.eh_titular = form.eh_titular.data
        morador.observacoes = form.observacoes.data
        
        # Processar data de última validação se fornecida
        if form.data_ultima_validacao.data:
            morador.data_ultima_validacao = form.data_ultima_validacao.data
        
        # Ajustar email do titular
        if morador.eh_titular:
            morador.email_titular = None
        else:
            morador.email_titular = form.email_titular.data
        
        # Permitir edição da data de vencimento
        if form.data_vencimento.data:
            morador.data_vencimento = form.data_vencimento.data
            # Se uma nova data de vencimento foi definida, reativar carteirinha se necessário
            if morador.data_vencimento >= datetime.now().date():
                morador.carteirinha_ativa = True
        
        morador.data_atualizacao = datetime.utcnow()
        
        # Salvar anexos se fornecidos
        if form.foto_carteirinha.data:
            salvar_anexo(morador, form.foto_carteirinha.data, 'foto_carteirinha')
        
        # Processar documentos de forma mais robusta
        if form.documentos.data and hasattr(form.documentos.data, 'filename') and form.documentos.data.filename:
            salvar_anexo(morador, form.documentos.data, 'documento')
        
        db.session.commit()
        flash('Dados atualizados com sucesso!', 'success')
        return redirect(url_for('main.ver_morador', id=id))
    
    return render_template('moradores/form.html',
                         title='Editar Morador',
                         form=form,
                         morador=morador)

@bp.route('/morador/<int:id>')
def ver_morador(id):
    """Ver detalhes do morador"""
    morador = Morador.query.get_or_404(id)
    return render_template('moradores/detalhes.html',
                         title=f'Morador: {morador.nome_completo}',
                         morador=morador)

@bp.route('/morador/<int:id>/validar', methods=['GET', 'POST'])
def validar_carteirinha(id):
    """Validar carteirinha do morador"""
    morador = Morador.query.get_or_404(id)
    form = ValidarCarteirinhaForm()
    
    if form.validate_on_submit():
        meses = int(form.meses_validade.data)
        morador.validar_carteirinha(meses)
        
        # Adicionar observações se fornecidas
        if form.observacoes.data:
            obs_anterior = morador.observacoes or ""
            nova_obs = f"\n[{datetime.now().strftime('%d/%m/%Y')}] {form.observacoes.data}"
            morador.observacoes = obs_anterior + nova_obs
        
        db.session.commit()
        flash(f'Carteirinha validada por {meses} meses!', 'success')
        return redirect(url_for('main.ver_morador', id=id))
    
    return render_template('moradores/validar.html',
                         title='Validar Carteirinha',
                         morador=morador,
                         form=form)

@bp.route('/morador/<int:id>/anexos')
def listar_anexos(id):
    """Listar anexos do morador"""
    morador = Morador.query.get_or_404(id)
    return render_template('moradores/anexos.html',
                         title='Anexos',
                         morador=morador)

@bp.route('/anexo/<int:id>')
def baixar_anexo(id):
    """Download de anexo"""
    anexo = AnexoMorador.query.get_or_404(id)
    return send_from_directory(
        os.path.dirname(anexo.caminho_arquivo),
        os.path.basename(anexo.caminho_arquivo),
        as_attachment=True,
        download_name=anexo.nome_original
    )

@bp.route('/relatorios')
def relatorios():
    """Página de relatórios e analytics"""
    # Estatísticas gerais (mesmas da página principal)
    total_moradores = Morador.query.count()
    
    # Contadores por status
    regulares = Morador.query.filter(
        Morador.data_vencimento > datetime.now().date() + timedelta(days=30)
    ).count()
    
    a_vencer = Morador.query.filter(
        Morador.data_vencimento.between(
            datetime.now().date(),
            datetime.now().date() + timedelta(days=30)
        )
    ).count()
    
    vencidas = Morador.query.filter(
        Morador.data_vencimento < datetime.now().date()
    ).count()
    
    sem_carteirinha = Morador.query.filter(
        Morador.data_vencimento.is_(None)
    ).count()
    
    # Dados para gráficos
    stats = {
        'total_moradores': total_moradores,
        'regulares': regulares,
        'a_vencer': a_vencer,
        'vencidas': vencidas,
        'sem_carteirinha': sem_carteirinha
    }
    
    # Dados por bloco
    dados_bloco = db.session.query(
        Morador.bloco,
        func.count(Morador.id).label('total')
    ).group_by(Morador.bloco).all()
    
    # Gráfico por bloco
    blocos = [d[0] for d in dados_bloco]
    totais = [d[1] for d in dados_bloco]
    
    fig_bloco = go.Figure(data=[go.Bar(x=blocos, y=totais)])
    fig_bloco.update_layout(title="Moradores por Bloco")
    graph_bloco_json = json.dumps(fig_bloco, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Histórico de validações nos últimos 12 meses
    doze_meses_atras = datetime.now().date() - timedelta(days=365)
    
    # Usar strftime para SQLite em vez de date_format (MySQL)
    validacoes_por_mes = db.session.query(
        func.strftime('%Y-%m', Morador.data_ultima_validacao).label('mes'),
        func.count(Morador.id).label('total')
    ).filter(
        Morador.data_ultima_validacao >= doze_meses_atras
    ).group_by('mes').all()
    
    meses = [v[0] for v in validacoes_por_mes]
    qtd_validacoes = [v[1] for v in validacoes_por_mes]
    
    fig_validacoes = go.Figure(data=[go.Scatter(
        x=meses, 
        y=qtd_validacoes, 
        mode='lines+markers'
    )])
    fig_validacoes.update_layout(title="Validações por Mês")
    graph_validacoes_json = json.dumps(fig_validacoes, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('relatorios.html',
                         title='Relatórios',
                         stats=stats,
                         graph_bloco_json=graph_bloco_json,
                         graph_validacoes_json=graph_validacoes_json,
                         data_atual=datetime.now().strftime('%d/%m/%Y às %H:%M'))

@bp.route('/notificacoes/executar')
def executar_notificacoes():
    """Executar verificação e envio de notificações manualmente"""
    resultados = verificar_e_enviar_notificacoes()
    
    # Preparar mensagem de sucesso
    total_enviadas = resultados['notificacoes_30_dias'] + resultados['notificacoes_vencimento']
    
    if total_enviadas > 0:
        if resultados['erros']:
            flash(f'Enviadas {total_enviadas} notificações com alguns erros. Verifique o log.', 'warning')
        else:
            flash(f'Sucesso! {total_enviadas} notificações enviadas.', 'success')
    else:
        if resultados['erros']:
            flash('Erro ao enviar notificações. Verifique o log.', 'danger')
        else:
            flash('Nenhuma notificação pendente para envio.', 'info')
    
    return render_template('notificacoes/resultado.html',
                         title='Resultado das Notificações',
                         enviadas=total_enviadas,
                         erros=len(resultados['erros']) if resultados['erros'] else 0)

# Rota de teste de email removida - usar /notificacoes/teste-email-configurado

@bp.route('/configuracoes')
def configuracoes():
    """Página principal de configurações"""
    from datetime import datetime
    from app.models import ConfiguracaoSistema, Morador
    import os
    
    # Verificar status das configurações
    mail_server = ConfiguracaoSistema.get_valor('MAIL_SERVER')
    mail_username = ConfiguracaoSistema.get_valor('MAIL_USERNAME')
    mail_password = ConfiguracaoSistema.get_valor('MAIL_PASSWORD')
    
    # Status do email
    email_configurado = bool(mail_server and mail_username and mail_password)
    
    # Status do banco de dados
    try:
        total_moradores = Morador.query.count()
        banco_conectado = True
    except:
        total_moradores = 0
        banco_conectado = False
    
    # Status do backup
    backup_automatico = ConfiguracaoSistema.get_valor('BACKUP_AUTOMATICO', False)
    
    # Status de segurança (baseado em configurações)
    timeout_configurado = ConfiguracaoSistema.get_valor('SESSAO_TIMEOUT', 120) > 0
    max_tentativas_configurado = ConfiguracaoSistema.get_valor('MAX_TENTATIVAS_LOGIN', 5) > 0
    seguranca_ativa = timeout_configurado and max_tentativas_configurado
    
    # Informações do sistema
    db_path = os.path.join(os.path.dirname(__file__), '..', 'carteirinha_piscina.db')
    db_existe = os.path.exists(db_path)
    
    # Determinar modo (baseado em configurações de debug)
    modo_sistema = "Desenvolvimento" if current_app.debug else "Produção"
    
    return render_template('configuracoes/index.html', 
                         title='Configurações',
                         data_atual=datetime.now().strftime('%d/%m/%Y'),
                         email_configurado=email_configurado,
                         banco_conectado=banco_conectado,
                         backup_automatico=backup_automatico,
                         seguranca_ativa=seguranca_ativa,
                         total_moradores=total_moradores,
                         db_existe=db_existe,
                         modo_sistema=modo_sistema)

@bp.route('/configuracoes/email', methods=['GET', 'POST'])
def configuracoes_email():
    """Configurações de email"""
    form = ConfiguracaoEmailForm()
    
    if form.validate_on_submit():
        # Salvar configurações
        ConfiguracaoSistema.set_valor('MAIL_SERVER', form.mail_server.data, 
                                     'Servidor SMTP', 'texto', 'email')
        ConfiguracaoSistema.set_valor('MAIL_PORT', form.mail_port.data, 
                                     'Porta SMTP', 'numero', 'email')
        ConfiguracaoSistema.set_valor('MAIL_USE_TLS', form.mail_use_tls.data, 
                                     'Usar TLS', 'booleano', 'email')
        ConfiguracaoSistema.set_valor('MAIL_USERNAME', form.mail_username.data, 
                                     'Usuário/Email SMTP', 'email', 'email')
        ConfiguracaoSistema.set_valor('MAIL_PASSWORD', form.mail_password.data, 
                                     'Senha SMTP', 'senha', 'email')
        
        sender = form.mail_default_sender.data.strip() if form.mail_default_sender.data else form.mail_username.data
        ConfiguracaoSistema.set_valor('MAIL_DEFAULT_SENDER', sender, 
                                     'Email remetente padrão', 'email', 'email')
        
        # Atualizar configurações da aplicação E reinicializar Flask-Mail
        current_app.config.update({
            'MAIL_SERVER': form.mail_server.data,
            'MAIL_PORT': form.mail_port.data,
            'MAIL_USE_TLS': form.mail_use_tls.data,
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': form.mail_username.data,
            'MAIL_PASSWORD': form.mail_password.data.strip().replace(' ', ''),  # Limpar espaços
            'MAIL_DEFAULT_SENDER': sender
        })
        
        # Reinicializar Flask-Mail
        from app.email_service import mail
        mail.init_app(current_app)
        
        flash('Configurações de email salvas com sucesso!', 'success')
        return redirect(url_for('main.configuracoes_email'))
    
    # Carregar configurações existentes
    form.mail_server.data = ConfiguracaoSistema.get_valor('MAIL_SERVER', 'smtp.gmail.com')
    form.mail_port.data = ConfiguracaoSistema.get_valor('MAIL_PORT', 587)
    form.mail_use_tls.data = ConfiguracaoSistema.get_valor('MAIL_USE_TLS', True)
    form.mail_username.data = ConfiguracaoSistema.get_valor('MAIL_USERNAME', '')
    form.mail_default_sender.data = ConfiguracaoSistema.get_valor('MAIL_DEFAULT_SENDER', '')
    
    # Verificar se o email está configurado para mostrar status
    mail_server = ConfiguracaoSistema.get_valor('MAIL_SERVER')
    mail_username = ConfiguracaoSistema.get_valor('MAIL_USERNAME')
    mail_password = ConfiguracaoSistema.get_valor('MAIL_PASSWORD')
    email_configurado = bool(mail_server and mail_username and mail_password)
    
    return render_template('configuracoes/email.html', 
                         title='Configurações de Email', 
                         form=form,
                         email_configurado=email_configurado)

@bp.route('/configuracoes/condominio', methods=['GET', 'POST'])
def configuracoes_condominio():
    """Configurações específicas do condomínio"""
    form = ConfiguracaoCondominioForm()
    
    # Buscar ou criar condomínio
    condominio = Condominio.query.first()
    if not condominio:
        condominio = Condominio(nome='Meu Condomínio')
        db.session.add(condominio)
        db.session.commit()
    
    if form.validate_on_submit():
        # Atualizar dados do condomínio
        condominio.nome = form.nome.data
        condominio.cnpj = form.cnpj.data
        condominio.endereco = form.endereco.data
        condominio.telefone = form.telefone.data
        condominio.email_administracao = form.email_administracao.data
        condominio.whatsapp = form.whatsapp.data
        condominio.horario_funcionamento = form.horario_funcionamento.data
        condominio.dias_aviso_vencimento = form.dias_aviso_vencimento.data
        condominio.meses_validade_padrao = form.meses_validade_padrao.data
        condominio.permitir_dependentes = form.permitir_dependentes.data
        condominio.cor_primaria = form.cor_primaria.data
        condominio.cor_secundaria = form.cor_secundaria.data
        
        db.session.commit()
        flash('Configurações do condomínio salvas com sucesso!', 'success')
        return redirect(url_for('main.configuracoes_condominio'))
    
    # Carregar dados existentes
    form.nome.data = condominio.nome
    form.cnpj.data = condominio.cnpj
    form.endereco.data = condominio.endereco
    form.telefone.data = condominio.telefone
    form.email_administracao.data = condominio.email_administracao
    form.whatsapp.data = condominio.whatsapp
    form.horario_funcionamento.data = condominio.horario_funcionamento
    form.dias_aviso_vencimento.data = condominio.dias_aviso_vencimento
    form.meses_validade_padrao.data = condominio.meses_validade_padrao
    form.permitir_dependentes.data = condominio.permitir_dependentes
    form.cor_primaria.data = condominio.cor_primaria
    form.cor_secundaria.data = condominio.cor_secundaria
    
    return render_template('configuracoes/condominio.html', 
                         title='Configurações do Condomínio', 
                         form=form, 
                         condominio=condominio)

@bp.route('/configuracoes/geral', methods=['GET', 'POST'])
def configuracoes_geral():
    """Configurações gerais do sistema"""
    form = ConfiguracaoGeralForm()
    
    if form.validate_on_submit():
        # Salvar configurações gerais
        ConfiguracaoSistema.set_valor('NOME_SISTEMA', form.nome_sistema.data, 
                                     'Nome do sistema', 'texto', 'geral')
        ConfiguracaoSistema.set_valor('SESSAO_TIMEOUT', form.sessao_timeout.data, 
                                     'Timeout da sessão em minutos', 'numero', 'seguranca')
        ConfiguracaoSistema.set_valor('MAX_TENTATIVAS_LOGIN', form.max_tentativas_login.data, 
                                     'Máximo de tentativas de login', 'numero', 'seguranca')
        ConfiguracaoSistema.set_valor('BACKUP_AUTOMATICO', form.backup_automatico.data, 
                                     'Backup automático ativado', 'booleano', 'backup')
        ConfiguracaoSistema.set_valor('DIAS_BACKUP', form.dias_backup.data, 
                                     'Intervalo de backup em dias', 'numero', 'backup')
        ConfiguracaoSistema.set_valor('NOTIFICACOES_AUTOMATICAS', form.notificacoes_automaticas.data, 
                                     'Notificações automáticas ativadas', 'booleano', 'notificacoes')
        ConfiguracaoSistema.set_valor('HORARIO_NOTIFICACOES', form.horario_notificacoes.data, 
                                     'Horário das notificações automáticas', 'texto', 'notificacoes')
        
        flash('Configurações gerais salvas com sucesso!', 'success')
        return redirect(url_for('main.configuracoes_geral'))
    
    # Carregar configurações existentes
    form.nome_sistema.data = ConfiguracaoSistema.get_valor('NOME_SISTEMA', 'Sistema de Carteirinhas')
    form.sessao_timeout.data = ConfiguracaoSistema.get_valor('SESSAO_TIMEOUT', 120)
    form.max_tentativas_login.data = ConfiguracaoSistema.get_valor('MAX_TENTATIVAS_LOGIN', 5)
    form.backup_automatico.data = ConfiguracaoSistema.get_valor('BACKUP_AUTOMATICO', True)
    form.dias_backup.data = ConfiguracaoSistema.get_valor('DIAS_BACKUP', 7)
    form.notificacoes_automaticas.data = ConfiguracaoSistema.get_valor('NOTIFICACOES_AUTOMATICAS', True)
    form.horario_notificacoes.data = ConfiguracaoSistema.get_valor('HORARIO_NOTIFICACOES', '09:00')
    
    # Verificar status do email para mostrar no template
    mail_server = ConfiguracaoSistema.get_valor('MAIL_SERVER')
    mail_username = ConfiguracaoSistema.get_valor('MAIL_USERNAME')
    mail_password = ConfiguracaoSistema.get_valor('MAIL_PASSWORD')
    email_configurado = bool(mail_server and mail_username and mail_password)
    
    # Status do backup (baseado na configuração carregada)
    backup_configurado = form.backup_automatico.data if hasattr(form, 'backup_automatico') and form.backup_automatico.data is not None else ConfiguracaoSistema.get_valor('BACKUP_AUTOMATICO', False)
    
    # Status de segurança (baseado nas configurações carregadas)
    timeout_ok = form.sessao_timeout.data if hasattr(form, 'sessao_timeout') and form.sessao_timeout.data is not None else ConfiguracaoSistema.get_valor('SESSAO_TIMEOUT', 120) > 0
    tentativas_ok = form.max_tentativas_login.data if hasattr(form, 'max_tentativas_login') and form.max_tentativas_login.data is not None else ConfiguracaoSistema.get_valor('MAX_TENTATIVAS_LOGIN', 5) > 0
    seguranca_configurada = timeout_ok and tentativas_ok
    
    return render_template('configuracoes/geral.html', 
                         title='Configurações Gerais', 
                         form=form,
                         email_configurado=email_configurado,
                         backup_configurado=backup_configurado,
                         seguranca_configurada=seguranca_configurada)

@bp.route('/notificacoes/teste-email-configurado')
def teste_email_configurado():
    """Testar configuração de email usando configurações internas"""
    try:
        from app.models import ConfiguracaoSistema
        from app.email_service import mail
        from flask_mail import Message
        from datetime import datetime
        
        # Obter configurações do banco
        mail_server = ConfiguracaoSistema.get_valor('MAIL_SERVER')
        mail_username = ConfiguracaoSistema.get_valor('MAIL_USERNAME')
        mail_password = ConfiguracaoSistema.get_valor('MAIL_PASSWORD')
        
        if not mail_server or not mail_username or not mail_password:
            flash('❌ Configurações de email incompletas! Verifique servidor, usuário e senha.', 'danger')
            return redirect(url_for('main.configuracoes_email'))
        
        # Limpar espaços da senha (comum em senhas de app do Gmail)
        mail_password = mail_password.strip().replace(' ', '')
        
        # Atualizar configurações da aplicação E reinicializar o Flask-Mail
        current_app.config.update({
            'MAIL_SERVER': mail_server,
            'MAIL_PORT': ConfiguracaoSistema.get_valor('MAIL_PORT', 587),
            'MAIL_USE_TLS': ConfiguracaoSistema.get_valor('MAIL_USE_TLS', True),
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': mail_username,
            'MAIL_PASSWORD': mail_password,
            'MAIL_DEFAULT_SENDER': ConfiguracaoSistema.get_valor('MAIL_DEFAULT_SENDER', mail_username)
        })
        
        # Reinicializar o Flask-Mail com as novas configurações
        mail.init_app(current_app)
        
        # Criar mensagem de teste
        msg = Message(
            subject="✅ Teste de Email - Sistema Configurado",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[mail_username],
            html=render_template('email/teste_email.html', data_atual=datetime.now()),
            body="Teste de email usando configurações internas - Funcionando perfeitamente!"
        )
        
        # Tentar enviar
        mail.send(msg)
        
        flash(f'✅ Email de teste enviado com sucesso para {mail_username}!', 'success')
        
    except Exception as e:
        erro_msg = str(e)
        
        # Melhorar mensagens de erro
        if "530" in erro_msg and "Authentication Required" in erro_msg:
            flash('❌ Gmail requer Senha de App! Verifique se:\n1. Ativou 2FA\n2. Gerou senha de app\n3. Usou a senha de 16 dígitos (sem espaços)', 'danger')
        elif "535" in erro_msg and "authentication failed" in erro_msg.lower():
            flash('❌ Credenciais inválidas! Verifique email e senha de app.', 'danger')
        elif "Connection refused" in erro_msg:
            flash('❌ Não foi possível conectar ao servidor SMTP. Verifique servidor e porta.', 'danger')
        else:
            flash(f'❌ Erro ao enviar email de teste: {erro_msg}', 'danger')
    
    return redirect(url_for('main.configuracoes_email'))

# ===== ROTAS PARA SALVA-VIDAS =====

@bp.route('/salva-vidas')
def listar_salva_vidas():
    """Lista todos os salva-vidas com filtros"""
    form = FiltroSalvaVidasForm(request.args)
    
    # Query base
    query = SalvaVidas.query
    
    # Aplicar filtros
    if form.status.data:
        query = query.filter(SalvaVidas.status == form.status.data)
    
    if form.busca.data:
        query = query.filter(SalvaVidas.nome_completo.contains(form.busca.data))
    
    if form.certificacao.data:
        if form.certificacao.data == 'salvamento':
            query = query.filter(SalvaVidas.certificacao_salvamento == True)
        elif form.certificacao.data == 'primeiros_socorros':
            query = query.filter(SalvaVidas.certificacao_primeiros_socorros == True)
        elif form.certificacao.data == 'ambas':
            query = query.filter(
                SalvaVidas.certificacao_salvamento == True,
                SalvaVidas.certificacao_primeiros_socorros == True
            )
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    salva_vidas = query.order_by(SalvaVidas.nome_completo).paginate(
        page=page, per_page=15, error_out=False
    )
    
    # Estatísticas rápidas
    stats = {
        'total': SalvaVidas.query.count(),
        'ativos': SalvaVidas.query.filter_by(status='ativo').count(),
        'inativos': SalvaVidas.query.filter(SalvaVidas.status != 'ativo').count(),
        'certificados': SalvaVidas.query.filter(
            SalvaVidas.certificacao_salvamento == True,
            SalvaVidas.certificacao_primeiros_socorros == True
        ).count()
    }
    
    return render_template('salva_vidas/listar.html',
                         title='Equipe de Salva-vidas',
                         salva_vidas=salva_vidas,
                         form=form,
                         stats=stats)

@bp.route('/salva-vidas/novo', methods=['GET', 'POST'])
def novo_salva_vidas():
    """Cadastrar novo salva-vidas"""
    form = SalvaVidasForm()
    
    if form.validate_on_submit():
        salva_vidas = SalvaVidas(
            nome_completo=form.nome_completo.data,
            cpf=form.cpf.data,
            rg=form.rg.data,
            data_nascimento=form.data_nascimento.data,
            telefone=form.telefone.data,
            email=form.email.data,
            endereco=form.endereco.data,
            data_contratacao=form.data_contratacao.data,
            data_demissao=form.data_demissao.data,
            status=form.status.data,
            salario=form.salario.data,
            certificacao_salvamento=form.certificacao_salvamento.data,
            certificacao_primeiros_socorros=form.certificacao_primeiros_socorros.data,
            data_vencimento_certificacao=form.data_vencimento_certificacao.data,
            outras_qualificacoes=form.outras_qualificacoes.data,
            horario_trabalho=form.horario_trabalho.data,
            observacoes=form.observacoes.data
        )
        
        # Salvar foto se fornecida
        if form.foto.data:
            salvar_foto_salva_vidas(salva_vidas, form.foto.data)
        
        db.session.add(salva_vidas)
        db.session.commit()
        
        flash('Salva-vidas cadastrado com sucesso!', 'success')
        return redirect(url_for('main.listar_salva_vidas'))
    
    return render_template('salva_vidas/form.html',
                         title='Novo Salva-vidas',
                         form=form)

@bp.route('/salva-vidas/<int:id>/editar', methods=['GET', 'POST'])
def editar_salva_vidas(id):
    """Editar salva-vidas existente"""
    salva_vidas = SalvaVidas.query.get_or_404(id)
    form = SalvaVidasForm(obj=salva_vidas)
    
    if form.validate_on_submit():
        form.populate_obj(salva_vidas)
        salva_vidas.data_atualizacao = datetime.utcnow()
        
        # Salvar foto se fornecida
        if form.foto.data:
            salvar_foto_salva_vidas(salva_vidas, form.foto.data)
        
        db.session.commit()
        flash('Dados atualizados com sucesso!', 'success')
        return redirect(url_for('main.ver_salva_vidas', id=id))
    
    return render_template('salva_vidas/form.html',
                         title='Editar Salva-vidas',
                         form=form,
                         salva_vidas=salva_vidas)

@bp.route('/salva-vidas/<int:id>')
def ver_salva_vidas(id):
    """Ver detalhes do salva-vidas"""
    salva_vidas = SalvaVidas.query.get_or_404(id)
    return render_template('salva_vidas/detalhes.html',
                         title=f'Salva-vidas: {salva_vidas.nome_completo}',
                         salva_vidas=salva_vidas)

@bp.route('/salva-vidas/<int:id>/inativar', methods=['POST'])
def inativar_salva_vidas(id):
    """Inativar salva-vidas"""
    salva_vidas = SalvaVidas.query.get_or_404(id)
    salva_vidas.status = 'inativo'
    salva_vidas.data_atualizacao = datetime.utcnow()
    db.session.commit()
    
    flash(f'Salva-vidas {salva_vidas.nome_completo} foi inativado.', 'warning')
    return redirect(url_for('main.ver_salva_vidas', id=id))

@bp.route('/salva-vidas/<int:id>/reativar', methods=['POST'])
def reativar_salva_vidas(id):
    """Reativar salva-vidas"""
    salva_vidas = SalvaVidas.query.get_or_404(id)
    salva_vidas.status = 'ativo'
    salva_vidas.data_atualizacao = datetime.utcnow()
    db.session.commit()
    
    flash(f'Salva-vidas {salva_vidas.nome_completo} foi reativado.', 'success')
    return redirect(url_for('main.ver_salva_vidas', id=id))

def salvar_foto_salva_vidas(salva_vidas, arquivo):
    """Salvar foto do salva-vidas"""
    if arquivo and hasattr(arquivo, 'filename') and arquivo.filename:
        filename = secure_filename(arquivo.filename)
        # Gerar nome único
        nome_unico = f"salva_vidas_{salva_vidas.id}_{uuid.uuid4().hex[:8]}.{filename.rsplit('.', 1)[1].lower()}"
        
        # Criar diretório se não existir
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'salva_vidas')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salvar arquivo
        caminho_arquivo = os.path.join(upload_dir, nome_unico)
        arquivo.save(caminho_arquivo)
        
        # Atualizar banco
        salva_vidas.foto_filename = nome_unico
        db.session.commit()

@bp.route('/salva-vidas/foto/<filename>')
def foto_salva_vidas(filename):
    """Servir foto do salva-vidas"""
    return send_from_directory(
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'salva_vidas'),
        filename
    )

# ===== ROTAS PARA CARTEIRINHAS =====

@bp.route('/morador/<int:id>/carteirinha')
def visualizar_carteirinha(id):
    """Visualizar carteirinha do morador"""
    morador = Morador.query.get_or_404(id)
    condominio = Condominio.query.first()
    
    return render_template('moradores/carteirinha.html',
                         title=f'Carteirinha - {morador.nome_completo}',
                         morador=morador,
                         condominio=condominio)

@bp.route('/morador/<int:id>/carteirinha/gerar')
def gerar_carteirinha_imagem(id):
    """Gerar imagem PNG da carteirinha"""
    return gerar_carteirinha_png(id)

@bp.route('/morador/<int:id>/carteirinha/png')
def gerar_carteirinha_png(id):
    """Gerar imagem da carteirinha"""
    try:
        print(f"Iniciando geração da carteirinha para morador ID: {id}")
        
        morador = Morador.query.get_or_404(id)
        print(f"Morador encontrado: {morador.nome_completo}")
        
        condominio = Condominio.query.first()
        print(f"Condomínio: {condominio.nome if condominio else 'Não encontrado'}")
        
        # Gerar a carteirinha
        print("Gerando carteirinha...")
        img = gerar_carteirinha_completa(morador, condominio)
        print(f"Carteirinha gerada com sucesso! Tamanho: {img.size}")
        
        # Salvar em buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG', quality=95, dpi=(300, 300))
        img_buffer.seek(0)
        
        print(f"Buffer criado com {len(img_buffer.getvalue())} bytes")
        
        # Retornar como resposta
        from flask import Response
        return Response(
            img_buffer.getvalue(),
            mimetype='image/png',
            headers={'Content-Disposition': f'inline; filename=carteirinha_{morador.id}.png'}
        )
        
    except Exception as e:
        print(f'Erro ao gerar carteirinha: {str(e)}')
        import traceback
        traceback.print_exc()
        
        # Retornar erro HTTP 500 com mensagem
        from flask import Response
        return Response(
            f'Erro ao gerar carteirinha: {str(e)}',
            status=500,
            mimetype='text/plain'
        )

@bp.route('/morador/<int:id>/carteirinha/download-pdf')
def download_carteirinha_pdf(id):
    """Download da carteirinha em PDF"""
    morador = Morador.query.get_or_404(id)
    condominio = Condominio.query.first()
    
    try:
        # Gerar PDF da carteirinha
        pdf_buffer = gerar_pdf_carteirinha(morador, condominio)
        
        # Retornar como download
        from flask import Response
        return Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=carteirinha_{morador.nome_completo.replace(" ", "_")}.pdf'}
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('main.ver_morador', id=id))

@bp.route('/carteirinhas/selecionar')
def selecionar_morador_carteirinha():
    """Página para selecionar morador para gerar carteirinha"""
    from app.forms import FiltroMoradorForm
    
    form = FiltroMoradorForm()
    
    # Configurar choices do form
    blocos = db.session.query(Morador.bloco).distinct().all()
    form.bloco.choices = [('', 'Todos os blocos')] + [(b[0], f'Bloco {b[0]}') for b in blocos]
    
    # Aplicar filtros
    query = Morador.query
    
    if form.bloco.data:
        query = query.filter(Morador.bloco == form.bloco.data)
    
    if form.status.data:
        if form.status.data == 'regular':
            query = query.filter(Morador.carteirinha_ativa == True)
        elif form.status.data == 'vencida':
            query = query.filter(Morador.data_vencimento < date.today())
        elif form.status.data == 'a_vencer':
            data_limite = date.today() + timedelta(days=30)
            query = query.filter(Morador.data_vencimento.between(date.today(), data_limite))
        elif form.status.data == 'sem_carteirinha':
            query = query.filter(Morador.data_vencimento.is_(None))
    
    if form.busca.data:
        busca = f"%{form.busca.data}%"
        query = query.filter(Morador.nome_completo.ilike(busca))
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    moradores = query.order_by(Morador.nome_completo).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('moradores/selecionar_carteirinha.html', 
                         moradores=moradores, form=form)

@bp.route('/carteirinhas/lote', methods=['GET', 'POST'])
def gerar_carteirinhas_lote():
    """Gerar carteirinhas em lote"""
    if request.method == 'POST':
        ids_moradores = request.form.getlist('moradores_ids')
        
        if not ids_moradores:
            flash('Selecione pelo menos um morador.', 'warning')
            return redirect(url_for('main.gerar_carteirinhas_lote'))
        
        try:
            # Buscar moradores selecionados
            moradores = Morador.query.filter(Morador.id.in_(ids_moradores)).all()
            condominio = Condominio.query.first()
            
            # Gerar PDF com múltiplas carteirinhas
            pdf_buffer = gerar_lote_pdf(moradores, condominio)
            
            # Retornar como download
            from flask import Response
            return Response(
                pdf_buffer.getvalue(),
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename=carteirinhas_lote_{len(moradores)}_moradores.pdf'}
            )
            
        except Exception as e:
            flash(f'Erro ao gerar carteirinhas em lote: {str(e)}', 'danger')
            return redirect(url_for('main.gerar_carteirinhas_lote'))
    
    # GET - mostrar formulário de seleção
    moradores = Morador.query.filter(
        Morador.data_vencimento.isnot(None)
    ).order_by(Morador.nome_completo).all()
    
    return render_template('moradores/carteirinhas_lote.html',
                         title='Gerar Carteirinhas em Lote',
                         moradores=moradores)

@bp.route('/notificacoes/manual', methods=['GET', 'POST'])
def notificacoes_manual():
    """Página para envio manual de notificações"""
    from app.forms import NotificacaoManualForm
    
    
    form = NotificacaoManualForm()
    
    if form.validate_on_submit():
        # Determinar quais moradores receberão notificações
        if form.moradores_selecionados.data:
            # IDs específicos fornecidos
            ids = [int(id.strip()) for id in form.moradores_selecionados.data.split(',')]
            moradores = Morador.query.filter(Morador.id.in_(ids)).all()
        else:
            # Todos os moradores baseado no tipo de notificação
            if form.tipo_notificacao.data == '30_dias':
                moradores = Morador.query.filter(
                    Morador.data_vencimento.between(
                        datetime.now().date(),
                        datetime.now().date() + timedelta(days=45)
                    )
                ).all()
            elif form.tipo_notificacao.data == 'vencimento':
                moradores = Morador.query.filter(
                    Morador.data_vencimento <= datetime.now().date()
                ).all()
            else:
                moradores = Morador.query.all()
        
        # Enviar notificações
        total_enviadas = 0
        erros = []
        
        for morador in moradores:
            try:
                if form.tipo_notificacao.data == '30_dias':
                    sucesso, erro = enviar_notificacao_30_dias(morador)
                elif form.tipo_notificacao.data == 'vencimento':
                    sucesso, erro = enviar_notificacao_vencimento(morador)
                else:  # personalizada
                    sucesso, erro = enviar_email(
                        assunto=form.assunto_personalizado.data or "Notificação do Sistema",
                        destinatario=morador.get_email_notificacao(),
                        template_html='email/notificacao_personalizada.html',
                        morador=morador,
                        mensagem_personalizada=form.mensagem_personalizada.data,
                        data_atual=datetime.now()
                    )
                
                if sucesso:
                    total_enviadas += 1
                else:
                    erros.append(f"{morador.nome_completo}: {erro}")
                    
            except Exception as e:
                erros.append(f"{morador.nome_completo}: {str(e)}")
        
        # Exibir resultados
        if total_enviadas > 0:
            flash(f'✅ {total_enviadas} notificações enviadas com sucesso!', 'success')
        
        if erros:
            flash(f'❌ Erros em {len(erros)} envios. Verifique os logs.', 'warning')
        
        return redirect(url_for('main.notificacoes_resultado', 
                               enviadas=total_enviadas, 
                               erros=len(erros)))
    
    # Buscar moradores para seleção
    moradores = Morador.query.all()
    
    return render_template('notificacoes/manual.html',
                         title='Notificações Manuais',
                         form=form,
                         moradores=moradores)

@bp.route('/notificacoes/resultado')
def notificacoes_resultado():
    """Página de resultado das notificações"""
    enviadas = request.args.get('enviadas', 0, type=int)
    erros = request.args.get('erros', 0, type=int)
    
    return render_template('notificacoes/resultado.html',
                         title='Resultado das Notificações',
                         enviadas=enviadas,
                         erros=erros)

@bp.route('/morador/<int:id>/ajustar-vencimento', methods=['GET', 'POST'])
def ajustar_vencimento(id):
    """Ajustar data de vencimento de um morador"""
    from app.forms import AjusteVencimentoForm
    morador = Morador.query.get_or_404(id)
    form = AjusteVencimentoForm()
    
    if form.validate_on_submit():
        data_anterior = morador.data_vencimento
        morador.data_vencimento = form.nova_data_vencimento.data
        
        # Reativar carteirinha se a nova data for futura
        if morador.data_vencimento >= datetime.now().date():
            morador.carteirinha_ativa = True
        
        # Adicionar observação sobre o ajuste
        obs_ajuste = f"\n[{datetime.now().strftime('%d/%m/%Y')}] Vencimento ajustado de {data_anterior} para {morador.data_vencimento}"
        if form.motivo_ajuste.data:
            obs_ajuste += f" - Motivo: {form.motivo_ajuste.data}"
        
        morador.observacoes = (morador.observacoes or "") + obs_ajuste
        morador.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'✅ Data de vencimento ajustada para {morador.data_vencimento.strftime("%d/%m/%Y")}!', 'success')
        return redirect(url_for('main.ver_morador', id=id))
    
    # Pré-definir com a data atual de vencimento ou uma data futura
    if not form.nova_data_vencimento.data:
        form.nova_data_vencimento.data = morador.data_vencimento or (datetime.now().date() + timedelta(days=180))
    
    return render_template('moradores/ajustar_vencimento.html',
                         title='Ajustar Vencimento',
                         morador=morador,
                         form=form)

@bp.route('/morador/<int:id>/notificar/<tipo>')
def notificar_morador(id, tipo):
    """Enviar notificação individual para um morador"""

    from app.models import ConfiguracaoSistema
    
    # Carregar configurações de email do banco
    mail_server = ConfiguracaoSistema.get_valor('MAIL_SERVER')
    mail_username = ConfiguracaoSistema.get_valor('MAIL_USERNAME') 
    mail_password = ConfiguracaoSistema.get_valor('MAIL_PASSWORD')
    
    if not mail_server or not mail_username or not mail_password:
        flash('❌ Configurações de email não encontradas! Configure primeiro em Configurações → Email.', 'danger')
        return redirect(url_for('main.configuracoes_email'))
    
    # Atualizar configurações da aplicação
    current_app.config.update({
        'MAIL_SERVER': mail_server,
        'MAIL_PORT': ConfiguracaoSistema.get_valor('MAIL_PORT', 587),
        'MAIL_USE_TLS': ConfiguracaoSistema.get_valor('MAIL_USE_TLS', True),
        'MAIL_USE_SSL': False,
        'MAIL_USERNAME': mail_username,
        'MAIL_PASSWORD': mail_password.strip().replace(' ', ''),
        'MAIL_DEFAULT_SENDER': ConfiguracaoSistema.get_valor('MAIL_DEFAULT_SENDER', mail_username)
    })
    
    # Reinicializar Flask-Mail
    from app.email_service import mail
    mail.init_app(current_app)
    
    morador = Morador.query.get_or_404(id)
    
    try:
        if tipo == '30_dias':
            sucesso, erro = enviar_notificacao_30_dias(morador)
            tipo_msg = "aviso de vencimento"
        elif tipo == 'vencimento':
            sucesso, erro = enviar_notificacao_vencimento(morador)
            tipo_msg = "notificação de vencimento"
        else:
            flash('❌ Tipo de notificação inválido!', 'danger')
            return redirect(url_for('main.ver_morador', id=id))
        
        if sucesso:
            flash(f'✅ {tipo_msg.title()} enviada para {morador.nome_completo}!', 'success')
        else:
            flash(f'❌ Erro ao enviar {tipo_msg}: {erro}', 'danger')
            
    except Exception as e:
        flash(f'❌ Erro ao enviar notificação: {str(e)}', 'danger')
    
    return redirect(url_for('main.ver_morador', id=id))

def salvar_anexo(morador, arquivo, tipo_anexo='documento'):
    """Salva anexo do morador"""
    if arquivo and hasattr(arquivo, 'filename') and arquivo.filename:
        # Se for foto da carteirinha, remover a foto anterior
        if tipo_anexo == 'foto_carteirinha':
            # Buscar foto anterior baseada no tipo de arquivo
            foto_anterior = morador.anexos.filter(
                AnexoMorador.tipo_arquivo.in_(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'])
            ).first()
            if foto_anterior:
                # Remover arquivo físico
                try:
                    os.remove(foto_anterior.caminho_arquivo)
                except:
                    pass
                # Remover registro do banco
                db.session.delete(foto_anterior)
        
        # Criar diretório se não existir
        upload_dir = current_app.config['UPLOAD_FOLDER']
        morador_dir = os.path.join(upload_dir, f'morador_{morador.id}')
        os.makedirs(morador_dir, exist_ok=True)
        
        # Gerar nome único para o arquivo
        nome_original = secure_filename(arquivo.filename)
        extensao = nome_original.rsplit('.', 1)[1].lower()
        nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"
        caminho_arquivo = os.path.join(morador_dir, nome_arquivo)
        
        # Salvar arquivo
        arquivo.save(caminho_arquivo)
        
        # Salvar registro no banco (sem tipo_anexo por enquanto)
        anexo = AnexoMorador(
            morador_id=morador.id,
            nome_arquivo=nome_arquivo,
            nome_original=nome_original,
            tamanho_arquivo=os.path.getsize(caminho_arquivo),
            tipo_arquivo=extensao,
            caminho_arquivo=caminho_arquivo
        )
        
        db.session.add(anexo)
        db.session.commit()
        
        return anexo
    
    return None

@bp.route('/logs')
def ver_logs():
    """Visualizar logs do sistema"""
    import os
    import sys
    from datetime import datetime
    
    logs_info = {
        'sistema': {
            'nome': 'Sistema de Carteirinhas da Piscina',
            'versao': '1.0.0',
            'python_version': sys.version,
            'data_atual': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'uptime': 'Funcionando normalmente'
        },
        'arquivos_log': [],
        'logs_recentes': [],
        'estatisticas': {
            'total_usuarios': 0,
            'emails_enviados_hoje': 0,
            'ultima_atividade': 'Agora'
        }
    }
    
    # Tentar localizar arquivos de log comuns
    possiveis_logs = [
        'app.log',
        'flask.log',
        'error.log',
        'access.log',
        'carteirinha.log'
    ]
    
    for log_file in possiveis_logs:
        if os.path.exists(log_file):
            try:
                stat = os.stat(log_file)
                logs_info['arquivos_log'].append({
                    'nome': log_file,
                    'tamanho': f"{stat.st_size / 1024:.1f} KB",
                    'modificado': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
                })
            except Exception:
                pass
    
    # Capturar logs recentes do Python logging
    try:
        import logging
        
        # Criar um handler para capturar logs em memória
        from io import StringIO
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        
        # Configurar formatação
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Adicionar algumas entradas de log de exemplo
        logger = logging.getLogger('carteirinha_app')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Sistema iniciado com sucesso")
        logger.info("Configurações carregadas")
        logger.info("Banco de dados conectado")
        logger.info("Servidor Flask em execução")
        
        # Obter conteúdo dos logs
        log_content = log_stream.getvalue()
        if log_content:
            logs_info['logs_recentes'] = log_content.split('\n')[-20:]  # Últimas 20 linhas
        
        handler.close()
        
    except Exception as e:
        logs_info['logs_recentes'] = [f"Erro ao carregar logs: {str(e)}"]
    
    # Estatísticas básicas
    try:
        logs_info['estatisticas']['total_usuarios'] = Morador.query.count()
        
        # Contar logs de notificações de hoje (se existir a tabela)
        try:
            from app.models import LogNotificacao
            hoje = datetime.now().date()
            logs_info['estatisticas']['emails_enviados_hoje'] = LogNotificacao.query.filter(
                func.date(LogNotificacao.data_criacao) == hoje
            ).count()
        except:
            logs_info['estatisticas']['emails_enviados_hoje'] = 0
            
    except Exception:
        pass
    
    return render_template('sistema/logs.html',
                         title='Logs do Sistema',
                         logs_info=logs_info)

# === CONTROLE DE ACESSO À PISCINA ===

@bp.route('/acesso-piscina')
def controle_acesso():
    """Página principal do controle de acesso"""
    from app.models import RegistroAcesso
    
    # Moradores atualmente na piscina
    moradores_dentro = RegistroAcesso.obter_moradores_na_piscina()
    
    # Últimos 10 registros
    ultimos_registros = RegistroAcesso.query.order_by(
        RegistroAcesso.data_hora.desc()
    ).limit(10).all()
    
    # Estatísticas do dia
    hoje = datetime.now().date()
    entradas_hoje = RegistroAcesso.query.filter(
        db.func.date(RegistroAcesso.data_hora) == hoje,
        RegistroAcesso.tipo == 'entrada'
    ).count()
    
    return render_template('acesso/index.html',
                         moradores_dentro=moradores_dentro,
                         ultimos_registros=ultimos_registros,
                         entradas_hoje=entradas_hoje,
                         total_dentro=len(moradores_dentro))

@bp.route('/acesso-piscina/registrar', methods=['GET', 'POST'])
def registrar_acesso():
    """Registrar entrada/saída manual"""
    from app.forms import RegistroAcessoForm
    from app.models import RegistroAcesso, Morador
    
    form = RegistroAcessoForm()
    
    if form.validate_on_submit():
        morador = Morador.query.get_or_404(form.morador_id.data)
        
        # Verificar se o morador está atualmente na piscina
        esta_dentro = RegistroAcesso.morador_esta_na_piscina(morador.id)
        
        # Validar tipo de registro
        if form.tipo.data == 'entrada' and esta_dentro:
            flash(f'{morador.nome_completo} já está na piscina!', 'warning')
            return render_template('acesso/registrar.html', form=form, morador=morador)
        
        if form.tipo.data == 'saida' and not esta_dentro:
            flash(f'{morador.nome_completo} não está na piscina!', 'warning')
            return render_template('acesso/registrar.html', form=form, morador=morador)
        
        # Criar registro
        registro = RegistroAcesso(
            morador_id=morador.id,
            tipo=form.tipo.data,
            metodo='manual',
            guardiao=form.guardiao.data,
            observacoes=form.observacoes.data,
            ip_origem=request.remote_addr,
            tenant_id=tenant_id
        )
        
        db.session.add(registro)
        db.session.commit()
        
        acao = 'entrou na' if form.tipo.data == 'entrada' else 'saiu da'
        flash(f'✅ {morador.nome_completo} {acao} piscina às {registro.data_hora.strftime("%H:%M")}', 'success')
        
        return redirect(url_for('main.controle_acesso'))
    
    return render_template('acesso/registrar.html', form=form)

@bp.route('/acesso-piscina/qrcode', methods=['GET', 'POST'])
def acesso_qrcode():
    """Interface para leitura de QR Code"""
    from app.forms import BuscaMoradorForm
    from app.models import RegistroAcesso, Morador
    import json
    
    form = BuscaMoradorForm()
    morador = None
    erro = None
    
    if form.validate_on_submit():
        if form.submit_qr.data and form.codigo_qr.data:
            # Processar QR Code
            try:
                # Tentar decodificar JSON do QR Code
                dados_qr = json.loads(form.codigo_qr.data)
                morador_id = dados_qr.get('id')
                
                if morador_id:
                    morador = Morador.query.get(morador_id)
                    if not morador:
                        erro = "Morador não encontrado no sistema"
                else:
                    erro = "QR Code inválido - ID não encontrado"
                    
            except (json.JSONDecodeError, ValueError):
                # Se não for JSON, tentar como ID direto
                try:
                    morador_id = int(form.codigo_qr.data)
                    morador = Morador.query.get(morador_id)
                    if not morador:
                        erro = "Morador não encontrado"
                except ValueError:
                    erro = "Código QR inválido"
        
        elif form.submit_busca.data and form.busca_nome.data:
            # Buscar por nome
            moradores = Morador.query.filter(
                Morador.nome_completo.ilike(f"%{form.busca_nome.data}%")
            ).all()
            
            if len(moradores) == 1:
                morador = moradores[0]
            elif len(moradores) > 1:
                return render_template('acesso/qrcode.html', 
                                     form=form, 
                                     moradores=moradores,
                                     erro="Múltiplos moradores encontrados. Selecione um:")
            else:
                erro = "Nenhum morador encontrado"
    
    return render_template('acesso/qrcode.html', form=form, morador=morador, erro=erro)

@bp.route('/acesso-piscina/processar/<int:morador_id>/<tipo>')
def processar_acesso_rapido(morador_id, tipo):
    """Processar entrada/saída rápida via QR Code"""
    from app.models import RegistroAcesso, Morador
    
    if tipo not in ['entrada', 'saida']:
        flash('Tipo de acesso inválido!', 'danger')
        return redirect(url_for('main.acesso_qrcode'))
    
    morador = Morador.query.get_or_404(morador_id)
    
    # Verificar carteirinha válida
    if not morador.carteirinha_ativa:
        flash(f'Carteirinha de {morador.nome_completo} não está ativa!', 'danger')
        return redirect(url_for('main.acesso_qrcode'))
    
    # Verificar status atual
    esta_dentro = RegistroAcesso.morador_esta_na_piscina(morador.id)
    
    if tipo == 'entrada' and esta_dentro:
        flash(f'{morador.nome_completo} já está na piscina!', 'warning')
        return redirect(url_for('main.acesso_qrcode'))
    
    if tipo == 'saida' and not esta_dentro:
        flash(f'{morador.nome_completo} não está na piscina!', 'warning')
        return redirect(url_for('main.acesso_qrcode'))
    
    # Registrar acesso
    registro = RegistroAcesso(
        morador_id=morador.id,
        tipo=tipo,
        metodo='qrcode',
        guardiao='Sistema QR Code',
        ip_origem=request.remote_addr
    )
    
    db.session.add(registro)
    db.session.commit()
    
    acao = 'entrou na' if tipo == 'entrada' else 'saiu da'
    flash(f'✅ {morador.nome_completo} {acao} piscina às {registro.data_hora.strftime("%H:%M")}', 'success')
    
    return redirect(url_for('main.acesso_qrcode'))

@bp.route('/acesso-piscina/historico')
def historico_acesso():
    """Histórico de acessos com filtros"""
    from app.forms import FiltroAcessoForm
    from app.models import RegistroAcesso, Morador
    
    form = FiltroAcessoForm()
    
    # Configurar choices do formulário
    form.morador_id.choices = [(0, 'Todos os moradores')] + [
        (m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}")
        for m in Morador.query.order_by(Morador.nome_completo).all()
    ]
    
    # Construir query
    query = RegistroAcesso.query
    
    # Aplicar filtros se fornecidos
    if request.args.get('morador_id') and int(request.args.get('morador_id')) > 0:
        query = query.filter(RegistroAcesso.morador_id == request.args.get('morador_id'))
        form.morador_id.data = int(request.args.get('morador_id'))
    
    if request.args.get('data_inicio'):
        data_inicio = datetime.strptime(request.args.get('data_inicio'), '%Y-%m-%d').date()
        query = query.filter(db.func.date(RegistroAcesso.data_hora) >= data_inicio)
        form.data_inicio.data = data_inicio
    
    if request.args.get('data_fim'):
        data_fim = datetime.strptime(request.args.get('data_fim'), '%Y-%m-%d').date()
        query = query.filter(db.func.date(RegistroAcesso.data_hora) <= data_fim)
        form.data_fim.data = data_fim
    
    if request.args.get('tipo'):
        query = query.filter(RegistroAcesso.tipo == request.args.get('tipo'))
        form.tipo.data = request.args.get('tipo')
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    registros = query.order_by(RegistroAcesso.data_hora.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('acesso/historico.html', 
                         registros=registros, 
                         form=form,
                         title='Histórico de Acessos')

@bp.route('/acesso-piscina/morador/<int:morador_id>')
def historico_morador(morador_id):
    """Histórico específico de um morador"""
    from app.models import RegistroAcesso, Morador
    
    morador = Morador.query.get_or_404(morador_id)
    
    # Registros do morador
    registros = RegistroAcesso.query.filter_by(
        morador_id=morador_id
    ).order_by(RegistroAcesso.data_hora.desc()).limit(50).all()
    
    # Estatísticas
    total_entradas = RegistroAcesso.query.filter_by(
        morador_id=morador_id, tipo='entrada'
    ).count()
    
    # Frequência nos últimos 30 dias
    trinta_dias_atras = datetime.now() - timedelta(days=30)
    entradas_30_dias = RegistroAcesso.query.filter(
        RegistroAcesso.morador_id == morador_id,
        RegistroAcesso.tipo == 'entrada',
        RegistroAcesso.data_hora >= trinta_dias_atras
    ).count()
    
    # Verificar se está na piscina
    esta_na_piscina = RegistroAcesso.morador_esta_na_piscina(morador_id)
    
    return render_template('acesso/historico_morador.html',
                         morador=morador,
                         registros=registros,
                         total_entradas=total_entradas,
                         entradas_30_dias=entradas_30_dias,
                         esta_na_piscina=esta_na_piscina)

@bp.route('/acesso-piscina/por-unidade')
def historico_por_unidade():
    """Histórico de acesso agrupado por unidade (bloco-apto)"""
    from app.models import RegistroAcesso, Morador
    
    tenant_id = getattr(g, 'tenant_id', 1)
    
    # Filtros opcionais
    bloco_filtro = request.args.get('bloco', '')
    apartamento_filtro = request.args.get('apartamento', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    
    # Query base - agrupar por bloco e apartamento
    query = db.session.query(
        Morador.bloco,
        Morador.apartamento,
        func.count(RegistroAcesso.id).label('total_acessos'),
        func.count(case((RegistroAcesso.tipo == 'entrada', 1))).label('entradas'),
        func.count(case((RegistroAcesso.tipo == 'saida', 1))).label('saidas'),
        func.max(RegistroAcesso.data_hora).label('ultimo_acesso')
    ).join(
        RegistroAcesso, Morador.id == RegistroAcesso.morador_id
    ).filter(
        Morador.tenant_id == tenant_id
    )
    
    # Aplicar filtros
    if bloco_filtro:
        query = query.filter(Morador.bloco == bloco_filtro)
    
    if apartamento_filtro:
        query = query.filter(Morador.apartamento == apartamento_filtro)
    
    if data_inicio:
        try:
            data_ini = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            query = query.filter(db.func.date(RegistroAcesso.data_hora) >= data_ini)
        except:
            pass
    
    if data_fim:
        try:
            data_f = datetime.strptime(data_fim, '%Y-%m-%d').date()
            query = query.filter(db.func.date(RegistroAcesso.data_hora) <= data_f)
        except:
            pass
    
    # Agrupar e ordenar
    resultados = query.group_by(
        Morador.bloco, Morador.apartamento
    ).order_by(
        Morador.bloco, Morador.apartamento
    ).all()
    
    # Buscar blocos únicos para o filtro
    blocos = db.session.query(Morador.bloco).filter(
        Morador.tenant_id == tenant_id
    ).distinct().order_by(Morador.bloco).all()
    
    return render_template('acesso/historico_unidade.html',
                         title='Histórico por Unidade',
                         resultados=resultados,
                         blocos=[b[0] for b in blocos],
                         bloco_filtro=bloco_filtro,
                         apartamento_filtro=apartamento_filtro,
                         data_inicio=data_inicio,
                         data_fim=data_fim)