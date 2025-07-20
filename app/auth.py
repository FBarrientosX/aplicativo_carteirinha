from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.models import Usuario, SalvaVidas
from app.forms import LoginForm, CadastroUsuarioForm
from datetime import datetime

# Criar blueprint para autenticação
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('main.index'))
        else:
            return redirect(url_for('auth.salva_vidas_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Usuário ou senha inválidos', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.ativo:
            flash('Sua conta está desativada. Contate o administrador.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Atualizar último login
        user.data_ultimo_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        # Redirecionar para página solicitada ou dashboard apropriado
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.is_admin():
                next_page = url_for('main.index')
            else:
                next_page = url_for('auth.salva_vidas_dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/salva-vidas-dashboard')
@login_required
def salva_vidas_dashboard():
    """Dashboard específico para salva-vidas"""
    if current_user.is_admin():
        return redirect(url_for('main.index'))
    
    if not current_user.is_salva_vidas():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('auth.login'))
    
    from app.models import RegistroAcesso
    
    # Estatísticas para o salva-vidas
    hoje = datetime.now().date()
    
    # Moradores atualmente na piscina
    moradores_dentro = RegistroAcesso.obter_moradores_na_piscina()
    
    # Entradas de hoje
    entradas_hoje = RegistroAcesso.query.filter(
        db.func.date(RegistroAcesso.data_hora) == hoje,
        RegistroAcesso.tipo == 'entrada'
    ).count()
    
    # Últimos 10 registros
    ultimos_registros = RegistroAcesso.query.order_by(
        RegistroAcesso.data_hora.desc()
    ).limit(10).all()
    
    return render_template('auth/salva_vidas_dashboard.html',
                         title='Dashboard Salva-vidas',
                         moradores_dentro=moradores_dentro,
                         entradas_hoje=entradas_hoje,
                         ultimos_registros=ultimos_registros,
                         total_dentro=len(moradores_dentro))

@auth_bp.route('/cadastrar-usuario', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    """Cadastrar novo usuário (apenas admin)"""
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem cadastrar usuários.', 'danger')
        return redirect(url_for('main.index'))
    
    form = CadastroUsuarioForm()
    
    # Carregar opções de salva-vidas
    salva_vidas_options = [('', 'Nenhum')]
    salva_vidas_options.extend([(sv.id, sv.nome_completo) for sv in SalvaVidas.query.filter_by(status='ativo').all()])
    form.salva_vidas_id.choices = salva_vidas_options
    
    if form.validate_on_submit():
        # Verificar se username já existe
        if Usuario.query.filter_by(username=form.username.data).first():
            flash('Nome de usuário já existe. Escolha outro.', 'danger')
            return render_template('auth/cadastrar_usuario.html', form=form)
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado. Use outro email.', 'danger')
            return render_template('auth/cadastrar_usuario.html', form=form)
        
        # Criar novo usuário
        # Tratar salva_vidas_id - converter string vazia para None
        salva_vidas_id = None
        if form.salva_vidas_id.data and form.salva_vidas_id.data != '':
            try:
                salva_vidas_id = int(form.salva_vidas_id.data)
            except (ValueError, TypeError):
                salva_vidas_id = None
        
        user = Usuario(
            username=form.username.data,
            email=form.email.data,
            nome_completo=form.nome_completo.data,
            tipo_usuario=form.tipo_usuario.data,
            salva_vidas_id=salva_vidas_id,
            tenant_id=getattr(current_user, 'tenant_id', 1)  # Adicionar tenant_id
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuário {user.username} cadastrado com sucesso!', 'success')
        return redirect(url_for('auth.listar_usuarios'))
    
    return render_template('auth/cadastrar_usuario.html', title='Cadastrar Usuário', form=form)

@auth_bp.route('/usuarios')
@login_required
def listar_usuarios():
    """Listar todos os usuários (apenas admin)"""
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    # Filtrar usuários por tenant_id
    tenant_id = getattr(current_user, 'tenant_id', 1)
    usuarios = Usuario.query.filter_by(tenant_id=tenant_id).all()
    return render_template('auth/listar_usuarios.html', title='Usuários', usuarios=usuarios)

@auth_bp.route('/usuario/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_usuario_status(id):
    """Ativar/desativar usuário (apenas admin)"""
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('Você não pode desativar sua própria conta.', 'warning')
        return redirect(url_for('auth.listar_usuarios'))
    
    usuario.ativo = not usuario.ativo
    db.session.commit()
    
    status = 'ativado' if usuario.ativo else 'desativado'
    flash(f'Usuário {usuario.username} foi {status}.', 'success')
    
    return redirect(url_for('auth.listar_usuarios')) 