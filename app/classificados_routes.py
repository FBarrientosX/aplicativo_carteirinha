"""Rotas para módulo de Classificados/Marketplace"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app, g, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.models import Classificado, FotoClassificado, AvaliacaoClassificado, Morador
from app.forms import ClassificadoForm, AvaliacaoClassificadoForm, FiltroClassificadoForm
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import os
import uuid

classificados_bp = Blueprint('classificados', __name__, url_prefix='/classificados')

@classificados_bp.route('/')
@login_required
def listar_classificados():
    """Lista todos os classificados"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = FiltroClassificadoForm(request.args)
    
    # Query base
    query = Classificado.query.filter_by(tenant_id=tenant_id)
    
    # Aplicar filtros
    if form.tipo.data:
        query = query.filter_by(tipo=form.tipo.data)
    
    if form.categoria.data:
        query = query.filter(Classificado.categoria.contains(form.categoria.data))
    
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    if form.busca.data:
        query = query.filter(
            or_(
                Classificado.titulo.contains(form.busca.data),
                Classificado.descricao.contains(form.busca.data)
            )
        )
    
    # Ordenação
    if form.ordenar.data == 'visualizacoes':
        query = query.order_by(Classificado.visualizacoes.desc())
    elif form.ordenar.data == 'avaliacao':
        # Ordenar por melhor avaliação (mais complexo, precisa join)
        query = query.order_by(Classificado.data_criacao.desc())
    elif form.ordenar.data == 'preco_menor':
        query = query.order_by(Classificado.preco.asc().nullslast())
    elif form.ordenar.data == 'preco_maior':
        query = query.order_by(Classificado.preco.desc().nullslast())
    else:  # recentes
        query = query.order_by(Classificado.data_criacao.desc())
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    classificados = query.paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Estatísticas
    total_ativos = Classificado.query.filter_by(tenant_id=tenant_id, status='ativo').count()
    total_produtos = Classificado.query.filter_by(tenant_id=tenant_id, tipo='produto', status='ativo').count()
    total_servicos = Classificado.query.filter_by(tenant_id=tenant_id, tipo='servico', status='ativo').count()
    
    stats = {
        'total_ativos': total_ativos,
        'total_produtos': total_produtos,
        'total_servicos': total_servicos
    }
    
    return render_template('classificados/listar.html',
                         title='Marketplace - Classificados',
                         classificados=classificados,
                         form=form,
                         stats=stats)


