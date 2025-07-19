#!/usr/bin/env python3
"""
Migração simples e corrigida para finalizar setup CondoTech
"""
from datetime import datetime
from sqlalchemy import text
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app, db

def finalizar_setup():
    """Finaliza configuração CondoTech Solutions"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Finalizando configuração CondoTech...")
        
        try:
            # Verificar e inserir módulos
            result = db.session.execute(text("SELECT COUNT(*) FROM modulos")).fetchone()
            if result[0] == 0:
                print("📦 Criando módulos...")
                
                # Módulo Piscina
                db.session.execute(text("""
                    INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """), ('Controle de Piscina', 'piscina', 'Sistema completo de controle de acesso à piscina', 'fas fa-swimming-pool', '#007bff', 1, 1, datetime.now()))
                
                # Módulo Manutenção
                db.session.execute(text("""
                    INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """), ('Manutenção & Chamados', 'manutencao', 'Gestão completa de chamados de manutenção', 'fas fa-tools', '#28a745', 2, 1, datetime.now()))
                
                print("✅ Módulos criados!")
            else:
                print("✅ Módulos já existem!")
            
            # Verificar e ativar módulos para tenant
            tenant_modules = db.session.execute(text("SELECT COUNT(*) FROM modulos_tenant WHERE tenant_id = 1")).fetchone()
            if tenant_modules[0] == 0:
                print("🔌 Ativando módulos para tenant...")
                
                db.session.execute(text("""
                    INSERT INTO modulos_tenant (tenant_id, modulo_id, ativo, data_ativacao)
                    SELECT 1, id, 1, ? FROM modulos WHERE slug IN ('piscina', 'manutencao')
                """), (datetime.now(),))
                
                print("✅ Módulos ativados!")
            else:
                print("✅ Módulos já ativados!")
            
            # Verificar e criar categorias de manutenção
            result = db.session.execute(text("SELECT COUNT(*) FROM categorias_manutencao WHERE tenant_id = 1")).fetchone()
            if result[0] == 0:
                print("🔧 Criando categorias...")
                
                categorias = [
                    ('Elétrica', 'Problemas elétricos, iluminação, tomadas', 'fas fa-bolt', '#ffc107', 4, 'alta'),
                    ('Hidráulica', 'Vazamentos, entupimentos, pressão de água', 'fas fa-tint', '#007bff', 2, 'alta'),
                    ('Ar Condicionado', 'Climatização, ventilação, refrigeração', 'fas fa-snowflake', '#17a2b8', 24, 'media'),
                    ('Pintura', 'Pintura, acabamentos, reparos estéticos', 'fas fa-paint-brush', '#6f42c1', 72, 'baixa'),
                    ('Limpeza', 'Limpeza geral, áreas comuns, jardinagem', 'fas fa-broom', '#28a745', 12, 'media'),
                    ('Segurança', 'Portões, fechaduras, câmeras, alarmes', 'fas fa-shield-alt', '#dc3545', 1, 'urgente')
                ]
                
                for categoria in categorias:
                    db.session.execute(text("""
                        INSERT INTO categorias_manutencao 
                        (tenant_id, nome, descricao, icone, cor, tempo_resposta_horas, prioridade_default, data_criacao)
                        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                    """), (*categoria, datetime.now()))
                
                print("✅ Categorias criadas!")
            else:
                print("✅ Categorias já existem!")
            
            db.session.commit()
            
            print("\n🎉 SETUP COMPLETO!")
            print("=" * 50)
            print("✅ Sistema CondoTech Solutions configurado")
            print("✅ Módulos: Piscina + Manutenção")
            print("✅ 6 categorias de manutenção")
            print("\n🌐 Acesse: https://barrientos.pythonanywhere.com")
            print("👤 Login: admin / admin123")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    finalizar_setup() 