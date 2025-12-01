"""adicionar unidade e campos core

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2024-11-24 23:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'e4f5a6b7c8d9'
down_revision = 'd3e4f5a6b7c8'
branch_labels = None
depends_on = None


def upgrade():
    # Verificar se as colunas/tabelas já existem
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # 1. Criar tabela unidades
    if 'unidades' not in tables:
        op.create_table('unidades',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=False),
            sa.Column('condominio_id', sa.Integer(), nullable=False),
            sa.Column('bloco', sa.String(length=10), nullable=False),
            sa.Column('apartamento', sa.String(length=10), nullable=False),
            sa.Column('tipo', sa.String(length=20), nullable=True, server_default='apartamento'),
            sa.Column('area_util', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('vagas_garagem', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('ocupada', sa.Boolean(), nullable=True, server_default='0'),
            sa.Column('data_criacao', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['condominio_id'], ['condominio.id'], ),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('tenant_id', 'bloco', 'apartamento', name='uq_unidade_tenant')
        )
        op.create_index(op.f('ix_unidades_tenant_id'), 'unidades', ['tenant_id'], unique=False)
    
    # 2. Adicionar campos ao condominio
    if 'condominio' in tables:
        columns = [col['name'] for col in inspector.get_columns('condominio')]
        
        if 'tenant_id' not in columns:
            op.add_column('condominio', sa.Column('tenant_id', sa.Integer(), nullable=True, server_default='1'))
            op.create_index(op.f('ix_condominio_tenant_id'), 'condominio', ['tenant_id'], unique=False)
            op.create_foreign_key('fk_condominio_tenant_id', 'condominio', 'tenants', ['tenant_id'], ['id'])
            op.execute("UPDATE condominio SET tenant_id = 1 WHERE tenant_id IS NULL")
            # Tornar NOT NULL após popular
            op.alter_column('condominio', 'tenant_id', nullable=False)
        
        if 'email_portaria' not in columns:
            op.add_column('condominio', sa.Column('email_portaria', sa.String(length=120), nullable=True))
        
        if 'email_sindico' not in columns:
            op.add_column('condominio', sa.Column('email_sindico', sa.String(length=120), nullable=True))
        
        if 'documentos' not in columns:
            # SQLite não suporta JSON nativamente, usar TEXT
            op.add_column('condominio', sa.Column('documentos', sa.Text(), nullable=True))
        
        if 'data_atualizacao' not in columns:
            op.add_column('condominio', sa.Column('data_atualizacao', sa.DateTime(), nullable=True))
    
    # 3. Adicionar campos ao usuarios
    if 'usuarios' in tables:
        columns = [col['name'] for col in inspector.get_columns('usuarios')]
        
        if 'unidade_id' not in columns:
            op.add_column('usuarios', sa.Column('unidade_id', sa.Integer(), nullable=True))
            op.create_foreign_key('fk_usuarios_unidade_id', 'usuarios', 'unidades', ['unidade_id'], ['id'])
        
        if 'email_verificado' not in columns:
            op.add_column('usuarios', sa.Column('email_verificado', sa.Boolean(), nullable=True, server_default='0'))
        
        if 'data_ultimo_acesso' not in columns:
            op.add_column('usuarios', sa.Column('data_ultimo_acesso', sa.DateTime(), nullable=True))


def downgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Remover campos de usuarios
    if 'usuarios' in tables:
        columns = [col['name'] for col in inspector.get_columns('usuarios')]
        
        if 'data_ultimo_acesso' in columns:
            op.drop_column('usuarios', 'data_ultimo_acesso')
        
        if 'email_verificado' in columns:
            op.drop_column('usuarios', 'email_verificado')
        
        if 'unidade_id' in columns:
            try:
                op.drop_constraint('fk_usuarios_unidade_id', 'usuarios', type_='foreignkey')
            except Exception:
                pass
            op.drop_column('usuarios', 'unidade_id')
    
    # Remover campos de condominio
    if 'condominio' in tables:
        columns = [col['name'] for col in inspector.get_columns('condominio')]
        
        if 'data_atualizacao' in columns:
            op.drop_column('condominio', 'data_atualizacao')
        
        if 'documentos' in columns:
            op.drop_column('condominio', 'documentos')
        
        if 'email_sindico' in columns:
            op.drop_column('condominio', 'email_sindico')
        
        if 'email_portaria' in columns:
            op.drop_column('condominio', 'email_portaria')
        
        if 'tenant_id' in columns:
            try:
                op.drop_constraint('fk_condominio_tenant_id', 'condominio', type_='foreignkey')
            except Exception:
                pass
            try:
                op.drop_index(op.f('ix_condominio_tenant_id'), table_name='condominio')
            except Exception:
                pass
            op.drop_column('condominio', 'tenant_id')
    
    # Remover tabela unidades
    if 'unidades' in tables:
        op.drop_table('unidades')

