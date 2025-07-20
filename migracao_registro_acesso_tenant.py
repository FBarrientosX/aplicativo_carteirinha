"""
Migração: Adicionar tenant_id ao RegistroAcesso
Criado em: 2024-01-20 17:50:00
VERSÃO MYSQL PARA PYTHONANYWHERE
"""

from app import db, create_app
from sqlalchemy import text

def executar_migracao():
    """Executar migração para adicionar tenant_id ao registro_acesso (MySQL)"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se coluna já existe (MySQL)
            result = db.session.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE()
                AND table_name = 'registro_acesso' 
                AND column_name = 'tenant_id'
            """)).fetchone()
            
            if result and result.count == 0:
                print("🔧 Adicionando coluna tenant_id à tabela registro_acesso...")
                
                # Adicionar coluna tenant_id (MySQL)
                db.session.execute(text("""
                    ALTER TABLE registro_acesso 
                    ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1
                """))
                
                print("   ✅ Coluna tenant_id adicionada")
                
                # Criar índice (MySQL)
                db.session.execute(text("""
                    CREATE INDEX idx_registro_acesso_tenant_id 
                    ON registro_acesso(tenant_id)
                """))
                
                print("   ✅ Índice criado")
                
                # Atualizar registros existentes baseado no morador (MySQL)
                db.session.execute(text("""
                    UPDATE registro_acesso ra
                    JOIN moradores m ON ra.morador_id = m.id
                    SET ra.tenant_id = m.tenant_id
                    WHERE ra.tenant_id = 1 AND m.tenant_id IS NOT NULL
                """))
                
                # Verificar quantos registros foram atualizados
                count_result = db.session.execute(text("""
                    SELECT COUNT(*) as count FROM registro_acesso 
                    WHERE tenant_id != 1
                """)).fetchone()
                
                print(f"   ✅ Registros com tenant_id atualizado: {count_result.count if count_result else 0}")
                
                # Criar foreign key se a tabela tenants existe
                try:
                    # Verificar se tabela tenants existe
                    db.session.execute(text("SELECT 1 FROM tenants LIMIT 1")).fetchone()
                    
                    # Criar foreign key
                    db.session.execute(text("""
                        ALTER TABLE registro_acesso 
                        ADD CONSTRAINT fk_registro_acesso_tenant_id 
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                    """))
                    print("   ✅ Foreign key criada")
                    
                except Exception as e:
                    print(f"   ⚠️  Foreign key não criada: {e}")
                
                db.session.commit()
                print("   ✅ Migração concluída com sucesso!")
                
            else:
                print("   ℹ️  Coluna tenant_id já existe na tabela registro_acesso")
                
            # Verificar resultado (MySQL)
            result_check = db.session.execute(text("DESCRIBE registro_acesso")).fetchall()
            print(f"\n📊 Estrutura atual da tabela registro_acesso:")
            for row in result_check:
                print(f"   - {row[0]} ({row[1]}) {'NOT NULL' if row[2] == 'NO' else 'NULL'} {row[4] if row[4] else ''}")
                
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Erro na migração: {e}")
            raise

if __name__ == "__main__":
    executar_migracao()