@classificados_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_classificado():
    """Criar novo classificado"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = ClassificadoForm()
    
    if form.validate_on_submit():
        # Buscar morador do usuário logado
        morador = Morador.query.filter_by(tenant_id=tenant_id).first()
        if not morador:
            flash('Você precisa estar cadastrado como morador para publicar classificados.', 'warning')
            return redirect(url_for('classificados.listar_classificados'))
        
        classificado = Classificado(
            tenant_id=tenant_id,
            morador_id=morador.id,
            titulo=form.titulo.data,
            descricao=form.descricao.data,
            tipo=form.tipo.data,
            categoria=form.categoria.data,
            preco=form.preco.data,
            tipo_preco=form.tipo_preco.data,
            telefone=form.telefone.data,
            email=form.email.data,
            whatsapp=form.whatsapp.data,
            status=form.status.data,
            destaque=form.destaque.data,
            apartamento=f"{morador.bloco}-{morador.apartamento}"
        )
        
        db.session.add(classificado)
        db.session.flush()  # Para obter o ID
        
        # Processar fotos se fornecidas
        # Quando multiple=True, request.files retorna uma lista
        fotos_arquivos = request.files.getlist('fotos')
        if fotos_arquivos:
            for idx, foto in enumerate(fotos_arquivos):
                if foto and hasattr(foto, 'filename') and foto.filename:
                    salvar_foto_classificado(classificado.id, foto, idx)
        
        db.session.commit()
        
        flash(f'Classificado "{classificado.titulo}" publicado com sucesso!', 'success')
        return redirect(url_for('classificados.ver_classificado', id=classificado.id))
    
    return render_template('classificados/form.html',
                         title='Novo Classificado',
                         form=form)


@classificados_bp.route('/<int:id>')
@login_required
def ver_classificado(id):
    """Ver detalhes do classificado"""
    tenant_id = getattr(g, 'tenant_id', 1)
    classificado = Classificado.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    # Incrementar visualizações
    classificado.incrementar_visualizacao()
    
    # Buscar avaliações aprovadas
    avaliacoes = AvaliacaoClassificado.query.filter_by(
        classificado_id=id,
        tenant_id=tenant_id,
        aprovado=True
    ).order_by(AvaliacaoClassificado.data_avaliacao.desc()).limit(10).all()
    
    # Formulário de avaliação
    form_avaliacao = AvaliacaoClassificadoForm()
    
    return render_template('classificados/detalhes.html',
                         title=classificado.titulo,
                         classificado=classificado,
                         avaliacoes=avaliacoes,
                         form_avaliacao=form_avaliacao)


@classificados_bp.route('/<int:id>/avaliar', methods=['POST'])
@login_required
def avaliar_classificado(id):
    """Avaliar um classificado"""
    tenant_id = getattr(g, 'tenant_id', 1)
    classificado = Classificado.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    form = AvaliacaoClassificadoForm()
    
    if form.validate_on_submit():
        # Verificar se o morador já avaliou
        morador = Morador.query.filter_by(tenant_id=tenant_id).first()
        if not morador:
            flash('Você precisa estar cadastrado como morador para avaliar.', 'warning')
            return redirect(url_for('classificados.ver_classificado', id=id))
        
        avaliacao_existente = AvaliacaoClassificado.query.filter_by(
            classificado_id=id,
            morador_id=morador.id,
            tenant_id=tenant_id
        ).first()
        
        if avaliacao_existente:
            flash('Você já avaliou este classificado!', 'warning')
            return redirect(url_for('classificados.ver_classificado', id=id))
        
        avaliacao = AvaliacaoClassificado(
            tenant_id=tenant_id,
            classificado_id=id,
            morador_id=morador.id,
            nota=form.nota.data,
            comentario=form.comentario.data,
            comprou=form.comprou.data,
            utilizou=form.utilizou.data,
            aprovado=True
        )
        
        db.session.add(avaliacao)
        db.session.commit()
        
        flash('Avaliação enviada com sucesso!', 'success')
        return redirect(url_for('classificados.ver_classificado', id=id))
    
    return redirect(url_for('classificados.ver_classificado', id=id))


@classificados_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_classificado(id):
    """Editar classificado"""
    tenant_id = getattr(g, 'tenant_id', 1)
    classificado = Classificado.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    form = ClassificadoForm(obj=classificado)
    
    if form.validate_on_submit():
        classificado.titulo = form.titulo.data
        classificado.descricao = form.descricao.data
        classificado.tipo = form.tipo.data
        classificado.categoria = form.categoria.data
        classificado.preco = form.preco.data
        classificado.tipo_preco = form.tipo_preco.data
        classificado.telefone = form.telefone.data
        classificado.email = form.email.data
        classificado.whatsapp = form.whatsapp.data
        classificado.status = form.status.data
        classificado.destaque = form.destaque.data
        classificado.data_atualizacao = datetime.utcnow()
        
        # Processar novas fotos se fornecidas
        fotos_arquivos = request.files.getlist('fotos')
        if fotos_arquivos:
            for idx, foto in enumerate(fotos_arquivos):
                if foto and hasattr(foto, 'filename') and foto.filename:
                    salvar_foto_classificado(classificado.id, foto, len(classificado.fotos) + idx)
        
        db.session.commit()
        
        flash('Classificado atualizado com sucesso!', 'success')
        return redirect(url_for('classificados.ver_classificado', id=id))
    
    return render_template('classificados/form.html',
                         title='Editar Classificado',
                         form=form,
                         classificado=classificado)


@classificados_bp.route('/meus-classificados')
@login_required
def meus_classificados():
    """Lista classificados do morador logado"""
    tenant_id = getattr(g, 'tenant_id', 1)
    
    # Buscar morador do usuário logado
    morador = Morador.query.filter_by(tenant_id=tenant_id).first()
    if not morador:
        flash('Você precisa estar cadastrado como morador.', 'warning')
        return redirect(url_for('classificados.listar_classificados'))
    
    classificados = Classificado.query.filter_by(
        tenant_id=tenant_id,
        morador_id=morador.id
    ).order_by(Classificado.data_criacao.desc()).all()
    
    return render_template('classificados/meus.html',
                         title='Meus Classificados',
                         classificados=classificados)


@classificados_bp.route('/foto/<filename>')
@login_required
def foto_classificado(filename):
    """Servir foto do classificado"""
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'classificados')
    return send_from_directory(upload_dir, filename)


def salvar_foto_classificado(classificado_id, arquivo, ordem=0):
    """Salvar foto do classificado"""
    if arquivo and hasattr(arquivo, 'filename') and arquivo.filename:
        filename = secure_filename(arquivo.filename)
        nome_unico = f"classificado_{classificado_id}_{uuid.uuid4().hex[:8]}.{filename.rsplit('.', 1)[1].lower()}"
        
        # Criar diretório se não existir
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'classificados')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salvar arquivo
        caminho_arquivo = os.path.join(upload_dir, nome_unico)
        arquivo.save(caminho_arquivo)
        
        # Salvar registro no banco
        foto = FotoClassificado(
            classificado_id=classificado_id,
            nome_arquivo=nome_unico,
            caminho_arquivo=caminho_arquivo,
            nome_original=filename,
            tamanho=os.path.getsize(caminho_arquivo),
            ordem=ordem
        )
        
        db.session.add(foto)
        db.session.commit()
        
        return foto
    
    return None

