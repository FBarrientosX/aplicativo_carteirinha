"""Rotas para módulo Achados e Perdidos"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, g, current_app, send_from_directory
from flask_login import login_required
from app import db
from app.models import AchadoPerdido, Morador
from datetime import datetime
from werkzeug.utils import secure_filename
import os

achados_bp = Blueprint('achados', __name__, url_prefix='/achados')

@achados_bp.route('/')
@login_required
def listar():
    tenant_id = getattr(g, 'tenant_id', 1)
    itens = AchadoPerdido.query.filter_by(tenant_id=tenant_id).order_by(AchadoPerdido.data_registro.desc()).all()
    return render_template('achados/listar.html', title='Achados e Perdidos', itens=itens)

@achados_bp.route('/novo', methods=['GET','POST'])
@login_required
def novo():
    tenant_id = getattr(g, 'tenant_id', 1)
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        local = request.form.get('local')
        if not tipo or not titulo:
            flash('Tipo e título são obrigatórios', 'danger')
            return render_template('achados/form.html')
        morador = Morador.query.filter_by(tenant_id=tenant_id).first()
        item = AchadoPerdido(
            tenant_id=tenant_id,
            morador_id=morador.id if morador else None,
            tipo=tipo,
            titulo=titulo,
            descricao=descricao,
            local=local,
            status='aberto'
        )
        arquivo = request.files.get('foto')
        if arquivo and arquivo.filename:
            filename = secure_filename(arquivo.filename)
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'achados')
            os.makedirs(upload_dir, exist_ok=True)
            nome_unico = f"ap_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            caminho = os.path.join(upload_dir, nome_unico)
            arquivo.save(caminho)
            item.foto_nome = nome_unico
            item.foto_caminho = caminho
        db.session.add(item)
        db.session.commit()
        flash('Registro criado!', 'success')
        return redirect(url_for('achados.listar'))
    return render_template('achados/form.html', title='Novo Registro')

@achados_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def alterar_status(id):
    tenant_id = getattr(g, 'tenant_id', 1)
    item = AchadoPerdido.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    novo = request.form.get('status')
    if novo:
        item.status = novo
        db.session.commit()
        flash('Status atualizado.', 'success')
    return redirect(url_for('achados.listar'))

@achados_bp.route('/foto/<filename>')
@login_required
def foto(filename):
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'achados')
    return send_from_directory(upload_dir, filename)
