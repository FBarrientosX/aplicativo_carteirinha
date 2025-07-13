
import sys
import os

# Adicionar o diretório do seu projeto ao path
project_home = '/home/SEU_USUARIO/aplicativo_carteirinha'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Configurar variáveis de ambiente
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'sqlite:///home/SEU_USUARIO/aplicativo_carteirinha/carteirinha_piscina.db'

# Importar a aplicação
from app import create_app

# Criar aplicação
application = create_app()

if __name__ == "__main__":
    application.run()
