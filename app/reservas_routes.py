"""Rotas para módulo de Reserva de Espaços Comuns"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app, g
from flask_login import login_required, current_user
from app import db
from app.models import EspacoComum, ReservaEspaco, Morador, Usuario
from app.forms import EspacoComumForm, ReservaEspacoForm, FiltroReservaForm
from datetime import datetime, timedelta, time, date
from sqlalchemy import and_, or_

reservas_bp = Blueprint('reservas', __name__, url_prefix='/reservas')

@reservas_bp.route('/')
@login_required
def listar_espacos():
    """Lista todos os espaços comuns disponíveis"""
    tenant_id = getattr(g, 'tenant_id', 1)
    
    espacos = EspacoComum.query.filter_by(tenant_id=tenant_id, ativo=True).all()
    
    # Estatísticas
    total_espacos = len(espacos)
    reservas_hoje = ReservaEspaco.query.filter_by(
        tenant_id=tenant_id,
        data_reserva=date.today()
    ).count()
    reservas_pendentes = ReservaEspaco.query.filter_by(
        tenant_id=tenant_id,
        status='pendente'
    ).count()
    
    stats = {
        'total_espacos': total_espacos,
        'reservas_hoje': reservas_hoje,
        'reservas_pendentes': reservas_pendentes
    }
    
    return render_template('reservas/espacos.html',
                         title='Espaços Comuns',
                         espacos=espacos,
                         stats=stats)


@reservas_bp.route('/espaco/novo', methods=['GET', 'POST'])
@login_required
def novo_espaco():
    """Cadastrar novo espaço comum"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = EspacoComumForm()
    
    if form.validate_on_submit():
        espaco = EspacoComum(
            tenant_id=tenant_id,
            nome=form.nome.data,
            descricao=form.descricao.data,
            capacidade_maxima=form.capacidade_maxima.data,
            area_metros=form.area_metros.data,
            tempo_antecipacao_horas=form.tempo_antecipacao_horas.data or 24,
            tempo_maximo_horas=form.tempo_maximo_horas.data or 4,
            valor_taxa=form.valor_taxa.data or 0,
            requer_aprovacao=form.requer_aprovacao.data,
            horario_inicio=form.horario_inicio.data,
            horario_fim=form.horario_fim.data,
            equipamentos=form.equipamentos.data,
            ativo=form.ativo.data
        )
        
        db.session.add(espaco)
        db.session.commit()
        
        flash('Espaço comum cadastrado com sucesso!', 'success')
        return redirect(url_for('reservas.listar_espacos'))
    
    return render_template('reservas/espaco_form.html',
                         title='Novo Espaço Comum',
                         form=form)


