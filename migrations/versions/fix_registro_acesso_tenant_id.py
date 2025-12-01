"""fix registro_acesso tenant_id - garantir que coluna existe

Revision ID: fix_registro_acesso_tenant
Revises: e4f5a6b7c8d9
Create Date: 2025-11-05 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'fix_registro_acesso_tenant'
down_revision = 'f1a2b3c4d5e6'  # Após módulo piscina
branch_labels = None
depends_on = None


def upgrade():
    """Garantir que tenant_id existe na tabela registro_acesso"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'registro_acesso' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('registro_acesso')]
    
    if 'tenant_id' not in columns:
        # Adicionar coluna tenant_id
        op.add_column('registro_acesso', sa.Column('tenant_id', sa.Integer(), nullable=True))
        
        # Atualizar valores existentes para tenant_id = 1
        op.execute("UPDATE registro_acesso SET tenant_id = 1 WHERE tenant_id IS NULL")
        
        # Criar índice
        try:
            op.create_index('ix_registro_acesso_tenant_id', 'registro_acesso', ['tenant_id'], unique=False)
        except Exception:
            pass  # Índice pode já existir
        
        # Criar foreign key
        try:
            op.create_foreign_key(
                'fk_registro_acesso_tenant_id',
                'registro_acesso',
                'tenants',
                ['tenant_id'],
                ['id']
            )
        except Exception:
            pass  # Foreign key pode já existir
    else:
        # Coluna já existe, apenas garantir que valores NULL sejam atualizados
        op.execute("UPDATE registro_acesso SET tenant_id = 1 WHERE tenant_id IS NULL")


def downgrade():
    """Remover tenant_id da tabela registro_acesso (se necessário)"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'registro_acesso' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('registro_acesso')]
    
    if 'tenant_id' in columns:
        try:
            op.drop_constraint('fk_registro_acesso_tenant_id', 'registro_acesso', type_='foreignkey')
        except Exception:
            pass
        
        try:
            op.drop_index('ix_registro_acesso_tenant_id', table_name='registro_acesso')
        except Exception:
            pass
        
        try:
            op.drop_column('registro_acesso', 'tenant_id')
        except Exception:
            pass

