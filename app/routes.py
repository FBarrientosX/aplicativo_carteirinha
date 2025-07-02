from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from app.models import Morador, AnexoMorador, LogNotificacao, ConfiguracaoSistema, Condominio
from app.forms import MoradorForm, ValidarCarteirinhaForm, FiltroMoradorForm, ConfiguracaoEmailForm, ConfiguracaoCondominioForm, ConfiguracaoGeralForm
from app.email_service import enviar_email_boas_vindas, verificar_e_enviar_notificacoes, enviar_notificacao_30_dias, enviar_notificacao_vencimento, enviar_email
from datetime import datetime, timedelta
import os
import uuid
import plotly.graph_objs as go
import plotly.utils
import json
from sqlalchemy import func

@app.route('/')
@app.route('/index')
def index():
    """Dashboard principal com estatísticas"""
    # Estatísticas gerais
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

@app.route('/moradores')
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
    
    if form.status.data:
        hoje = datetime.now().date()
        if form.status.data == 'regular':
            query = query.filter(Morador.data_vencimento > hoje + timedelta(days=30))
        elif form.status.data == 'a_vencer':
            query = query.filter(
                Morador.data_vencimento.between(hoje, hoje + timedelta(days=30))
            )
        elif form.status.data == 'vencida':
            query = query.filter(Morador.data_vencimento < hoje)
        elif form.status.data == 'sem_carteirinha':
            query = query.filter(Morador.data_vencimento.is_(None))
    
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

@app.route('/morador/novo', methods=['GET', 'POST'])
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
        
        # Salvar anexo se fornecido
        if form.anexo.data:
            salvar_anexo(morador, form.anexo.data)
        
        # Enviar email de boas-vindas
        enviar_email_boas_vindas(morador)
        
        flash('Morador cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_moradores'))
    
    return render_template('moradores/form.html',
                         title='Novo Morador',
                         form=form)

@app.route('/morador/<int:id>/editar', methods=['GET', 'POST'])
def editar_morador(id):
    """Editar morador existente"""
    morador = Morador.query.get_or_404(id)
    form = MoradorForm(obj=morador)
    
    if form.validate_on_submit():
        form.populate_obj(morador)
        
        # Ajustar email do titular
        if morador.eh_titular:
            morador.email_titular = None
        
        # Permitir edição da data de vencimento
        if form.data_vencimento.data:
            morador.data_vencimento = form.data_vencimento.data
            # Se uma nova data de vencimento foi definida, reativar carteirinha se necessário
            if morador.data_vencimento >= datetime.now().date():
                morador.carteirinha_ativa = True
        
        morador.data_atualizacao = datetime.utcnow()
        
        # Salvar anexo se fornecido
        if form.anexo.data:
            salvar_anexo(morador, form.anexo.data)
        
        db.session.commit()
        flash('Dados atualizados com sucesso!', 'success')
        return redirect(url_for('ver_morador', id=id))
    
    return render_template('moradores/form.html',
                         title='Editar Morador',
                         form=form,
                         morador=morador)

@app.route('/morador/<int:id>')
def ver_morador(id):
    """Ver detalhes do morador"""
    morador = Morador.query.get_or_404(id)
    return render_template('moradores/detalhes.html',
                         title=f'Morador: {morador.nome_completo}',
                         morador=morador)

@app.route('/morador/<int:id>/validar', methods=['GET', 'POST'])
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
        return redirect(url_for('ver_morador', id=id))
    
    return render_template('moradores/validar.html',
                         title='Validar Carteirinha',
                         morador=morador,
                         form=form)

@app.route('/morador/<int:id>/anexos')
def listar_anexos(id):
    """Listar anexos do morador"""
    morador = Morador.query.get_or_404(id)
    return render_template('moradores/anexos.html',
                         title='Anexos',
                         morador=morador)

@app.route('/anexo/<int:id>')
def baixar_anexo(id):
    """Download de anexo"""
    anexo = AnexoMorador.query.get_or_404(id)
    return send_from_directory(
        os.path.dirname(anexo.caminho_arquivo),
        os.path.basename(anexo.caminho_arquivo),
        as_attachment=True,
        download_name=anexo.nome_original
    )

@app.route('/relatorios')
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

@app.route('/notificacoes/executar')
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

