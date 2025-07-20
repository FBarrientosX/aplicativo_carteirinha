"""
Rotas para o módulo de Manutenção & Chamados
CondoTech Solutions
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

from app import db
from app.models import (
    ChamadoManutencao, CategoriaManutencao, AnexoChamado, 
    HistoricoChamado, Usuario, ModuloTenant
)
from sqlalchemy import text
from app.forms import ChamadoManutencaoForm, FiltrosChamadosForm

# Criar blueprint
manutencao_bp = Blueprint('manutencao', __name__, url_prefix='/manutencao')

@manutencao_bp.before_request
def verificar_modulo_ativo():
    """Verifica se o módulo de manutenção está ativo para o tenant"""
    from flask import g
    
    # Pular verificação para rotas estáticas e de erro
    if request.endpoint and (request.endpoint.startswith('static') or 'error' in request.endpoint):
        return
    
    # ADMIN SEMPRE TEM ACESSO - bypass completo para administradores
    if current_user.is_authenticated and current_user.is_admin():
        return  # Admin pode acessar todos os módulos sempre
    
    tenant_id = getattr(g, 'tenant_id', 1)  # Usar tenant_id padrão se não definido
    
    try:
        # Verificar se o módulo está ativo
        modulo_ativo = db.session.execute(text("""
            SELECT mt.ativo FROM modulos_tenant mt
            JOIN modulos m ON m.id = mt.modulo_id
            WHERE mt.tenant_id = :tenant_id AND m.slug = 'manutencao' AND mt.ativo = 1
        """), {'tenant_id': tenant_id}).fetchone()
        
        if not modulo_ativo:
            flash('Módulo de Manutenção não está ativo para seu condomínio. Entre em contato com o administrador.', 'warning')
            return redirect(url_for('main.index'))
    except Exception as e:
        # Em caso de erro, permitir acesso (graceful degradation)
        pass

@manutencao_bp.route('/')
@login_required
def dashboard():
    """Dashboard do módulo de manutenção"""
    
    # Estatísticas gerais
    total_chamados = db.session.execute(text("""
        SELECT COUNT(*) FROM chamados_manutencao 
        WHERE tenant_id = :tenant_id
    """), {'tenant_id': current_user.tenant_id}).fetchone()[0]
    
    chamados_abertos = db.session.execute(text("""
        SELECT COUNT(*) FROM chamados_manutencao 
        WHERE tenant_id = :tenant_id AND status IN ('aberto', 'em_andamento')
    """), {'tenant_id': current_user.tenant_id}).fetchone()[0]
    
    chamados_urgentes = db.session.execute(text("""
        SELECT COUNT(*) FROM chamados_manutencao 
        WHERE tenant_id = :tenant_id AND prioridade = 'urgente' AND status != 'concluido'
    """), {'tenant_id': current_user.tenant_id}).fetchone()[0]
    
    # Chamados recentes
    chamados_recentes = db.session.execute(text("""
        SELECT c.id, c.numero, c.titulo, c.status, c.prioridade, c.data_abertura, 
               cat.nome as categoria, u.nome_completo as solicitante
        FROM chamados_manutencao c
        JOIN categorias_manutencao cat ON cat.id = c.categoria_id
        JOIN usuarios u ON u.id = c.solicitante_id
        WHERE c.tenant_id = :tenant_id
        ORDER BY c.data_abertura DESC
        LIMIT 10
    """), {'tenant_id': current_user.tenant_id}).fetchall()
    
    # Estatísticas por categoria
    stats_categoria = db.session.execute(text("""
        SELECT cat.nome, COUNT(c.id) as total,
               SUM(CASE WHEN c.status IN ('aberto', 'em_andamento') THEN 1 ELSE 0 END) as abertos
        FROM categorias_manutencao cat
        LEFT JOIN chamados_manutencao c ON c.categoria_id = cat.id AND c.tenant_id = :tenant_id
        WHERE cat.tenant_id = :tenant_id
        GROUP BY cat.id, cat.nome
        ORDER BY total DESC
    """), {'tenant_id': current_user.tenant_id}).fetchall()
    
    return render_template('manutencao/dashboard.html',
                         title='Manutenção & Chamados',
                         total_chamados=total_chamados,
                         chamados_abertos=chamados_abertos,
                         chamados_urgentes=chamados_urgentes,
                         chamados_recentes=chamados_recentes,
                         stats_categoria=stats_categoria)

@manutencao_bp.route('/chamados')
@login_required
def listar_chamados():
    """Lista todos os chamados"""
    
    # Filtros
    status = request.args.get('status', '')
    categoria = request.args.get('categoria', '')
    prioridade = request.args.get('prioridade', '')
    busca = request.args.get('busca', '')
    
    # Query base
    query = """
        SELECT c.id, c.numero, c.titulo, c.status, c.prioridade, c.data_abertura,
               c.local, cat.nome as categoria, cat.cor as categoria_cor,
               sol.nome_completo as solicitante, resp.nome_completo as responsavel
        FROM chamados_manutencao c
        JOIN categorias_manutencao cat ON cat.id = c.categoria_id
        JOIN usuarios sol ON sol.id = c.solicitante_id
        LEFT JOIN usuarios resp ON resp.id = c.responsavel_id
        WHERE c.tenant_id = :tenant_id
    """
    params = {'tenant_id': current_user.tenant_id}
    
    # Aplicar filtros
    if status:
        query += " AND c.status = :status"
        params['status'] = status
    
    if categoria:
        query += " AND c.categoria_id = :categoria"
        params['categoria'] = categoria
    
    if prioridade:
        query += " AND c.prioridade = :prioridade"
        params['prioridade'] = prioridade
    
    if busca:
        query += " AND (c.titulo LIKE :busca OR c.descricao LIKE :busca OR c.numero LIKE :busca)"
        params['busca'] = f"%{busca}%"
    
    query += " ORDER BY c.data_abertura DESC"
    
    chamados = db.session.execute(text(query), params).fetchall()
    
    # Buscar categorias para filtro
    categorias = db.session.execute(text("""
        SELECT id, nome FROM categorias_manutencao 
        WHERE tenant_id = :tenant_id AND ativo = 1
        ORDER BY nome
    """), {'tenant_id': current_user.tenant_id}).fetchall()
    
    return render_template('manutencao/listar_chamados.html',
                         title='Chamados de Manutenção',
                         chamados=chamados,
                         categorias=categorias,
                         filtros={'status': status, 'categoria': categoria, 
                                'prioridade': prioridade, 'busca': busca})

@manutencao_bp.route('/chamado/novo', methods=['GET', 'POST'])
@login_required
def novo_chamado():
    """Criar novo chamado"""
    
    if request.method == 'POST':
        try:
            # Gerar número do chamado
            import random
            import string
            year = datetime.now().year
            random_str = ''.join(random.choices(string.digits, k=4))
            numero = f"CH{year}{random_str}"
            
            # Verificar se número já existe
            while db.session.execute(text("SELECT id FROM chamados_manutencao WHERE numero = :numero"), {'numero': numero}).fetchone():
                random_str = ''.join(random.choices(string.digits, k=4))
                numero = f"CH{year}{random_str}"
            
            # Inserir chamado
            db.session.execute(text("""
                INSERT INTO chamados_manutencao 
                (numero, tenant_id, titulo, descricao, local, categoria_id, 
                 solicitante_id, prioridade, data_abertura)
                VALUES (:numero, :tenant_id, :titulo, :descricao, :local, :categoria_id, :solicitante_id, :prioridade, :data_abertura)
            """), {
                'numero': numero,
                'tenant_id': current_user.tenant_id,
                'titulo': request.form['titulo'],
                'descricao': request.form['descricao'],
                'local': request.form['local'],
                'categoria_id': request.form['categoria_id'],
                'solicitante_id': current_user.id,
                'prioridade': request.form['prioridade'],
                'data_abertura': datetime.now()
            })
            
            # Buscar ID do chamado criado
            chamado_id = db.session.execute(text("""
                SELECT id FROM chamados_manutencao WHERE numero = :numero
            """), {'numero': numero}).fetchone()[0]
            
            # Adicionar ao histórico
            db.session.execute(text("""
                INSERT INTO historico_chamados 
                (chamado_id, usuario_id, acao, comentario, data_acao)
                VALUES (:chamado_id, :usuario_id, 'criado', 'Chamado criado', :data_acao)
            """), {'chamado_id': chamado_id, 'usuario_id': current_user.id, 'data_acao': datetime.now()})
            
            db.session.commit()
            
            flash(f'Chamado {numero} criado com sucesso!', 'success')
            return redirect(url_for('manutencao.ver_chamado', id=chamado_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar chamado: {str(e)}', 'danger')
    
    # Buscar categorias
    categorias = db.session.execute(text("""
        SELECT id, nome, icone, cor FROM categorias_manutencao 
        WHERE tenant_id = :tenant_id AND ativo = 1
        ORDER BY nome
    """), {'tenant_id': current_user.tenant_id}).fetchall()
    
    return render_template('manutencao/novo_chamado.html',
                         title='Novo Chamado',
                         categorias=categorias)

@manutencao_bp.route('/chamado/<int:id>')
@login_required 
def ver_chamado(id):
    """Visualizar chamado específico"""
    
    # Buscar chamado
    chamado = db.session.execute(text("""
        SELECT c.*, cat.nome as categoria, cat.icone as categoria_icone, cat.cor as categoria_cor,
               sol.nome_completo as solicitante, sol.email as solicitante_email,
               resp.nome_completo as responsavel, resp.email as responsavel_email
        FROM chamados_manutencao c
        JOIN categorias_manutencao cat ON cat.id = c.categoria_id
        JOIN usuarios sol ON sol.id = c.solicitante_id
        LEFT JOIN usuarios resp ON resp.id = c.responsavel_id
        WHERE c.id = :id AND c.tenant_id = :tenant_id
    """), {'id': id, 'tenant_id': current_user.tenant_id}).fetchone()
    
    if not chamado:
        abort(404)
    
    # Buscar histórico
    historico = db.session.execute(text("""
        SELECT h.*, u.nome_completo as usuario_nome
        FROM historico_chamados h
        JOIN usuarios u ON u.id = h.usuario_id
        WHERE h.chamado_id = :chamado_id
        ORDER BY h.data_acao DESC
    """), {'chamado_id': id}).fetchall()
    
    # Buscar anexos
    anexos = db.session.execute(text("""
        SELECT * FROM anexos_chamados 
        WHERE chamado_id = :chamado_id
        ORDER BY data_upload DESC
    """), {'chamado_id': id}).fetchall()
    
    return render_template('manutencao/ver_chamado.html',
                         title=f'Chamado {chamado.numero}',
                         chamado=chamado,
                         historico=historico,
                         anexos=anexos)

@manutencao_bp.route('/chamado/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_chamado(id):
    """Editar chamado (apenas responsável ou admin)"""
    
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manutencao.ver_chamado', id=id))
    
    # Buscar chamado
    chamado = db.session.execute(text("""
        SELECT * FROM chamados_manutencao 
        WHERE id = :id AND tenant_id = :tenant_id
    """), {'id': id, 'tenant_id': current_user.tenant_id}).fetchone()
    
    if not chamado:
        abort(404)
    
    if request.method == 'POST':
        try:
            # Atualizar chamado
            db.session.execute(text("""
                UPDATE chamados_manutencao 
                SET status = :status, prioridade = :prioridade, responsavel_id = :responsavel_id,
                    diagnostico = :diagnostico, solucao = :solucao, observacoes_internas = :observacoes_internas
                WHERE id = :id
            """), {
                'status': request.form['status'],
                'prioridade': request.form['prioridade'],
                'responsavel_id': request.form.get('responsavel_id') or None,
                'diagnostico': request.form.get('diagnostico', ''),
                'solucao': request.form.get('solucao', ''),
                'observacoes_internas': request.form.get('observacoes_internas', ''),
                'id': id
            })
            
            # Adicionar ao histórico
            db.session.execute(text("""
                INSERT INTO historico_chamados 
                (chamado_id, usuario_id, acao, comentario, data_acao)
                VALUES (:chamado_id, :usuario_id, 'atualizado', :comentario, :data_acao)
            """), {'chamado_id': id, 'usuario_id': current_user.id, 'comentario': 'Chamado atualizado', 'data_acao': datetime.now()})
            
            db.session.commit()
            
            flash('Chamado atualizado com sucesso!', 'success')
            return redirect(url_for('manutencao.ver_chamado', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar chamado: {str(e)}', 'danger')
    
    # Buscar usuários para responsável
    usuarios = db.session.execute(text("""
        SELECT id, nome_completo FROM usuarios 
        WHERE tenant_id = :tenant_id AND ativo = 1
        ORDER BY nome_completo
    """), {'tenant_id': current_user.tenant_id}).fetchall()
    
    return render_template('manutencao/editar_chamado.html',
                         title='Editar Chamado',
                         chamado=chamado,
                         usuarios=usuarios)

@manutencao_bp.route('/categorias')
@login_required
def categorias():
    """Gerenciar categorias (apenas admin)"""
    
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manutencao.dashboard'))
    
    categorias = db.session.execute(text("""
        SELECT *, 
               (SELECT COUNT(*) FROM chamados_manutencao 
                WHERE categoria_id = categorias_manutencao.id) as total_chamados
        FROM categorias_manutencao 
        WHERE tenant_id = :tenant_id
        ORDER BY nome
    """), {'tenant_id': current_user.tenant_id}).fetchall()
    
    return render_template('manutencao/categorias.html',
                         title='Categorias de Manutenção',
                         categorias=categorias) 

# ===== ROTAS DE CATEGORIAS =====

@manutencao_bp.route('/categoria/nova', methods=['POST'])
@login_required
def nova_categoria():
    """Criar nova categoria de manutenção"""
    
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manutencao.categorias'))
    
    try:
        # Inserir nova categoria
        db.session.execute(text("""
            INSERT INTO categorias_manutencao 
            (tenant_id, nome, descricao, icone, cor, ativo, data_criacao)
            VALUES (:tenant_id, :nome, :descricao, :icone, :cor, 1, :data_criacao)
        """), {
            'tenant_id': current_user.tenant_id,
            'nome': request.form['nome'],
            'descricao': request.form.get('descricao', ''),
            'icone': request.form.get('icone', 'fa-wrench'),
            'cor': request.form.get('cor', '#6c757d'),
            'data_criacao': datetime.now()
        })
        
        db.session.commit()
        flash(f'Categoria "{request.form["nome"]}" criada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar categoria: {str(e)}', 'danger')
    
    return redirect(url_for('manutencao.categorias'))

@manutencao_bp.route('/categoria/<int:id>/editar', methods=['POST'])
@login_required
def editar_categoria(id):
    """Editar categoria de manutenção"""
    
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manutencao.categorias'))
    
    try:
        # Atualizar categoria
        db.session.execute(text("""
            UPDATE categorias_manutencao 
            SET nome = :nome, descricao = :descricao, icone = :icone, 
                cor = :cor, ativo = :ativo
            WHERE id = :id AND tenant_id = :tenant_id
        """), {
            'nome': request.form['nome'],
            'descricao': request.form.get('descricao', ''),
            'icone': request.form.get('icone', 'fa-wrench'),
            'cor': request.form.get('cor', '#6c757d'),
            'ativo': 1 if request.form.get('ativo') else 0,
            'id': id,
            'tenant_id': current_user.tenant_id
        })
        
        db.session.commit()
        flash(f'Categoria atualizada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar categoria: {str(e)}', 'danger')
    
    return redirect(url_for('manutencao.categorias'))

@manutencao_bp.route('/categoria/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_categoria(id):
    """Ativar/desativar categoria"""
    
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manutencao.categorias'))
    
    try:
        # Alternar status da categoria
        db.session.execute(text("""
            UPDATE categorias_manutencao 
            SET ativo = NOT ativo
            WHERE id = :id AND tenant_id = :tenant_id
        """), {'id': id, 'tenant_id': current_user.tenant_id})
        
        db.session.commit()
        flash('Status da categoria alterado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status da categoria: {str(e)}', 'danger')
    
    return redirect(url_for('manutencao.categorias'))

@manutencao_bp.route('/categoria/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_categoria(id):
    """Excluir categoria (apenas se não tiver chamados)"""
    
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manutencao.categorias'))
    
    try:
        # Verificar se categoria tem chamados
        total_chamados = db.session.execute(text("""
            SELECT COUNT(*) FROM chamados_manutencao 
            WHERE categoria_id = :id
        """), {'id': id}).fetchone()[0]
        
        if total_chamados > 0:
            flash('Não é possível excluir categoria que possui chamados associados.', 'warning')
            return redirect(url_for('manutencao.categorias'))
        
        # Excluir categoria
        db.session.execute(text("""
            DELETE FROM categorias_manutencao 
            WHERE id = :id AND tenant_id = :tenant_id
        """), {'id': id, 'tenant_id': current_user.tenant_id})
        
        db.session.commit()
        flash('Categoria excluída com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir categoria: {str(e)}', 'danger')
    
    return redirect(url_for('manutencao.categorias')) 