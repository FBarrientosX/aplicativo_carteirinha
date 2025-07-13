#!/usr/bin/env python3
"""
Script para configurar o sistema para funcionar no PythonAnywhere
Execute no console: python3.10 configurar_pythonanywhere.py
"""

import os
import sys
from datetime import datetime, timedelta

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Tenant, Usuario, Plano, ConfiguracaoTenant

def configurar_pythonanywhere():
    """Configura o sistema para funcionar no PythonAnywhere"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Configurando sistema para PythonAnywhere...")
        
        # Verificar se já existe um tenant
        tenant = Tenant.query.filter_by(id=1).first()
        
        if not tenant:
            print("⚠️  Tenant padrão não encontrado, criando...")
            
            # Buscar plano básico
            plano = Plano.query.filter_by(nome='Básico').first()
            if not plano:
                print("❌ ERRO: Plano básico não encontrado!")
                return False
            
            # Criar tenant padrão
            tenant = Tenant(
                nome='Condomínio Demo',
                subdominio='demo',
                email_responsavel='admin@demo.com',
                telefone='(11) 99999-9999',
                endereco='Rua Demo, 123',
                plano_id=plano.id,
                data_inicio=datetime.utcnow().date(),
                data_vencimento=datetime.utcnow().date() + timedelta(days=365),
                status='ativo'
            )
            
            db.session.add(tenant)
            db.session.commit()
            
            print("✅ Tenant padrão criado!")
        else:
            print("✅ Tenant padrão já existe!")
        
        # Verificar usuário admin
        admin = Usuario.query.filter_by(tenant_id=1, tipo_usuario='admin').first()
        
        if not admin:
            print("⚠️  Usuário admin não encontrado, criando...")
            
            admin = Usuario(
                username='admin',
                nome_completo='Administrador Demo',
                email='admin@demo.com',
                tenant_id=1,
                tipo_usuario='admin',
                ativo=True
            )
            
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário admin criado!")
        else:
            print("✅ Usuário admin já existe!")
        
        # Verificar configurações
        config = ConfiguracaoTenant.query.filter_by(tenant_id=1).first()
        
        if not config:
            print("⚠️  Configurações não encontradas, criando...")
            
            # Criar configurações usando o modelo correto
            configs = [
                ConfiguracaoTenant(tenant_id=1, categoria='sistema', chave='nome_sistema', valor='Sistema Carteirinha Demo'),
                ConfiguracaoTenant(tenant_id=1, categoria='email', chave='email_remetente', valor='admin@demo.com'),
                ConfiguracaoTenant(tenant_id=1, categoria='sistema', chave='mensagem_boas_vindas', valor='Bem-vindo ao sistema de carteirinhas!'),
                ConfiguracaoTenant(tenant_id=1, categoria='sistema', chave='dias_aviso_vencimento', valor='7', tipo='numero'),
                ConfiguracaoTenant(tenant_id=1, categoria='sistema', chave='permitir_auto_cadastro', valor='true', tipo='booleano'),
                ConfiguracaoTenant(tenant_id=1, categoria='sistema', chave='requerer_aprovacao', valor='false', tipo='booleano'),
                ConfiguracaoTenant(tenant_id=1, categoria='visual', chave='cor_primaria', valor='#007bff'),
                ConfiguracaoTenant(tenant_id=1, categoria='visual', chave='cor_secundaria', valor='#6c757d')
            ]
            
            for config in configs:
                db.session.add(config)
            
            db.session.commit()
            
            print("✅ Configurações criadas!")
        else:
            print("✅ Configurações já existem!")
        
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("=" * 50)
        print("INFORMAÇÕES DE ACESSO:")
        print(f"🌐 URL: https://barrientos.pythonanywhere.com")
        print(f"📧 Email: admin@demo.com")
        print(f"🔑 Senha: 123456")
        print("=" * 50)
        
        return True

def main():
    """Função principal"""
    try:
        if configurar_pythonanywhere():
            print("\n✅ Sistema configurado com sucesso!")
            print("🚀 Acesse: https://barrientos.pythonanywhere.com")
        else:
            print("\n❌ Erro na configuração!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 