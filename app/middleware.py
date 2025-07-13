# Middleware para gerenciar multi-tenancy
from flask import g, request, abort
import re

def init_tenant_middleware(app):
    """Inicializar middleware de tenant com a aplicação Flask"""
    
    @app.before_request
    def load_tenant():
        """Carrega tenant atual em todas as requisições"""
        # Pular rotas que não precisam de tenant
        if is_public_route():
            return
        
        tenant = get_current_tenant()
        
        if not tenant:
            # Em desenvolvimento, criar tenant padrão se não existir
            if is_local_development():
                tenant = create_default_tenant()
            else:
                abort(404, "Tenant não encontrado")
        
        # Verificar se tenant está ativo
        if tenant and hasattr(tenant, 'status') and tenant.status != 'ativo':
            if tenant.status == 'suspenso':
                abort(402, "Conta suspensa por falta de pagamento")
            elif tenant.status == 'cancelado':
                abort(403, "Conta cancelada")
        
        # Definir tenant atual
        g.tenant = tenant
        g.tenant_id = tenant.id if tenant else 1
    
    @app.teardown_appcontext
    def cleanup_tenant(exception):
        """Limpar contexto do tenant"""
        if hasattr(g, 'tenant'):
            g.pop('tenant', None)
        if hasattr(g, 'tenant_id'):
            g.pop('tenant_id', None)


def get_current_tenant():
    """Identifica o tenant atual baseado no subdomínio ou parâmetro"""
    from app.models import Tenant
    
    # Método 1: Subdomínio (cliente1.sistema.com.br)
    host = request.headers.get('Host', '')
    tenant = get_tenant_by_subdomain(host)
    
    if tenant:
        return tenant
    
    # Método 2: Parâmetro na URL (?tenant=cliente1)
    tenant_param = request.args.get('tenant')
    if tenant_param:
        try:
            tenant = Tenant.query.filter_by(subdominio=tenant_param).first()
            if tenant:
                return tenant
        except:
            pass
    
    # Método 3: Fallback para desenvolvimento local
    if is_local_development():
        try:
            return Tenant.query.filter_by(id=1).first()
        except:
            # Se não existe, retorna None e será criado
            return None
    
    return None


def get_tenant_by_subdomain(host):
    """Extrai tenant do subdomínio"""
    from app.models import Tenant
    
    try:
        # Regex para extrair subdomínio
        # Exemplo: cliente1.sistema.com.br -> cliente1
        pattern = r'^([^.]+)\.([^.]+\.[^.]+)$'
        match = re.match(pattern, host)
        
        if match:
            subdominio = match.group(1)
            
            # Pular subdomínios reservados
            if subdominio in ['www', 'api', 'admin', 'app', 'sistema']:
                return None
            
            tenant = Tenant.query.filter_by(subdominio=subdominio).first()
            return tenant
    except:
        pass
    
    return None


def is_public_route():
    """Verifica se é uma rota pública (não precisa de tenant)"""
    public_routes = [
        '/static/',
        '/favicon.ico',
        '/health',
        '/ping',
        '/signup',
        '/cadastro',
        '/api/public/',
        '/webhooks/',
    ]
    
    for route in public_routes:
        if request.path.startswith(route):
            return True
    
    return False


def is_local_development():
    """Verifica se está em desenvolvimento local"""
    host = request.headers.get('Host', '')
    return any([
        host.startswith('localhost'),
        host.startswith('127.0.0.1'),
        host.startswith('0.0.0.0'),
        'localhost' in host,
        ':5000' in host
    ])


def create_default_tenant():
    """Cria tenant padrão para desenvolvimento"""
    from app.models import Tenant, Plano
    from app import db
    
    try:
        # Verificar se já existe
        existing = Tenant.query.filter_by(id=1).first()
        if existing:
            return existing
        
        # Verificar se existe plano padrão
        plano = Plano.query.filter_by(id=1).first()
        if not plano:
            # Criar plano padrão
            from datetime import datetime
            plano = Plano(
                id=1,
                nome='Desenvolvimento',
                descricao='Plano para desenvolvimento',
                preco_mensal=0,
                limite_moradores=1000,
                limite_usuarios=10,
                limite_anexos_mb=5000,
                funcionalidades={},
                ativo=True,
                publico=False
            )
            db.session.add(plano)
            db.session.commit()
        
        # Criar tenant padrão
        from datetime import datetime, timedelta
        tenant = Tenant(
            id=1,
            nome='Condomínio de Desenvolvimento',
            subdominio='dev',
            email_responsavel='admin@dev.local',
            plano_id=1,
            data_inicio=datetime.now().date(),
            data_vencimento=datetime.now().date() + timedelta(days=365),
            status='ativo'
        )
        
        db.session.add(tenant)
        db.session.commit()
        
        return tenant
        
    except Exception as e:
        print(f"Erro ao criar tenant padrão: {e}")
        return None


def require_tenant(f):
    """Decorator para garantir que existe um tenant"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant') or not g.tenant:
            abort(404, "Tenant não encontrado")
        return f(*args, **kwargs)
    return decorated_function


def get_current_tenant_id():
    """Retorna o ID do tenant atual"""
    if hasattr(g, 'tenant_id'):
        return g.tenant_id
    return 1  # Fallback para desenvolvimento 