"""
Rotas do Módulo Piscina
"""
from flask import render_template, flash, redirect, url_for, request, jsonify, g
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, and_, exists
from app import db
from app.models import Morador
from app.modules.piscina import piscina_bp
from app.modules.piscina.models import (
    CarteirinhaPiscina, RegistroAcessoPiscina, 
    OcorrenciaPiscina, PlantaoSalvaVidas
)
from app.modules.piscina.forms import RegistroAcessoForm, OcorrenciaPiscinaForm
from app.core.permissions import require_permission


def get_tenant_id_safe():
    """Helper para obter tenant_id"""
    return getattr(g, 'tenant_id', 1)


@piscina_bp.route('/')
@piscina_bp.route('/dashboard')
@login_required
@require_permission('piscina', 'view')
def dashboard():
    """Dashboard do módulo Piscina"""
    tenant_id = get_tenant_id_safe()
    
    # Contador de pessoas atuais
    moradores_na_piscina = RegistroAcessoPiscina.obter_moradores_na_piscina(tenant_id)
    total_na_piscina = len(moradores_na_piscina)
    
    # Verificar se tenant_id existe na tabela registros_acesso_piscina
    from sqlalchemy import inspect
    try:
        conn = db.session.bind
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        if 'registros_acesso_piscina' in tables:
            columns = [col['name'] for col in inspector.get_columns('registros_acesso_piscina')]
            has_tenant_id_registro = 'tenant_id' in columns
        else:
            has_tenant_id_registro = False
    except Exception:
        has_tenant_id_registro = False
    
    # Tempo médio de permanência (últimas 24h)
    if has_tenant_id_registro:
        registros_24h = RegistroAcessoPiscina.query.filter(
            RegistroAcessoPiscina.tenant_id == tenant_id,
            RegistroAcessoPiscina.tipo == 'saida',
            RegistroAcessoPiscina.timestamp >= datetime.utcnow() - timedelta(hours=24),
            RegistroAcessoPiscina.tempo_permanencia_minutos.isnot(None)
        ).all()
    else:
        registros_24h = RegistroAcessoPiscina.query.filter(
            RegistroAcessoPiscina.tipo == 'saida',
            RegistroAcessoPiscina.timestamp >= datetime.utcnow() - timedelta(hours=24),
            RegistroAcessoPiscina.tempo_permanencia_minutos.isnot(None)
        ).all()
    
    tempo_medio = 0
    if registros_24h:
        tempo_medio = sum(r.tempo_permanencia_minutos for r in registros_24h) / len(registros_24h)
    
    # Salva-vidas de plantão
    plantao = PlantaoSalvaVidas.obter_plantao_ativo(tenant_id)
    
    # Dados para gráfico (pessoas por hora - hoje)
    dados_grafico = obter_dados_grafico_por_hora(tenant_id)
    
    return render_template('piscina/dashboard.html',
                         moradores_na_piscina=total_na_piscina,
                         tempo_medio_minutos=int(tempo_medio),
                         plantao=plantao,
                         dados_grafico=dados_grafico,
                         lista_moradores=moradores_na_piscina)


def obter_dados_grafico_por_hora(tenant_id, data=None):
    """Retorna dados para gráfico de pessoas por hora"""
    if not data:
        data = datetime.now().date()
    
    # Agrupar por hora
    registros = db.session.query(
        func.extract('hour', RegistroAcessoPiscina.timestamp).label('hora'),
        RegistroAcessoPiscina.tipo,
        func.count(RegistroAcessoPiscina.id).label('quantidade')
    ).filter(
        RegistroAcessoPiscina.tenant_id == tenant_id,
        func.date(RegistroAcessoPiscina.timestamp) == data
    ).group_by(
        'hora', 'tipo'
    ).all()
    
    # Processar dados
    horas = list(range(24))
    dados = {h: 0 for h in horas}
    
    for registro in registros:
        hora = int(registro.hora)
        if registro.tipo == 'entrada':
            dados[hora] += registro.quantidade
        else:
            dados[hora] -= registro.quantidade
    
    # Calcular acumulado
    acumulado = 0
    resultado = []
    for h in horas:
        acumulado += dados[h]
        resultado.append({'hora': h, 'pessoas': max(0, acumulado)})
    
    return resultado


@piscina_bp.route('/api/contador-pessoas')
@login_required
@require_permission('piscina', 'view')
def api_contador_pessoas():
    """API para atualizar contador de pessoas em tempo real"""
    tenant_id = get_tenant_id_safe()
    moradores = RegistroAcessoPiscina.obter_moradores_na_piscina(tenant_id)
    
    return jsonify({
        'contador': len(moradores),
        'timestamp': datetime.utcnow().isoformat()
    })


