#!/usr/bin/env python
"""
Script para corrigir o banco de dados
Execute: python fix_database.py
"""

import os
import sys
from datetime import datetime, timedelta

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import *

def main():
    """Função principal para corrigir o banco de dados"""
    print("🔧 Corrigindo banco de dados...")
    print("=" * 50)
    
    # Criar app
    app = create_app()
    
    with app.app_context():
        try:
            # Remover banco existente se houver
            if os.path.exists('carteirinha_piscina.db'):
                os.remove('carteirinha_piscina.db')
                print("✅ Banco de dados antigo removido")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Todas as tabelas criadas com sucesso!")
            
            # Criar condomínio padrão
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
            
            # Criar usuário admin
            admin = Usuario(
                username='admin',
                email='admin@condominio.com',
                nome_completo='Administrador do Sistema',
                tipo_usuario='admin',
                ativo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Criar configurações padrão
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
                config = ConfiguracaoSistema(
                    chave=chave,
                    valor=valor,
                    descricao=descricao,
                    tipo=tipo,
                    categoria=categoria
                )
                db.session.add(config)
            
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
            
            # Salvar tudo
            db.session.commit()
            print("✅ Dados iniciais criados com sucesso!")
            
            # Criar diretórios de upload
            upload_dir = os.path.join('app', 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            os.makedirs(os.path.join(upload_dir, 'carteirinhas'), exist_ok=True)
            print("✅ Diretórios de upload criados!")
            
            print("\n" + "=" * 50)
            print("✅ Banco de dados corrigido com sucesso!")
            print("\n📋 Credenciais de acesso:")
            print("   Usuário: admin")
            print("   Senha: admin123")
            print("\n🚀 Execute: python run.py")
            print("🌐 Acesse: http://localhost:5000")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Erro ao corrigir banco de dados: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    main() 