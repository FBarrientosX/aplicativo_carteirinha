# Middleware para gerenciar multi-tenancy
from flask import g, request, abort, current_app
from functools import wraps
import re

class TenantMiddleware:
    """Middleware para gerenciar tenants"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar middleware com a aplicação Flask"""
        app.before_request(self.load_tenant)
        app.teardown_appcontext(self.cleanup_tenant)
    
    def load_tenant(self):
        """Carrega tenant atual em todas as requisições"""
        # Pular rotas que não precisam de tenant
        if self.is_public_route():
            return
        
        tenant = self.get_current_tenant()
        
        if not tenant:
            abort(404, "Tenant não encontrado")
        
        # Verificar se tenant está ativo
        if tenant.status != 'ativo':
            if tenant.status == 'suspenso':
                abort(402, "Conta suspensa por falta de pagamento")
            elif tenant.status == 'cancelado':
                abort(403, "Conta cancelada")
        
        # Verificar se tenant está vencido
        if tenant.esta_vencido and not self.is_admin_route():
            abort(402, "Plano vencido. Entre em contato com o suporte.")
        
        # Definir tenant atual
        g.tenant = tenant
        g.tenant_id = tenant.id
    
    def cleanup_tenant(self, exception):
        """Limpar contexto do tenant"""
        if hasattr(g, 'tenant'):
            g.pop('tenant', None)
        if hasattr(g, 'tenant_id'):
            g.pop('tenant_id', None)
    
    def get_current_tenant(self):
        """Identifica o tenant atual baseado no subdomínio ou parâmetro"""
        # Importar aqui para evitar circular imports
        from app.models import Tenant
        
        # Método 1: Subdomínio (cliente1.sistema.com.br)
        host = request.headers.get('Host', '')
        tenant = self.get_tenant_by_subdomain(host)
        
        if tenant:
            return tenant
        
        # Método 2: Parâmetro na URL (?tenant=cliente1)
        tenant_param = request.args.get('tenant')
        if tenant_param:
            tenant = Tenant.query.filter_by(subdominio=tenant_param).first()
            if tenant:
                return tenant
        
        # Método 3: Domínio personalizado (cliente.com.br)
        tenant = self.get_tenant_by_custom_domain(host)
        if tenant:
            return tenant
        
        # Método 4: Fallback para desenvolvimento local
        if self.is_local_development():
            return Tenant.query.filter_by(id=1).first()
        
        return None
    
    def get_tenant_by_subdomain(self, host):
        """Extrai tenant do subdomínio"""
        from app.models import Tenant
        
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
        
        return None
    
    def get_tenant_by_custom_domain(self, host):
        """Busca tenant por domínio personalizado"""
        from app.models import Tenant
        
        # Remover www se existir
        domain = host.replace('www.', '')
        
        tenant = Tenant.query.filter_by(dominio_personalizado=domain).first()
        return tenant
    
    def is_public_route(self):
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
            '/admin/login',
            '/admin/signup'
        ]
        
        for route in public_routes:
            if request.path.startswith(route):
                return True
        
        return False
    
    def is_admin_route(self):
        """Verifica se é uma rota administrativa"""
        admin_routes = ['/admin/', '/super/', '/system/']
        
        for route in admin_routes:
            if request.path.startswith(route):
                return True
        
        return False
    
    def is_local_development(self):
        """Verifica se está em desenvolvimento local"""
        host = request.headers.get('Host', '')
        return any([
            host.startswith('localhost'),
            host.startswith('127.0.0.1'),
            host.startswith('0.0.0.0'),
            current_app.config.get('ENV') == 'development'
        ])


def require_tenant(f):
    """Decorator para garantir que existe um tenant"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant') or not g.tenant:
            abort(404, "Tenant não encontrado")
        return f(*args, **kwargs)
    return decorated_function


def require_tenant_permission(permission):
    """Decorator para verificar permissão do tenant"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant') or not g.tenant:
                abort(404, "Tenant não encontrado")
            
            # Verificar se o plano tem a funcionalidade
            if not g.tenant.plano_atual.tem_funcionalidade(permission):
                abort(403, f"Funcionalidade '{permission}' não disponível no seu plano")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_tenant_limit(limit_type, max_allowed=None):
    """Decorator para verificar limites do tenant"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant') or not g.tenant:
                abort(404, "Tenant não encontrado")
            
            # Verificar limite de moradores
            if limit_type == 'moradores':
                if not g.tenant.pode_adicionar_morador():
                    abort(403, f"Limite de moradores excedido ({g.tenant.plano_atual.limite_moradores})")
            
            # Verificar limite de usuários
            elif limit_type == 'usuarios':
                if not g.tenant.pode_adicionar_usuario():
                    abort(403, f"Limite de usuários excedido ({g.tenant.plano_atual.limite_usuarios})")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class TenantContext:
    """Context manager para executar código no contexto de um tenant específico"""
    
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.original_tenant = None
        self.original_tenant_id = None
    
    def __enter__(self):
        # Salvar contexto atual
        self.original_tenant = getattr(g, 'tenant', None)
        self.original_tenant_id = getattr(g, 'tenant_id', None)
        
        # Carregar novo tenant
        from app.models import Tenant
        tenant = Tenant.query.get(self.tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {self.tenant_id} não encontrado")
        
        g.tenant = tenant
        g.tenant_id = tenant.id
        
        return tenant
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restaurar contexto original
        if self.original_tenant:
            g.tenant = self.original_tenant
            g.tenant_id = self.original_tenant_id
        else:
            g.pop('tenant', None)
            g.pop('tenant_id', None)


def with_tenant(tenant_id):
    """Decorator para executar função no contexto de um tenant específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            with TenantContext(tenant_id):
                return f(*args, **kwargs)
        return decorated_function
    return decorator


# Exemplo de uso dos decorators
"""
@app.route('/moradores')
@require_tenant
def listar_moradores():
    # g.tenant está automaticamente disponível
    moradores = Morador.query_for_tenant().all()
    return render_template('moradores/listar.html', moradores=moradores)

@app.route('/moradores/novo')
@require_tenant
@require_tenant_limit('moradores')
def novo_morador():
    # Verificar se pode adicionar mais moradores
    form = MoradorForm()
    return render_template('moradores/form.html', form=form)

@app.route('/api/moradores')
@require_tenant
@require_tenant_permission('api_access')
def api_moradores():
    # Verificar se o plano permite acesso à API
    moradores = Morador.query_for_tenant().all()
    return jsonify([m.to_dict() for m in moradores])

# Executar código no contexto de outro tenant
def processar_todos_tenants():
    from app.models import Tenant
    
    tenants = Tenant.query.filter_by(status='ativo').all()
    
    for tenant in tenants:
        with TenantContext(tenant.id):
            # Código executado no contexto do tenant
            total_moradores = Morador.query_for_tenant().count()
            print(f"Tenant {tenant.nome}: {total_moradores} moradores")
""" 