@piscina_bp.route('/registrar-acesso', methods=['GET', 'POST'])
@login_required
@require_permission('piscina', 'create')
def registrar_acesso():
    """Registro de acesso otimizado para tablet"""
    tenant_id = get_tenant_id_safe()
    form = RegistroAcessoForm()
    
    if form.validate_on_submit():
        morador_id = int(form.morador_id.data)
        tipo = form.tipo.data
        
        # Verificar carteirinha válida
        morador = Morador.query.get_or_404(morador_id)
        
        # Verificar se a tabela carteirinhas_piscina existe
        from sqlalchemy import inspect
        try:
            conn = db.session.bind
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            if 'carteirinhas_piscina' not in tables:
                flash('Sistema de carteirinhas não configurado ainda!', 'warning')
                return render_template('piscina/registrar_acesso.html', form=form)
            
            columns = [col['name'] for col in inspector.get_columns('carteirinhas_piscina')]
            has_tenant_id = 'tenant_id' in columns
        except Exception:
            has_tenant_id = False
        
        try:
            if has_tenant_id:
                carteirinha = CarteirinhaPiscina.query.filter_by(
                    morador_id=morador_id,
                    tenant_id=tenant_id,
                    ativa=True
                ).order_by(CarteirinhaPiscina.data_criacao.desc()).first()
            else:
                carteirinha = CarteirinhaPiscina.query.filter_by(
                    morador_id=morador_id,
                    ativa=True
                ).order_by(CarteirinhaPiscina.data_criacao.desc()).first()
        except Exception:
            flash('Erro ao verificar carteirinha!', 'danger')
            return render_template('piscina/registrar_acesso.html', form=form)
        
        if not carteirinha or not carteirinha.esta_valida:
            flash('Carteirinha inválida ou vencida!', 'danger')
            return render_template('piscina/registrar_acesso.html', form=form)
        
        # Verificar se já está dentro (para entrada) ou fora (para saída)
        esta_dentro = RegistroAcessoPiscina.morador_esta_na_piscina(morador_id, tenant_id)
        
        if tipo == 'entrada' and esta_dentro:
            flash(f'{morador.nome_completo} já está na piscina!', 'warning')
            return render_template('piscina/registrar_acesso.html', form=form)
        
        if tipo == 'saida' and not esta_dentro:
            flash(f'{morador.nome_completo} não está na piscina!', 'warning')
            return render_template('piscina/registrar_acesso.html', form=form)
        
        # Verificar se tenant_id existe na tabela registros_acesso_piscina
        from sqlalchemy import inspect
        try:
            conn = db.session.bind
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            if 'registros_acesso_piscina' in tables:
                columns = [col['name'] for col in inspector.get_columns('registros_acesso_piscina')]
                has_tenant_id_registro = 'tenant_id' in columns
            else:
                has_tenant_id_registro = False
        except Exception:
            has_tenant_id_registro = False
        
        # Criar registro
        registro_data = {
            'morador_id': morador_id,
            'carteirinha_id': carteirinha.id,
            'salva_vidas_id': current_user.id if current_user.is_salva_vidas() else None,
            'tipo': tipo,
            'metodo': form.metodo.data,
            'observacoes': form.observacoes.data,
            'ip_origem': request.remote_addr
        }
        # Só adicionar tenant_id se a coluna existir
        if has_tenant_id_registro:
            registro_data['tenant_id'] = tenant_id
        
        registro = RegistroAcessoPiscina(**registro_data)
        
        # Se for saída, calcular tempo de permanência
        if tipo == 'saida':
            entrada = RegistroAcessoPiscina.query.filter_by(
                morador_id=morador_id,
                tipo='entrada',
                tenant_id=tenant_id
            ).order_by(RegistroAcessoPiscina.timestamp.desc()).first()
            
            if entrada:
                db.session.add(registro)
                db.session.flush()  # Para obter o ID
                RegistroAcessoPiscina.calcular_tempo_permanencia(
                    morador_id, entrada.id, registro.id, tenant_id
                )
        else:
            db.session.add(registro)
        
        db.session.commit()
        
        flash(f'✅ {morador.nome_completo} {tipo} piscina!', 'success')
        return redirect(url_for('piscina.registrar_acesso'))
    
    return render_template('piscina/registrar_acesso.html', form=form)


