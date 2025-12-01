# 🚀 Otimizações para PythonAnywhere

## Configurações Específicas para Deploy

### 1. Estrutura de Arquivos

**Arquivos que devem estar na raiz do projeto:**
- `wsgi.py` - Configuração WSGI
- `requirements.txt` - Dependências
- `.pythonanywhere` (opcional) - Configurações específicas

### 2. wsgi.py Otimizado

```python
# wsgi.py
import sys
import os

# Adicionar path do projeto
path = '/home/seu_usuario/aplicativo_carteirinha'
if path not in sys.path:
    sys.path.insert(0, path)

# Variáveis de ambiente
os.environ['FLASK_APP'] = 'run.py'
os.environ['FLASK_ENV'] = 'production'

# Importar app
from app import create_app
application = create_app()

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO)
```

### 3. Configurações de Banco de Dados

**app/config.py** - Adicionar configuração para PythonAnywhere:

```python
import os

class Config:
    # ... outras configurações ...
    
    # PythonAnywhere usa MySQL por padrão
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql://usuario:senha@seu_usuario.mysql.pythonanywhere-services.com/seu_usuario$nome_db'
    
    # Otimizações para produção
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {
            'charset': 'utf8mb4'
        }
    }
    
    # Desabilitar track modifications para performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### 4. Otimizações de Performance

#### 4.1 Cache de Templates
```python
# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Em produção, cache templates
    if not app.debug:
        app.config['TEMPLATES_AUTO_RELOAD'] = False
    
    return app
```

#### 4.2 Compressão de Respostas
```python
# Adicionar ao requirements.txt
# flask-compress

# app/__init__.py
from flask_compress import Compress

def create_app():
    app = Flask(__name__)
    Compress(app)  # Comprimir respostas
    return app
```

#### 4.3 Limitar Queries
```python
# app/core/utils.py - Já implementado
def paginate_query(query, page=1, per_page=20):
    """Sempre usar paginação para evitar queries grandes"""
    return query.paginate(page=page, per_page=per_page, error_out=False)
```

### 5. Arquivos Estáticos

**PythonAnywhere serve arquivos estáticos automaticamente:**
- `/static/` → `https://seu_usuario.pythonanywhere.com/static/`
- Não precisa configurar nada especial

**Otimizações:**
- Minificar CSS/JS antes de fazer upload
- Usar CDN para bibliotecas grandes (Bootstrap, Font Awesome)
- Comprimir imagens

### 6. Logs e Debugging

**Configurar logging:**
```python
# app/__init__.py
import logging
from logging.handlers import RotatingFileHandler

def create_app():
    app = Flask(__name__)
    
    if not app.debug:
        # Logs em produção
        file_handler = RotatingFileHandler(
            'logs/condotech.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CondoTech Solutions startup')
    
    return app
```

### 7. Variáveis de Ambiente

**Criar arquivo `.env` (não commitar):**
```
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=mysql://usuario:senha@host/database
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=senha_app
```

**No PythonAnywhere, configurar via Web Interface:**
- Web → Web app → Variables for your web app

### 8. Tarefas Agendadas (Cron Jobs)

**PythonAnywhere permite cron jobs:**

```bash
# Executar diariamente às 9h
0 9 * * * cd /home/seu_usuario/aplicativo_carteirinha && /home/seu_usuario/.virtualenvs/venv/bin/python -c "from app import create_app, db; from app.email_service import verificar_e_enviar_notificacoes; app = create_app(); app.app_context().push(); verificar_e_enviar_notificacoes()"
```

### 9. Migrações no PythonAnywhere

**Após fazer deploy:**
```bash
# No console do PythonAnywhere
cd /home/seu_usuario/aplicativo_carteirinha
source venv/bin/activate  # ou seu ambiente virtual
flask db upgrade
```

### 10. Upload de Arquivos

**PythonAnywhere limita uploads:**
- Máximo: 100MB por arquivo
- Otimizar imagens antes do upload
- Considerar usar serviços externos (S3, Cloudinary) para produção

**Código otimizado:**
```python
# app/core/utils.py
def salvar_arquivo_otimizado(file, pasta, max_size_mb=5):
    """Salva arquivo com validação de tamanho"""
    max_size = max_size_mb * 1024 * 1024  # Converter para bytes
    
    if file.content_length > max_size:
        raise ValueError(f"Arquivo muito grande. Máximo: {max_size_mb}MB")
    
    # ... resto do código ...
```

### 11. Timeout e Limites

**PythonAnywhere tem limites:**
- Timeout de requisição: 100 segundos
- Memória: Depende do plano
- CPU: Limitado

**Otimizações:**
- Usar background tasks para operações longas
- Limitar queries complexas
- Cache de dados frequentes

### 12. HTTPS e Segurança

**PythonAnywhere fornece HTTPS automaticamente:**
- Certificado SSL incluído
- Forçar HTTPS no código:

```python
# app/__init__.py
from flask_talisman import Talisman

def create_app():
    app = Flask(__name__)
    
    if not app.debug:
        Talisman(app, force_https=True)
    
    return app
```

### 13. Checklist de Deploy

- [ ] Atualizar `wsgi.py` com path correto
- [ ] Configurar variáveis de ambiente no PythonAnywhere
- [ ] Executar `flask db upgrade` no console
- [ ] Verificar permissões de arquivos (chmod 755 para diretórios)
- [ ] Testar rotas principais
- [ ] Verificar logs para erros
- [ ] Configurar domínio personalizado (se aplicável)
- [ ] Configurar cron jobs (se necessário)
- [ ] Testar upload de arquivos
- [ ] Verificar performance

### 14. Comandos Úteis

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
flask db upgrade

# Criar superusuário
python criar_admin.py

# Ver logs
tail -f logs/condotech.log

# Reiniciar aplicação (via Web Interface)
# Web → Web app → Reload
```

### 15. Troubleshooting

**Problema: ImportError**
- Verificar se todos os módulos estão no path
- Verificar se `__init__.py` existe em todos os pacotes

**Problema: Database locked (SQLite)**
- PythonAnywhere não recomenda SQLite para produção
- Migrar para MySQL

**Problema: Timeout**
- Otimizar queries
- Usar paginação
- Cache de dados

**Problema: Memory Error**
- Limitar queries
- Usar `.limit()` em todas as queries grandes
- Paginar resultados

---

**Versão**: 1.0  
**Data**: 2024-11-24  
**Nota**: Estas otimizações garantem melhor performance no PythonAnywhere

