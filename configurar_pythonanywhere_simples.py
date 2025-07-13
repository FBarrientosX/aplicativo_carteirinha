#!/usr/bin/env python3
"""
Script SIMPLES para configurar o PythonAnywhere
Execute: python3.10 configurar_pythonanywhere_simples.py
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def configurar_pythonanywhere():
    """Configura o sistema usando SQL direto"""
    
    try:
        # Conectar ao banco SQLite
        conn = sqlite3.connect('carteirinha_piscina.db')
        cursor = conn.cursor()
        
        print("🔧 Configurando sistema para PythonAnywhere...")
        
        # 1. Verificar se tenant já existe
        cursor.execute("SELECT id FROM tenants WHERE id = 1")
        tenant_exists = cursor.fetchone()
        
        if not tenant_exists:
            print("⚠️  Tenant não encontrado, criando...")
            
            # Buscar plano
            cursor.execute("SELECT id FROM planos WHERE nome = 'Básico'")
            plano = cursor.fetchone()
            
            if plano:
                plano_id = plano[0]
                data_inicio = datetime.now().date()
                data_vencimento = data_inicio + timedelta(days=365)
                
                # Criar tenant
                cursor.execute("""
                    INSERT INTO tenants (nome, subdominio, email_responsavel, telefone, endereco, 
                                       plano_id, data_inicio, data_vencimento, status, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'Condomínio Demo',
                    'demo',
                    'admin@demo.com',
                    '(11) 99999-9999',
                    'Rua Demo, 123',
                    plano_id,
                    data_inicio,
                    data_vencimento,
                    'ativo',
                    datetime.now()
                ))
                
                print("✅ Tenant criado!")
            else:
                print("❌ Plano não encontrado!")
                return False
        else:
            print("✅ Tenant já existe!")
        
        # 2. Verificar usuário admin
        cursor.execute("SELECT id FROM usuarios WHERE tenant_id = 1 AND tipo_usuario = 'admin'")
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            print("⚠️  Usuário admin não encontrado, criando...")
            
            password_hash = generate_password_hash('123456')
            
            cursor.execute("""
                INSERT INTO usuarios (username, nome_completo, email, password_hash, 
                                    tenant_id, tipo_usuario, ativo, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'admin',
                'Administrador Demo',
                'admin@demo.com',
                password_hash,
                1,
                'admin',
                True,
                datetime.now()
            ))
            
            print("✅ Usuário admin criado!")
        else:
            print("✅ Usuário admin já existe!")
        
        # 3. Configurações básicas
        cursor.execute("SELECT id FROM configuracoes_tenant WHERE tenant_id = 1")
        config_exists = cursor.fetchone()
        
        if not config_exists:
            print("⚠️  Configurações não encontradas, criando...")
            
            configs = [
                (1, 'sistema', 'nome_sistema', 'Sistema Carteirinha Demo', 'texto'),
                (1, 'email', 'email_remetente', 'admin@demo.com', 'email'),
                (1, 'sistema', 'mensagem_boas_vindas', 'Bem-vindo ao sistema de carteirinhas!', 'texto'),
                (1, 'sistema', 'dias_aviso_vencimento', '7', 'numero'),
                (1, 'visual', 'cor_primaria', '#007bff', 'texto'),
                (1, 'visual', 'cor_secundaria', '#6c757d', 'texto')
            ]
            
            for config in configs:
                cursor.execute("""
                    INSERT INTO configuracoes_tenant (tenant_id, categoria, chave, valor, tipo, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (*config, datetime.now()))
            
            print("✅ Configurações criadas!")
        else:
            print("✅ Configurações já existem!")
        
        # Commit das mudanças
        conn.commit()
        conn.close()
        
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("=" * 50)
        print("INFORMAÇÕES DE ACESSO:")
        print(f"🌐 URL: https://barrientos.pythonanywhere.com")
        print(f"📧 Email: admin@demo.com")
        print(f"🔑 Senha: 123456")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

def main():
    """Função principal"""
    try:
        if configurar_pythonanywhere():
            print("\n✅ Sistema configurado com sucesso!")
            print("🚀 Agora reload o Web App e acesse: https://barrientos.pythonanywhere.com")
        else:
            print("\n❌ Erro na configuração!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 