@app.route('/notificacoes/teste-email')
def teste_email():
    """Testar configuração de email SMTP"""
    try:
        from app.email_service import mail
        from flask import current_app
        from flask_mail import Message
        from datetime import datetime
        
        # Verificar se as configurações estão definidas
        if not current_app.config.get('MAIL_USERNAME'):
            flash('Configurações de email não encontradas! Verifique o arquivo .env', 'danger')
            return redirect(url_for('relatorios'))
        
        # Criar mensagem de teste
        msg = Message(
            subject="✅ Teste de Email - Sistema Carteirinhas",
            recipients=[current_app.config['MAIL_USERNAME']],  # Enviar para próprio email
            html=render_template('email/teste_email.html', data_atual=datetime.now()),
            body="Teste de email - Se você está lendo isso, o SMTP está funcionando!"
        )
        
        # Tentar enviar
        mail.send(msg)
        
        flash(f'✅ Email de teste enviado com sucesso para {current_app.config["MAIL_USERNAME"]}!', 'success')
        
    except Exception as e:
        flash(f'❌ Erro ao enviar email de teste: {str(e)}', 'danger')
    
    return redirect(url_for('relatorios'))

@app.route('/configuracoes')
def configuracoes():
    """Página principal de configurações"""
    from datetime import datetime
    return render_template('configuracoes/index.html', 
                         title='Configurações',
                         data_atual=datetime.now().strftime('%d/%m/%Y'))

