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
@login_required
def dashboard():
    """Dashboard administrativo"""
    
    # Estatísticas gerais do sistema
    total_tenants = Tenant.query.count()
    tenants_ativos = Tenant.query.filter_by(status='ativo').count()
    total_usuarios = Usuario.query.count()
    total_modulos = Modulo.query.count()
    
    # Tenants recentes
    tenants_recentes = Tenant.query.order_by(Tenant.data_criacao.desc()).limit(5).all()
    
    # Módulos e suas ativações
    modulos_stats = db.session.execute(text("""
        SELECT m.nome, m.slug, COUNT(mt.id) as total_ativacoes,
               COUNT(CASE WHEN mt.ativo = 1 THEN 1 END) as ativacoes_ativas
        FROM modulos m
        LEFT JOIN modulos_tenant mt ON mt.modulo_id = m.id
        GROUP BY m.id, m.nome, m.slug
        ORDER BY total_ativacoes DESC
    """)).fetchall()
    
    return render_template('admin/dashboard.html',
                         title='Administração do Sistema',
                         total_tenants=total_tenants,
                         tenants_ativos=tenants_ativos,
                         total_usuarios=total_usuarios,
                         total_modulos=total_modulos,
                         tenants_recentes=tenants_recentes,
                         modulos_stats=modulos_stats)

@admin_bp.route('/tenants')
@login_required
def listar_tenants():
    """Listar todos os tenants"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    tenants = Tenant.query.order_by(Tenant.data_criacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/tenants.html',
                         title='Gerenciar Condomínios',
                         tenants=tenants)

@admin_bp.route('/tenants/<int:tenant_id>')
@login_required
def detalhe_tenant(tenant_id):
    """Detalhes de um tenant específico"""
    
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Módulos do tenant
    modulos_tenant = db.session.execute(text("""
        SELECT m.id, m.nome, m.slug, m.descricao, m.icone, m.cor,
               mt.ativo, mt.data_ativacao, mt.id as modulo_tenant_id
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
    """Ativar/desativar módulo para tenant"""
    
    tenant = Tenant.query.get_or_404(tenant_id)
    modulo = Modulo.query.get_or_404(modulo_id)
    
    # Verificar se já existe registro
    modulo_tenant = ModuloTenant.query.filter_by(
        tenant_id=tenant_id, 
        modulo_id=modulo_id
    ).first()
    
    if modulo_tenant:
        # Toggle status
        modulo_tenant.ativo = not modulo_tenant.ativo
        if modulo_tenant.ativo:
            modulo_tenant.data_ativacao = datetime.now()
        action = 'ativado' if modulo_tenant.ativo else 'desativado'
    else:
        # Criar novo registro ativo
        modulo_tenant = ModuloTenant()
        modulo_tenant.tenant_id = tenant_id
        modulo_tenant.modulo_id = modulo_id
        modulo_tenant.ativo = True
        modulo_tenant.data_ativacao = datetime.now()
        db.session.add(modulo_tenant)
        action = 'ativado'
    
    db.session.commit()
    
    flash(f'Módulo "{modulo.nome}" {action} para {tenant.nome}!', 'success')
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
                # Criar nova ativação
                modulo_tenant = ModuloTenant()
                modulo_tenant.tenant_id = admin_tenant_id
                modulo_tenant.modulo_id = modulo.id
                modulo_tenant.ativo = True
                modulo_tenant.data_ativacao = datetime.now()
                db.session.add(modulo_tenant)
                ativacoes += 1
            elif not modulo_tenant.ativo:
                # Ativar existente
                modulo_tenant.ativo = True
                modulo_tenant.data_ativacao = datetime.now()
                ativacoes += 1
        
        db.session.commit()
        
        if ativacoes > 0:
            flash(f'✅ {ativacoes} módulos ativados para admin!', 'success')
        else:
            flash('✅ Admin já tem acesso a todos os módulos!', 'info')
            
    except Exception as e:
        flash(f'Erro: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/system/info')
@login_required
def system_info():
    """Informações do sistema"""
    
    # Informações detalhadas do banco
    info_sistema = {}
    info_sistema['tenants'] = Tenant.query.count()
    info_sistema['usuarios'] = Usuario.query.count()
    info_sistema['modulos'] = Modulo.query.count()
    info_sistema['planos'] = Plano.query.count()
    info_sistema['ativacoes_modulos'] = ModuloTenant.query.filter_by(ativo=True).count()
    
    # Verificar estrutura do banco
    try:
        tabelas = db.session.execute(text("SHOW TABLES")).fetchall()
        info_sistema['tabelas'] = [t[0] for t in tabelas]
    except:
        info_sistema['tabelas'] = []
    
    return render_template('admin/system_info.html',
                         title='Informações do Sistema',
                         info_sistema=info_sistema) 