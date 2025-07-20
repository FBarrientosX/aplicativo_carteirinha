import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env')) # Aponta para o .env na raiz do projeto

class Config:
    """Configuração base da aplicação"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuração do banco de dados
    # Prioriza MySQL em produção, fallback para SQLite em desenvolvimento
    if os.environ.get('MYSQL_DATABASE'):
        # MySQL para produção (PythonAnywhere)
        MYSQL_USER = os.environ.get('MYSQL_USER', 'barrientos')
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
        MYSQL_HOST = os.environ.get('MYSQL_HOST', 'barrientos.mysql.pythonanywhere-services.com')
        MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'barrientos$default')
        
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'
    else:
        # SQLite para desenvolvimento local
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(basedir, '..', 'carteirinha_piscina.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'charset': 'utf8mb4'} if 'mysql' in SQLALCHEMY_DATABASE_URI else {}
    }
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Configurações de email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Configuração de upload de arquivos
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

    # Configuração do Scheduler
    SCHEDULER_API_ENABLED = True

    # Outras configurações da aplicação podem ser adicionadas aqui
    # Ex: MAIL_SERVER, MAIL_PORT, etc.