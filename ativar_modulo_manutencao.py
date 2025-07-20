#!/usr/bin/env python3
"""
Script para ativar o módulo de manutenção para o tenant padrão
"""

import os
import sys
from datetime import datetime

# Configurar variáveis de ambiente
os.environ['MYSQL_DATABASE'] = 'barrientos$default'
os.environ['MYSQL_USER'] = 'barrientos'
os.environ['MYSQL_HOST'] = 'barrientos.mysql.pythonanywhere-services.com'

# Solicitar senha
mysql_password = input("Digite a senha do MySQL: ").strip()
if not mysql_password:
    print("❌ Senha do MySQL é obrigatória!")
    sys.exit(1)

os.environ['MYSQL_PASSWORD'] = mysql_password

# Adicionar path da aplicação
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def ativar_modulo_manutencao():
    """Ativa o módulo de manutenção para o tenant padrão"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔌 Conectando ao MySQL...")
            
            # Testar conexão
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("  ✅ Conexão estabelecida!")
            
            # Buscar tenant padrão
            tenant_result = db.session.execute(text("SELECT id FROM tenants WHERE subdominio = 'default' LIMIT 1")).fetchone()
            if not tenant_result:
                print("❌ Tenant padrão não encontrado!")
                return False
            
            tenant_id = tenant_result.id
            print(f"  📋 Tenant ID: {tenant_id}")
            
            # Buscar módulo de manutenção
            modulo_result = db.session.execute(text("SELECT id FROM modulos WHERE slug = 'manutencao' LIMIT 1")).fetchone()
            if not modulo_result:
                print("❌ Módulo de manutenção não encontrado!")
                return False
            
            modulo_id = modulo_result.id
            print(f"  📦 Módulo ID: {modulo_id}")
            
            # Verificar se já está ativo
            ativo_result = db.session.execute(text("""
                SELECT ativo FROM modulos_tenant 
                WHERE tenant_id = :tenant_id AND modulo_id = :modulo_id
            """), {'tenant_id': tenant_id, 'modulo_id': modulo_id}).fetchone()
            
            if ativo_result:
                if ativo_result.ativo:
                    print("  ✅ Módulo já está ativo!")
                else:
                    # Ativar módulo existente
                    db.session.execute(text("""
                        UPDATE modulos_tenant 
                        SET ativo = 1, data_ativacao = :data_ativacao
                        WHERE tenant_id = :tenant_id AND modulo_id = :modulo_id
                    """), {
                        'tenant_id': tenant_id, 
                        'modulo_id': modulo_id,
                        'data_ativacao': datetime.now()
                    })
                    db.session.commit()
                    print("  ✅ Módulo ativado!")
            else:
                # Inserir novo registro ativo
                db.session.execute(text("""
                    INSERT INTO modulos_tenant (tenant_id, modulo_id, ativo, data_ativacao)
                    VALUES (:tenant_id, :modulo_id, :ativo, :data_ativacao)
                """), {
                    'tenant_id': tenant_id,
                    'modulo_id': modulo_id,
                    'ativo': True,
                    'data_ativacao': datetime.now()
                })
                db.session.commit()
                print("  ✅ Módulo ativado!")
            
            print("\n🎉 MÓDULO DE MANUTENÇÃO ATIVADO!")
            print("✅ Agora você pode acessar o módulo de manutenção")
            print("🌐 Acesse: https://barrientos.pythonanywhere.com/manutencao/")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = ativar_modulo_manutencao()
    if not success:
        sys.exit(1) 