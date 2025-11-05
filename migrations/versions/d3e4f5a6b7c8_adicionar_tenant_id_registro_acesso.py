"""adicionar tenant_id registro_acesso

Revision ID: d3e4f5a6b7c8
Revises: c22ad5b7299f
Create Date: 2025-11-05 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3e4f5a6b7c8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # Verificar se a coluna tenant_id já existe antes de adicionar
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection
    
    # Obter conexão do Alembic
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Verificar se a tabela existe
    tables = inspector.get_table_names()
    if 'registro_acesso' not in tables:
        return
    
    # Verificar se a coluna já existe
    columns = [col['name'] for col in inspector.get_columns('registro_acesso')]
    
    if 'tenant_id' not in columns:
        # Adicionar coluna tenant_id à tabela registro_acesso
        op.add_column('registro_acesso', sa.Column('tenant_id', sa.Integer(), nullable=True))
        
        # Atualizar valores existentes para tenant_id = 1
        op.execute("UPDATE registro_acesso SET tenant_id = 1 WHERE tenant_id IS NULL")
        
        # Criar índice
        try:
            op.create_index(op.f('ix_registro_acesso_tenant_id'), 'registro_acesso', ['tenant_id'], unique=False)
        except Exception:
            pass  # Índice pode já existir
        
        # Criar foreign key
        try:
            op.create_foreign_key('fk_registro_acesso_tenant_id', 'registro_acesso', 'tenants', ['tenant_id'], ['id'])
        except Exception:
            pass  # Foreign key pode já existir
    else:
        # Coluna já existe, apenas garantir que valores NULL sejam atualizados
        op.execute("UPDATE registro_acesso SET tenant_id = 1 WHERE tenant_id IS NULL")


def downgrade():
    # Remover coluna tenant_id da tabela registro_acesso
    from sqlalchemy import inspect
    
    # Obter conexão do Alembic
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Verificar se a tabela existe
    tables = inspector.get_table_names()
    if 'registro_acesso' not in tables:
        return
    
    # Verificar se a coluna existe
    columns = [col['name'] for col in inspector.get_columns('registro_acesso')]
    
    if 'tenant_id' in columns:
        try:
            # Remover foreign key
            op.drop_constraint('fk_registro_acesso_tenant_id', 'registro_acesso', type_='foreignkey')
        except Exception:
            pass
        
        try:
            # Remover índice
            op.drop_index(op.f('ix_registro_acesso_tenant_id'), table_name='registro_acesso')
        except Exception:
            pass
        
        try:
            # Remover coluna
            op.drop_column('registro_acesso', 'tenant_id')
        except Exception:
            pass

