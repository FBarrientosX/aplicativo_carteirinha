"""Rotas para módulo de Atividades e Inscrições"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, g
from flask_login import login_required
from app import db
from app.models import Atividade, TurmaAtividade, InscricaoAtividade, Morador
from datetime import datetime

atividades_bp = Blueprint('atividades', __name__, url_prefix='/atividades')

@atividades_bp.route('/')
@login_required
def listar():
    tenant_id = getattr(g, 'tenant_id', 1)
    atividades = Atividade.query.filter_by(tenant_id=tenant_id).all()
    return render_template('atividades/listar.html', title='Atividades', atividades=atividades)

@atividades_bp.route('/nova', methods=['GET','POST'])
@login_required
def nova():
    tenant_id = getattr(g, 'tenant_id', 1)
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return render_template('atividades/form.html')
        atividade = Atividade(
            tenant_id=tenant_id,
            nome=nome,
            descricao=request.form.get('descricao'),
            exige_pagamento=bool(request.form.get('exige_pagamento')),
            valor_taxa=request.form.get('valor_taxa') or None
        )
        db.session.add(atividade)
        db.session.commit()
        flash('Atividade criada!', 'success')
        return redirect(url_for('atividades.listar'))
    return render_template('atividades/form.html', title='Nova Atividade')

@atividades_bp.route('/<int:atividade_id>')
@login_required
def detalhes(atividade_id):
    atividade = Atividade.query.get_or_404(atividade_id)
    return render_template('atividades/detalhes.html', title=atividade.nome, atividade=atividade)

@atividades_bp.route('/<int:atividade_id>/turma/nova', methods=['POST'])
@login_required
def nova_turma(atividade_id):
    nome = request.form.get('nome_turma')
    if not nome:
        flash('Nome da turma é obrigatório', 'danger')
        return redirect(url_for('atividades.detalhes', atividade_id=atividade_id))
    turma = TurmaAtividade(
        atividade_id=atividade_id,
        nome_turma=nome,
        horario=request.form.get('horario'),
        vagas=int(request.form.get('vagas') or 0)
    )
    db.session.add(turma)
    db.session.commit()
    flash('Turma criada!', 'success')
    return redirect(url_for('atividades.detalhes', atividade_id=atividade_id))

@atividades_bp.route('/turma/<int:turma_id>/inscrever', methods=['POST'])
@login_required
def inscrever(turma_id):
    tenant_id = getattr(g, 'tenant_id', 1)
    morador = Morador.query.filter_by(tenant_id=tenant_id).first()
    if not morador:
        flash('Morador não identificado', 'danger')
        return redirect(request.referrer or url_for('atividades.listar'))
    ja = InscricaoAtividade.query.filter_by(turma_id=turma_id, morador_id=morador.id).first()
    if ja:
        flash('Você já está inscrito nesta turma.', 'warning')
        return redirect(request.referrer or url_for('atividades.listar'))
    ins = InscricaoAtividade(turma_id=turma_id, morador_id=morador.id, status='ativa', pago=False)
    db.session.add(ins)
    db.session.commit()
    # Stub de pagamento: marcar pago se checkbox veio marcado
    if request.form.get('marcar_pago'):
        ins.pago = True
        db.session.commit()
    flash('Inscrição realizada!', 'success')
    return redirect(request.referrer or url_for('atividades.listar'))
