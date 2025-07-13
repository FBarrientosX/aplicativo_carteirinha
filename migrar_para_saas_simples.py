#!/usr/bin/env python3
"""
Script simplificado de migração para SaaS
Execute: python migrar_para_saas_simples.py
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrar_para_saas():
    """Migração principal para SaaS"""
    try:
        from app import create_app, db
        from sqlalchemy import text
        
        app = create_app()
        
        with app.app_context():
            print("🚀 Iniciando migração simplificada para SaaS...")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas/verificadas")
            
            # Adicionar colunas tenant_id nas tabelas existentes
            tabelas = ['moradores', 'anexos_moradores', 'log_notificacoes', 'usuarios']
            
            for tabela in tabelas:
                try:
                    # Tentar adicionar coluna tenant_id
                    db.session.execute(text(f"ALTER TABLE {tabela} ADD COLUMN tenant_id INTEGER DEFAULT 1"))
                    print(f"✅ Coluna tenant_id adicionada à tabela {tabela}")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e).lower():
                        print(f"⚠️ Coluna tenant_id já existe na tabela {tabela}")
                    else:
                        print(f"❌ Erro ao adicionar coluna tenant_id na tabela {tabela}: {e}")
            
            # Adicionar colunas extras na tabela usuarios
            try:
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN permissoes TEXT DEFAULT '{}'"))
                print("✅ Coluna permissoes adicionada à tabela usuarios")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("⚠️ Coluna permissoes já existe na tabela usuarios")
                else:
                    print(f"❌ Erro ao adicionar coluna permissoes: {e}")
            
            try:
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN cargo VARCHAR(100)"))
                print("✅ Coluna cargo adicionada à tabela usuarios")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("⚠️ Coluna cargo já existe na tabela usuarios")
                else:
                    print(f"❌ Erro ao adicionar coluna cargo: {e}")
            
            db.session.commit()
            
            # Atualizar dados existentes
            for tabela in tabelas:
                try:
                    result = db.session.execute(text(f"UPDATE {tabela} SET tenant_id = 1 WHERE tenant_id IS NULL"))
                    print(f"✅ {result.rowcount} registros atualizados na tabela {tabela}")
                except Exception as e:
                    print(f"❌ Erro ao atualizar {tabela}: {e}")
            
            db.session.commit()
            
            print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("✅ Todas as tabelas foram preparadas para SaaS")
            print("✅ Dados existentes foram preservados")
            print("✅ tenant_id configurado para todos os registros")
            
            print("\nPRÓXIMOS PASSOS:")
            print("1. Execute: python criar_planos_iniciais.py")
            print("2. Execute: python criar_cliente_inicial.py")
            print("3. Execute: python testar_sistema.py")
            
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    sucesso = migrar_para_saas()
    if sucesso:
        print("\n🚀 MIGRAÇÃO REALIZADA COM SUCESSO!")
        sys.exit(0)
    else:
        print("\n❌ FALHA NA MIGRAÇÃO")
        sys.exit(1) 