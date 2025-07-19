#!/usr/bin/env python3
"""
Migração corrigida para adicionar sistema modular e módulo de manutenção
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def executar_migracoes():
    """Executa as migrações para sistema modular"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Executando migrações do sistema modular...")
        
        # Criar tabelas de módulos
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS modulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL,
                slug VARCHAR(50) NOT NULL UNIQUE,
                descricao TEXT,
                icone VARCHAR(50) DEFAULT 'fas fa-cog',
                cor VARCHAR(20) DEFAULT '#007bff',
                ordem INTEGER DEFAULT 0,
                ativo BOOLEAN DEFAULT 1,
                config_json JSON DEFAULT '{}',
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS modulos_tenant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                modulo_id INTEGER NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                configuracoes JSON DEFAULT '{}',
                data_ativacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_desativacao DATETIME,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id),
                FOREIGN KEY (modulo_id) REFERENCES modulos (id),
                UNIQUE(tenant_id, modulo_id)
            )
        """))
        
        # Criar tabelas de manutenção
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS categorias_manutencao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                nome VARCHAR(100) NOT NULL,
                descricao TEXT,
                cor VARCHAR(20) DEFAULT '#007bff',
                icone VARCHAR(50) DEFAULT 'fas fa-tools',
                ativo BOOLEAN DEFAULT 1,
                tempo_resposta_horas INTEGER DEFAULT 24,
                prioridade_default VARCHAR(20) DEFAULT 'media',
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id)
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS chamados_manutencao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero VARCHAR(20) NOT NULL UNIQUE,
                tenant_id INTEGER NOT NULL,
                titulo VARCHAR(200) NOT NULL,
                descricao TEXT NOT NULL,
                local VARCHAR(200) NOT NULL,
                categoria_id INTEGER NOT NULL,
                solicitante_id INTEGER NOT NULL,
                responsavel_id INTEGER,
                status VARCHAR(20) DEFAULT 'aberto',
                prioridade VARCHAR(20) DEFAULT 'media',
                data_abertura DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_inicio DATETIME,
                data_conclusao DATETIME,
                prazo_estimado DATETIME,
                diagnostico TEXT,
                solucao TEXT,
                observacoes_internas TEXT,
                avaliacao_atendimento INTEGER,
                comentario_avaliacao TEXT,
                custo_estimado DECIMAL(10,2),
                custo_real DECIMAL(10,2),
                aprovado_custo BOOLEAN DEFAULT 0,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id),
                FOREIGN KEY (categoria_id) REFERENCES categorias_manutencao (id),
                FOREIGN KEY (solicitante_id) REFERENCES usuarios (id),
                FOREIGN KEY (responsavel_id) REFERENCES usuarios (id)
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS anexos_chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                nome_original VARCHAR(255) NOT NULL,
                nome_arquivo VARCHAR(255) NOT NULL,
                caminho VARCHAR(500) NOT NULL,
                tipo_mime VARCHAR(100),
                tamanho INTEGER,
                tipo VARCHAR(20) DEFAULT 'foto',
                descricao VARCHAR(255),
                data_upload DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamado_id) REFERENCES chamados_manutencao (id)
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                acao VARCHAR(50) NOT NULL,
                campo_alterado VARCHAR(50),
                valor_anterior TEXT,
                valor_novo TEXT,
                comentario TEXT,
                data_acao DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamado_id) REFERENCES chamados_manutencao (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        """))
        
        db.session.commit()
        print("✅ Tabelas criadas com sucesso!")
        
        return True

def criar_modulos_iniciais():
    """Cria módulos iniciais do sistema"""
    
    app = create_app()
    
    with app.app_context():
        print("📦 Criando módulos iniciais...")
        
        # Verificar se já existem módulos
        result = db.session.execute(text("SELECT COUNT(*) FROM modulos")).fetchone()
        if result[0] > 0:
            print("✅ Módulos já existem!")
            return True
        
        # Inserir módulo Piscina
        db.session.execute(text("""
            INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """), ('Controle de Piscina', 'piscina', 'Sistema completo de controle de acesso à piscina com carteirinhas digitais e QR Code', 'fas fa-swimming-pool', '#007bff', 1, 1, datetime.now()))
        
        # Inserir módulo Manutenção
        db.session.execute(text("""
            INSERT INTO modulos (nome, slug, descricao, icone, cor, ordem, ativo, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """), ('Manutenção & Chamados', 'manutencao', 'Gestão completa de chamados de manutenção, ordens de serviço e controle de técnicos', 'fas fa-tools', '#28a745', 2, 1, datetime.now()))
        
        db.session.commit()
        print("✅ Módulos iniciais criados!")
        
        return True

