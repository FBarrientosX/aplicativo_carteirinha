"""fix usuarios campos - garantir que colunas existem

Revision ID: fix_usuarios_campos
Revises: fix_registro_acesso_tenant
Create Date: 2025-12-01 23:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'fix_usuarios_campos'
down_revision = 'fix_registro_acesso_tenant'
branch_labels = None
depends_on = None


def upgrade():
    """Garantir que colunas opcionais existem na tabela usuarios"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'usuarios' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('usuarios')]
    
    # Adicionar email_verificado se não existir
    if 'email_verificado' not in columns:
        op.add_column('usuarios', sa.Column('email_verificado', sa.Boolean(), nullable=True, server_default='0'))
        op.execute("UPDATE usuarios SET email_verificado = 0 WHERE email_verificado IS NULL")
    
    # Adicionar data_ultimo_acesso se não existir
    if 'data_ultimo_acesso' not in columns:
        op.add_column('usuarios', sa.Column('data_ultimo_acesso', sa.DateTime(), nullable=True))
    
    # Adicionar unidade_id se não existir
    if 'unidade_id' not in columns:
        op.add_column('usuarios', sa.Column('unidade_id', sa.Integer(), nullable=True))
        try:
            op.create_foreign_key(
                'fk_usuarios_unidade_id',
                'usuarios',
                'unidades',
                ['unidade_id'],
                ['id']
            )
        except Exception:
            pass  # Foreign key pode falhar se tabela unidades não existir
    
    # Adicionar permissoes se não existir (JSON/TEXT)
    if 'permissoes' not in columns:
        # SQLite não suporta JSON nativamente, usar TEXT
        op.add_column('usuarios', sa.Column('permissoes', sa.Text(), nullable=True))
        op.execute("UPDATE usuarios SET permissoes = '{}' WHERE permissoes IS NULL")


def downgrade():
    """Remover colunas opcionais (se necessário)"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'usuarios' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('usuarios')]
    
    if 'permissoes' in columns:
        try:
            op.drop_column('usuarios', 'permissoes')
        except Exception:
            pass
    
    if 'unidade_id' in columns:
        try:
            op.drop_constraint('fk_usuarios_unidade_id', 'usuarios', type_='foreignkey')
        except Exception:
            pass
        try:
            op.drop_column('usuarios', 'unidade_id')
        except Exception:
            pass
    
    if 'data_ultimo_acesso' in columns:
        try:
            op.drop_column('usuarios', 'data_ultimo_acesso')
        except Exception:
            pass
    
    if 'email_verificado' in columns:
        try:
            op.drop_column('usuarios', 'email_verificado')
        except Exception:
            pass

