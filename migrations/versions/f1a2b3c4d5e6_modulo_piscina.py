"""Adicionar tabelas do módulo Piscina

Revision ID: f1a2b3c4d5e6
Revises: e4f5a6b7c8d9
Create Date: 2025-11-24 21:25:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e4f5a6b7c8d9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'carteirinhas_piscina',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('morador_id', sa.Integer(), nullable=False),
        sa.Column('data_emissao', sa.Date(), nullable=False),
        sa.Column('data_validade', sa.Date(), nullable=False),
        sa.Column('aprovada', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('ativa', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('qr_code', sa.String(length=500), nullable=False),
        sa.Column('qr_code_image', sa.String(length=500), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=True),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['morador_id'], ['moradores.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_carteirinhas_piscina_tenant_id'), 'carteirinhas_piscina', ['tenant_id'], unique=False)

    op.create_table(
        'plantoes_salva_vidas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('salva_vidas_id', sa.Integer(), nullable=False),
        sa.Column('data_inicio', sa.DateTime(), nullable=False),
        sa.Column('data_fim', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='ativo'),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['salva_vidas_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plantoes_salva_vidas_tenant_id'), 'plantoes_salva_vidas', ['tenant_id'], unique=False)

    op.create_table(
        'registros_acesso_piscina',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('morador_id', sa.Integer(), nullable=False),
        sa.Column('carteirinha_id', sa.Integer(), nullable=True),
        sa.Column('salva_vidas_id', sa.Integer(), nullable=True),
        sa.Column('tipo', sa.String(length=10), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metodo', sa.String(length=20), nullable=False, server_default='manual'),
        sa.Column('tempo_permanencia_minutos', sa.Integer(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('ip_origem', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['carteirinha_id'], ['carteirinhas_piscina.id'], ),
        sa.ForeignKeyConstraint(['morador_id'], ['moradores.id'], ),
        sa.ForeignKeyConstraint(['salva_vidas_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_registros_acesso_piscina_tenant_id'), 'registros_acesso_piscina', ['tenant_id'], unique=False)

    op.create_table(
        'ocorrencias_piscina',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('salva_vidas_id', sa.Integer(), nullable=False),
        sa.Column('morador_id', sa.Integer(), nullable=True),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('severidade', sa.String(length=20), nullable=False, server_default='baixa'),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('fotos', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='aberta'),
        sa.Column('data_ocorrencia', sa.DateTime(), nullable=False),
        sa.Column('data_resolucao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['morador_id'], ['moradores.id'], ),
        sa.ForeignKeyConstraint(['salva_vidas_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ocorrencias_piscina_tenant_id'), 'ocorrencias_piscina', ['tenant_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ocorrencias_piscina_tenant_id'), table_name='ocorrencias_piscina')
    op.drop_table('ocorrencias_piscina')
    op.drop_index(op.f('ix_registros_acesso_piscina_tenant_id'), table_name='registros_acesso_piscina')
    op.drop_table('registros_acesso_piscina')
    op.drop_index(op.f('ix_plantoes_salva_vidas_tenant_id'), table_name='plantoes_salva_vidas')
    op.drop_table('plantoes_salva_vidas')
    op.drop_index(op.f('ix_carteirinhas_piscina_tenant_id'), table_name='carteirinhas_piscina')
    op.drop_table('carteirinhas_piscina')


