"""Rotas para módulo de Votação/Assembleias"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, g
from flask_login import login_required
from app import db
from app.models import Assembleia, Pauta, Voto, Morador
from datetime import datetime

votacao_bp = Blueprint('votacao', __name__, url_prefix='/votacao')

@votacao_bp.route('/')
@login_required
def listar_assembleias():
    tenant_id = getattr(g, 'tenant_id', 1)
    assembleias = Assembleia.query.filter_by(tenant_id=tenant_id).order_by(Assembleia.inicio.desc()).all()
    return render_template('votacao/assembleias.html', title='Assembleias', assembleias=assembleias)

@votacao_bp.route('/nova', methods=['GET','POST'])
@login_required
def nova_assembleia():
    tenant_id = getattr(g, 'tenant_id', 1)
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        inicio = request.form.get('inicio')
        fim = request.form.get('fim')
        if not titulo or not inicio or not fim:
            flash('Título, início e fim são obrigatórios', 'danger')
            return render_template('votacao/assembleia_form.html')
        asm = Assembleia(
            tenant_id=tenant_id,
            titulo=titulo,
            descricao=request.form.get('descricao'),
            inicio=datetime.fromisoformat(inicio),
            fim=datetime.fromisoformat(fim),
            status='aberta'
        )
        db.session.add(asm)
        db.session.commit()
        flash('Assembleia criada!', 'success')
        return redirect(url_for('votacao.listar_assembleias'))
    return render_template('votacao/assembleia_form.html', title='Nova Assembleia')

@votacao_bp.route('/<int:id>')
@login_required
def detalhes_assembleia(id):
    asm = Assembleia.query.get_or_404(id)
    pautas = Pauta.query.filter_by(assembleia_id=id).all()
    return render_template('votacao/assembleia_detalhes.html', title=asm.titulo, asm=asm, pautas=pautas)

@votacao_bp.route('/<int:assembleia_id>/pauta/nova', methods=['POST'])
@login_required
def nova_pauta(assembleia_id):
    titulo = request.form.get('titulo')
    if not titulo:
        flash('Título da pauta é obrigatório', 'danger')
        return redirect(url_for('votacao.detalhes_assembleia', id=assembleia_id))
    pauta = Pauta(assembleia_id=assembleia_id, titulo=titulo, descricao=request.form.get('descricao'))
    db.session.add(pauta)
    db.session.commit()
    flash('Pauta adicionada!', 'success')
    return redirect(url_for('votacao.detalhes_assembleia', id=assembleia_id))

@votacao_bp.route('/pauta/<int:pauta_id>/votar', methods=['POST'])
@login_required
def votar(pauta_id):
    tenant_id = getattr(g, 'tenant_id', 1)
    morador = Morador.query.filter_by(tenant_id=tenant_id).first()
    escolha = request.form.get('escolha')  # sim, nao, abstenção
    if not escolha:
        flash('Escolha inválida', 'danger')
        return redirect(request.referrer or url_for('votacao.listar_assembleias'))
    voto = Voto.query.filter_by(pauta_id=pauta_id, morador_id=morador.id).first()
    if voto:
        flash('Você já votou nesta pauta.', 'warning')
        return redirect(request.referrer or url_for('votacao.listar_assembleias'))
    novo = Voto(pauta_id=pauta_id, morador_id=morador.id, escolha=escolha)
    db.session.add(novo)
    db.session.commit()
    flash('Voto registrado!', 'success')
    return redirect(request.referrer or url_for('votacao.listar_assembleias'))
