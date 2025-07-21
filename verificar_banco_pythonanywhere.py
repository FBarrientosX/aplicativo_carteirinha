#!/usr/bin/env python3
"""
Verificar Status do Banco no PythonAnywhere
Diagnosticar problema com tenant_id
"""

from app import create_app, db
from sqlalchemy import text
import sys

def verificar_banco():
    """Verificar estrutura e tipo do banco"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 DIAGNÓSTICO DO BANCO DE DADOS")
            print("=" * 50)
            
            # 1. Verificar tipo de banco
            print("1. TIPO DE BANCO:")
            engine_name = db.engine.name
            print(f"   Motor: {engine_name}")
            print(f"   URL: {str(db.engine.url)}")
            
            # 2. Verificar se tabela registro_acesso existe
            print("\n2. VERIFICAR TABELA registro_acesso:")
            try:
                if engine_name == 'sqlite':
                    # SQLite
                    result = db.session.execute(text("PRAGMA table_info(registro_acesso)")).fetchall()
                    if result:
                        print("   ✅ Tabela existe")
                        print("   Colunas:")
                        for row in result:
                            print(f"      - {row[1]} ({row[2]})")
                        
                        # Verificar se tenant_id existe
                        colunas = [row[1] for row in result]
                        if 'tenant_id' in colunas:
                            print("   ✅ Coluna tenant_id EXISTS!")
                        else:
                            print("   ❌ Coluna tenant_id NÃO EXISTE!")
                    else:
                        print("   ❌ Tabela não existe")
                        
                elif engine_name == 'mysql':
                    # MySQL
                    result = db.session.execute(text("DESCRIBE registro_acesso")).fetchall()
                    if result:
                        print("   ✅ Tabela existe")
                        print("   Colunas:")
                        for row in result:
                            print(f"      - {row[0]} ({row[1]})")
                        
                        # Verificar se tenant_id existe
                        colunas = [row[0] for row in result]
                        if 'tenant_id' in colunas:
                            print("   ✅ Coluna tenant_id EXISTS!")
                        else:
                            print("   ❌ Coluna tenant_id NÃO EXISTE!")
                    else:
                        print("   ❌ Tabela não existe")
                        
                else:
                    print(f"   ⚠️ Tipo de banco não suportado: {engine_name}")
                    
            except Exception as e:
                print(f"   ❌ Erro ao verificar tabela: {e}")
            
            # 3. Verificar dados na tabela
            print("\n3. DADOS NA TABELA:")
            try:
                result = db.session.execute(text("SELECT COUNT(*) FROM registro_acesso")).fetchone()
                count = result[0] if result else 0
                print(f"   Total de registros: {count}")
                
                if count > 0:
                    sample = db.session.execute(text("SELECT * FROM registro_acesso LIMIT 1")).fetchone()
                    print(f"   Amostra: {sample}")
                    
            except Exception as e:
                print(f"   ❌ Erro ao contar registros: {e}")
            
            # 4. Verificar tabela tenants
            print("\n4. VERIFICAR TABELA tenants:")
            try:
                if engine_name == 'sqlite':
                    result = db.session.execute(text("PRAGMA table_info(tenants)")).fetchall()
                elif engine_name == 'mysql':
                    result = db.session.execute(text("DESCRIBE tenants")).fetchall()
                    
                if result:
                    print("   ✅ Tabela tenants existe")
                else:
                    print("   ❌ Tabela tenants NÃO EXISTE!")
                    
            except Exception as e:
                print(f"   ❌ Erro: {e}")
            
            # 5. Tentar executar migração
            print("\n5. EXECUTAR MIGRAÇÃO AUTOMÁTICA:")
            try:
                if engine_name == 'sqlite':
                    # SQLite
                    db.session.execute(text("ALTER TABLE registro_acesso ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1"))
                    print("   ✅ Coluna tenant_id adicionada (SQLite)")
                elif engine_name == 'mysql':
                    # MySQL
                    db.session.execute(text("ALTER TABLE registro_acesso ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1"))
                    print("   ✅ Coluna tenant_id adicionada (MySQL)")
                
                db.session.commit()
                print("   ✅ Migração aplicada com sucesso!")
                
            except Exception as e:
                print(f"   ⚠️ Migração falhou ou já foi aplicada: {e}")
                db.session.rollback()
            
            # 6. Verificar novamente
            print("\n6. VERIFICAÇÃO FINAL:")
            try:
                if engine_name == 'sqlite':
                    result = db.session.execute(text("PRAGMA table_info(registro_acesso)")).fetchall()
                    colunas = [row[1] for row in result]
                elif engine_name == 'mysql':
                    result = db.session.execute(text("DESCRIBE registro_acesso")).fetchall()
                    colunas = [row[0] for row in result]
                
                if 'tenant_id' in colunas:
                    print("   🎉 TENANT_ID AGORA EXISTE!")
                    
                    # Testar query
                    test = db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1")).fetchone()
                    print(f"   ✅ Query test OK: {test}")
                    
                else:
                    print("   ❌ tenant_id ainda não existe")
                    
            except Exception as e:
                print(f"   ❌ Erro na verificação final: {e}")
                
        except Exception as e:
            print(f"❌ ERRO GERAL: {e}")

if __name__ == "__main__":
    verificar_banco() 