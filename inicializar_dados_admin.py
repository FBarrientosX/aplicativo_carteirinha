#!/usr/bin/env python3
"""
Script para inicializar dados básicos necessários para o sistema administrativo
"""

from app import create_app, db
from app.models import Plano, Modulo
from datetime import datetime

def criar_planos_basicos():
    """Criar planos básicos se não existirem"""
    
    planos_basicos = [
        {
            'nome': 'Básico',
            'descricao': 'Plano básico para condomínios pequenos',
            'preco_mensal': 89.00,
            'preco_anual': 890.00,
            'limite_moradores': 100,
            'limite_usuarios': 2,
            'limite_anexos_mb': 500,
            'funcionalidades': {
                'piscina': True,
                'carteirinhas': True,
                'qr_scanner': True,
                'notificacoes': True,
                'relatorios_basicos': True
            },
            'ativo': True,
            'publico': True,
            'ordem': 1
        },
        {
            'nome': 'Profissional',
            'descricao': 'Plano completo para condomínios médios',
            'preco_mensal': 149.00,
            'preco_anual': 1490.00,
            'limite_moradores': 300,
            'limite_usuarios': 5,
            'limite_anexos_mb': 2000,
            'funcionalidades': {
                'piscina': True,
                'carteirinhas': True,
                'qr_scanner': True,
                'notificacoes': True,
                'relatorios_basicos': True,
                'relatorios_avancados': True,
                'manutencao': True,
                'salva_vidas': True,
                'personalizacao': True
            },
            'ativo': True,
            'publico': True,
            'ordem': 2
        },
        {
            'nome': 'Enterprise',
            'descricao': 'Plano premium para grandes condomínios',
            'preco_mensal': 299.00,
            'preco_anual': 2990.00,
            'limite_moradores': 1000,
            'limite_usuarios': 15,
            'limite_anexos_mb': 10000,
            'funcionalidades': {
                'piscina': True,
                'carteirinhas': True,
                'qr_scanner': True,
                'notificacoes': True,
                'relatorios_basicos': True,
                'relatorios_avancados': True,
                'manutencao': True,
                'salva_vidas': True,
                'personalizacao': True,
                'api_integracoes': True,
                'suporte_prioritario': True,
                'backup_avancado': True
            },
            'ativo': True,
            'publico': True,
            'ordem': 3
        }
    ]
    
    planos_criados = 0
    
    for dados_plano in planos_basicos:
        # Verificar se já existe
        plano_existente = Plano.query.filter_by(nome=dados_plano['nome']).first()
        
        if not plano_existente:
            plano = Plano(**dados_plano)
            db.session.add(plano)
            planos_criados += 1
            print(f"✅ Plano '{dados_plano['nome']}' criado")
        else:
            print(f"⚠️ Plano '{dados_plano['nome']}' já existe")
    
    if planos_criados > 0:
        db.session.commit()
        print(f"\n🎯 {planos_criados} planos criados com sucesso!")
    else:
        print("\n📋 Todos os planos já existem")
    
    return planos_criados

def criar_modulos_basicos():
    """Criar módulos básicos se não existirem"""
    
    modulos_basicos = [
        {
            'nome': 'Piscina',
            'slug': 'piscina',
            'descricao': 'Controle de acesso à piscina com carteirinhas e QR Code',
            'icone': 'fas fa-swimming-pool',
            'cor': '#007bff',
            'ordem': 1,
            'ativo': True,
            'config_json': {
                'permite_dependentes': True,
                'validade_padrao_meses': 12,
                'aviso_vencimento_dias': 30,
                'qr_scanner': True,
                'notificacoes_automaticas': True
            }
        },
        {
            'nome': 'Manutenção',
            'slug': 'manutencao',
            'descricao': 'Sistema de chamados de manutenção com SLA e categorias',
            'icone': 'fas fa-tools',
            'cor': '#28a745',
            'ordem': 2,
            'ativo': True,
            'config_json': {
                'categorias_predefinidas': True,
                'sla_automatico': True,
                'anexos_permitidos': True,
                'workflow_aprovacao': False
            }
        },
        {
            'nome': 'Salva-Vidas',
            'slug': 'salva_vidas',
            'descricao': 'Gestão da equipe de salva-vidas e certificações',
            'icone': 'fas fa-user-shield',
            'cor': '#dc3545',
            'ordem': 3,
            'ativo': True,
            'config_json': {
                'controle_certificacoes': True,
                'gestao_horarios': True,
                'interface_scanner': True
            }
        },
        {
            'nome': 'Financeiro',
            'slug': 'financeiro',
            'descricao': 'Controle financeiro e cobrança (em desenvolvimento)',
            'icone': 'fas fa-dollar-sign',
            'cor': '#ffc107',
            'ordem': 4,
            'ativo': False,
            'config_json': {
                'cobranca_automatica': False,
                'relatorios_financeiros': False,
                'integracao_bancaria': False
            }
        }
    ]
    
    modulos_criados = 0
    
    for dados_modulo in modulos_basicos:
        # Verificar se já existe
        modulo_existente = Modulo.query.filter_by(slug=dados_modulo['slug']).first()
        
        if not modulo_existente:
            modulo = Modulo(**dados_modulo)
            db.session.add(modulo)
            modulos_criados += 1
            print(f"✅ Módulo '{dados_modulo['nome']}' criado")
        else:
            print(f"⚠️ Módulo '{dados_modulo['nome']}' já existe")
    
    if modulos_criados > 0:
        db.session.commit()
        print(f"\n🔧 {modulos_criados} módulos criados com sucesso!")
    else:
        print("\n📋 Todos os módulos já existem")
    
    return modulos_criados

def verificar_admin_usuario():
    """Verificar se existe pelo menos um usuário admin"""
    from app.models import Usuario
    
    admin_count = Usuario.query.filter_by(tipo_usuario='admin').count()
    
    if admin_count == 0:
        print("\n⚠️ AVISO: Não foi encontrado nenhum usuário administrador!")
        print("💡 Execute o script 'criar_admin.py' para criar um usuário administrador")
        return False
    else:
        print(f"\n👤 {admin_count} usuário(s) administrador(es) encontrado(s)")
        return True

def main():
    """Função principal"""
    print("🚀 Inicializando dados básicos do sistema administrativo...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se as tabelas existem
            db.create_all()
            print("✅ Tabelas do banco de dados verificadas/criadas")
            
            # Criar planos básicos
            print("\n📋 Verificando planos de assinatura...")
            planos_criados = criar_planos_basicos()
            
            # Criar módulos básicos
            print("\n🔧 Verificando módulos do sistema...")
            modulos_criados = criar_modulos_basicos()
            
            # Verificar usuário admin
            print("\n👤 Verificando usuários administradores...")
            admin_ok = verificar_admin_usuario()
            
            print("\n" + "=" * 60)
            print("✅ Inicialização concluída!")
            print(f"📊 Resumo:")
            print(f"   • {planos_criados} planos criados")
            print(f"   • {modulos_criados} módulos criados")
            print(f"   • Admin OK: {'Sim' if admin_ok else 'Não'}")
            
            if not admin_ok:
                print(f"\n⚠️ PRÓXIMOS PASSOS:")
                print(f"   1. Execute: python criar_admin.py")
                print(f"   2. Acesse: /admin/tenants/novo")
                print(f"   3. Cadastre seu primeiro condomínio")
            else:
                print(f"\n🎯 SISTEMA PRONTO!")
                print(f"   • Acesse: /admin/tenants/novo")
                print(f"   • Cadastre novos condomínios")
            
        except Exception as e:
            print(f"\n❌ Erro durante a inicialização: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
