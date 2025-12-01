"""
Módulo Piscina - Controle completo de acesso e métricas
"""
from flask import Blueprint

piscina_bp = Blueprint('piscina', __name__, url_prefix='/piscina')

# Importa rotas para registrar no blueprint
from app.modules.piscina import routes, api  # noqa: E402,F401
"""
Módulo de Controle de Piscina
"""
from flask import Blueprint

piscina_bp = Blueprint('piscina', __name__, url_prefix='/piscina')

from app.modules.piscina import routes
