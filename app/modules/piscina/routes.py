"""
Rotas principais do módulo Piscina
"""
from datetime import datetime, timedelta
from flask import render_template, request, flash, redirect, url_for, g
from flask_login import login_required, current_user
from app import db
from app.models import Morador
from app.forms import BuscaMoradorForm
from app.core.permissions import require_permission
from app.core.utils import format_timedelta
from app.modules.piscina import piscina_bp
from app.modules.piscina.forms import RegistroAcessoPiscinaForm
from app.modules.piscina.models import (
    RegistroAcessoPiscina,
    CarteirinhaPiscina,
    PlantaoSalvaVidas,
)


def _get_tenant_id():
    return getattr(g, 'tenant_id', 1)


@piscina_bp.route('/dashboard')
@login_required
@require_permission('piscina', 'view')
def dashboard():
    """Dashboard do módulo Piscina"""
    tenant_id = _get_tenant_id()
    
    entradas = RegistroAcessoPiscina.query.filter_by(tenant_id=tenant_id, tipo='entrada').count()
    saidas = RegistroAcessoPiscina.query.filter_by(tenant_id=tenant_id, tipo='saida').count()
    moradores_na_piscina = max(0, entradas - saidas)
    
    registros_24h = RegistroAcessoPiscina.query.filter(
        RegistroAcessoPiscina.tenant_id == tenant_id,
        RegistroAcessoPiscina.tipo == 'saida',
        RegistroAcessoPiscina.tempo_permanencia_minutos.isnot(None),
        RegistroAcessoPiscina.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    tempo_medio_minutos = 0
    if registros_24h:
        tempo_medio_minutos = sum(r.tempo_permanencia_minutos for r in registros_24h) // len(registros_24h)
    
    plantao = PlantaoSalvaVidas.plantao_ativo(tenant_id)
    
    # Dados para gráfico por hora (últimas 12h)
    horas = []
    contagem = []
    agora = datetime.utcnow()
    for i in range(12, -1, -1):
        hora_base = agora - timedelta(hours=i)
        proxima = hora_base + timedelta(hours=1)
        total_hora = RegistroAcessoPiscina.query.filter(
            RegistroAcessoPiscina.tenant_id == tenant_id,
            RegistroAcessoPiscina.timestamp >= hora_base,
            RegistroAcessoPiscina.timestamp < proxima
        ).count()
        horas.append(hora_base.strftime('%Hh'))
        contagem.append(total_hora)
    
    return render_template(
        'piscina/dashboard.html',
        title='Piscina - Dashboard',
        moradores_na_piscina=moradores_na_piscina,
        tempo_medio=format_timedelta(timedelta(minutes=tempo_medio_minutos)),
        plantao=plantao,
        horas=horas,
        contagem=contagem
    )


@piscina_bp.route('/acesso/registrar', methods=['GET', 'POST'])
@login_required
@require_permission('piscina', 'create')
def registrar_acesso():
    """Registrar entrada ou saída (interface otimizada para tablet)"""
    tenant_id = _get_tenant_id()
    form = RegistroAcessoPiscinaForm()
    busca_form = BuscaMoradorForm(request.args)
    
    # Processar registro
    if form.validate_on_submit():
        morador = Morador.query.get_or_404(int(form.morador_id.data))
        
        # Validar carteirinha
        carteirinha = CarteirinhaPiscina.query.filter_by(
            tenant_id=tenant_id,
            morador_id=morador.id,
            ativa=True
        ).order_by(CarteirinhaPiscina.data_criacao.desc()).first()
        
        if not carteirinha or not carteirinha.esta_valida:
            flash('Carteirinha inválida ou vencida.', 'danger')
            return redirect(url_for('piscina.registrar_acesso'))
        
        esta_dentro = RegistroAcessoPiscina.morador_esta_na_piscina(morador.id, tenant_id)
        if form.tipo.data == 'entrada' and esta_dentro:
            flash(f'{morador.nome_completo} já está na piscina.', 'warning')
            return redirect(url_for('piscina.registrar_acesso'))
        
        if form.tipo.data == 'saida' and not esta_dentro:
            flash(f'{morador.nome_completo} não está na piscina.', 'warning')
            return redirect(url_for('piscina.registrar_acesso'))
        
        registro = RegistroAcessoPiscina(
            tenant_id=tenant_id,
            morador_id=morador.id,
            carteirinha_id=carteirinha.id,
            salva_vidas_id=current_user.id if current_user.is_salva_vidas() else None,
            tipo=form.tipo.data,
            metodo=form.metodo.data,
            observacoes=form.observacoes.data,
            ip_origem=request.remote_addr
        )
        db.session.add(registro)
        db.session.commit()
        
        # Calcular tempo de permanência ao registrar saída
        if form.tipo.data == 'saida':
            entrada = RegistroAcessoPiscina.query.filter_by(
                tenant_id=tenant_id,
                morador_id=morador.id,
                tipo='entrada'
            ).order_by(RegistroAcessoPiscina.timestamp.desc()).first()
            RegistroAcessoPiscina.calcular_tempo_permanencia(entrada, registro)
        
        flash('Registro salvo com sucesso!', 'success')
        return redirect(url_for('piscina.registrar_acesso'))
    
    # Resultados de busca (modo servidor para fallback)
    moradores = []
    if busca_form.busca.data:
        termo = f"%{busca_form.busca.data.strip()}%"
        moradores = Morador.query.filter(
            Morador.nome_completo.ilike(termo)
        ).order_by(Morador.nome_completo).limit(10).all()
    
    return render_template(
        'piscina/registrar_acesso.html',
        title='Registrar Acesso',
        form=form,
        busca_form=busca_form,
        moradores=moradores
    )
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
from app.core.utils import get_tenant_id


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
    
    # Tempo médio de permanência (últimas 24h)
    registros_24h = RegistroAcessoPiscina.query.filter(
        RegistroAcessoPiscina.tenant_id == tenant_id,
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
        carteirinha = CarteirinhaPiscina.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id,
            ativa=True
        ).order_by(CarteirinhaPiscina.data_criacao.desc()).first()
        
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
        
        # Criar registro
        registro = RegistroAcessoPiscina(
            tenant_id=tenant_id,
            morador_id=morador_id,
            carteirinha_id=carteirinha.id,
            salva_vidas_id=current_user.id if current_user.is_salva_vidas() else None,
            tipo=tipo,
            metodo=form.metodo.data,
            observacoes=form.observacoes.data,
            ip_origem=request.remote_addr
        )
        
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
    moradores = Morador.query.filter_by(tenant_id=tenant_id).order_by(Morador.nome_completo).all()
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
    
    ocorrencias = OcorrenciaPiscina.query.filter_by(
        tenant_id=tenant_id
    ).order_by(OcorrenciaPiscina.data_ocorrencia.desc()).limit(50).all()
    
    return render_template('piscina/ocorrencias.html', ocorrencias=ocorrencias)
