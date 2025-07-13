#!/usr/bin/env python3
"""
Script para migrar dados existentes para o sistema SaaS multi-tenant
Execute: python migrar_para_saas.py
"""

from app import create_app, db
from datetime import datetime, timedelta
from decimal import Decimal

def migrar_para_saas():
    """Migra dados existentes para o sistema SaaS"""
    
    app = create_app()
    
    with app.app_context():
        print("🚀 Iniciando migração para SaaS multi-tenant...")
        
        # 1. Criar tabelas novas (se não existirem)
        try:
            db.create_all()
            print("✅ Tabelas criadas/verificadas")
        except Exception as e:
            print(f"⚠️ Erro ao criar tabelas: {e}")
        
        # 2. Criar plano padrão
        criar_plano_padrao()
        
        # 3. Criar tenant padrão
        tenant = criar_tenant_padrao()
        
        # 4. Adicionar colunas tenant_id se não existirem
        adicionar_colunas_tenant_id()
        
        # 5. Atualizar dados existentes
        atualizar_dados_existentes(tenant.id)
        
        # 6. Criar usuário administrador padrão
        criar_usuario_admin(tenant.id)
        
        print("\n🎉 Migração concluída com sucesso!")
        print(f"🌐 Tenant padrão: {tenant.nome}")
        print(f"📧 Admin: admin@sistema.local")
        print(f"🔑 Senha: admin123")

def criar_plano_padrao():
    """Cria plano padrão se não existir"""
    from app.models import Plano
    
    plano = Plano.query.filter_by(id=1).first()
    if plano:
        print("✅ Plano padrão já existe")
        return plano
    
    plano = Plano(
        id=1,
        nome='Plano Padrão',
        descricao='Plano para migração de dados existentes',
        preco_mensal=Decimal('0.00'),
        preco_anual=Decimal('0.00'),
        limite_moradores=10000,
        limite_usuarios=100,
        limite_anexos_mb=50000,
        funcionalidades={
            'notificacoes_email': True,
            'relatorios_basicos': True,
            'backup_automatico': True,
            'suporte_email': True,
            'api_access': True,
            'whatsapp_integration': False,
            'custom_domain': False,
            'advanced_reports': True
        },
        ativo=True,
        publico=False,
        ordem=0
    )
    
    db.session.add(plano)
    db.session.commit()
    print("✅ Plano padrão criado")
    return plano

def criar_tenant_padrao():
    """Cria tenant padrão se não existir"""
    from app.models import Tenant
    
    tenant = Tenant.query.filter_by(id=1).first()
    if tenant:
        print("✅ Tenant padrão já existe")
        return tenant
    
    tenant = Tenant(
        id=1,
        nome='Sistema Migrado',
        subdominio='sistema',
        email_responsavel='admin@sistema.local',
        telefone='',
        plano_id=1,
        data_inicio=datetime.now().date(),
        data_vencimento=datetime.now().date() + timedelta(days=365),
        status='ativo',
        configuracoes={},
        cor_primaria='#007bff',
        cor_secundaria='#6c757d'
    )
    
    db.session.add(tenant)
    db.session.commit()
    print("✅ Tenant padrão criado")
    return tenant

def adicionar_colunas_tenant_id():
    """Adiciona colunas tenant_id nas tabelas existentes"""
    from sqlalchemy import text
    
    tabelas_colunas = [
        ('moradores', 'tenant_id'),
        ('anexos_moradores', 'tenant_id'), 
        ('log_notificacoes', 'tenant_id'),
        ('usuarios', 'tenant_id'),
        ('usuarios', 'permissoes'),
        ('usuarios', 'cargo')
    ]
    
    for tabela, coluna in tabelas_colunas:
        try:
            if coluna == 'tenant_id':
                sql = text(f"""
                ALTER TABLE {tabela} 
                ADD COLUMN {coluna} INTEGER DEFAULT 1 
                REFERENCES tenants(id)
                """)
            elif coluna == 'permissoes':
                sql = text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} JSON DEFAULT '{{}}'")
            elif coluna == 'cargo':
                sql = text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} VARCHAR(100)")
            
            db.session.execute(sql)
            db.session.commit()
            print(f"✅ Coluna {coluna} adicionada à tabela {tabela}")
            
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print(f"⚠️ Coluna {coluna} já existe na tabela {tabela}")
            else:
                print(f"❌ Erro ao adicionar coluna {coluna} na tabela {tabela}: {e}")

