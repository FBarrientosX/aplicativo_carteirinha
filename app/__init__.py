from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from app.config import Config
from datetime import datetime

# Inicialização das extensões
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
scheduler = APScheduler()

def create_app(config_class=Config):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Configurar Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))

    # Filtro personalizado para formatação de datas
    @app.template_filter('dateformat')
    def dateformat(value, format='%d/%m/%Y'):
        """Filtro para formatação de datas nos templates"""
        if value is None:
            return ''
        if isinstance(value, str):
            # Se for string, tentar converter para datetime
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d')
                except:
                    return value
        return value.strftime(format)

    @app.template_filter('now')
    def now_filter(value, format='%Y'):
        """Filtro para data atual"""
        return datetime.now().strftime(format)

    # Inicializar o scheduler apenas em produção e se não estiver já rodando
    if not app.debug and not scheduler.running:
        try:
            scheduler.init_app(app)
            scheduler.start()
        except Exception as e:
            print(f"Aviso: Scheduler não pôde ser iniciado: {e}")
            pass

    # Importa as rotas e modelos após a criação de 'app' e 'db'
    from app import models
    from app.routes import bp as main_bp
    from app.auth import auth_bp
    from app.salva_vidas_routes import salva_vidas_bp
    from app.manutencao_routes import manutencao_bp  # Novo módulo
    
    # NOVO: Inicializar middleware de multi-tenancy
    try:
        from app.middleware import init_tenant_middleware
        init_tenant_middleware(app)
        print("✅ Middleware de multi-tenancy inicializado")
    except Exception as e:
        print(f"⚠️ Aviso: Middleware de multi-tenancy não pôde ser inicializado: {e}")
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(salva_vidas_bp, url_prefix='/salva_vidas')
    app.register_blueprint(manutencao_bp, url_prefix='/manutencao')  # Registrar módulo
    
    return app

# Para compatibilidade com versões anteriores
app = create_app() 