@reservas_bp.route('/espaco/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_espaco(id):
    """Editar espaço comum"""
    tenant_id = getattr(g, 'tenant_id', 1)
    espaco = EspacoComum.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    form = EspacoComumForm(obj=espaco)
    
    if form.validate_on_submit():
        espaco.nome = form.nome.data
        espaco.descricao = form.descricao.data
        espaco.capacidade_maxima = form.capacidade_maxima.data
        espaco.area_metros = form.area_metros.data
        espaco.tempo_antecipacao_horas = form.tempo_antecipacao_horas.data or 24
        espaco.tempo_maximo_horas = form.tempo_maximo_horas.data or 4
        espaco.valor_taxa = form.valor_taxa.data or 0
        espaco.requer_aprovacao = form.requer_aprovacao.data
        espaco.horario_inicio = form.horario_inicio.data
        espaco.horario_fim = form.horario_fim.data
        espaco.equipamentos = form.equipamentos.data
        espaco.ativo = form.ativo.data
        espaco.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        flash('Espaço comum atualizado com sucesso!', 'success')
        return redirect(url_for('reservas.ver_espaco', id=id))
    
    return render_template('reservas/espaco_form.html',
                         title='Editar Espaço Comum',
                         form=form,
                         espaco=espaco)


@reservas_bp.route('/espaco/<int:id>')
@login_required
def ver_espaco(id):
    """Ver detalhes do espaço comum"""
    tenant_id = getattr(g, 'tenant_id', 1)
    espaco = EspacoComum.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    # Próximas reservas
    proximas_reservas = ReservaEspaco.query.filter_by(
        espaco_id=id,
        tenant_id=tenant_id
    ).filter(
        or_(
            ReservaEspaco.data_reserva > date.today(),
            and_(
                ReservaEspaco.data_reserva == date.today(),
                ReservaEspaco.hora_inicio >= datetime.now().time()
            )
        )
    ).order_by(ReservaEspaco.data_reserva, ReservaEspaco.hora_inicio).limit(10).all()
    
    # Reservas hoje
    reservas_hoje = ReservaEspaco.query.filter_by(
        espaco_id=id,
        tenant_id=tenant_id,
        data_reserva=date.today()
    ).order_by(ReservaEspaco.hora_inicio).all()
    
    return render_template('reservas/espaco_detalhes.html',
                         title=f'Espaço: {espaco.nome}',
                         espaco=espaco,
                         proximas_reservas=proximas_reservas,
                         reservas_hoje=reservas_hoje)


@reservas_bp.route('/solicitar', methods=['GET', 'POST'])
@login_required
def solicitar_reserva():
    """Solicitar reserva de espaço"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = ReservaEspacoForm()
    
    # Configurar choices
    espacos = EspacoComum.query.filter_by(tenant_id=tenant_id, ativo=True).all()
    form.espaco_id.choices = [(e.id, e.nome) for e in espacos]
    
    moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
    form.morador_id.choices = [(m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}") for m in moradores]
    
    if form.validate_on_submit():
        espaco = EspacoComum.query.filter_by(id=form.espaco_id.data, tenant_id=tenant_id).first_or_404()
        
        # Verificar conflitos de horário
        conflito = ReservaEspaco.query.filter_by(
            tenant_id=tenant_id,
            espaco_id=espaco.id,
            data_reserva=form.data_reserva.data
        ).filter(
            or_(
                and_(
                    ReservaEspaco.hora_inicio <= form.hora_inicio.data,
                    ReservaEspaco.hora_fim > form.hora_inicio.data
                ),
                and_(
                    ReservaEspaco.hora_inicio < form.hora_fim.data,
                    ReservaEspaco.hora_fim >= form.hora_fim.data
                ),
                and_(
                    ReservaEspaco.hora_inicio >= form.hora_inicio.data,
                    ReservaEspaco.hora_fim <= form.hora_fim.data
                )
            )
        ).filter(ReservaEspaco.status.in_(['pendente', 'aprovado'])).first()
        
        if conflito:
            flash(f'Conflito de horário! Já existe uma reserva das {conflito.hora_inicio.strftime("%H:%M")} às {conflito.hora_fim.strftime("%H:%M")}', 'danger')
            return render_template('reservas/solicitar.html', form=form, espaco=espaco)
        
        # Criar reserva
        reserva = ReservaEspaco(
            tenant_id=tenant_id,
            espaco_id=espaco.id,
            morador_id=form.morador_id.data,
            data_reserva=form.data_reserva.data,
            hora_inicio=form.hora_inicio.data,
            hora_fim=form.hora_fim.data,
            quantidade_pessoas=form.quantidade_pessoas.data or 1,
            finalidade=form.finalidade.data,
            observacoes=form.observacoes.data,
            status='pendente' if espaco.requer_aprovacao else 'aprovado'
        )
        
        reserva.numero = reserva.gerar_numero()
        
        if not espaco.requer_aprovacao:
            reserva.aprovado_por = current_user.id
            reserva.data_aprovacao = datetime.utcnow()
        
        db.session.add(reserva)
        db.session.commit()
        
        status_msg = 'aprovada' if not espaco.requer_aprovacao else 'solicitada e aguardando aprovação'
        flash(f'Reserva {status_msg} com sucesso! Número: {reserva.numero}', 'success')
        return redirect(url_for('reservas.minhas_reservas'))
    
    return render_template('reservas/solicitar.html',
                         title='Solicitar Reserva',
                         form=form)


@reservas_bp.route('/minhas-reservas')
@login_required
def minhas_reservas():
    """Lista reservas do morador logado"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = FiltroReservaForm(request.args)
    
    # Query base
    query = ReservaEspaco.query.filter_by(tenant_id=tenant_id)
    
    # Se for morador, filtrar por morador
    # Se for admin, mostrar todas
    if not current_user.is_admin():
        # Assumindo que há um relacionamento entre Usuario e Morador
        # Por enquanto, mostrar todas (será ajustado conforme necessário)
        pass
    
    # Aplicar filtros
    if form.espaco_id.data:
        query = query.filter_by(espaco_id=form.espaco_id.data)
    
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    if form.data_inicio.data:
        query = query.filter(ReservaEspaco.data_reserva >= form.data_inicio.data)
    
    if form.data_fim.data:
        query = query.filter(ReservaEspaco.data_reserva <= form.data_fim.data)
    
    # Configurar choices do formulário
    espacos = EspacoComum.query.filter_by(tenant_id=tenant_id, ativo=True).all()
    form.espaco_id.choices = [('', 'Todos')] + [(e.id, e.nome) for e in espacos]
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    reservas = query.order_by(ReservaEspaco.data_reserva.desc(), ReservaEspaco.hora_inicio.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('reservas/listar.html',
                         title='Minhas Reservas',
                         reservas=reservas,
                         form=form)


@reservas_bp.route('/reserva/<int:id>/aprovar', methods=['POST'])
@login_required
def aprovar_reserva(id):
    """Aprovar reserva"""
    tenant_id = getattr(g, 'tenant_id', 1)
    reserva = ReservaEspaco.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    if reserva.status != 'pendente':
        flash('Apenas reservas pendentes podem ser aprovadas!', 'warning')
        return redirect(url_for('reservas.ver_reserva', id=id))
    
    reserva.status = 'aprovado'
    reserva.aprovado_por = current_user.id
    reserva.data_aprovacao = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Reserva {reserva.numero} aprovada com sucesso!', 'success')
    return redirect(url_for('reservas.ver_reserva', id=id))


@reservas_bp.route('/reserva/<int:id>/recusar', methods=['POST'])
@login_required
def recusar_reserva(id):
    """Recusar reserva"""
    tenant_id = getattr(g, 'tenant_id', 1)
    reserva = ReservaEspaco.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    motivo = request.form.get('motivo', '')
    
    if reserva.status != 'pendente':
        flash('Apenas reservas pendentes podem ser recusadas!', 'warning')
        return redirect(url_for('reservas.ver_reserva', id=id))
    
    reserva.status = 'recusado'
    reserva.motivo_recusa = motivo
    reserva.aprovado_por = current_user.id
    reserva.data_aprovacao = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Reserva {reserva.numero} recusada.', 'warning')
    return redirect(url_for('reservas.ver_reserva', id=id))


@reservas_bp.route('/reserva/<int:id>')
@login_required
def ver_reserva(id):
    """Ver detalhes da reserva"""
    tenant_id = getattr(g, 'tenant_id', 1)
    reserva = ReservaEspaco.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    return render_template('reservas/reserva_detalhes.html',
                         title=f'Reserva {reserva.numero}',
                         reserva=reserva)


@reservas_bp.route('/reserva/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_reserva(id):
    """Cancelar reserva"""
    tenant_id = getattr(g, 'tenant_id', 1)
    reserva = ReservaEspaco.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    if reserva.status in ['concluido', 'cancelado']:
        flash('Não é possível cancelar esta reserva!', 'warning')
        return redirect(url_for('reservas.ver_reserva', id=id))
    
    reserva.status = 'cancelado'
    reserva.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Reserva {reserva.numero} cancelada.', 'info')
    return redirect(url_for('reservas.minhas_reservas'))

