"""Rotas para módulo de Controle de Visitantes"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app, g
from flask_login import login_required, current_user
from app import db
from app.models import Visitante, Morador, Usuario
from app.forms import VisitanteForm, FiltroVisitanteForm
from datetime import datetime, timedelta

visitantes_bp = Blueprint('visitantes', __name__, url_prefix='/visitantes')

@visitantes_bp.route('/')
@login_required
def listar_visitantes():
    """Lista todos os visitantes"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = FiltroVisitanteForm(request.args)
    
    try:
        # Query base
        query = Visitante.query.filter_by(tenant_id=tenant_id)
        
        # Aplicar filtros
        if form.tipo.data:
            query = query.filter_by(tipo=form.tipo.data)
        
        if form.status.data:
            query = query.filter_by(status=form.status.data)
        
        if form.morador_id.data:
            query = query.filter_by(morador_id=form.morador_id.data)
        
        if form.busca.data:
            query = query.filter(
                Visitante.nome_completo.contains(form.busca.data)
            )
        
        # Configurar choices do formulário
        moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
        form.morador_id.choices = [('', 'Todos')] + [(m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}") for m in moradores]
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        visitantes = query.order_by(Visitante.data_entrada.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Estatísticas
        visitantes_dentro = Visitante.query.filter_by(
            tenant_id=tenant_id,
            status='em_visita'
        ).count()
        
        visitantes_hoje = Visitante.query.filter_by(tenant_id=tenant_id).filter(
            db.func.date(Visitante.data_entrada) == datetime.now().date()
        ).count()
        
        stats = {
            'total': visitantes.total,
            'dentro': visitantes_dentro,
            'hoje': visitantes_hoje
        }
    except Exception as e:
        # Se a tabela não existe, mostrar mensagem amigável
        if 'no such table: visitantes' in str(e).lower():
            flash('A tabela de visitantes ainda não foi criada. Por favor, execute a migration do banco de dados.', 'warning')
            current_app.logger.error(f'Tabela visitantes não existe: {e}')
            # Criar objeto paginação vazio
            from flask_sqlalchemy import Pagination
            visitantes = Pagination(query=None, page=1, per_page=20, total=0, items=[])
            stats = {
                'total': 0,
                'dentro': 0,
                'hoje': 0
            }
            moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
            form.morador_id.choices = [('', 'Todos')] + [(m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}") for m in moradores]
        else:
            raise
    
    return render_template('visitantes/listar.html',
                         title='Controle de Visitantes',
                         visitantes=visitantes,
                         form=form,
                         stats=stats)


@visitantes_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_visitante():
    """Registrar novo visitante"""
    tenant_id = getattr(g, 'tenant_id', 1)
    form = VisitanteForm()
    
    # Configurar choices
    moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
    form.morador_id.choices = [(m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}") for m in moradores]
    
    if form.validate_on_submit():
        try:
            visitante = Visitante(
                tenant_id=tenant_id,
                nome_completo=form.nome_completo.data,
                documento=form.documento.data,
                tipo_documento=form.tipo_documento.data,
                telefone=form.telefone.data,
                veiculo_placa=form.veiculo_placa.data,
                veiculo_modelo=form.veiculo_modelo.data,
                tipo=form.tipo.data,
                empresa=form.empresa.data,
                morador_id=form.morador_id.data,
                apartamento_destino=form.apartamento_destino.data,
                data_saida_prevista=datetime.combine(form.data_saida_prevista.data, datetime.min.time()) if form.data_saida_prevista.data else None,
                observacoes=form.observacoes.data,
                entrada_autorizada=True,
                autorizado_por=current_user.id
            )
            
            db.session.add(visitante)
            db.session.commit()
            
            flash(f'Visitante {visitante.nome_completo} registrado com sucesso!', 'success')
            return redirect(url_for('visitantes.listar_visitantes'))
        except Exception as e:
            if 'no such table: visitantes' in str(e).lower():
                flash('A tabela de visitantes ainda não foi criada. Por favor, execute a migration do banco de dados.', 'warning')
                current_app.logger.error(f'Tabela visitantes não existe: {e}')
            else:
                flash(f'Erro ao registrar visitante: {str(e)}', 'danger')
                current_app.logger.error(f'Erro ao registrar visitante: {e}', exc_info=True)
    
    return render_template('visitantes/form.html',
                         title='Registrar Visitante',
                         form=form)


@visitantes_bp.route('/<int:id>')
@login_required
def ver_visitante(id):
    """Ver detalhes do visitante"""
    tenant_id = getattr(g, 'tenant_id', 1)
    
    try:
        visitante = Visitante.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    except Exception as e:
        if 'no such table: visitantes' in str(e).lower():
            flash('A tabela de visitantes ainda não foi criada. Por favor, execute a migration do banco de dados.', 'warning')
            current_app.logger.error(f'Tabela visitantes não existe: {e}')
            return redirect(url_for('visitantes.listar_visitantes'))
        else:
            raise
    
    return render_template('visitantes/detalhes.html',
                         title=f'Visitante: {visitante.nome_completo}',
                         visitante=visitante)


@visitantes_bp.route('/<int:id>/registrar-saida', methods=['POST'])
@login_required
def registrar_saida(id):
    """Registrar saída do visitante"""
    tenant_id = getattr(g, 'tenant_id', 1)
    
    try:
        visitante = Visitante.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    except Exception as e:
        if 'no such table: visitantes' in str(e).lower():
            flash('A tabela de visitantes ainda não foi criada. Por favor, execute a migration do banco de dados.', 'warning')
            current_app.logger.error(f'Tabela visitantes não existe: {e}')
            return redirect(url_for('visitantes.listar_visitantes'))
        else:
            raise
    
    if visitante.status != 'em_visita':
        flash('Visitante já saiu do condomínio!', 'warning')
        return redirect(url_for('visitantes.ver_visitante', id=id))
    
    visitante.status = 'saiu'
    visitante.data_saida_real = datetime.utcnow()
    visitante.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Saída de {visitante.nome_completo} registrada com sucesso!', 'success')
    return redirect(url_for('visitantes.listar_visitantes'))


@visitantes_bp.route('/visitantes-no-condominio')
@login_required
def visitantes_dentro():
    """Lista visitantes atualmente no condomínio"""
    tenant_id = getattr(g, 'tenant_id', 1)
    
    try:
        visitantes = Visitante.query.filter_by(
            tenant_id=tenant_id,
            status='em_visita'
        ).order_by(Visitante.data_entrada).all()
    except Exception as e:
        if 'no such table: visitantes' in str(e).lower():
            current_app.logger.error(f'Tabela visitantes não existe: {e}')
            visitantes = []
        else:
            raise
    
    return render_template('visitantes/dentro.html',
                         title='Visitantes no Condomínio',
                         visitantes=visitantes,
                         total=len(visitantes))

