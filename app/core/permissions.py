"""
Sistema de Permissões Granulares
Gerencia permissões por módulo e ação
"""
from functools import wraps
from flask import g, abort, current_app
from flask_login import current_user

# Permissões por módulo e ação
PERMISSIONS = {
    'piscina': {
        'view': ['admin', 'sindico', 'portaria', 'salva_vidas'],
        'create': ['admin', 'sindico', 'portaria', 'salva_vidas'],
        'edit': ['admin', 'sindico'],
        'delete': ['admin']
    },
    'reservas': {
        'view': ['admin', 'sindico', 'morador'],
        'create': ['admin', 'sindico', 'morador'],
        'edit': ['admin', 'sindico'],
        'delete': ['admin']
    },
    'acesso': {
        'view': ['admin', 'sindico', 'portaria', 'funcionario'],
        'create': ['admin', 'sindico', 'portaria', 'funcionario'],
        'edit': ['admin', 'sindico'],
        'delete': ['admin']
    },
    'encomendas': {
        'view': ['admin', 'sindico', 'portaria', 'morador'],
        'create': ['admin', 'sindico', 'portaria'],
        'edit': ['admin', 'sindico', 'portaria'],
        'delete': ['admin']
    },
    'manutencao': {
        'view': ['admin', 'sindico', 'morador'],
        'create': ['admin', 'sindico', 'morador'],
        'edit': ['admin', 'sindico'],
        'delete': ['admin']
    },
    'admin': {
        'view': ['admin', 'sindico'],
        'create': ['admin'],
        'edit': ['admin'],
        'delete': ['admin']
    }
}


def has_permission(module, action):
    """
    Verifica se o usuário atual tem permissão para uma ação em um módulo
    
    Args:
        module (str): Nome do módulo (ex: 'piscina', 'reservas')
        action (str): Ação desejada (ex: 'view', 'create', 'edit', 'delete')
    
    Returns:
        bool: True se tem permissão, False caso contrário
    """
    if not current_user.is_authenticated:
        return False
    
    # Admin sempre tem todas as permissões
    if current_user.tipo_usuario == 'admin':
        return True
    
    # Verificar permissões do módulo
    module_perms = PERMISSIONS.get(module, {})
    allowed_roles = module_perms.get(action, [])
    
    return current_user.tipo_usuario in allowed_roles


def require_permission(module, action):
    """
    Decorator para verificar permissão antes de executar uma rota
    
    Usage:
        @bp.route('/exemplo')
        @login_required
        @require_permission('piscina', 'view')
        def exemplo():
            return render_template('exemplo.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(module, action):
                current_app.logger.warning(
                    f"Usuário {current_user.id} tentou acessar {module}.{action} sem permissão"
                )
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator para rotas que requerem permissão de admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def get_user_permissions(user):
    """
    Retorna todas as permissões de um usuário
    
    Args:
        user: Objeto Usuario
    
    Returns:
        dict: Dicionário com permissões por módulo
    """
    if not user:
        return {}
    
    if user.tipo_usuario == 'admin':
        # Admin tem todas as permissões
        return {
            module: ['view', 'create', 'edit', 'delete']
            for module in PERMISSIONS.keys()
        }
    
    user_perms = {}
    for module, actions in PERMISSIONS.items():
        module_perms = []
        for action, roles in actions.items():
            if user.tipo_usuario in roles:
                module_perms.append(action)
        if module_perms:
            user_perms[module] = module_perms
    
    return user_perms

