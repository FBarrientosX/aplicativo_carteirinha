#!/usr/bin/env python3
"""
Verificar se existe usuário administrador
"""

from app import create_app, db
from app.models import Usuario

def verificar_admin():
    """Verificar usuários administradores"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Verificando usuários administradores...")
        
        # Listar todos os usuários
        usuarios = Usuario.query.all()
        print(f"📊 Total de usuários: {len(usuarios)}")
        
        for usuario in usuarios:
            print(f"  - {usuario.email} (Tipo: {usuario.tipo_usuario}, Ativo: {usuario.ativo})")
            print(f"    Nome: {usuario.nome_completo}")
            print(f"    Admin: {usuario.is_admin()}")
            print()
        
        # Contar admins
        admins = Usuario.query.filter_by(tipo_usuario='admin').all()
        print(f"👤 Administradores encontrados: {len(admins)}")
        
        if len(admins) == 0:
            print("\n⚠️ NENHUM ADMINISTRADOR ENCONTRADO!")
            print("💡 Execute: python criar_admin.py")
            return False
        else:
            print("\n✅ Administradores OK")
            return True

if __name__ == '__main__':
    verificar_admin()
