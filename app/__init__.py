"""
Aplicativo CondoTech Solutions
Sistema SaaS multi-tenant para gestão de condomínios
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import Config
import logging
from logging.handlers import RotatingFileHandler

# Instâncias dos plugins
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()

def create_app(config_class=Config):
    """Factory function para criar a aplicação Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar plugins
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    
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
    
    print("✅ Flask app criado")

    # Importar modelos para que sejam conhecidos pelo Alembic
    from app import models
    print("✅ Modelos importados")

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
    
    print("✅ Blueprints registrados")

    # NOVO: Inicializar middleware de multi-tenancy
    try:
        from app.middleware import init_tenant_middleware
        init_tenant_middleware(app)
        print("✅ Middleware de multi-tenancy inicializado")
    except Exception as e:
        print(f"⚠️ Aviso: Middleware de multi-tenancy não pôde ser inicializado: {e}")

    # User loader para Flask-Login
    @login.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))
    
    print("✅ User loader configurado")
    
    return app 