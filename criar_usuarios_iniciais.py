#!/usr/bin/env python3
"""
Script para criar usuários iniciais do sistema
"""

from app import create_app, db
from app.models import Usuario, SalvaVidas
from datetime import datetime

def criar_usuarios_iniciais():
    """Criar usuários iniciais para o sistema"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Criando usuários iniciais...")
        
        # Verificar se já existe usuário admin
        admin_existente = Usuario.query.filter_by(tipo_usuario='admin').first()
        if admin_existente:
            print(f"⚠️  Usuário administrador já existe: {admin_existente.username}")
        else:
            # Criar usuário administrador
            admin = Usuario(
                username='admin',
                email='admin@condominio.com',
                nome_completo='Administrador do Sistema',
                tipo_usuario='admin'
            )
            admin.set_password('admin123')  # Senha padrão - DEVE SER ALTERADA
            
            db.session.add(admin)
            print("✅ Usuário administrador criado:")
            print(f"   Usuário: admin")
            print(f"   Senha: admin123")
            print(f"   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
        
        # Criar usuário salva-vidas de exemplo (se existir salva-vidas cadastrado)
        salva_vidas_exemplo = SalvaVidas.query.filter_by(status='ativo').first()
        if salva_vidas_exemplo:
            # Verificar se já tem usuário para este salva-vidas
            user_salva_vidas = Usuario.query.filter_by(salva_vidas_id=salva_vidas_exemplo.id).first()
            if not user_salva_vidas:
                user_salva_vidas = Usuario(
                    username=f'salva_vidas_{salva_vidas_exemplo.id}',
                    email=salva_vidas_exemplo.email or f'salva_vidas_{salva_vidas_exemplo.id}@condominio.com',
                    nome_completo=salva_vidas_exemplo.nome_completo,
                    tipo_usuario='salva_vidas',
                    salva_vidas_id=salva_vidas_exemplo.id
                )
                user_salva_vidas.set_password('salva123')  # Senha padrão
                
                db.session.add(user_salva_vidas)
                print("✅ Usuário salva-vidas criado:")
                print(f"   Usuário: {user_salva_vidas.username}")
                print(f"   Senha: salva123")
                print(f"   Nome: {salva_vidas_exemplo.nome_completo}")
        else:
            # Criar usuário salva-vidas genérico
            user_salva_vidas = Usuario(
                username='salva_vidas',
                email='salva_vidas@condominio.com',
                nome_completo='Salva-vidas da Piscina',
                tipo_usuario='salva_vidas'
            )
            user_salva_vidas.set_password('salva123')
            
            db.session.add(user_salva_vidas)
            print("✅ Usuário salva-vidas genérico criado:")
            print(f"   Usuário: salva_vidas")
            print(f"   Senha: salva123")
        
        try:
            db.session.commit()
            print("\n🎉 Usuários criados com sucesso!")
            print("\n📋 Resumo dos acessos:")
            print("=" * 50)
            print("🔐 ADMINISTRADOR:")
            print("   URL: http://localhost:5000/auth/login")
            print("   Usuário: admin")
            print("   Senha: admin123")
            print("   Acesso: Sistema completo")
            print()
            print("🏊 SALVA-VIDAS:")
            print("   URL: http://localhost:5000/auth/login")
            print("   Usuário: salva_vidas (ou salva_vidas_X)")
            print("   Senha: salva123")
            print("   Acesso: Apenas QR Code e controle de acesso")
            print()
            print("⚠️  IMPORTANTE: Altere as senhas após o primeiro login!")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Erro ao salvar usuários: {e}")
            db.session.rollback()

if __name__ == '__main__':
    criar_usuarios_iniciais() 