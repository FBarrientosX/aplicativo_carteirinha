"""
Aplicativo CondoTech Solutions
Sistema SaaS multi-tenant para gestão de condomínios
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from app.config import Config
import logging
from logging.handlers import RotatingFileHandler

# Instâncias dos plugins
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    """Factory function para criar a aplicação Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar plugins
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    
    # Configurar login
    login.login_view = 'auth.login'
    login.login_message = 'Faça login para acessar esta página.'
    login.login_message_category = 'info'
    
    # Configurar logging se não estivermos em debug
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/condotech.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CondoTech Solutions startup')
    
    print("Flask app criado")

    # Importar modelos para que sejam conhecidos pelo Alembic
    from app import models
    from app.modules.piscina import models as piscina_models
    print("Modelos importados")

    # Registrar blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.salva_vidas_routes import salva_vidas_bp
    app.register_blueprint(salva_vidas_bp, url_prefix='/salva-vidas')
    
    from app.manutencao_routes import manutencao_bp
    app.register_blueprint(manutencao_bp)
    
    # NOVO: Blueprint administrativo
    from app.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    
    # Blueprint core (condomínio, funcionários)
    from app.core.routes import core_bp
    app.register_blueprint(core_bp)
    
    # Blueprint módulo Piscina (novo)
    from app.modules.piscina import piscina_bp
    app.register_blueprint(piscina_bp)
    
    # Blueprint módulo Piscina
    from app.modules.piscina import piscina_bp
    app.register_blueprint(piscina_bp)
    
    # Blueprint módulo Piscina
    from app.modules.piscina import piscina_bp
    app.register_blueprint(piscina_bp)
    
    # NOVO: Blueprint financeiro
    from app.financeiro_routes import financeiro_bp
    app.register_blueprint(financeiro_bp)
    
    # NOVO: Blueprints de módulos adicionais (MyCond-like)
    from app.reservas_routes import reservas_bp
    app.register_blueprint(reservas_bp)
    
    from app.visitantes_routes import visitantes_bp
    app.register_blueprint(visitantes_bp)
    
    from app.encomendas_routes import encomendas_bp
    app.register_blueprint(encomendas_bp)
    
    from app.classificados_routes import classificados_bp
    app.register_blueprint(classificados_bp)
    
    # NOVOS MÓDULOS
    from app.ocorrencias_routes import ocorrencias_bp
    app.register_blueprint(ocorrencias_bp)
    
    from app.achados_routes import achados_bp
    app.register_blueprint(achados_bp)
    
    from app.votacao_routes import votacao_bp
    app.register_blueprint(votacao_bp)
    
    from app.atividades_routes import atividades_bp
    app.register_blueprint(atividades_bp)
    
    print("Blueprints registrados")

    # NOVO: Inicializar middleware de multi-tenancy
    try:
        from app.middleware import init_tenant_middleware
        init_tenant_middleware(app)
        print("Middleware de multi-tenancy inicializado")
    except Exception as e:
        print(f"⚠️ Aviso: Middleware de multi-tenancy não pôde ser inicializado: {e}")

    # User loader para Flask-Login
    @login.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))
    
    print("User loader configurado")
    
    
    # ===== FILTROS PERSONALIZADOS JINJA2 =====
    
    @app.template_filter('dateformat')
    def dateformat(value, format='%d/%m/%Y'):
        """Filtro para formatar datas"""
        if value is None:
            return ''
        try:
            if isinstance(value, str):
                return value
            return value.strftime(format)
        except Exception:
            return str(value) if value else ''
    
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        """Filtro para formatar data e hora"""
        if value is None:
            return ''
        try:
            if isinstance(value, str):
                return value
            return value.strftime(format)
        except Exception:
            return str(value) if value else ''
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Filtro para formatar moeda"""
        if value is None:
            return 'R$ 0,00'
        try:
            return f'R$ {float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        except Exception:
            return str(value) if value else 'R$ 0,00'
    
    @app.template_filter('status_badge')
    def status_badge(value):
        """Filtro para classe CSS de status"""
        status_classes = {
            'ativo': 'success',
            'inativo': 'secondary',
            'demitido': 'danger',
            'ferias': 'warning',
            'licenca': 'info',
            'regular': 'success',
            'a_vencer': 'warning',
            'vencida': 'danger',
            'sem_carteirinha': 'secondary'
        }
        return status_classes.get(str(value).lower(), 'secondary')


    return app 