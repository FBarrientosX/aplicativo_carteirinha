from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
from app import db
from app.models import Morador, RegistroAcesso
from app.forms import BuscaMoradorForm
from datetime import datetime
import json
import traceback

# Blueprint para funcionalidades específicas de salva-vidas
salva_vidas_bp = Blueprint('salva_vidas', __name__)

@salva_vidas_bp.route('/qr-scanner')
@login_required
def qr_scanner():
    """Interface principal para leitura de QR Code"""
    if not current_user.is_salva_vidas():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = BuscaMoradorForm()
    return render_template('salva_vidas/qr_scanner.html', 
                         title='Leitor QR Code', 
                         form=form)

@salva_vidas_bp.route('/processar-qr', methods=['POST'])
@login_required
def processar_qr():
    """Processar QR Code lido"""
    if not current_user.is_salva_vidas():
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        codigo_qr = data.get('codigo_qr', '').strip()
        
        if not codigo_qr:
            return jsonify({'error': 'Código QR não fornecido'}), 400
        
        morador = None
        erro = None
        
        # Primeiro, tentar como ID direto (mais comum)
        try:
            morador_id = int(codigo_qr)
            tenant_id = getattr(g, 'tenant_id', 1)
            morador = Morador.query.filter_by(
                id=morador_id,
                tenant_id=tenant_id
            ).first()
            if not morador:
                erro = "Morador não encontrado neste condomínio"
        except ValueError:
            # Se não for um número, tentar decodificar como JSON
            try:
                dados_qr = json.loads(codigo_qr)
                if isinstance(dados_qr, dict):
                    morador_id = dados_qr.get('id')
                    
                    if morador_id:
                        morador = Morador.query.get(morador_id)
                        if not morador:
                            erro = "Morador não encontrado no sistema"
                    else:
                        erro = "QR Code inválido - ID não encontrado"
                else:
                    erro = "Formato de QR Code inválido"
                    
            except (json.JSONDecodeError, TypeError):
                erro = "Código QR inválido"
        
        if morador:
            # Verificar status da carteirinha
            status_carteirinha = morador.status_carteirinha
            
            # Verificar se está na piscina
            esta_dentro = RegistroAcesso.morador_esta_na_piscina(morador.id)
            
            return jsonify({
                'success': True,
                'morador': {
                    'id': morador.id,
                    'nome': morador.nome_completo,
                    'bloco': morador.bloco,
                    'apartamento': morador.apartamento,
                    'status_carteirinha': status_carteirinha,
                    'data_vencimento': morador.data_vencimento.strftime('%d/%m/%Y') if morador.data_vencimento else None,
                    'esta_dentro': esta_dentro,
                    'carteirinha_valida': status_carteirinha == 'regular'
                }
            })
        else:
            return jsonify({'error': erro or 'Morador não encontrado'}), 400
            
    except Exception as e:
        # Log detalhado do erro
        error_details = traceback.format_exc()
        print(f"ERRO NO PROCESSAR QR: {error_details}")
        
        return jsonify({
            'error': f'Erro interno do servidor: {str(e)}',
            'details': error_details
        }), 500

