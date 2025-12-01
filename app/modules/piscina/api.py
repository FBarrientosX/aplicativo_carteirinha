"""
Endpoints auxiliares (AJAX) para o módulo Piscina
Compatível com PythonAnywhere (sem WebSockets)
"""
from flask import jsonify, g, request
from flask_login import login_required
from app.modules.piscina import piscina_bp
from app.modules.piscina.models import RegistroAcessoPiscina, PlantaoSalvaVidas


def _get_tenant_id():
    return getattr(g, 'tenant_id', 1)


@piscina_bp.route('/api/contador-atual')
@login_required
def api_contador_atual():
    """Retorna número de pessoas na piscina (para atualizações via fetch)"""
    tenant_id = _get_tenant_id()
    entradas = RegistroAcessoPiscina.query.filter_by(tenant_id=tenant_id, tipo='entrada').count()
    saidas = RegistroAcessoPiscina.query.filter_by(tenant_id=tenant_id, tipo='saida').count()
    total = max(0, entradas - saidas)
    
    plantao = PlantaoSalvaVidas.plantao_ativo(tenant_id)
    
    return jsonify({
        'total': total,
        'plantao': plantao.salva_vidas.nome_completo if plantao else None
    })


@piscina_bp.route('/api/buscar-moradores')
@login_required
def api_buscar_moradores():
    """Busca moradores por nome/bloco apto (para autocomplete)"""
    from app.models import Morador
    
    termo = request.args.get('q', '').strip()
    if not termo:
        return jsonify([])
    
    like = f"%{termo}%"
    moradores = Morador.query.filter(
        (Morador.nome_completo.ilike(like)) |
        (Morador.bloco.ilike(like)) |
        (Morador.apartamento.ilike(like))
    ).order_by(Morador.nome_completo).limit(10).all()
    
    return jsonify([
        {
            'id': morador.id,
            'nome': morador.nome_completo,
            'bloco': morador.bloco,
            'apartamento': morador.apartamento
        }
        for morador in moradores
    ])