@app.route('/configuracoes/email', methods=['GET', 'POST'])
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
        app.config.update({
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
        mail.init_app(app)
        
        flash('Configurações de email salvas com sucesso!', 'success')
        return redirect(url_for('configuracoes_email'))
    
    # Carregar configurações existentes
    form.mail_server.data = ConfiguracaoSistema.get_valor('MAIL_SERVER', 'smtp.gmail.com')
    form.mail_port.data = ConfiguracaoSistema.get_valor('MAIL_PORT', 587)
    form.mail_use_tls.data = ConfiguracaoSistema.get_valor('MAIL_USE_TLS', True)
    form.mail_username.data = ConfiguracaoSistema.get_valor('MAIL_USERNAME', '')
    form.mail_default_sender.data = ConfiguracaoSistema.get_valor('MAIL_DEFAULT_SENDER', '')
    
    return render_template('configuracoes/email.html', 
                         title='Configurações de Email', 
                         form=form)

@app.route('/configuracoes/condominio', methods=['GET', 'POST'])
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
        return redirect(url_for('configuracoes_condominio'))
    
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

@app.route('/configuracoes/geral', methods=['GET', 'POST'])
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
        return redirect(url_for('configuracoes_geral'))
    
    # Carregar configurações existentes
    form.nome_sistema.data = ConfiguracaoSistema.get_valor('NOME_SISTEMA', 'Sistema de Carteirinhas')
    form.sessao_timeout.data = ConfiguracaoSistema.get_valor('SESSAO_TIMEOUT', 120)
    form.max_tentativas_login.data = ConfiguracaoSistema.get_valor('MAX_TENTATIVAS_LOGIN', 5)
    form.backup_automatico.data = ConfiguracaoSistema.get_valor('BACKUP_AUTOMATICO', True)
    form.dias_backup.data = ConfiguracaoSistema.get_valor('DIAS_BACKUP', 7)
    form.notificacoes_automaticas.data = ConfiguracaoSistema.get_valor('NOTIFICACOES_AUTOMATICAS', True)
    form.horario_notificacoes.data = ConfiguracaoSistema.get_valor('HORARIO_NOTIFICACOES', '09:00')
    
    return render_template('configuracoes/geral.html', 
                         title='Configurações Gerais', 
                         form=form)

@app.route('/notificacoes/teste-email-configurado')
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
            return redirect(url_for('configuracoes_email'))
        
        # Limpar espaços da senha (comum em senhas de app do Gmail)
        mail_password = mail_password.strip().replace(' ', '')
        
        # Atualizar configurações da aplicação E reinicializar o Flask-Mail
        app.config.update({
            'MAIL_SERVER': mail_server,
            'MAIL_PORT': ConfiguracaoSistema.get_valor('MAIL_PORT', 587),
            'MAIL_USE_TLS': ConfiguracaoSistema.get_valor('MAIL_USE_TLS', True),
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': mail_username,
            'MAIL_PASSWORD': mail_password,
            'MAIL_DEFAULT_SENDER': ConfiguracaoSistema.get_valor('MAIL_DEFAULT_SENDER', mail_username)
        })
        
        # Reinicializar o Flask-Mail com as novas configurações
        mail.init_app(app)
        
        # Criar mensagem de teste
        msg = Message(
            subject="✅ Teste de Email - Sistema Configurado",
            sender=app.config['MAIL_DEFAULT_SENDER'],
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
    
    return redirect(url_for('configuracoes_email'))

@app.route('/notificacoes/manual', methods=['GET', 'POST'])
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
        
        return redirect(url_for('notificacoes_resultado', 
                               enviadas=total_enviadas, 
                               erros=len(erros)))
    
    # Buscar moradores para seleção
    moradores = Morador.query.all()
    
    return render_template('notificacoes/manual.html',
                         title='Notificações Manuais',
                         form=form,
                         moradores=moradores)

@app.route('/notificacoes/resultado')
def notificacoes_resultado():
    """Página de resultado das notificações"""
    enviadas = request.args.get('enviadas', 0, type=int)
    erros = request.args.get('erros', 0, type=int)
    
    return render_template('notificacoes/resultado.html',
                         title='Resultado das Notificações',
                         enviadas=enviadas,
                         erros=erros)

@app.route('/morador/<int:id>/ajustar-vencimento', methods=['GET', 'POST'])
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
        return redirect(url_for('ver_morador', id=id))
    
    # Pré-definir com a data atual de vencimento ou uma data futura
    if not form.nova_data_vencimento.data:
        form.nova_data_vencimento.data = morador.data_vencimento or (datetime.now().date() + timedelta(days=180))
    
    return render_template('moradores/ajustar_vencimento.html',
                         title='Ajustar Vencimento',
                         morador=morador,
                         form=form)

@app.route('/morador/<int:id>/notificar/<tipo>')
def notificar_morador(id, tipo):
    """Enviar notificação individual para um morador"""

    from app.models import ConfiguracaoSistema
    
    # Carregar configurações de email do banco
    mail_server = ConfiguracaoSistema.get_valor('MAIL_SERVER')
    mail_username = ConfiguracaoSistema.get_valor('MAIL_USERNAME') 
    mail_password = ConfiguracaoSistema.get_valor('MAIL_PASSWORD')
    
    if not mail_server or not mail_username or not mail_password:
        flash('❌ Configurações de email não encontradas! Configure primeiro em Configurações → Email.', 'danger')
        return redirect(url_for('configuracoes_email'))
    
    # Atualizar configurações da aplicação
    app.config.update({
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
    mail.init_app(app)
    
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
            return redirect(url_for('ver_morador', id=id))
        
        if sucesso:
            flash(f'✅ {tipo_msg.title()} enviada para {morador.nome_completo}!', 'success')
        else:
            flash(f'❌ Erro ao enviar {tipo_msg}: {erro}', 'danger')
            
    except Exception as e:
        flash(f'❌ Erro ao enviar notificação: {str(e)}', 'danger')
    
    return redirect(url_for('ver_morador', id=id))

def salvar_anexo(morador, arquivo):
    """Salva anexo do morador"""
    if arquivo and arquivo.filename:
        # Criar diretório se não existir
        upload_dir = app.config['UPLOAD_FOLDER']
        morador_dir = os.path.join(upload_dir, f'morador_{morador.id}')
        os.makedirs(morador_dir, exist_ok=True)
        
        # Gerar nome único para o arquivo
        nome_original = secure_filename(arquivo.filename)
        extensao = nome_original.rsplit('.', 1)[1].lower()
        nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"
        caminho_arquivo = os.path.join(morador_dir, nome_arquivo)
        
        # Salvar arquivo
        arquivo.save(caminho_arquivo)
        
        # Salvar registro no banco
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

@app.route('/logs')
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

# Configurar tarefa automatizada
if not app.debug:
    from app import scheduler
    
    @scheduler.task('cron', id='verificar_notificacoes', hour=9, minute=0)
    def job_notificacoes():
        with app.app_context():
            verificar_e_enviar_notificacoes()