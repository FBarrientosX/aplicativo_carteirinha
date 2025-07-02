#!/usr/bin/env python
"""
Script para inicializar o banco de dados
Execute: python init_db.py
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init as migrate_init, migrate as migrate_migrate, upgrade as migrate_upgrade

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from app.models import Morador, AnexoMorador, LogNotificacao, ConfiguracaoSistema, Condominio

def init_migrations():
    """Inicializar o sistema de migrações"""
    try:
        if not os.path.exists('migrations'):
            migrate_init()
            print("✅ Sistema de migrações inicializado!")
        else:
            print("ℹ️ Sistema de migrações já existe")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar migrações: {e}")
        return False

def create_migration():
    """Criar migração inicial"""
    try:
        migrate_migrate(message='Migração inicial - tabelas do sistema de carteirinhas')
        print("✅ Migração criada com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar migração: {e}")
        return False

def apply_migrations():
    """Aplicar migrações ao banco"""
    try:
        migrate_upgrade()
        print("✅ Migrações aplicadas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao aplicar migrações: {e}")
        return False

def create_upload_directories():
    """Criar diretórios para upload de arquivos"""
    try:
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        print(f"✅ Diretório de uploads criado: {upload_dir}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar diretórios: {e}")
        return False

def create_sample_data():
    """Criar dados de exemplo (opcional)"""
    try:
        from datetime import datetime, timedelta
        
        # Verificar se já existem dados
        if Morador.query.count() > 0:
            print("ℹ️ Dados já existem no banco. Pulando criação de dados de exemplo.")
            return True
        
        # Criar alguns moradores de exemplo
        moradores_exemplo = [
            {
                'nome_completo': 'João Silva Santos',
                'bloco': 'A',
                'apartamento': '101',
                'email': 'joao.silva@example.com',
                'celular': '(11) 99999-1111',
                'eh_titular': True,
                'observacoes': 'Morador desde 2020'
            },
            {
                'nome_completo': 'Maria Oliveira Costa',
                'bloco': 'B',
                'apartamento': '205',
                'email': 'maria.oliveira@example.com',
                'celular': '(11) 99999-2222',
                'eh_titular': True,
                'observacoes': 'Titular do apartamento'
            },
            {
                'nome_completo': 'Pedro Santos Silva',
                'bloco': 'A',
                'apartamento': '101',
                'email': 'pedro.santos@example.com',
                'celular': '(11) 99999-3333',
                'eh_titular': False,
                'email_titular': 'joao.silva@example.com',
                'observacoes': 'Filho do titular'
            }
        ]
        
        for dados in moradores_exemplo:
            morador = Morador(**dados)
            
            # Definir algumas carteirinhas com diferentes status
            if dados['nome_completo'] == 'João Silva Santos':
                # Carteirinha regular
                morador.data_ultima_validacao = datetime.now().date() - timedelta(days=60)
                morador.data_vencimento = datetime.now().date() + timedelta(days=120)
                morador.carteirinha_ativa = True
            elif dados['nome_completo'] == 'Maria Oliveira Costa':
                # Carteirinha a vencer
                morador.data_ultima_validacao = datetime.now().date() - timedelta(days=150)
                morador.data_vencimento = datetime.now().date() + timedelta(days=15)
                morador.carteirinha_ativa = True
            # Pedro não tem carteirinha
            
            db.session.add(morador)
        
        db.session.commit()
        print("✅ Dados de exemplo criados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar dados de exemplo: {e}")
        db.session.rollback()
        return False

def criar_configuracoes_padrao():
    """Criar configurações padrão do sistema"""
    print("Criando configurações padrão...")
    
    # Configurações de sistema
    configuracoes_padrao = [
        ('NOME_SISTEMA', 'Sistema de Carteirinhas', 'Nome do sistema', 'texto', 'geral'),
        ('VERSAO', '1.0.0', 'Versão do sistema', 'texto', 'geral'),
        ('SESSAO_TIMEOUT', '120', 'Timeout da sessão em minutos', 'numero', 'seguranca'),
        ('MAX_TENTATIVAS_LOGIN', '5', 'Máximo de tentativas de login', 'numero', 'seguranca'),
        ('BACKUP_AUTOMATICO', 'true', 'Backup automático ativado', 'booleano', 'backup'),
        ('DIAS_BACKUP', '7', 'Intervalo de backup em dias', 'numero', 'backup'),
        ('NOTIFICACOES_AUTOMATICAS', 'true', 'Notificações automáticas ativadas', 'booleano', 'notificacoes'),
        ('HORARIO_NOTIFICACOES', '09:00', 'Horário das notificações automáticas', 'texto', 'notificacoes'),
        
        # Configurações de email (vazias inicialmente)
        ('MAIL_SERVER', 'smtp.gmail.com', 'Servidor SMTP', 'texto', 'email'),
        ('MAIL_PORT', '587', 'Porta SMTP', 'numero', 'email'),
        ('MAIL_USE_TLS', 'true', 'Usar TLS', 'booleano', 'email'),
        ('MAIL_USERNAME', '', 'Usuário/Email SMTP', 'email', 'email'),
        ('MAIL_PASSWORD', '', 'Senha SMTP', 'senha', 'email'),
        ('MAIL_DEFAULT_SENDER', '', 'Email remetente padrão', 'email', 'email'),
    ]
    
    for chave, valor, descricao, tipo, categoria in configuracoes_padrao:
        if not ConfiguracaoSistema.query.filter_by(chave=chave).first():
            config = ConfiguracaoSistema(
                chave=chave,
                valor=valor,
                descricao=descricao,
                tipo=tipo,
                categoria=categoria
            )
            db.session.add(config)
    
    # Criar condomínio padrão
    if not Condominio.query.first():
        condominio = Condominio(
            nome='Meu Condomínio',
            endereco='Configure o endereço nas configurações',
            email_administracao='admin@condominio.com',
            telefone='(11) 3333-4444',
            whatsapp='(11) 99999-9999',
            horario_funcionamento='Segunda a Sexta, 8h às 18h',
            dias_aviso_vencimento=30,
            meses_validade_padrao=12,
            permitir_dependentes=True,
            cor_primaria='#007bff',
            cor_secundaria='#6c757d'
        )
        db.session.add(condominio)
    
    db.session.commit()
    print("✅ Configurações padrão criadas!")

def main():
    """Função principal"""
    print("🚀 Inicializando Sistema de Carteirinhas - Versão Produto")
    print("=" * 60)
    
    with app.app_context():
        # 1. Inicializar migrações
        if not init_migrations():
            return
        
        # 2. Criar migração inicial
        if not create_migration():
            return
        
        # 3. Aplicar migrações
        if not apply_migrations():
            return
        
        # 4. Criar diretórios
        if not create_upload_directories():
            return
        
        # 5. Criar dados de exemplo (opcional)
        resposta = input("\n🤔 Deseja criar dados de exemplo? (s/N): ").lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            create_sample_data()
        
        # 6. Criar configurações padrão
        criar_configuracoes_padrao()
    
    print("\n" + "=" * 60)
    print("✅ Sistema inicializado com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Execute: python run.py")
    print("2. Acesse: http://localhost:5000")
    print("3. Configure o email em: Configurações → Email")
    print("4. Configure o condomínio em: Configurações → Condomínio")
    print("5. Teste as funcionalidades!")
    print("\n🏢 Sistema pronto para uso comercial!")
    print("=" * 60)

if __name__ == '__main__':
    main() 