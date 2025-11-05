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
    # Adicionar coluna tenant_id à tabela registro_acesso
    try:
        op.add_column('registro_acesso', sa.Column('tenant_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_registro_acesso_tenant_id'), 'registro_acesso', ['tenant_id'], unique=False)
        op.create_foreign_key(None, 'registro_acesso', 'tenants', ['tenant_id'], ['id'])
    except Exception as e:
        # Se a coluna já existir, ignorar o erro
        print(f"Erro ao adicionar coluna tenant_id: {e}")


def downgrade():
    # Remover coluna tenant_id da tabela registro_acesso
    try:
        op.drop_constraint(None, 'registro_acesso', type_='foreignkey')
        op.drop_index(op.f('ix_registro_acesso_tenant_id'), table_name='registro_acesso')
        op.drop_column('registro_acesso', 'tenant_id')
    except Exception:
        pass

