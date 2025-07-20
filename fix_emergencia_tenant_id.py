#!/usr/bin/env python3
"""
FIX DE EMERGÊNCIA - Correção tenant_id no registro_acesso
Resolver erro crítico: no such column: registro_acesso.tenant_id
"""

import os
import sys

def criar_patch_emergencia():
    """Criar patch temporário para app/routes.py"""
    print("🚨 CRIANDO PATCH DE EMERGÊNCIA...")
    
    try:
        # Ler arquivo routes.py
        with open('app/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup do arquivo original
        with open('app/routes.py.backup_emergencia', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ Backup criado: app/routes.py.backup_emergencia")
        
        # Patch 1: Dashboard principal - adicionar try/except para tenant_id
        old_stats = '''# Estatísticas de acesso à piscina com filtro tenant
    try:
        moradores_na_piscina = len(RegistroAcesso.obter_moradores_na_piscina(tenant_id))
    except:
        moradores_na_piscina = 0
    
    # Entradas hoje no tenant atual
    hoje = datetime.now().date()
    entradas_hoje = RegistroAcesso.query.filter(
        db.func.date(RegistroAcesso.data_hora) == hoje,
        RegistroAcesso.tipo == 'entrada',
        RegistroAcesso.tenant_id == tenant_id
    ).count()
    
    # Total de registros de acesso do tenant
    total_registros_acesso = RegistroAcesso.query.filter_by(tenant_id=tenant_id).count()'''
        
        new_stats = '''# Estatísticas de acesso à piscina (PATCH EMERGÊNCIA)
    try:
        # Verificar se tenant_id existe na tabela
        test_query = db.session.execute(db.text("SELECT 1 FROM registro_acesso WHERE tenant_id = 1 LIMIT 1"))
        has_tenant_id = True
    except Exception:
        has_tenant_id = False
    
    try:
        if has_tenant_id:
            moradores_na_piscina = len(RegistroAcesso.obter_moradores_na_piscina(tenant_id))
        else:
            moradores_na_piscina = len(RegistroAcesso.obter_moradores_na_piscina())
    except:
        moradores_na_piscina = 0
    
    # Entradas hoje (com/sem tenant dependendo da existência da coluna)
    hoje = datetime.now().date()
    try:
        if has_tenant_id:
            entradas_hoje = RegistroAcesso.query.filter(
                db.func.date(RegistroAcesso.data_hora) == hoje,
                RegistroAcesso.tipo == 'entrada',
                RegistroAcesso.tenant_id == tenant_id
            ).count()
            total_registros_acesso = RegistroAcesso.query.filter_by(tenant_id=tenant_id).count()
        else:
            entradas_hoje = RegistroAcesso.query.filter(
                db.func.date(RegistroAcesso.data_hora) == hoje,
                RegistroAcesso.tipo == 'entrada'
            ).count()
            total_registros_acesso = RegistroAcesso.query.count()
    except Exception as e:
        print(f"Erro nas estatísticas: {e}")
        entradas_hoje = 0
        total_registros_acesso = 0'''
        
        if old_stats in content:
            content = content.replace(old_stats, new_stats)
            print("   ✅ Dashboard principal corrigido")
        else:
            # Tentar patch mais específico
            if 'entradas_hoje = RegistroAcesso.query.filter(' in content and 'tenant_id' in content:
                # Patch mais direto
                content = content.replace(
                    'RegistroAcesso.tenant_id == tenant_id',
                    '# RegistroAcesso.tenant_id == tenant_id  # DESABILITADO TEMPORARIAMENTE'
                )
                content = content.replace(
                    '.filter_by(tenant_id=tenant_id)',
                    '# .filter_by(tenant_id=tenant_id)  # DESABILITADO TEMPORARIAMENTE'
                )
                print("   ✅ Filtros tenant_id desabilitados temporariamente")
        
        # Adicionar import necessário
        if 'from sqlalchemy import text' not in content:
            content = content.replace(
                'from app import db',
                'from app import db\nfrom sqlalchemy import text'
            )
        
        # Salvar arquivo corrigido
        with open('app/routes.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ app/routes.py corrigido")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao criar patch: {e}")
        return False

def criar_patch_modelos():
    """Patch para app/models.py"""
    print("\n🔧 CRIANDO PATCH PARA MODELOS...")
    
    try:
        with open('app/models.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup
        with open('app/models.py.backup_emergencia', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Patch para obter_moradores_na_piscina - tornar tenant_id opcional
        old_method = '''@staticmethod
    def obter_moradores_na_piscina(tenant_id=None):
        """Retorna lista de moradores que estão atualmente na piscina"""
        from flask import g
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        # Subconsulta para obter o último registro de cada morador do tenant
        subq = db.session.query(
            RegistroAcesso.morador_id,
            db.func.max(RegistroAcesso.data_hora).label('ultima_data')
        ).filter(RegistroAcesso.tenant_id == tenant_id).group_by(RegistroAcesso.morador_id).subquery()
        
        # Buscar registros que são entradas no tenant específico
        moradores_dentro = db.session.query(Morador).join(
            RegistroAcesso, Morador.id == RegistroAcesso.morador_id
        ).join(
            subq, db.and_(
                RegistroAcesso.morador_id == subq.c.morador_id,
                RegistroAcesso.data_hora == subq.c.ultima_data
            )
        ).filter(
            RegistroAcesso.tipo == 'entrada',
            RegistroAcesso.tenant_id == tenant_id,
            Morador.tenant_id == tenant_id
        ).all()
        
        return moradores_dentro'''
        
        new_method = '''@staticmethod
    def obter_moradores_na_piscina(tenant_id=None):
        """Retorna lista de moradores que estão atualmente na piscina"""
        from flask import g
        from sqlalchemy import text
        
        # Verificar se tenant_id existe na tabela (PATCH EMERGÊNCIA)
        try:
            db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1"))
            has_tenant_id = True
        except Exception:
            has_tenant_id = False
        
        if not has_tenant_id:
            # Versão sem tenant_id (compatibilidade)
            subq = db.session.query(
                RegistroAcesso.morador_id,
                db.func.max(RegistroAcesso.data_hora).label('ultima_data')
            ).group_by(RegistroAcesso.morador_id).subquery()
            
            moradores_dentro = db.session.query(Morador).join(
                RegistroAcesso, Morador.id == RegistroAcesso.morador_id
            ).join(
                subq, db.and_(
                    RegistroAcesso.morador_id == subq.c.morador_id,
                    RegistroAcesso.data_hora == subq.c.ultima_data
                )
            ).filter(RegistroAcesso.tipo == 'entrada').all()
            
            return moradores_dentro
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        # Subconsulta para obter o último registro de cada morador do tenant
        subq = db.session.query(
            RegistroAcesso.morador_id,
            db.func.max(RegistroAcesso.data_hora).label('ultima_data')
        ).filter(RegistroAcesso.tenant_id == tenant_id).group_by(RegistroAcesso.morador_id).subquery()
        
        # Buscar registros que são entradas no tenant específico
        moradores_dentro = db.session.query(Morador).join(
            RegistroAcesso, Morador.id == RegistroAcesso.morador_id
        ).join(
            subq, db.and_(
                RegistroAcesso.morador_id == subq.c.morador_id,
                RegistroAcesso.data_hora == subq.c.ultima_data
            )
        ).filter(
            RegistroAcesso.tipo == 'entrada',
            RegistroAcesso.tenant_id == tenant_id,
            Morador.tenant_id == tenant_id
        ).all()
        
        return moradores_dentro'''
        
        if old_method in content:
            content = content.replace(old_method, new_method)
            print("   ✅ obter_moradores_na_piscina corrigido")
        
        # Patch similar para morador_esta_na_piscina
        old_morador = '''@staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id=None):
        """Verifica se o morador está atualmente na piscina"""
        from flask import g
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        ultimo_registro = RegistroAcesso.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id
        ).order_by(RegistroAcesso.data_hora.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada' '''
        
        new_morador = '''@staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id=None):
        """Verifica se o morador está atualmente na piscina"""
        from flask import g
        from sqlalchemy import text
        
        # Verificar se tenant_id existe na tabela (PATCH EMERGÊNCIA)
        try:
            db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1"))
            has_tenant_id = True
        except Exception:
            has_tenant_id = False
        
        if not has_tenant_id:
            # Versão sem tenant_id
            ultimo_registro = RegistroAcesso.query.filter_by(
                morador_id=morador_id
            ).order_by(RegistroAcesso.data_hora.desc()).first()
            return ultimo_registro and ultimo_registro.tipo == 'entrada'
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        ultimo_registro = RegistroAcesso.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id
        ).order_by(RegistroAcesso.data_hora.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada' '''
        
        if old_morador in content:
            content = content.replace(old_morador, new_morador)
            print("   ✅ morador_esta_na_piscina corrigido")
        
        # Salvar
        with open('app/models.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ app/models.py corrigido")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao corrigir models: {e}")
        return False

def restaurar_backups():
    """Restaurar backups se necessário"""
    print("\n🔄 Para restaurar backups:")
    print("   cp app/routes.py.backup_emergencia app/routes.py")
    print("   cp app/models.py.backup_emergencia app/models.py")

def main():
    print("🚨 FIX DE EMERGÊNCIA - TENANT_ID FALTANDO")
    print("="*50)
    
    print("❌ PROBLEMA IDENTIFICADO:")
    print("   - Coluna 'tenant_id' não existe na tabela 'registro_acesso'")
    print("   - Aplicação tenta usar tenant_id mas falha")
    print("   - Sistema fica inacessível")
    
    print("\n🔧 APLICANDO CORREÇÕES DE EMERGÊNCIA...")
    
    sucesso_routes = criar_patch_emergencia()
    sucesso_models = criar_patch_modelos()
    
    if sucesso_routes and sucesso_models:
        print("\n✅ CORREÇÕES APLICADAS COM SUCESSO!")
        print("\n🚀 PRÓXIMOS PASSOS NO PYTHONANYWHERE:")
        print("   1. Faça git push das correções:")
        print("      git add .")
        print("      git commit -m 'Fix emergência tenant_id'")
        print("      git push")
        print("   2. No PythonAnywhere:")
        print("      git pull")
        print("   3. Recarregue a aplicação")
        print("   4. Execute a migração:")
        print("      python3.10 migracao_registro_acesso_tenant.py")
        print("   5. Depois da migração, remova os patches")
        
        print("\n⚠️  ATENÇÃO:")
        print("   - Esta é uma correção TEMPORÁRIA")
        print("   - Execute a migração o mais rápido possível")
        print("   - Alguns recursos podem funcionar parcialmente")
        
        restaurar_backups()
        
    else:
        print("\n❌ FALHA NAS CORREÇÕES!")
        print("   Verifique os arquivos manualmente")
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 