def atualizar_dados_existentes(tenant_id):
    """Atualiza dados existentes com tenant_id"""
    from sqlalchemy import text
    
    # Atualizar moradores
    try:
        sql = text(f"UPDATE moradores SET tenant_id = {tenant_id} WHERE tenant_id IS NULL")
        result = db.session.execute(sql)
        db.session.commit()
        print(f"✅ {result.rowcount} moradores atualizados com tenant_id")
    except Exception as e:
        print(f"❌ Erro ao atualizar moradores: {e}")
    
    # Atualizar anexos
    try:
        sql = text(f"UPDATE anexos_moradores SET tenant_id = {tenant_id} WHERE tenant_id IS NULL")
        result = db.session.execute(sql)
        db.session.commit()
        print(f"✅ {result.rowcount} anexos atualizados com tenant_id")
    except Exception as e:
        print(f"❌ Erro ao atualizar anexos: {e}")
    
    # Atualizar logs de notificação
    try:
        sql = text(f"UPDATE log_notificacoes SET tenant_id = {tenant_id} WHERE tenant_id IS NULL")
        result = db.session.execute(sql)
        db.session.commit()
        print(f"✅ {result.rowcount} logs de notificação atualizados com tenant_id")
    except Exception as e:
        print(f"❌ Erro ao atualizar logs: {e}")
    
    # Atualizar usuários
    try:
        sql = text(f"UPDATE usuarios SET tenant_id = {tenant_id} WHERE tenant_id IS NULL")
        result = db.session.execute(sql)
        db.session.commit()
        print(f"✅ {result.rowcount} usuários atualizados com tenant_id")
    except Exception as e:
        print(f"❌ Erro ao atualizar usuários: {e}")

def criar_usuario_admin(tenant_id):
    """Cria usuário administrador padrão"""
    from app.models import Usuario
    from sqlalchemy import text
    
    # Verificar se já existe usando SQL direto para evitar problema com colunas
    try:
        result = db.session.execute(text("SELECT id FROM usuarios WHERE username = 'admin'"))
        admin_id = result.scalar()
        
        if admin_id:
            # Atualizar usuário existente
            db.session.execute(text(f"""
                UPDATE usuarios 
                SET tenant_id = {tenant_id},
                    permissoes = '{{"admin_tenant": true, "criar_morador": true, "editar_morador": true, "excluir_morador": true, "validar_carteirinha": true, "gerar_carteirinha": true, "ver_relatorios": true, "exportar_dados": true, "configurar_sistema": true, "gerenciar_usuarios": true}}',
                    cargo = 'Administrador do Sistema'
                WHERE id = {admin_id}
            """))
            db.session.commit()
            print("✅ Usuário admin existente atualizado")
            return True
    except Exception as e:
        print(f"⚠️ Erro ao verificar usuário admin: {e}")
    
    # Criar novo usuário admin
    admin = Usuario(
        username='admin',
        email='admin@sistema.local',
        nome_completo='Administrador do Sistema',
        tipo_usuario='admin',
        tenant_id=tenant_id,
        permissoes={
            'admin_tenant': True,
            'criar_morador': True,
            'editar_morador': True,
            'excluir_morador': True,
            'validar_carteirinha': True,
            'gerar_carteirinha': True,
            'ver_relatorios': True,
            'exportar_dados': True,
            'configurar_sistema': True,
            'gerenciar_usuarios': True
        },
        cargo='Administrador do Sistema',
        ativo=True
    )
    
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    print("✅ Usuário administrador criado")
    return admin

def verificar_integridade():
    """Verifica integridade dos dados após migração"""
    from app.models import Tenant, Plano, Morador, Usuario
    
    print("\n📊 Verificando integridade dos dados...")
    
    # Contar registros
    total_tenants = Tenant.query.count()
    total_planos = Plano.query.count() 
    total_moradores = Morador.query.count()
    total_usuarios = Usuario.query.count()
    
    print(f"• Tenants: {total_tenants}")
    print(f"• Planos: {total_planos}")
    print(f"• Moradores: {total_moradores}")
    print(f"• Usuários: {total_usuarios}")
    
    # Verificar moradores sem tenant_id
    moradores_sem_tenant = Morador.query.filter(Morador.tenant_id.is_(None)).count()
    if moradores_sem_tenant > 0:
        print(f"⚠️ {moradores_sem_tenant} moradores sem tenant_id")
    else:
        print("✅ Todos os moradores têm tenant_id")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'verificar':
        app = create_app()
        with app.app_context():
            verificar_integridade()
    else:
        migrar_para_saas() 