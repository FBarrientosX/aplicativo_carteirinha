#!/usr/bin/env python3
"""
Configuração FINAL FUNCIONAL do CondoTech Solutions para MySQL
Execute: python3.10 configurar_condotech_mysql_final_funcional.py
"""

import os
import sys
from datetime import datetime, date

# Configurar variáveis de ambiente para MySQL
os.environ['MYSQL_DATABASE'] = 'barrientos$default'
os.environ['MYSQL_USER'] = 'barrientos'
os.environ['MYSQL_HOST'] = 'barrientos.mysql.pythonanywhere-services.com'

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def configurar_sistema_mysql():
    """Configura o sistema CondoTech Solutions no MySQL"""
    
    print("🚀 CondoTech Solutions - Configuração FINAL FUNCIONAL MySQL")
    print("=" * 65)
    
    # Verificar se a senha do MySQL foi definida
    mysql_password = input("Digite a senha do MySQL: ").strip()
    if not mysql_password:
        print("❌ Senha do MySQL é obrigatória!")
        return False
    
    os.environ['MYSQL_PASSWORD'] = mysql_password
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔌 Conectando ao MySQL...")
            
            # Testar conexão
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("  ✅ Conexão MySQL estabelecida!")
            
            # Criar todas as tabelas
            print("📋 Criando estrutura do banco...")
            db.create_all()
            print("  ✅ Tabelas criadas!")
            
            # PASSO 1: Criar plano padrão e obter ID real
            print("📦 Configurando plano padrão...")
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM planos")).fetchone()
            planos_count = result.count if result else 0
            
            if planos_count == 0:
                db.session.execute(text("""
                    INSERT INTO planos (nome, descricao, preco_mensal, limite_usuarios, limite_moradores, funcionalidades, ativo)
                    VALUES (:nome, :descricao, :preco_mensal, :limite_usuarios, :limite_moradores, :funcionalidades, :ativo)
                """), {
                    'nome': 'Básico',
                    'descricao': 'Plano básico CondoTech',
                    'preco_mensal': 0.00,
                    'limite_usuarios': 10,
                    'limite_moradores': 1000,
                    'funcionalidades': '{"piscina": true, "manutencao": true}',
                    'ativo': True
                })
                db.session.commit()
                print("  ✅ Plano padrão criado!")
            else:
                print("  ✅ Plano já existe!")
            
            # Buscar ID real do plano
            plano_result = db.session.execute(text("SELECT id FROM planos WHERE nome = 'Básico' LIMIT 1")).fetchone()
            if not plano_result:
                print("❌ Erro: Plano não encontrado!")
                return False
            
            plano_id_real = plano_result.id
            print(f"  📋 Plano ID real: {plano_id_real}")
            
            # PASSO 2: Criar tenant usando ID real do plano
            print("🏢 Configurando tenant padrão...")
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM tenants")).fetchone()
            tenant_exists = result.count if result else 0
            
            if tenant_exists == 0:
                db.session.execute(text("""
                    INSERT INTO tenants (nome, subdominio, email_responsavel, plano_id, data_inicio, data_vencimento, status, data_criacao)
                    VALUES (:nome, :subdominio, :email_responsavel, :plano_id, :data_inicio, :data_vencimento, :status, :data_criacao)
                """), {
                    'nome': 'Condomínio Padrão',
                    'subdominio': 'default',
                    'email_responsavel': 'admin@condotech.com',
                    'plano_id': plano_id_real,
                    'data_inicio': date.today(),
                    'data_vencimento': date(2025, 12, 31),
                    'status': 'ativo',
                    'data_criacao': datetime.now()
                })
                db.session.commit()
                print("  ✅ Tenant criado!")
            else:
                print("  ✅ Tenant já existe!")
            
            # Buscar ID real do tenant
            tenant_result = db.session.execute(text("SELECT id FROM tenants WHERE subdominio = 'default' LIMIT 1")).fetchone()
            if not tenant_result:
                print("❌ Erro: Tenant não encontrado!")
                return False
            
            tenant_id_real = tenant_result.id
            print(f"  📋 Tenant ID real: {tenant_id_real}")
            
            # PASSO 3: Criar usuário admin usando ID real do tenant
            print("👤 Configurando usuário administrador...")
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM usuarios WHERE username = 'admin'")).fetchone()
            admin_exists = result.count if result else 0
            
            if admin_exists == 0:
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash('admin123')
                
                db.session.execute(text("""
                    INSERT INTO usuarios (username, email, nome_completo, tipo_usuario, password_hash, ativo, tenant_id, data_criacao)
                    VALUES (:username, :email, :nome_completo, :tipo_usuario, :password_hash, :ativo, :tenant_id, :data_criacao)
                """), {
                    'username': 'admin',
                    'email': 'admin@condotech.com',
                    'nome_completo': 'Administrador CondoTech',
                    'tipo_usuario': 'admin',
                    'password_hash': password_hash,
                    'ativo': True,
                    'tenant_id': tenant_id_real,
                    'data_criacao': datetime.now()
                })
                db.session.commit()
                print("  ✅ Admin criado! (admin / admin123)")
            else:
                print("  ✅ Admin já existe!")
            
            # PASSO 4: Configurar sistema usando tabela chave-valor
            print("⚙️ Configurando sistema...")
            
            configuracoes = [
                ('nome_condominio', 'CondoTech Solutions', 'Nome do condomínio'),
                ('endereco', 'Rua da Tecnologia, 123', 'Endereço do condomínio'),
                ('cidade', 'São Paulo', 'Cidade'),
                ('estado', 'SP', 'Estado'),
                ('cep', '01234-567', 'CEP'),
                ('sistema_ativo', 'true', 'Sistema ativo', 'booleano'),
                ('versao_sistema', '2.0', 'Versão do sistema'),
            ]
            
            for chave, valor, descricao, *tipo in configuracoes:
                tipo_config = tipo[0] if tipo else 'texto'
                
                result = db.session.execute(
                    text("SELECT COUNT(*) as count FROM configuracao_sistema WHERE chave = :chave"), 
                    {'chave': chave}
                ).fetchone()
                
                if result and result.count == 0:
                    db.session.execute(text("""
                        INSERT INTO configuracao_sistema (chave, valor, descricao, tipo, categoria)
                        VALUES (:chave, :valor, :descricao, :tipo, :categoria)
                    """), {
                        'chave': chave,
                        'valor': valor,
                        'descricao': descricao,
                        'tipo': tipo_config,
                        'categoria': 'geral'
                    })
            
            db.session.commit()
            print("  ✅ Configurações do sistema criadas!")
            
            # PASSO 5: Criar módulos do sistema
            print("📦 Configurando módulos...")
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM modulos")).fetchone()
            modulos_count = result.count if result else 0
            
            if modulos_count == 0:
                # Módulo Piscina
                db.session.execute(text("""
                    INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
                    VALUES (:nome, :slug, :descricao, :icone, :cor, :ordem, :ativo, :data_criacao)
                """), {
                    'nome': 'Controle de Piscina',
                    'slug': 'piscina',
                    'descricao': 'Sistema completo de controle de acesso à piscina com carteirinhas digitais e QR Code',
                    'icone': 'fas fa-swimming-pool',
                    'cor': '#007bff',
                    'ordem': 1,
                    'ativo': True,
                    'data_criacao': datetime.now()
                })
                
                # Módulo Manutenção
                db.session.execute(text("""
                    INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
                    VALUES (:nome, :slug, :descricao, :icone, :cor, :ordem, :ativo, :data_criacao)
                """), {
                    'nome': 'Manutenção & Chamados',
                    'slug': 'manutencao',
                    'descricao': 'Gestão completa de chamados de manutenção, ordens de serviço e controle de técnicos',
                    'icone': 'fas fa-tools',
                    'cor': '#28a745',
                    'ordem': 2,
                    'ativo': True,
                    'data_criacao': datetime.now()
                })
                
                db.session.commit()
                print("  ✅ Módulos criados!")
            else:
                print("  ✅ Módulos já existem!")
            
            # PASSO 6: Ativar módulos para tenant
            print("🔌 Ativando módulos para tenant...")
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM modulos_tenant WHERE tenant_id = :tenant_id"), {'tenant_id': tenant_id_real}).fetchone()
            tenant_modules_count = result.count if result else 0
            
            if tenant_modules_count == 0:
                modulos = db.session.execute(text("SELECT id FROM modulos WHERE ativo = 1")).fetchall()
                
                for modulo in modulos:
                    db.session.execute(text("""
                        INSERT INTO modulos_tenant (tenant_id, modulo_id, ativo, data_ativacao)
                        VALUES (:tenant_id, :modulo_id, :ativo, :data_ativacao)
                    """), {
                        'tenant_id': tenant_id_real,
                        'modulo_id': modulo.id,
                        'ativo': True,
                        'data_ativacao': datetime.now()
                    })
                
                db.session.commit()
                print("  ✅ Módulos ativados para tenant!")
            else:
                print("  ✅ Módulos já ativados!")
            
            # PASSO 7: Criar categorias de manutenção
            print("🔧 Configurando categorias de manutenção...")
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM categorias_manutencao WHERE tenant_id = :tenant_id"), {'tenant_id': tenant_id_real}).fetchone()
            categorias_count = result.count if result else 0
            
            if categorias_count == 0:
                categorias = [
                    ('Elétrica', 'Problemas elétricos, iluminação, tomadas', 'fas fa-bolt', '#ffc107', 4, 'alta'),
                    ('Hidráulica', 'Vazamentos, entupimentos, pressão de água', 'fas fa-tint', '#007bff', 2, 'alta'),
                    ('Ar Condicionado', 'Climatização, ventilação, refrigeração', 'fas fa-snowflake', '#17a2b8', 24, 'media'),
                    ('Pintura', 'Pintura, acabamentos, reparos estéticos', 'fas fa-paint-brush', '#6f42c1', 72, 'baixa'),
                    ('Limpeza', 'Limpeza geral, áreas comuns, jardinagem', 'fas fa-broom', '#28a745', 12, 'media'),
                    ('Segurança', 'Portões, fechaduras, câmeras, alarmes', 'fas fa-shield-alt', '#dc3545', 1, 'urgente')
                ]
                
                for categoria in categorias:
                    db.session.execute(text("""
                        INSERT INTO categorias_manutencao 
                        (tenant_id, nome, descricao, icone, cor, tempo_resposta_horas, prioridade_default, data_criacao)
                        VALUES (:tenant_id, :nome, :descricao, :icone, :cor, :tempo_resposta_horas, :prioridade_default, :data_criacao)
                    """), {
                        'tenant_id': tenant_id_real,
                        'nome': categoria[0],
                        'descricao': categoria[1],
                        'icone': categoria[2],
                        'cor': categoria[3],
                        'tempo_resposta_horas': categoria[4],
                        'prioridade_default': categoria[5],
                        'data_criacao': datetime.now()
                    })
                
                db.session.commit()
                print("  ✅ 6 categorias criadas!")
            else:
                print("  ✅ Categorias já existem!")
            
            # PASSO 8: Criar condomínio padrão (SEM tenant_id)
            print("🏘️ Configurando condomínio padrão...")
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM condominio")).fetchone()
            condo_exists = result.count if result else 0
            
            if condo_exists == 0:
                db.session.execute(text("""
                    INSERT INTO condominio (nome, endereco, cnpj)
                    VALUES (:nome, :endereco, :cnpj)
                """), {
                    'nome': 'CondoTech Solutions',
                    'endereco': 'Rua da Tecnologia, 123 - São Paulo/SP - CEP: 01234-567',
                    'cnpj': '00.000.000/0001-00'
                })
                db.session.commit()
                print("  ✅ Condomínio padrão criado!")
            else:
                print("  ✅ Condomínio já existe!")
            
            # Commit final
            db.session.commit()
            
            print("\n🎉 CONFIGURAÇÃO MYSQL FINAL FUNCIONAL CONCLUÍDA!")
            print("=" * 65)
            print("✅ Sistema CondoTech Solutions 100% configurado")
            print("✅ Banco de dados: MySQL Professional")
            print(f"✅ Plano básico (ID: {plano_id_real})")
            print(f"✅ Tenant padrão (ID: {tenant_id_real})")
            print("✅ Usuário admin funcional")
            print("✅ Configurações sistema (chave-valor)")
            print("✅ Módulos ativos:")
            print("   🏊 Controle de Piscina")
            print("   🔧 Manutenção & Chamados")
            print("✅ 6 categorias de manutenção")
            print("✅ Condomínio padrão configurado")
            print("✅ Estruturas corretas utilizadas")
            print("✅ Zero erros de schema!")
            print("")
            print("🌐 Acesse: https://barrientos.pythonanywhere.com")
            print("👤 Login: admin / admin123")
            print("")
            print("🚀 Sistema MySQL FINAL FUNCIONAL!")
            print("💪 Todas as tabelas respeitadas!")
            print("🎯 Produção 100% operacional!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante configuração: {e}")
            print("💡 Verifique se a senha do MySQL está correta")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = configurar_sistema_mysql()
    if not success:
        sys.exit(1) 