"""fix all missing columns - garantir que todas as colunas opcionais existem

Revision ID: fix_all_missing_columns
Revises: fix_usuarios_campos
Create Date: 2025-12-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'fix_all_missing_columns'
down_revision = 'fix_usuarios_campos'
branch_labels = None
depends_on = None


def upgrade():
    """Garantir que todas as colunas opcionais existem"""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # ===== TABELA: condominio =====
    if 'condominio' in tables:
        columns = [col['name'] for col in inspector.get_columns('condominio')]
        
        if 'tenant_id' not in columns:
            op.add_column('condominio', sa.Column('tenant_id', sa.Integer(), nullable=True, server_default='1'))
            op.create_index('ix_condominio_tenant_id', 'condominio', ['tenant_id'], unique=False)
            try:
                op.create_foreign_key('fk_condominio_tenant_id', 'condominio', 'tenants', ['tenant_id'], ['id'])
            except Exception:
                pass
            op.execute("UPDATE condominio SET tenant_id = 1 WHERE tenant_id IS NULL")
        
        if 'email_portaria' not in columns:
            op.add_column('condominio', sa.Column('email_portaria', sa.String(length=120), nullable=True))
        
        if 'email_sindico' not in columns:
            op.add_column('condominio', sa.Column('email_sindico', sa.String(length=120), nullable=True))
        
        if 'documentos' not in columns:
            # SQLite não suporta JSON nativamente, usar TEXT
            op.add_column('condominio', sa.Column('documentos', sa.Text(), nullable=True))
        
        if 'data_atualizacao' not in columns:
            op.add_column('condominio', sa.Column('data_atualizacao', sa.DateTime(), nullable=True))
    
    # ===== TABELA: unidades =====
    if 'unidades' in tables:
        columns = [col['name'] for col in inspector.get_columns('unidades')]
        
        if 'tenant_id' not in columns:
            op.add_column('unidades', sa.Column('tenant_id', sa.Integer(), nullable=True, server_default='1'))
            op.create_index('ix_unidades_tenant_id', 'unidades', ['tenant_id'], unique=False)
            try:
                op.create_foreign_key('fk_unidades_tenant_id', 'unidades', 'tenants', ['tenant_id'], ['id'])
            except Exception:
                pass
            op.execute("UPDATE unidades SET tenant_id = 1 WHERE tenant_id IS NULL")
    
    # ===== TABELA: moradores =====
    if 'moradores' in tables:
        columns = [col['name'] for col in inspector.get_columns('moradores')]
        
        if 'tenant_id' not in columns:
            op.add_column('moradores', sa.Column('tenant_id', sa.Integer(), nullable=True, server_default='1'))
            op.create_index('ix_moradores_tenant_id', 'moradores', ['tenant_id'], unique=False)
            try:
                op.create_foreign_key('fk_moradores_tenant_id', 'moradores', 'tenants', ['tenant_id'], ['id'])
            except Exception:
                pass
            op.execute("UPDATE moradores SET tenant_id = 1 WHERE tenant_id IS NULL")
    
    # ===== TABELA: anexos_moradores =====
    if 'anexos_moradores' in tables:
        columns = [col['name'] for col in inspector.get_columns('anexos_moradores')]
        
        if 'tenant_id' not in columns:
            op.add_column('anexos_moradores', sa.Column('tenant_id', sa.Integer(), nullable=True, server_default='1'))
            op.create_index('ix_anexos_moradores_tenant_id', 'anexos_moradores', ['tenant_id'], unique=False)
            try:
                op.create_foreign_key('fk_anexos_moradores_tenant_id', 'anexos_moradores', 'tenants', ['tenant_id'], ['id'])
            except Exception:
                pass
            op.execute("UPDATE anexos_moradores SET tenant_id = 1 WHERE tenant_id IS NULL")
    
    # ===== TABELA: log_notificacoes =====
    if 'log_notificacoes' in tables:
        columns = [col['name'] for col in inspector.get_columns('log_notificacoes')]
        
        if 'tenant_id' not in columns:
            op.add_column('log_notificacoes', sa.Column('tenant_id', sa.Integer(), nullable=True, server_default='1'))
            op.create_index('ix_log_notificacoes_tenant_id', 'log_notificacoes', ['tenant_id'], unique=False)
            try:
                op.create_foreign_key('fk_log_notificacoes_tenant_id', 'log_notificacoes', 'tenants', ['tenant_id'], ['id'])
            except Exception:
                pass
            op.execute("UPDATE log_notificacoes SET tenant_id = 1 WHERE tenant_id IS NULL")


def downgrade():
    """Remover colunas opcionais (se necessário)"""
    # Esta função pode ser deixada vazia ou implementada conforme necessário
    pass

