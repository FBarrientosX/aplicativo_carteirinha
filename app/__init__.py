from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_apscheduler import APScheduler
from app.config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Inicialização das extensões
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
scheduler = APScheduler()

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
def now_filter(format='%Y'):
    """Filtro para data atual"""
    return datetime.now().strftime(format)

# Inicializar o scheduler apenas em produção
if not app.debug:
    scheduler.init_app(app)
    scheduler.start()

# Importa as rotas e modelos após a criação de 'app' e 'db'
from app import routes, models 