"""
Rotas Administrativas do CondoTech Solutions
Área exclusiva para administradores do sistema
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models import Tenant, Plano, Modulo, ModuloTenant, Usuario
from sqlalchemy import text
# from app.forms import TenantForm, ModuloTenantForm  # Formulários serão criados depois

# Blueprint administrativo
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def verificar_admin():
    """Verificar se usuário é admin do sistema"""
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Acesso negado. Área restrita para administradores.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard administrativo principal"""
    
    # Estatísticas gerais
    total_tenants = Tenant.query.count()
    total_usuarios = Usuario.query.count()
    total_modulos = Modulo.query.count()
    modulos_ativos = Modulo.query.filter_by(ativo=True).count()
    
    # Tenants mais ativos (com mais usuários)
    tenants_ativos = db.session.execute(text("""
        SELECT t.id, t.nome, COUNT(u.id) as total_usuarios
        FROM tenants t
        LEFT JOIN usuarios u ON u.tenant_id = t.id
        GROUP BY t.id, t.nome
        ORDER BY total_usuarios DESC
        LIMIT 5
    """)).fetchall()
    
    return render_template('admin/dashboard.html',
                         title='Dashboard Administrativo',
                         total_tenants=total_tenants,
                         total_usuarios=total_usuarios,
                         total_modulos=total_modulos,
                         modulos_ativos=modulos_ativos,
                         tenants_ativos=tenants_ativos)