@piscina_bp.route('/plantao/iniciar', methods=['POST'])
@login_required
@require_permission('piscina', 'create')
def iniciar_plantao():
    """Inicia plantão do salva-vidas"""
    if not current_user.is_salva_vidas():
        flash('Apenas salva-vidas podem iniciar plantão!', 'danger')
        return redirect(url_for('piscina.dashboard'))
    
    tenant_id = get_tenant_id_safe()
    
    # Verificar se já existe plantão ativo
    plantao_ativo = PlantaoSalvaVidas.obter_plantao_ativo(tenant_id)
    if plantao_ativo:
        flash('Já existe um plantão ativo!', 'warning')
        return redirect(url_for('piscina.dashboard'))
    
    # Criar novo plantão
    plantao = PlantaoSalvaVidas(
        tenant_id=tenant_id,
        salva_vidas_id=current_user.id,
        status='ativo'
    )
    db.session.add(plantao)
    db.session.commit()
    
    flash('Plantão iniciado com sucesso!', 'success')
    return redirect(url_for('piscina.dashboard'))


@piscina_bp.route('/plantao/finalizar', methods=['POST'])
@login_required
def finalizar_plantao():
    """Finaliza plantão do salva-vidas"""
    tenant_id = get_tenant_id_safe()
    plantao = PlantaoSalvaVidas.obter_plantao_ativo(tenant_id)
    
    if not plantao or plantao.salva_vidas_id != current_user.id:
        flash('Você não tem um plantão ativo!', 'danger')
        return redirect(url_for('piscina.dashboard'))
    
    plantao.finalizar()
    flash('Plantão finalizado com sucesso!', 'success')
    return redirect(url_for('piscina.dashboard'))


@piscina_bp.route('/ocorrencia/nova', methods=['GET', 'POST'])
@login_required
@require_permission('piscina', 'create')
def nova_ocorrencia():
    """Registrar nova ocorrência (apenas salva-vidas)"""
    if not current_user.is_salva_vidas():
        flash('Apenas salva-vidas podem registrar ocorrências!', 'danger')
        return redirect(url_for('piscina.dashboard'))
    
    tenant_id = get_tenant_id_safe()
    form = OcorrenciaPiscinaForm()
    
    # Carregar moradores para o select
    # Verificar se tenant_id existe na tabela moradores
    from sqlalchemy import inspect
    try:
        conn = db.session.bind
        inspector = inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('moradores')]
        has_tenant_id = 'tenant_id' in columns
    except Exception:
        has_tenant_id = False
    
    if has_tenant_id:
        moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
    else:
        moradores = Morador.query.order_by(Morador.nome_completo).all()
    form.morador_id.choices = [('', 'Nenhum')] + [(str(m.id), m.nome_completo) for m in moradores]
    
    if form.validate_on_submit():
        ocorrencia = OcorrenciaPiscina(
            tenant_id=tenant_id,
            salva_vidas_id=current_user.id,
            morador_id=form.morador_id.data if form.morador_id.data else None,
            tipo=form.tipo.data,
            severidade=form.severidade.data,
            titulo=form.titulo.data,
            descricao=form.descricao.data,
            fotos=[]  # TODO: Implementar upload de fotos
        )
        
        db.session.add(ocorrencia)
        db.session.commit()
        
        flash('Ocorrência registrada com sucesso!', 'success')
        return redirect(url_for('piscina.listar_ocorrencias'))
    
    return render_template('piscina/ocorrencia_form.html', form=form)


@piscina_bp.route('/ocorrencias')
@login_required
@require_permission('piscina', 'view')
def listar_ocorrencias():
    """Listar ocorrências"""
    tenant_id = get_tenant_id_safe()
    
    # Verificar se a tabela ocorrencias_piscina existe
    from sqlalchemy import inspect
    try:
        conn = db.session.bind
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        if 'ocorrencias_piscina' not in tables:
            # Tabela não existe, retornar lista vazia
            ocorrencias = []
        else:
            columns = [col['name'] for col in inspector.get_columns('ocorrencias_piscina')]
            has_tenant_id_ocorrencia = 'tenant_id' in columns
            
            if has_tenant_id_ocorrencia:
                ocorrencias = OcorrenciaPiscina.query.filter_by(
                    tenant_id=tenant_id
                ).order_by(OcorrenciaPiscina.data_ocorrencia.desc()).limit(50).all()
            else:
                ocorrencias = OcorrenciaPiscina.query.order_by(OcorrenciaPiscina.data_ocorrencia.desc()).limit(50).all()
    except Exception:
        # Se houver erro, retornar lista vazia
        ocorrencias = []
    
    return render_template('piscina/ocorrencias.html', ocorrencias=ocorrencias)
