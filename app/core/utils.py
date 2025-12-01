"""
Utilitários compartilhados do sistema
"""
from datetime import datetime, timedelta
from flask import g
from app import db


def get_tenant_id():
    """
    Retorna o tenant_id do contexto atual
    
    Returns:
        int: ID do tenant ou 1 (default)
    """
    return getattr(g, 'tenant_id', 1)


def format_timedelta(td):
    """
    Formata timedelta em formato legível
    
    Args:
        td: timedelta object
    
    Returns:
        str: String formatada (ex: "2h 30min")
    """
    if not td:
        return "0min"
    
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}min"
    return f"{minutes}min"


def format_currency(value):
    """
    Formata valor monetário
    
    Args:
        value: float ou Decimal
    
    Returns:
        str: String formatada (ex: "R$ 1.234,56")
    """
    if value is None:
        return "R$ 0,00"
    
    return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def paginate_query(query, page=1, per_page=20):
    """
    Aplica paginação a uma query
    
    Args:
        query: SQLAlchemy query
        page: Número da página
        per_page: Itens por página
    
    Returns:
        Pagination object
    """
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_or_create(model, **kwargs):
    """
    Obtém ou cria um registro
    
    Args:
        model: Classe do modelo SQLAlchemy
        **kwargs: Filtros para busca
    
    Returns:
        tuple: (instance, created)
    """
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    
    instance = model(**kwargs)
    db.session.add(instance)
    db.session.commit()
    return instance, True

