#!/usr/bin/env python3
"""
Script para criar o primeiro cliente de teste no sistema SaaS
Execute após o deploy: python criar_cliente_inicial.py
"""

import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Tenant, Usuario, Plano, Cobranca, ConfiguracaoTenant, Morador

def criar_cliente_inicial():
    """Cria o primeiro cliente de teste com dados de exemplo"""
    
    app = create_app()
    
    with app.app_context():
        print("🏢 Criando primeiro cliente de teste...")
        
        # Verificar se já existe um tenant
        tenant_existente = Tenant.query.first()
        if tenant_existente:
            print(f"✅ Tenant já existe: {tenant_existente.nome}")
            return tenant_existente
        
        # Buscar plano básico
        plano_basico = Plano.query.filter_by(nome='Básico').first()
        if not plano_basico:
            print("❌ ERRO: Plano básico não encontrado. Execute 'python criar_planos_iniciais.py' primeiro")
            return None
        
        # Criar tenant de teste
        tenant = Tenant(
            nome='Condomínio Teste',
            subdominio='teste',
            email='admin@teste.com',
            telefone='(11) 99999-9999',
            endereco='Rua de Teste, 123',
            cidade='São Paulo',
            estado='SP',
            cep='01234-567',
            plano_id=plano_basico.id,
            ativo=True,
            data_criacao=datetime.utcnow()
        )
        
        db.session.add(tenant)
        db.session.flush()  # Para obter o ID do tenant
        
        # Criar usuário administrador do tenant
        usuario_admin = Usuario(
            username='admin',
            nome_completo='Administrador Teste',
            email='admin@teste.com',
            tenant_id=tenant.id,
            tipo_usuario='admin',
            ativo=True
        )
        
        usuario_admin.set_password('123456')
        db.session.add(usuario_admin)
        
        # Criar configurações do tenant
        configuracoes = ConfiguracaoTenant(
            tenant_id=tenant.id,
            nome_sistema='Sistema Carteirinha Teste',
            email_remetente='admin@teste.com',
            mensagem_boas_vindas='Bem-vindo ao nosso sistema de carteirinhas!',
            dias_aviso_vencimento=7,
            permitir_auto_cadastro=True,
            requerer_aprovacao=False,
            logo_url='',
            cor_primaria='#007bff',
            cor_secundaria='#6c757d'
        )
        
        db.session.add(configuracoes)
        
        # Criar cobrança inicial (período de teste)
        cobranca = Cobranca(
            tenant_id=tenant.id,
            valor=plano_basico.preco,
            data_vencimento=datetime.utcnow() + timedelta(days=30),
            status='pendente',
            referencia=f'teste-{datetime.now().strftime("%Y%m")}'
        )
        
        db.session.add(cobranca)
        
        # Criar alguns moradores de exemplo
        moradores_exemplo = [
            {
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'apartamento': '101',
                'bloco': 'A',
                'telefone': '(11) 98765-4321',
                'cpf': '123.456.789-00',
                'data_nascimento': datetime(1985, 5, 15),
                'observacoes': 'Morador exemplo - Criado automaticamente'
            },
            {
                'nome': 'Maria Santos',
                'email': 'maria@teste.com',
                'apartamento': '102',
                'bloco': 'A',
                'telefone': '(11) 98765-4322',
                'cpf': '123.456.789-01',
                'data_nascimento': datetime(1990, 8, 20),
                'observacoes': 'Morador exemplo - Criado automaticamente'
            },
            {
                'nome': 'Pedro Oliveira',
                'email': 'pedro@teste.com',
                'apartamento': '103',
                'bloco': 'A',
                'telefone': '(11) 98765-4323',
                'cpf': '123.456.789-02',
                'data_nascimento': datetime(1988, 12, 10),
                'observacoes': 'Morador exemplo - Criado automaticamente'
            }
        ]
        
        for dados_morador in moradores_exemplo:
            morador = Morador(
                tenant_id=tenant.id,
                **dados_morador,
                data_vencimento=datetime.utcnow() + timedelta(days=365),
                ativo=True,
                data_criacao=datetime.utcnow()
            )
            db.session.add(morador)
        
        # Salvar todas as mudanças
        db.session.commit()
        
        print(f"✅ Cliente criado com sucesso!")
        print(f"🏢 Tenant: {tenant.nome}")
        print(f"🌐 Subdomínio: {tenant.subdominio}")
        print(f"👤 Admin: {usuario_admin.email}")
        print(f"🔑 Senha: 123456")
        print(f"📋 Plano: {plano_basico.nome}")
        print(f"👥 Moradores: {len(moradores_exemplo)} criados")
        
        return tenant

def criar_usuario_super_admin():
    """Cria um usuário super admin global"""
    
    app = create_app()
    
    with app.app_context():
        print("🔐 Criando usuário super admin...")
        
        # Verificar se já existe
        super_admin = Usuario.query.filter_by(tipo_usuario='super_admin').first()
        if super_admin:
            print(f"✅ Super admin já existe: {super_admin.email}")
            return super_admin
        
        # Criar super admin
        super_admin = Usuario(
            username='superadmin',
            nome_completo='Super Admin',
            email='superadmin@sistema.com',
            tenant_id=None,  # Super admin não pertence a um tenant específico
            tipo_usuario='super_admin',
            ativo=True
        )
        
        super_admin.set_password('superadmin123')
        db.session.add(super_admin)
        db.session.commit()
        
        print(f"✅ Super admin criado!")
        print(f"📧 Email: {super_admin.email}")
        print(f"🔑 Senha: superadmin123")
        
        return super_admin

def main():
    """Função principal"""
    print("🚀 Configurando sistema SaaS...")
    print("=" * 50)
    
    # Criar super admin
    super_admin = criar_usuario_super_admin()
    
    # Criar cliente inicial
    cliente = criar_cliente_inicial()
    
    if cliente:
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("=" * 50)
        print("INFORMAÇÕES DE ACESSO:")
        print(f"🌐 URL Local: http://localhost:5000")
        print(f"🌐 URL Tenant: http://teste.localhost:5000")
        print(f"📧 Email Admin: admin@teste.com")
        print(f"🔑 Senha: 123456")
        print(f"📧 Super Admin: superadmin@sistema.com")
        print(f"🔑 Senha Super: superadmin123")
        print("\nPRÓXIMOS PASSOS:")
        print("1. Acessar o sistema e testar funcionalidades")
        print("2. Configurar domínio personalizado")
        print("3. Testar geração de carteirinhas")
        print("4. Verificar envio de emails")
        print("5. Fazer deploy para produção")
    else:
        print("\n❌ ERRO: Falha na configuração")
        sys.exit(1)

if __name__ == '__main__':
    main() 