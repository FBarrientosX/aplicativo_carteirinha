#!/usr/bin/env python3
"""
Configuração completa do CondoTech Solutions para MySQL
Execute: python3.10 configurar_condotech_mysql.py
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text

# Configurar variáveis de ambiente para MySQL
os.environ['MYSQL_DATABASE'] = 'barrientos$default'
os.environ['MYSQL_USER'] = 'barrientos'
os.environ['MYSQL_HOST'] = 'barrientos.mysql.pythonanywhere-services.com'

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def configurar_sistema_mysql():
    """Configura o sistema CondoTech Solutions no MySQL"""
    
    print("🚀 CondoTech Solutions - Configuração MySQL")
    print("=" * 50)
    
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
            db.engine.execute(text("SELECT 1"))
            print("  ✅ Conexão MySQL estabelecida!")
            
            # Criar todas as tabelas
            print("📋 Criando estrutura do banco...")
            db.create_all()
            print("  ✅ Tabelas criadas!")
            
            # PASSO 1: Criar/verificar tenant padrão
            print("🏢 Configurando tenant padrão...")
            
            tenant_exists = db.session.execute(text("SELECT COUNT(*) FROM tenants WHERE id = 1")).fetchone()[0]
            
            if tenant_exists == 0:
                db.session.execute(text("""
                    INSERT INTO tenants (nome, subdominio, ativo, data_criacao)
                    VALUES (%s, %s, %s, %s)
                """), ('Condomínio Padrão', 'default', 1, datetime.now()))
                print("  ✅ Tenant criado!")
            else:
                print("  ✅ Tenant já existe!")
            
            # PASSO 2: Criar usuário admin
            print("👤 Configurando usuário administrador...")
            
            admin_exists = db.session.execute(text("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")).fetchone()[0]
            
            if admin_exists == 0:
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash('admin123')
                
                db.session.execute(text("""
                    INSERT INTO usuarios (username, email, nome_completo, tipo_usuario, senha_hash, ativo, tenant_id, data_criacao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """), ('admin', 'admin@condotech.com', 'Administrador CondoTech', 'admin', password_hash, 1, 1, datetime.now()))
                print("  ✅ Admin criado! (admin / admin123)")
            else:
                print("  ✅ Admin já existe!")
            
            # PASSO 3: Configuração do sistema
            print("⚙️ Configurando sistema...")
            
            config_exists = db.session.execute(text("SELECT COUNT(*) FROM configuracao_sistema WHERE tenant_id = 1")).fetchone()[0]
            
            if config_exists == 0:
                db.session.execute(text("""
                    INSERT INTO configuracao_sistema (tenant_id, nome_condominio, endereco, cidade, estado, cep)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """), (1, 'CondoTech Solutions', 'Rua da Tecnologia, 123', 'São Paulo', 'SP', '01234-567'))
                print("  ✅ Configuração criada!")
            else:
                print("  ✅ Configuração já existe!")
            
            # PASSO 4: Criar módulos do sistema
            print("📦 Configurando módulos...")
            
            modulos_count = db.session.execute(text("SELECT COUNT(*) FROM modulos")).fetchone()[0]
            
            if modulos_count == 0:
                # Módulo Piscina
                db.session.execute(text("""
                    INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """), ('Controle de Piscina', 'piscina', 
                       'Sistema completo de controle de acesso à piscina com carteirinhas digitais e QR Code', 
                       'fas fa-swimming-pool', '#007bff', 1, 1, datetime.now()))
                
                # Módulo Manutenção
                db.session.execute(text("""
                    INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """), ('Manutenção & Chamados', 'manutencao', 
                       'Gestão completa de chamados de manutenção, ordens de serviço e controle de técnicos', 
                       'fas fa-tools', '#28a745', 2, 1, datetime.now()))
                
                print("  ✅ Módulos criados!")
            else:
                print("  ✅ Módulos já existem!")
            
            # PASSO 5: Ativar módulos para tenant
            print("🔌 Ativando módulos para tenant...")
            
            tenant_modules_count = db.session.execute(text("SELECT COUNT(*) FROM modulos_tenant WHERE tenant_id = 1")).fetchone()[0]
            
            if tenant_modules_count == 0:
                db.session.execute(text("""
                    INSERT INTO modulos_tenant (tenant_id, modulo_id, ativo, data_ativacao)
                    SELECT 1, id, 1, %s FROM modulos WHERE ativo = 1
                """), (datetime.now(),))
                print("  ✅ Módulos ativados para tenant!")
            else:
                print("  ✅ Módulos já ativados!")
            
            # PASSO 6: Criar categorias de manutenção
            print("🔧 Configurando categorias de manutenção...")
            
            categorias_count = db.session.execute(text("SELECT COUNT(*) FROM categorias_manutencao WHERE tenant_id = 1")).fetchone()[0]
            
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
                        VALUES (1, %s, %s, %s, %s, %s, %s, %s)
                    """), (*categoria, datetime.now()))
                
                print("  ✅ 6 categorias criadas!")
            else:
                print("  ✅ Categorias já existem!")
            
            # Commit de todas as mudanças
            db.session.commit()
            
            print("\n🎉 CONFIGURAÇÃO MYSQL CONCLUÍDA!")
            print("=" * 50)
            print("✅ Sistema CondoTech Solutions configurado")
            print("✅ Banco de dados: MySQL")
            print("✅ Tenant padrão criado")
            print("✅ Usuário admin configurado")
            print("✅ Módulos disponíveis:")
            print("   🏊 Controle de Piscina")
            print("   🔧 Manutenção & Chamados")
            print("✅ 6 categorias de manutenção")
            print("")
            print("🌐 Acesse: https://barrientos.pythonanywhere.com")
            print("👤 Login: admin / admin123")
            print("")
            print("🚀 Sistema pronto para uso!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante configuração: {e}")
            print("💡 Dica: Verifique se a senha do MySQL está correta")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = configurar_sistema_mysql()
    if not success:
        sys.exit(1) 