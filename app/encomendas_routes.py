"""Rotas para módulo de Portal de Encomendas"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app, g
from flask_login import login_required, current_user
from app import db
from app.models import Encomenda, Morador
from app.forms import EncomendaForm, FiltroEncomendaForm
from datetime import datetime, timedelta
from app.email_service import enviar_email
from app.whatsapp_service import send_whatsapp_message
from sqlalchemy import or_

encomendas_bp = Blueprint('encomendas', __name__, url_prefix='/encomendas')

@encomendas_bp.route('/')
@login_required
def listar_encomendas():
    """Lista todas as encomendas"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = FiltroEncomendaForm(request.args)
    
    # Query base
    query = Encomenda.query.filter_by(tenant_id=tenant_id)
    
    # Aplicar filtros
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    if form.morador_id.data:
        query = query.filter_by(morador_id=form.morador_id.data)
    
    if form.transportadora.data:
        query = query.filter(Encomenda.transportadora.contains(form.transportadora.data))
    
    if form.busca.data:
        query = query.filter(
            or_(
                Encomenda.numero.contains(form.busca.data),
                Encomenda.codigo_rastreamento.contains(form.busca.data),
                Encomenda.descricao.contains(form.busca.data)
            )
        )
    
    # Configurar choices do formulário
    moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
    form.morador_id.choices = [('', 'Todos')] + [(m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}") for m in moradores]
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    encomendas = query.order_by(Encomenda.data_cadastro.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas
    aguardando = Encomenda.query.filter_by(tenant_id=tenant_id, status='aguardando').count()
    recebidas = Encomenda.query.filter_by(tenant_id=tenant_id, status='recebida').count()
    retiradas = Encomenda.query.filter_by(tenant_id=tenant_id, status='retirada').count()
    
    stats = {
        'total': encomendas.total,
        'aguardando': aguardando,
        'recebidas': recebidas,
        'retiradas': retiradas
    }
    
    return render_template('encomendas/listar.html',
                         title='Portal de Encomendas',
                         encomendas=encomendas,
                         form=form,
                         stats=stats)


@encomendas_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def nova_encomenda():
    """Registrar nova encomenda"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = EncomendaForm()
    
    # Configurar choices
    moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
    form.morador_id.choices = [(m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}") for m in moradores]
    
    if form.validate_on_submit():
        encomenda = Encomenda(
            tenant_id=tenant_id,
            morador_id=form.morador_id.data,
            transportadora=form.transportadora.data,
            codigo_rastreamento=form.codigo_rastreamento.data,
            descricao=form.descricao.data,
            quantidade_pacotes=form.quantidade_pacotes.data or 1,
            local_armazenamento=form.local_armazenamento.data,
            observacoes=form.observacoes.data,
            status='aguardando'
        )
        
        encomenda.numero = encomenda.gerar_numero()
        
        db.session.add(encomenda)
        db.session.commit()
        
        flash(f'Encomenda {encomenda.numero} registrada com sucesso!', 'success')
        return redirect(url_for('encomendas.listar_encomendas'))
    
    return render_template('encomendas/form.html',
                         title='Registrar Encomenda',
                         form=form)


@encomendas_bp.route('/<int:id>')
@login_required
def ver_encomenda(id):
    """Ver detalhes da encomenda"""
    tenant_id = getattr(g, 'tenant_id', 1)
    encomenda = Encomenda.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    return render_template('encomendas/detalhes.html',
                         title=f'Encomenda {encomenda.numero}',
                         encomenda=encomenda)


@encomendas_bp.route('/<int:id>/marcar-recebida', methods=['POST'])
@login_required
def marcar_recebida(id):
    """Marcar encomenda como recebida"""
    tenant_id = getattr(g, 'tenant_id', 1)
    encomenda = Encomenda.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    if encomenda.status != 'aguardando':
        flash('Encomenda já foi processada!', 'warning')
        return redirect(url_for('encomendas.ver_encomenda', id=id))
    
    encomenda.status = 'recebida'
    encomenda.data_recebimento = datetime.utcnow()
    encomenda.data_atualizacao = datetime.utcnow()
    
    # Notificações ao morador: Email + WhatsApp (stub)
    try:
        morador = encomenda.morador
        email = morador.get_email_notificacao()
        if email:
            enviar_email(
                assunto=f'Encomenda Recebida - {encomenda.numero}',
                destinatario=email,
                template_html='email/encomenda_recebida.html',
                morador=morador,
                encomenda=encomenda,
                data_atual=datetime.now()
            )
            encomenda.notificacao_enviada = True
            encomenda.data_notificacao = datetime.utcnow()
        if morador.celular:
            msg = (
                f"Olá, {morador.nome_completo}. Chegou uma encomenda para você.\n"
                f"Número: {encomenda.numero} | Local: {encomenda.local_armazenamento or 'Portaria'}\n"
                f"Favor retirar apresentando documento."
            )
            send_whatsapp_message(morador.celular, msg)
    except Exception as e:
        print(f"Erro ao notificar: {e}")
    
    db.session.commit()
    
    flash(f'Encomenda {encomenda.numero} marcada como recebida e notificações enviadas!', 'success')
    return redirect(url_for('encomendas.listar_encomendas'))


@encomendas_bp.route('/<int:id>/registrar-retirada', methods=['GET', 'POST'])
@login_required
def registrar_retirada(id):
    """Registrar retirada da encomenda"""
    tenant_id = getattr(g, 'tenant_id', 1)
    encomenda = Encomenda.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        retirado_por = request.form.get('retirado_por', '')
        documento_retirada = request.form.get('documento_retirada', '')
        
        if not retirado_por:
            flash('Nome de quem retirou é obrigatório!', 'danger')
            return render_template('encomendas/retirada.html', encomenda=encomenda)
        
        encomenda.status = 'retirada'
        encomenda.data_retirada = datetime.utcnow()
        encomenda.retirado_por = retirado_por
        encomenda.documento_retirada = documento_retirada
        encomenda.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Retirada da encomenda {encomenda.numero} registrada com sucesso!', 'success')
        return redirect(url_for('encomendas.listar_encomendas'))
    
    return render_template('encomendas/retirada.html',
                         title=f'Registrar Retirada - {encomenda.numero}',
                         encomenda=encomenda)


@encomendas_bp.route('/minhas-encomendas')
@login_required
def minhas_encomendas():
    """Lista encomendas do morador logado"""
    tenant_id = getattr(g, 'tenant_id', 1)
    
    query = Encomenda.query.filter_by(tenant_id=tenant_id)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    encomendas = query.order_by(Encomenda.data_cadastro.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('encomendas/minhas.html',
                         title='Minhas Encomendas',
                         encomendas=encomendas)

