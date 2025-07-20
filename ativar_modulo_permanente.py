#!/usr/bin/env python3
"""
Script para ativar PERMANENTEMENTE o módulo de manutenção
Execute no PythonAnywhere para solução definitiva
"""

import os
import sys
from datetime import datetime

def configurar_ambiente():
    """Configura ambiente MySQL"""
    os.environ['MYSQL_DATABASE'] = 'barrientos$default'
    os.environ['MYSQL_USER'] = 'barrientos'
    os.environ['MYSQL_HOST'] = 'barrientos.mysql.pythonanywhere-services.com'
    
    # Solicitar senha
    mysql_password = input("Digite a senha do MySQL: ").strip()
    if not mysql_password:
        print("❌ Senha do MySQL é obrigatória!")
        return False
    
    os.environ['MYSQL_PASSWORD'] = mysql_password
    return True

def main():
    """Função principal"""
    print("🔧 CondoTech Solutions - Ativação Permanente Módulo Manutenção")
    print("=" * 65)
    
    # Configurar ambiente
    if not configurar_ambiente():
        return False
    
    # Adicionar path da aplicação
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from app import create_app, db
    from sqlalchemy import text
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔌 Conectando ao MySQL...")
            
            # Testar conexão
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("  ✅ Conexão estabelecida!")
            
            # 1. Buscar tenant padrão
            print("🏢 Buscando tenant padrão...")
            tenant_result = db.session.execute(text("""
                SELECT id, nome FROM tenants WHERE subdominio = 'default' LIMIT 1
            """)).fetchone()
            
            if not tenant_result:
                print("❌ Tenant padrão não encontrado!")
                return False
            
            tenant_id = tenant_result.id
            tenant_nome = tenant_result.nome
            print(f"  ✅ Tenant encontrado: {tenant_nome} (ID: {tenant_id})")
            
            # 2. Buscar módulo de manutenção
            print("📦 Buscando módulo de manutenção...")
            modulo_result = db.session.execute(text("""
                SELECT id, nome FROM modulos WHERE slug = 'manutencao' LIMIT 1
            """)).fetchone()
            
            if not modulo_result:
                print("❌ Módulo de manutenção não encontrado!")
                return False
            
            modulo_id = modulo_result.id
            modulo_nome = modulo_result.nome
            print(f"  ✅ Módulo encontrado: {modulo_nome} (ID: {modulo_id})")
            
            # 3. Verificar se já existe ativação
            print("🔍 Verificando ativação atual...")
            ativo_result = db.session.execute(text("""
                SELECT ativo FROM modulos_tenant 
                WHERE tenant_id = :tenant_id AND modulo_id = :modulo_id
            """), {'tenant_id': tenant_id, 'modulo_id': modulo_id}).fetchone()
            
            if ativo_result:
                if ativo_result.ativo:
                    print("  ✅ Módulo já está ativo!")
                else:
                    # Ativar módulo existente
                    print("  🔄 Ativando módulo existente...")
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
                    print("  ✅ Módulo ativado com sucesso!")
            else:
                # Inserir nova ativação
                print("  ➕ Criando nova ativação...")
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
                print("  ✅ Módulo ativado com sucesso!")
            
            # 4. Verificar outras ativações
            print("📋 Verificando todos os módulos ativos...")
            modulos_ativos = db.session.execute(text("""
                SELECT m.nome, m.slug, mt.ativo, mt.data_ativacao
                FROM modulos_tenant mt
                JOIN modulos m ON m.id = mt.modulo_id
                WHERE mt.tenant_id = :tenant_id AND mt.ativo = 1
                ORDER BY m.nome
            """), {'tenant_id': tenant_id}).fetchall()
            
            print("\n📊 MÓDULOS ATIVOS:")
            for modulo in modulos_ativos:
                data_ativacao = modulo.data_ativacao.strftime('%d/%m/%Y') if modulo.data_ativacao else 'N/A'
                print(f"  ✅ {modulo.nome} ({modulo.slug}) - Ativo desde: {data_ativacao}")
            
            print("\n🎉 ATIVAÇÃO PERMANENTE CONCLUÍDA!")
            print("=" * 50)
            print("✅ Módulo de Manutenção & Chamados ATIVO")
            print(f"✅ Tenant: {tenant_nome}")
            print(f"✅ Total de módulos ativos: {len(modulos_ativos)}")
            print("")
            print("🌐 Acesse: https://barrientos.pythonanywhere.com/manutencao/")
            print("👤 Login: admin / admin123")
            print("")
            print("🔒 Agora a verificação de segurança pode ser restaurada!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante ativação: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
    
    print("\n🚀 Execute 'git pull' e reload da aplicação para aplicar!") 