def ativar_modulos_tenant():
    """Ativa módulos para o tenant padrão"""
    
    app = create_app()
    
    with app.app_context():
        print("🔌 Ativando módulos para tenant padrão...")
        
        # Buscar módulos
        modulos = db.session.execute(text("SELECT id, slug FROM modulos WHERE ativo = 1")).fetchall()
        
        for modulo in modulos:
            # Verificar se já está ativo para o tenant 1
            existing = db.session.execute(text("""
                SELECT id FROM modulos_tenant 
                WHERE tenant_id = 1 AND modulo_id = ?
            """), (modulo[0],)).fetchone()
            
            if not existing:
                db.session.execute(text("""
                    INSERT INTO modulos_tenant (tenant_id, modulo_id, ativo, data_ativacao)
                    VALUES (?, ?, ?, ?)
                """), (1, modulo[0], 1, datetime.now()))
                
                print(f"  ✅ Módulo '{modulo[1]}' ativado para tenant 1")
        
        db.session.commit()
        print("✅ Módulos ativados!")
        
        return True

def criar_categorias_manutencao():
    """Cria categorias padrão de manutenção"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Criando categorias de manutenção...")
        
        # Verificar se já existem categorias
        result = db.session.execute(text("SELECT COUNT(*) FROM categorias_manutencao WHERE tenant_id = 1")).fetchone()
        if result[0] > 0:
            print("✅ Categorias já existem!")
            return True
        
        categorias = [
            {
                'nome': 'Elétrica',
                'descricao': 'Problemas elétricos, iluminação, tomadas',
                'icone': 'fas fa-bolt',
                'cor': '#ffc107',
                'tempo_resposta': 4,
                'prioridade': 'alta'
            },
            {
                'nome': 'Hidráulica',
                'descricao': 'Vazamentos, entupimentos, pressão de água',
                'icone': 'fas fa-tint',
                'cor': '#007bff',
                'tempo_resposta': 2,
                'prioridade': 'alta'
            },
            {
                'nome': 'Ar Condicionado',
                'descricao': 'Climatização, ventilação, refrigeração',
                'icone': 'fas fa-snowflake',
                'cor': '#17a2b8',
                'tempo_resposta': 24,
                'prioridade': 'media'
            },
            {
                'nome': 'Pintura',
                'descricao': 'Pintura, acabamentos, reparos estéticos',
                'icone': 'fas fa-paint-brush',
                'cor': '#6f42c1',
                'tempo_resposta': 72,
                'prioridade': 'baixa'
            },
            {
                'nome': 'Limpeza',
                'descricao': 'Limpeza geral, áreas comuns, jardinagem',
                'icone': 'fas fa-broom',
                'cor': '#28a745',
                'tempo_resposta': 12,
                'prioridade': 'media'
            },
            {
                'nome': 'Segurança',
                'descricao': 'Portões, fechaduras, câmeras, alarmes',
                'icone': 'fas fa-shield-alt',
                'cor': '#dc3545',
                'tempo_resposta': 1,
                'prioridade': 'urgente'
            }
        ]
        
        for categoria in categorias:
            db.session.execute(text("""
                INSERT INTO categorias_manutencao 
                (tenant_id, nome, descricao, icone, cor, tempo_resposta_horas, prioridade_default, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """), (
                1,
                categoria['nome'],
                categoria['descricao'],
                categoria['icone'],
                categoria['cor'],
                categoria['tempo_resposta'],
                categoria['prioridade'],
                datetime.now()
            ))
        
        db.session.commit()
        print("✅ Categorias de manutenção criadas!")
        
        return True

def main():
    """Função principal"""
    print("🚀 CondoTech Solutions - Sistema Modular")
    print("=" * 50)
    
    try:
        # Executar migrações
        if not executar_migracoes():
            print("❌ Erro nas migrações!")
            return
        
        # Criar módulos iniciais
        if not criar_modulos_iniciais():
            print("❌ Erro ao criar módulos!")
            return
        
        # Ativar módulos para tenant
        if not ativar_modulos_tenant():
            print("❌ Erro ao ativar módulos!")
            return
        
        # Criar categorias de manutenção
        if not criar_categorias_manutencao():
            print("❌ Erro ao criar categorias!")
            return
        
        print("\n🎉 MIGRAÇÃO CONCLUÍDA!")
        print("=" * 50)
        print("✅ Sistema modular configurado")
        print("✅ Módulos disponíveis:")
        print("   🏊 Controle de Piscina")
        print("   🔧 Manutenção & Chamados")
        print("✅ Categorias de manutenção criadas")
        print("\n🌐 Acesse: https://barrientos.pythonanywhere.com")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

if __name__ == '__main__':
    main() 