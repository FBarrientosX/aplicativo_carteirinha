#!/usr/bin/env python3
"""
Script para criar planos iniciais do SaaS
Execute: python criar_planos_iniciais.py
"""

from app import create_app, db
from app.models import Plano
from decimal import Decimal

def criar_planos_iniciais():
    """Cria planos iniciais para o SaaS"""
    
    app = create_app()
    
    with app.app_context():
        # Verificar se já existem planos
        if Plano.query.count() > 0:
            print("❌ Planos já existem! Use o comando de atualização.")
            return
        
        planos = [
            {
                'nome': 'Básico',
                'descricao': 'Ideal para condomínios pequenos',
                'preco_mensal': Decimal('99.00'),
                'preco_anual': Decimal('990.00'),  # 2 meses grátis
                'limite_moradores': 200,
                'limite_usuarios': 1,
                'limite_anexos_mb': 500,
                'funcionalidades': {
                    'notificacoes_email': True,
                    'relatorios_basicos': True,
                    'backup_automatico': True,
                    'suporte_email': True,
                    'api_access': False,
                    'whatsapp_integration': False,
                    'custom_domain': False,
                    'advanced_reports': False
                },
                'ativo': True,
                'publico': True,
                'ordem': 1
            },
            {
                'nome': 'Profissional',
                'descricao': 'Para condomínios de médio porte',
                'preco_mensal': Decimal('199.00'),
                'preco_anual': Decimal('1990.00'),  # 2 meses grátis
                'limite_moradores': 500,
                'limite_usuarios': 3,
                'limite_anexos_mb': 2000,
                'funcionalidades': {
                    'notificacoes_email': True,
                    'relatorios_basicos': True,
                    'backup_automatico': True,
                    'suporte_email': True,
                    'api_access': True,
                    'whatsapp_integration': True,
                    'custom_domain': False,
                    'advanced_reports': True,
                    'bulk_operations': True,
                    'export_data': True
                },
                'ativo': True,
                'publico': True,
                'ordem': 2
            },
            {
                'nome': 'Enterprise',
                'descricao': 'Para grandes condomínios e administradoras',
                'preco_mensal': Decimal('399.00'),
                'preco_anual': Decimal('3990.00'),  # 2 meses grátis
                'limite_moradores': 2000,
                'limite_usuarios': 10,
                'limite_anexos_mb': 10000,
                'funcionalidades': {
                    'notificacoes_email': True,
                    'relatorios_basicos': True,
                    'backup_automatico': True,
                    'suporte_email': True,
                    'api_access': True,
                    'whatsapp_integration': True,
                    'custom_domain': True,
                    'advanced_reports': True,
                    'bulk_operations': True,
                    'export_data': True,
                    'priority_support': True,
                    'phone_support': True,
                    'custom_branding': True,
                    'sla_guarantee': True
                },
                'ativo': True,
                'publico': True,
                'ordem': 3
            },
            {
                'nome': 'Teste Gratuito',
                'descricao': 'Para testes e demonstração',
                'preco_mensal': Decimal('0.00'),
                'preco_anual': Decimal('0.00'),
                'limite_moradores': 50,
                'limite_usuarios': 1,
                'limite_anexos_mb': 100,
                'funcionalidades': {
                    'notificacoes_email': True,
                    'relatorios_basicos': True,
                    'backup_automatico': False,
                    'suporte_email': False,
                    'api_access': False,
                    'whatsapp_integration': False,
                    'custom_domain': False,
                    'advanced_reports': False
                },
                'ativo': True,
                'publico': False,  # Não aparece na lista pública
                'ordem': 0
            }
        ]
        
        print("🚀 Criando planos iniciais...")
        
        for plano_data in planos:
            plano = Plano(**plano_data)
            db.session.add(plano)
            print(f"✅ Plano '{plano.nome}' criado - R$ {plano.preco_mensal}/mês")
        
        db.session.commit()
        print(f"\n🎉 {len(planos)} planos criados com sucesso!")
        
        # Exibir resumo
        print("\n📊 Resumo dos Planos:")
        for plano in Plano.query.order_by(Plano.ordem).all():
            print(f"• {plano.nome}: R$ {plano.preco_mensal}/mês ({plano.limite_moradores} moradores)")

def atualizar_planos():
    """Atualiza planos existentes"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Atualizando planos existentes...")
        
        # Atualizar funcionalidades dos planos
        atualizacoes = {
            'Básico': {
                'funcionalidades': {
                    'notificacoes_email': True,
                    'relatorios_basicos': True,
                    'backup_automatico': True,
                    'suporte_email': True,
                    'api_access': False,
                    'whatsapp_integration': False,
                    'custom_domain': False,
                    'advanced_reports': False
                }
            },
            'Profissional': {
                'funcionalidades': {
                    'notificacoes_email': True,
                    'relatorios_basicos': True,
                    'backup_automatico': True,
                    'suporte_email': True,
                    'api_access': True,
                    'whatsapp_integration': True,
                    'custom_domain': False,
                    'advanced_reports': True,
                    'bulk_operations': True,
                    'export_data': True
                }
            },
            'Enterprise': {
                'funcionalidades': {
                    'notificacoes_email': True,
                    'relatorios_basicos': True,
                    'backup_automatico': True,
                    'suporte_email': True,
                    'api_access': True,
                    'whatsapp_integration': True,
                    'custom_domain': True,
                    'advanced_reports': True,
                    'bulk_operations': True,
                    'export_data': True,
                    'priority_support': True,
                    'phone_support': True,
                    'custom_branding': True,
                    'sla_guarantee': True
                }
            }
        }
        
        for nome_plano, dados in atualizacoes.items():
            plano = Plano.query.filter_by(nome=nome_plano).first()
            if plano:
                plano.funcionalidades = dados['funcionalidades']
                print(f"✅ Plano '{nome_plano}' atualizado")
            else:
                print(f"❌ Plano '{nome_plano}' não encontrado")
        
        db.session.commit()
        print("🎉 Planos atualizados com sucesso!")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'atualizar':
        atualizar_planos()
    else:
        criar_planos_iniciais() 