@salva_vidas_bp.route('/registrar-acesso/<int:morador_id>/<tipo>')
@login_required
def registrar_acesso(morador_id, tipo):
    """Registrar entrada/saída via QR Code"""
    if not current_user.is_salva_vidas():
        return jsonify({'error': 'Acesso negado'}), 403
    
    if tipo not in ['entrada', 'saida']:
        return jsonify({'error': 'Tipo de acesso inválido'}), 400
    
    morador = Morador.query.get_or_404(morador_id)
    
    # Verificar se o morador está atualmente na piscina
    esta_dentro = RegistroAcesso.morador_esta_na_piscina(morador.id)
    
    # Validar tipo de registro
    if tipo == 'entrada' and esta_dentro:
        return jsonify({'error': f'{morador.nome_completo} já está na piscina!'}), 400
    
    if tipo == 'saida' and not esta_dentro:
        return jsonify({'error': f'{morador.nome_completo} não está na piscina!'}), 400
    
    # Verificar se a carteirinha está válida para entrada
    if tipo == 'entrada' and morador.status_carteirinha != 'regular':
        status_msg = {
            'a_vencer': 'Carteirinha vence em breve',
            'vencida': 'Carteirinha vencida',
            'sem_carteirinha': 'Sem carteirinha válida'
        }
        return jsonify({
            'warning': True,
            'message': f'⚠️ {status_msg.get(morador.status_carteirinha, "Carteirinha irregular")}',
            'morador': morador.nome_completo,
            'status': morador.status_carteirinha
        }), 200
    
    # Criar registro de acesso
    tenant_id = getattr(g, 'tenant_id', 1)
    registro = RegistroAcesso(
        morador_id=morador.id,
        tipo=tipo,
        metodo='qr_code',
        guardiao=current_user.nome_completo,
        observacoes=f'Registrado por {current_user.nome_completo} via QR Code',
        ip_origem=request.remote_addr,
        tenant_id=tenant_id
    )
    
    db.session.add(registro)
    db.session.commit()
    
    acao = 'entrou na' if tipo == 'entrada' else 'saiu da'
    
    return jsonify({
        'success': True,
        'message': f'✅ {morador.nome_completo} {acao} piscina às {registro.data_hora.strftime("%H:%M")}',
        'registro': {
            'id': registro.id,
            'morador': morador.nome_completo,
            'tipo': tipo,
            'horario': registro.data_hora.strftime('%H:%M'),
            'data': registro.data_hora.strftime('%d/%m/%Y')
        }
    })

@salva_vidas_bp.route('/buscar-morador', methods=['POST'])
@login_required
def buscar_morador():
    """Buscar morador por nome ou ID"""
    if not current_user.is_salva_vidas():
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    termo_busca = data.get('termo', '').strip()
    
    if not termo_busca:
        return jsonify({'error': 'Termo de busca não fornecido'}), 400
    
    try:
        # Tentar buscar por ID primeiro
        try:
            morador_id = int(termo_busca)
            morador = Morador.query.get(morador_id)
            if morador:
                return jsonify({
                    'success': True,
                    'moradores': [{
                        'id': morador.id,
                        'nome': morador.nome_completo,
                        'bloco': morador.bloco,
                        'apartamento': morador.apartamento,
                        'status_carteirinha': morador.status_carteirinha,
                        'esta_dentro': RegistroAcesso.morador_esta_na_piscina(morador.id)
                    }]
                })
        except ValueError:
            pass
        
        # Buscar por nome no tenant atual
        tenant_id = getattr(g, 'tenant_id', 1)
        moradores = Morador.query.filter(
            Morador.nome_completo.ilike(f"%{termo_busca}%"),
            Morador.tenant_id == tenant_id
        ).limit(10).all()
        
        if not moradores:
            return jsonify({'error': 'Nenhum morador encontrado'}), 404
        
        resultado = []
        for morador in moradores:
            resultado.append({
                'id': morador.id,
                'nome': morador.nome_completo,
                'bloco': morador.bloco,
                'apartamento': morador.apartamento,
                'status_carteirinha': morador.status_carteirinha,
                'esta_dentro': RegistroAcesso.morador_esta_na_piscina(morador.id)
            })
        
        return jsonify({
            'success': True,
            'moradores': resultado
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro na busca: {str(e)}'}), 500

@salva_vidas_bp.route('/historico-acesso')
@login_required
def historico_acesso():
    """Histórico de acessos (últimos registros)"""
    if not current_user.is_salva_vidas():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Últimos 50 registros do tenant atual
    tenant_id = getattr(g, 'tenant_id', 1)
    registros = RegistroAcesso.query.filter_by(
        tenant_id=tenant_id
    ).order_by(
        RegistroAcesso.data_hora.desc()
    ).limit(50).all()
    
    return render_template('salva_vidas/historico_acesso.html',
                         title='Histórico de Acessos',
                         registros=registros)

@salva_vidas_bp.route('/moradores-dentro')
@login_required
def moradores_dentro():
    """Lista de moradores atualmente na piscina"""
    if not current_user.is_salva_vidas():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('auth.login'))
    
    moradores_dentro = RegistroAcesso.obter_moradores_na_piscina()
    
    return render_template('salva_vidas/moradores_dentro.html',
                         title='Moradores na Piscina',
                         moradores_dentro=moradores_dentro) 