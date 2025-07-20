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

# Blueprint do módulo
manutencao_bp = Blueprint('manutencao', __name__, url_prefix='/manutencao')

@manutencao_bp.before_request
def verificar_modulo_ativo():
    """Verifica se o módulo de manutenção está ativo para o tenant"""
    from flask import g
    
    if hasattr(g, 'tenant_id'):
        # Verificar se o módulo está ativo
        modulo_ativo = db.session.execute(text("""
            SELECT mt.ativo FROM modulos_tenant mt
            JOIN modulos m ON m.id = mt.modulo_id
            WHERE mt.tenant_id = :tenant_id AND m.slug = 'manutencao' AND mt.ativo = 1
        """), {'tenant_id': g.tenant_id}).fetchone()
        
        if not modulo_ativo:
            flash('Módulo de Manutenção não está ativo para seu condomínio.', 'warning')
            return redirect(url_for('main.index'))

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
        WHERE c.tenant_id = ?
    """
    params = [current_user.tenant_id]
    
    # Aplicar filtros
    if status:
        query += " AND c.status = ?"
        params.append(status)
    
    if categoria:
        query += " AND c.categoria_id = ?"
        params.append(categoria)
    
    if prioridade:
        query += " AND c.prioridade = ?"
        params.append(prioridade)
    
    if busca:
        query += " AND (c.titulo LIKE ? OR c.descricao LIKE ? OR c.numero LIKE ?)"
        busca_term = f"%{busca}%"
        params.extend([busca_term, busca_term, busca_term])
    
    query += " ORDER BY c.data_abertura DESC"
    
    chamados = db.session.execute(query, params).fetchall()
    
    # Buscar categorias para filtro
    categorias = db.session.execute("""
        SELECT id, nome FROM categorias_manutencao 
        WHERE tenant_id = ? AND ativo = 1
        ORDER BY nome
    """, (current_user.tenant_id,)).fetchall()
    
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
            while db.session.execute("SELECT id FROM chamados_manutencao WHERE numero = ?", (numero,)).fetchone():
                random_str = ''.join(random.choices(string.digits, k=4))
                numero = f"CH{year}{random_str}"
            
            # Inserir chamado
            db.session.execute("""
                INSERT INTO chamados_manutencao 
                (numero, tenant_id, titulo, descricao, local, categoria_id, 
                 solicitante_id, prioridade, data_abertura)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                numero,
                current_user.tenant_id,
                request.form['titulo'],
                request.form['descricao'],
                request.form['local'],
                request.form['categoria_id'],
                current_user.id,
                request.form['prioridade'],
                datetime.now()
            ))
            
            # Buscar ID do chamado criado
            chamado_id = db.session.execute("""
                SELECT id FROM chamados_manutencao WHERE numero = ?
            """, (numero,)).fetchone()[0]
            
            # Adicionar ao histórico
            db.session.execute("""
                INSERT INTO historico_chamados 
                (chamado_id, usuario_id, acao, comentario, data_acao)
                VALUES (?, ?, 'criado', 'Chamado criado', ?)
            """, (chamado_id, current_user.id, datetime.now()))
            
            db.session.commit()
            
            flash(f'Chamado {numero} criado com sucesso!', 'success')
            return redirect(url_for('manutencao.ver_chamado', id=chamado_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar chamado: {str(e)}', 'danger')
    
    # Buscar categorias
    categorias = db.session.execute("""
        SELECT id, nome, icone, cor FROM categorias_manutencao 
        WHERE tenant_id = ? AND ativo = 1
        ORDER BY nome
    """, (current_user.tenant_id,)).fetchall()
    
    return render_template('manutencao/novo_chamado.html',
                         title='Novo Chamado',
                         categorias=categorias)

@manutencao_bp.route('/chamado/<int:id>')
@login_required 
def ver_chamado(id):
    """Visualizar chamado específico"""
    
    # Buscar chamado
    chamado = db.session.execute("""
        SELECT c.*, cat.nome as categoria, cat.icone as categoria_icone, cat.cor as categoria_cor,
               sol.nome_completo as solicitante, sol.email as solicitante_email,
               resp.nome_completo as responsavel, resp.email as responsavel_email
        FROM chamados_manutencao c
        JOIN categorias_manutencao cat ON cat.id = c.categoria_id
        JOIN usuarios sol ON sol.id = c.solicitante_id
        LEFT JOIN usuarios resp ON resp.id = c.responsavel_id
        WHERE c.id = ? AND c.tenant_id = ?
    """, (id, current_user.tenant_id)).fetchone()
    
    if not chamado:
        abort(404)
    
    # Buscar histórico
    historico = db.session.execute("""
        SELECT h.*, u.nome_completo as usuario_nome
        FROM historico_chamados h
        JOIN usuarios u ON u.id = h.usuario_id
        WHERE h.chamado_id = ?
        ORDER BY h.data_acao DESC
    """, (id,)).fetchall()
    
    # Buscar anexos
    anexos = db.session.execute("""
        SELECT * FROM anexos_chamados 
        WHERE chamado_id = ?
        ORDER BY data_upload DESC
    """, (id,)).fetchall()
    
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
    chamado = db.session.execute("""
        SELECT * FROM chamados_manutencao 
        WHERE id = ? AND tenant_id = ?
    """, (id, current_user.tenant_id)).fetchone()
    
    if not chamado:
        abort(404)
    
    if request.method == 'POST':
        try:
            # Atualizar chamado
            db.session.execute("""
                UPDATE chamados_manutencao 
                SET status = ?, prioridade = ?, responsavel_id = ?,
                    diagnostico = ?, solucao = ?, observacoes_internas = ?
                WHERE id = ?
            """, (
                request.form['status'],
                request.form['prioridade'],
                request.form.get('responsavel_id') or None,
                request.form.get('diagnostico', ''),
                request.form.get('solucao', ''),
                request.form.get('observacoes_internas', ''),
                id
            ))
            
            # Adicionar ao histórico
            db.session.execute("""
                INSERT INTO historico_chamados 
                (chamado_id, usuario_id, acao, comentario, data_acao)
                VALUES (?, ?, 'atualizado', ?, ?)
            """, (id, current_user.id, 'Chamado atualizado', datetime.now()))
            
            db.session.commit()
            
            flash('Chamado atualizado com sucesso!', 'success')
            return redirect(url_for('manutencao.ver_chamado', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar chamado: {str(e)}', 'danger')
    
    # Buscar usuários para responsável
    usuarios = db.session.execute("""
        SELECT id, nome_completo FROM usuarios 
        WHERE tenant_id = ? AND ativo = 1
        ORDER BY nome_completo
    """, (current_user.tenant_id,)).fetchall()
    
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
    
    categorias = db.session.execute("""
        SELECT *, 
               (SELECT COUNT(*) FROM chamados_manutencao 
                WHERE categoria_id = categorias_manutencao.id) as total_chamados
        FROM categorias_manutencao 
        WHERE tenant_id = ?
        ORDER BY nome
    """, (current_user.tenant_id,)).fetchall()
    
    return render_template('manutencao/categorias.html',
                         title='Categorias de Manutenção',
                         categorias=categorias) 