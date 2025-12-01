"""
Rotas administrativas core do sistema
CRUD de Condomínio e Funcionários
"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, g
from flask_login import login_required, current_user
from app import db
from app.models import Condominio, Unidade, Usuario
from app.forms import ConfiguracaoCondominioForm
from app.core.permissions import require_permission, admin_required
from flask import g

def get_tenant_id():
    """Helper para obter tenant_id do contexto"""
    return getattr(g, 'tenant_id', 1)
from datetime import datetime

core_bp = Blueprint('core', __name__)


@core_bp.route('/admin/condominio', methods=['GET', 'POST'])
@login_required
@require_permission('admin', 'view')
def configurar_condominio():
    """Configuração do condomínio (apenas admin)"""
    tenant_id = get_tenant_id()
    
    # Buscar condomínio do tenant
    condominio = Condominio.query.filter_by(tenant_id=tenant_id).first()
    
    form = ConfiguracaoCondominioForm(obj=condominio)
    
    if form.validate_on_submit():
        if condominio:
            # Atualizar
            condominio.nome = form.nome.data
            condominio.cnpj = form.cnpj.data
            condominio.endereco = form.endereco.data
            condominio.telefone = form.telefone.data
            condominio.email_administracao = form.email_administracao.data
            condominio.email_portaria = form.email_portaria.data if hasattr(form, 'email_portaria') else None
            condominio.email_sindico = form.email_sindico.data if hasattr(form, 'email_sindico') else None
            condominio.whatsapp = form.whatsapp.data
            condominio.horario_funcionamento = form.horario_funcionamento.data
            condominio.dias_aviso_vencimento = form.dias_aviso_vencimento.data
            condominio.meses_validade_padrao = form.meses_validade_padrao.data
            condominio.permitir_dependentes = form.permitir_dependentes.data
            condominio.cor_primaria = form.cor_primaria.data
            condominio.cor_secundaria = form.cor_secundaria.data
            condominio.data_atualizacao = datetime.utcnow()
        else:
            # Criar novo
            condominio = Condominio(
                tenant_id=tenant_id,
                nome=form.nome.data,
                cnpj=form.cnpj.data,
                endereco=form.endereco.data,
                telefone=form.telefone.data,
                email_administracao=form.email_administracao.data,
                whatsapp=form.whatsapp.data,
                horario_funcionamento=form.horario_funcionamento.data,
                dias_aviso_vencimento=form.dias_aviso_vencimento.data,
                meses_validade_padrao=form.meses_validade_padrao.data,
                permitir_dependentes=form.permitir_dependentes.data,
                cor_primaria=form.cor_primaria.data,
                cor_secundaria=form.cor_secundaria.data
            )
            db.session.add(condominio)
        
        db.session.commit()
        flash('Condomínio configurado com sucesso!', 'success')
        return redirect(url_for('core.configurar_condominio'))
    
    return render_template('admin/condominio.html',
                         title='Configurações do Condomínio',
                         form=form,
                         condominio=condominio)


@core_bp.route('/admin/funcionarios')
@login_required
@require_permission('admin', 'view')
def listar_funcionarios():
    """Listar funcionários do condomínio"""
    tenant_id = get_tenant_id()
    
    funcionarios = Usuario.query.filter(
        Usuario.tenant_id == tenant_id,
        Usuario.tipo_usuario.in_(['portaria', 'funcionario', 'salva_vidas'])
    ).order_by(Usuario.nome_completo).all()
    
    return render_template('admin/funcionarios.html',
                         title='Funcionários',
                         funcionarios=funcionarios)


@core_bp.route('/admin/funcionario/novo', methods=['GET', 'POST'])
@login_required
@require_permission('admin', 'create')
def novo_funcionario():
    """Cadastrar novo funcionário"""
    from app.forms import FuncionarioForm
    
    form = FuncionarioForm()
    tenant_id = get_tenant_id()
    
    if form.validate_on_submit():
        funcionario = Usuario(
            tenant_id=tenant_id,
            tipo_usuario=form.tipo_usuario.data,
            nome_completo=form.nome_completo.data,
            email=form.email.data,
            username=form.username.data,
            cargo=form.cargo.data,
            ativo=True
        )
        funcionario.set_password(form.password.data)
        
        db.session.add(funcionario)
        db.session.commit()
        
        flash('Funcionário cadastrado com sucesso!', 'success')
        return redirect(url_for('core.listar_funcionarios'))
    
    return render_template('admin/funcionario_form.html',
                         title='Novo Funcionário',
                         form=form)


@core_bp.route('/admin/funcionario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permission('admin', 'edit')
def editar_funcionario(id):
    """Editar funcionário existente"""
    from app.forms import FuncionarioForm
    
    tenant_id = get_tenant_id()
    funcionario = Usuario.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    form = FuncionarioForm(obj=funcionario)
    
    if form.validate_on_submit():
        funcionario.tipo_usuario = form.tipo_usuario.data
        funcionario.nome_completo = form.nome_completo.data
        funcionario.email = form.email.data
        funcionario.username = form.username.data
        funcionario.cargo = form.cargo.data
        funcionario.ativo = form.ativo.data
        
        if form.password.data:
            funcionario.set_password(form.password.data)
        
        db.session.commit()
        
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('core.listar_funcionarios'))
    
    return render_template('admin/funcionario_form.html',
                         title='Editar Funcionário',
                         form=form,
                         funcionario=funcionario)