@admin_bp.route('/tenants')
@login_required
def listar_tenants():
    """Listar todos os tenants (condomínios)"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    tenants = Tenant.query.order_by(Tenant.nome).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/tenants.html',
                         title='Gerenciar Condomínios',
                         tenants=tenants)

@admin_bp.route('/tenants/<int:tenant_id>')
@login_required
def detalhe_tenant(tenant_id):
    """Ver detalhes de um tenant específico"""
    
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Buscar módulos e status para este tenant
    modulos_tenant = db.session.execute(text("""
        SELECT m.id, m.nome, m.descricao, m.icone, m.cor, 
               COALESCE(mt.ativo, 0) as ativo
        FROM modulos m
        LEFT JOIN modulos_tenant mt ON mt.modulo_id = m.id AND mt.tenant_id = :tenant_id
        ORDER BY m.ordem, m.nome
    """), {'tenant_id': tenant_id}).fetchall()
    
    # Usuários do tenant
    usuarios = Usuario.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('admin/tenant_detalhe.html',
                         title=f'Condomínio: {tenant.nome}',
                         tenant=tenant,
                         modulos_tenant=modulos_tenant,
                         usuarios=usuarios)

@admin_bp.route('/tenants/<int:tenant_id>/modulo/<int:modulo_id>/toggle', methods=['POST'])
@login_required
def toggle_modulo_tenant(tenant_id, modulo_id):
    """Ativar/desativar módulo para um tenant"""
    
    tenant = Tenant.query.get_or_404(tenant_id)
    modulo = Modulo.query.get_or_404(modulo_id)
    
    # Verificar se já existe registro
    modulo_tenant = ModuloTenant.query.filter_by(
        tenant_id=tenant_id,
        modulo_id=modulo_id
    ).first()
    
    if modulo_tenant:
        # Alternar status
        modulo_tenant.ativo = not modulo_tenant.ativo
        action = "ativado" if modulo_tenant.ativo else "desativado"
    else:
        # Criar novo registro ativo
        modulo_tenant = ModuloTenant()
        modulo_tenant.tenant_id = tenant_id
        modulo_tenant.modulo_id = modulo_id
        modulo_tenant.ativo = True
        modulo_tenant.data_ativacao = datetime.utcnow()
        db.session.add(modulo_tenant)
        action = "ativado"
    
    try:
        db.session.commit()
        flash(f'Módulo "{modulo.nome}" {action} para {tenant.nome}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar módulo: {str(e)}', 'danger')
    
    return redirect(url_for('admin.detalhe_tenant', tenant_id=tenant_id))

@admin_bp.route('/modulos')
@login_required  
def listar_modulos():
    """Listar todos os módulos do sistema"""
    
    modulos = Modulo.query.order_by(Modulo.ordem, Modulo.nome).all()
    
    # Estatísticas de cada módulo
    modulos_com_stats = []
    for modulo in modulos:
        stats = db.session.execute(text("""
            SELECT COUNT(*) as total_tenants,
                   COUNT(CASE WHEN mt.ativo = 1 THEN 1 END) as tenants_ativos
            FROM modulos_tenant mt
            WHERE mt.modulo_id = :modulo_id
        """), {'modulo_id': modulo.id}).fetchone()
        
        modulos_com_stats.append({
            'modulo': modulo,
            'total_tenants': stats.total_tenants if stats else 0,
            'tenants_ativos': stats.tenants_ativos if stats else 0
        })
    
    return render_template('admin/modulos.html',
                         title='Gerenciar Módulos',
                         modulos_com_stats=modulos_com_stats)

# ===== ROTAS DE MÓDULOS DO SISTEMA =====

@admin_bp.route('/modulo/<int:id>/editar', methods=['POST'])
@login_required
def editar_modulo(id):
    """Editar informações de um módulo do sistema"""
    
    modulo = Modulo.query.get_or_404(id)
    
    try:
        # Atualizar informações do módulo
        modulo.nome = request.form.get('nome', modulo.nome)
        modulo.descricao = request.form.get('descricao', modulo.descricao)
        modulo.icone = request.form.get('icone', modulo.icone)
        modulo.cor = request.form.get('cor', modulo.cor)
        modulo.ordem = int(request.form.get('ordem', modulo.ordem or 1))
        modulo.versao = request.form.get('versao', modulo.versao)
        modulo.ativo = bool(request.form.get('ativo'))
        
        db.session.commit()
        flash(f'Módulo "{modulo.nome}" atualizado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar módulo: {str(e)}', 'danger')
    
    return redirect(url_for('admin.listar_modulos'))

@admin_bp.route('/modulo/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_modulo(id):
    """Ativar/desativar módulo do sistema"""
    
    modulo = Modulo.query.get_or_404(id)
    
    try:
        # Alternar status do módulo
        modulo.ativo = not modulo.ativo
        action = "ativado" if modulo.ativo else "desativado"
        
        db.session.commit()
        flash(f'Módulo "{modulo.nome}" {action} com sucesso!', 'success')
        
        # Se desativando, também desativar para todos os tenants
        if not modulo.ativo:
            db.session.execute(text("""
                UPDATE modulos_tenant 
                SET ativo = 0 
                WHERE modulo_id = :modulo_id
            """), {'modulo_id': id})
            db.session.commit()
            flash(f'Módulo também foi desativado para todos os condomínios.', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status do módulo: {str(e)}', 'danger')
    
    return redirect(url_for('admin.listar_modulos'))

@admin_bp.route('/garantir_admin_acesso')
@login_required
def garantir_admin_acesso():
    """Garantir que admin tenha acesso a todos os módulos"""
    
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Buscar tenant do admin
        admin_tenant_id = current_user.tenant_id or 1
        
        # Buscar todos os módulos
        modulos = Modulo.query.filter_by(ativo=True).all()
        
        ativacoes = 0
        for modulo in modulos:
            # Verificar se já existe
            modulo_tenant = ModuloTenant.query.filter_by(
                tenant_id=admin_tenant_id,
                modulo_id=modulo.id
            ).first()
            
            if not modulo_tenant:
                # Criar novo
                modulo_tenant = ModuloTenant()
                modulo_tenant.tenant_id = admin_tenant_id
                modulo_tenant.modulo_id = modulo.id
                modulo_tenant.ativo = True
                modulo_tenant.data_ativacao = datetime.utcnow()
                db.session.add(modulo_tenant)
                ativacoes += 1
            elif not modulo_tenant.ativo:
                # Ativar existente
                modulo_tenant.ativo = True
                ativacoes += 1
        
        db.session.commit()
        
        if ativacoes > 0:
            flash(f'✅ {ativacoes} módulo(s) ativado(s) para acesso administrativo!', 'success')
        else:
            flash('✅ Todos os módulos já estão disponíveis para você!', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao garantir acesso: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/system-info')
@login_required
def system_info():
    """Informações do sistema"""
    
    import sys
    import os
    import platform
    
    # Versões
    python_version = sys.version.split()[0]
    try:
        import flask
        flask_version = getattr(flask, '__version__', 'Unknown')
    except Exception:
        flask_version = 'N/A'
    
    try:
        import sqlalchemy
        sqlalchemy_version = getattr(sqlalchemy, '__version__', 'Unknown')
    except Exception:
        sqlalchemy_version = 'N/A'
    
    # Estatísticas
    stats = {
        'total_tenants': Tenant.query.count(),
        'total_usuarios': Usuario.query.count(),
        'total_modulos': Modulo.query.count(),
        'modulos_ativos': Modulo.query.filter_by(ativo=True).count()
    }
    
    # Configuração de email
    from app.models import ConfiguracaoSistema
    try:
        email_config = bool(
            ConfiguracaoSistema.get_valor('MAIL_SERVER') and
            ConfiguracaoSistema.get_valor('MAIL_USERNAME')
        )
    except Exception:
        email_config = False
    
    return render_template('admin/system_info.html',
                         title='Informações do Sistema',
                         python_version=python_version,
                         flask_version=flask_version,
                         sqlalchemy_version=sqlalchemy_version,
                         os_info=platform.platform(),
                         stats=stats,
                         email_config=email_config) 