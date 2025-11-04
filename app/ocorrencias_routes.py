"""Rotas para módulo de Ocorrências"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, g, current_app, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.models import Ocorrencia, Morador
from datetime import datetime
from werkzeug.utils import secure_filename
import os

ocorrencias_bp = Blueprint('ocorrencias', __name__, url_prefix='/ocorrencias')

@ocorrencias_bp.route('/')
@login_required
def listar():
    tenant_id = getattr(g, 'tenant_id', 1)
    ocorrencias = Ocorrencia.query.filter_by(tenant_id=tenant_id).order_by(Ocorrencia.data_abertura.desc()).all()
    return render_template('ocorrencias/listar.html', title='Ocorrências', ocorrencias=ocorrencias)

@ocorrencias_bp.route('/nova', methods=['GET','POST'])
@login_required
def nova():
    tenant_id = getattr(g, 'tenant_id', 1)
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        categoria = request.form.get('categoria')
        if not titulo or not descricao:
            flash('Título e descrição são obrigatórios', 'danger')
            return render_template('ocorrencias/form.html')
        morador = Morador.query.filter_by(tenant_id=tenant_id).first()
        oc = Ocorrencia(
            tenant_id=tenant_id,
            morador_id=morador.id if morador else None,
            titulo=titulo,
            descricao=descricao,
            categoria=categoria,
            status='aberta'
        )
        # Foto opcional
        arquivo = request.files.get('foto')
        if arquivo and arquivo.filename:
            filename = secure_filename(arquivo.filename)
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ocorrencias')
            os.makedirs(upload_dir, exist_ok=True)
            nome_unico = f"oc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            caminho = os.path.join(upload_dir, nome_unico)
            arquivo.save(caminho)
            oc.foto_nome = nome_unico
            oc.foto_caminho = caminho
        db.session.add(oc)
        db.session.commit()
        flash('Ocorrência registrada!', 'success')
        return redirect(url_for('ocorrencias.listar'))
    return render_template('ocorrencias/form.html', title='Nova Ocorrência')

@ocorrencias_bp.route('/<int:id>')
@login_required
def detalhes(id):
    tenant_id = getattr(g, 'tenant_id', 1)
    oc = Ocorrencia.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    return render_template('ocorrencias/detalhes.html', title=oc.titulo, oc=oc)

@ocorrencias_bp.route('/<int:id>/alterar-status', methods=['POST'])
@login_required
def alterar_status(id):
    tenant_id = getattr(g, 'tenant_id', 1)
    oc = Ocorrencia.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    novo = request.form.get('status')
    if novo:
        oc.status = novo
        if novo in ['resolvida','arquivada']:
            oc.data_fechamento = datetime.utcnow()
        db.session.commit()
        flash('Status atualizado.', 'success')
    return redirect(url_for('ocorrencias.detalhes', id=id))

@ocorrencias_bp.route('/foto/<filename>')
@login_required
def foto(filename):
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ocorrencias')
    return send_from_directory(upload_dir, filename)
