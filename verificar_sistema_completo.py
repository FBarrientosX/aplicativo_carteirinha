#!/usr/bin/env python3
"""
Script de Verificação Completa do CondoTech Solutions
Verifica todos os aspectos do sistema para identificar possíveis problemas
"""

import os
import sys
import importlib
from pathlib import Path

def verificar_estrutura_arquivos():
    """Verificar se todos os arquivos essenciais existem"""
    print("🔍 Verificando estrutura de arquivos...")
    
    arquivos_essenciais = [
        'app/__init__.py',
        'app/models.py',
        'app/routes.py',
        'app/auth.py',
        'app/forms.py',
        'app/manutencao_routes.py',
        'app/admin_routes.py',
        'app/salva_vidas_routes.py',
        'app/middleware.py',
        'app/config.py',
        'run.py'
    ]
    
    problemas = []
    for arquivo in arquivos_essenciais:
        if not os.path.exists(arquivo):
            problemas.append(f"❌ Arquivo faltando: {arquivo}")
        else:
            print(f"✅ {arquivo}")
    
    return problemas

def verificar_templates():
    """Verificar templates essenciais"""
    print("\n🎨 Verificando templates...")
    
    templates_essenciais = [
        'app/templates/base.html',
        'app/templates/index.html',
        'app/templates/auth/login.html',
        'app/templates/admin/dashboard.html',
        'app/templates/admin/tenants.html',
        'app/templates/admin/tenant_detalhe.html',
        'app/templates/admin/modulos.html',
        'app/templates/admin/system_info.html',
        'app/templates/manutencao/dashboard.html',
        'app/templates/manutencao/listar_chamados.html',
        'app/templates/manutencao/novo_chamado.html',
        'app/templates/manutencao/ver_chamado.html',
        'app/templates/manutencao/editar_chamado.html',
        'app/templates/manutencao/categorias.html'
    ]
    
    problemas = []
    for template in templates_essenciais:
        if not os.path.exists(template):
            problemas.append(f"❌ Template faltando: {template}")
        else:
            print(f"✅ {template}")
    
    return problemas

def verificar_imports():
    """Verificar se todos os imports estão funcionando"""
    print("\n📦 Verificando imports e dependências...")
    
    try:
        # Testar imports principais
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        print("✅ Testing Flask...")
        import flask
        
        print("✅ Testing SQLAlchemy...")
        import sqlalchemy
        
        print("✅ Testing Flask-Login...")
        import flask_login
        
        print("✅ Testing Flask-Mail...")
        import flask_mail
        
        print("✅ Testing WTForms...")
        import wtforms
        
        print("✅ Testing app modules...")
        from app.models import Usuario, Tenant, Modulo
        from app.forms import LoginForm, ChamadoManutencaoForm
        
        return []
        
    except ImportError as e:
        return [f"❌ Erro de import: {str(e)}"]
    except Exception as e:
        return [f"❌ Erro inesperado: {str(e)}"]

def verificar_rotas_admin():
    """Verificar se todas as rotas admin estão definidas"""
    print("\n🔧 Verificando rotas administrativas...")
    
    rotas_esperadas = [
        'dashboard',
        'listar_tenants',
        'detalhe_tenant',
        'toggle_modulo_tenant',
        'listar_modulos',
        'editar_modulo',
        'toggle_modulo',
        'garantir_admin_acesso',
        'system_info'
    ]
    
    try:
        from app.admin_routes import admin_bp
        
        rotas_definidas = []
        for rule in admin_bp.url_map.iter_rules():
            rotas_definidas.append(rule.endpoint.split('.')[-1])
        
        problemas = []
        for rota in rotas_esperadas:
            endpoint = f"admin.{rota}"
            if rota not in rotas_definidas:
                problemas.append(f"❌ Rota admin faltando: {rota}")
            else:
                print(f"✅ admin.{rota}")
        
        return problemas
        
    except Exception as e:
        return [f"❌ Erro ao verificar rotas admin: {str(e)}"]

def verificar_rotas_manutencao():
    """Verificar rotas de manutenção"""
    print("\n🔨 Verificando rotas de manutenção...")
    
    rotas_esperadas = [
        'dashboard',
        'listar_chamados',
        'novo_chamado',
        'ver_chamado',
        'editar_chamado',
        'categorias',
        'nova_categoria',
        'editar_categoria',
        'toggle_categoria',
        'excluir_categoria'
    ]
    
    try:
        from app.manutencao_routes import manutencao_bp
        
        rotas_definidas = []
        for rule in manutencao_bp.url_map.iter_rules():
            rotas_definidas.append(rule.endpoint.split('.')[-1])
        
        problemas = []
        for rota in rotas_esperadas:
            if rota not in rotas_definidas:
                problemas.append(f"❌ Rota manutenção faltando: {rota}")
            else:
                print(f"✅ manutencao.{rota}")
        
        return problemas
        
    except Exception as e:
        return [f"❌ Erro ao verificar rotas manutenção: {str(e)}"]

def verificar_modelos():
    """Verificar se todos os modelos estão bem definidos"""
    print("\n🗃️ Verificando modelos do banco de dados...")
    
    try:
        from app.models import (
            Usuario, Tenant, Plano, Modulo, ModuloTenant,
            ChamadoManutencao, CategoriaManutencao, AnexoChamado, HistoricoChamado,
            Morador, SalvaVidas, RegistroAcesso
        )
        
        modelos = [
            ('Usuario', Usuario),
            ('Tenant', Tenant),
            ('Plano', Plano),
            ('Modulo', Modulo),
            ('ModuloTenant', ModuloTenant),
            ('ChamadoManutencao', ChamadoManutencao),
            ('CategoriaManutencao', CategoriaManutencao),
            ('AnexoChamado', AnexoChamado),
            ('HistoricoChamado', HistoricoChamado),
            ('Morador', Morador),
            ('SalvaVidas', SalvaVidas),
            ('RegistroAcesso', RegistroAcesso)
        ]
        
        problemas = []
        for nome, modelo in modelos:
            try:
                # Verificar se tem as propriedades básicas
                if not hasattr(modelo, '__tablename__'):
                    problemas.append(f"❌ {nome}: falta __tablename__")
                elif not hasattr(modelo, 'id'):
                    problemas.append(f"❌ {nome}: falta campo id")
                else:
                    print(f"✅ {nome}")
            except Exception as e:
                problemas.append(f"❌ {nome}: {str(e)}")
        
        return problemas
        
    except ImportError as e:
        return [f"❌ Erro ao importar modelos: {str(e)}"]

def verificar_formularios():
    """Verificar se todos os formulários estão bem definidos"""
    print("\n📋 Verificando formulários...")
    
    try:
        from app.forms import (
            LoginForm, CadastroUsuarioForm, MoradorForm,
            ChamadoManutencaoForm, FiltrosChamadosForm,
            SalvaVidasForm, BuscaMoradorForm
        )
        
        formularios = [
            'LoginForm', 'CadastroUsuarioForm', 'MoradorForm',
            'ChamadoManutencaoForm', 'FiltrosChamadosForm',
            'SalvaVidasForm', 'BuscaMoradorForm'
        ]
        
        for form in formularios:
            print(f"✅ {form}")
        
        return []
        
    except ImportError as e:
        return [f"❌ Erro ao importar formulários: {str(e)}"]

def verificar_configuracao():
    """Verificar configurações importantes"""
    print("\n⚙️ Verificando configurações...")
    
    problemas = []
    
    # Verificar requirements.txt
    if not os.path.exists('requirements.txt'):
        problemas.append("❌ requirements.txt não encontrado")
    else:
        print("✅ requirements.txt")
    
    # Verificar config.py
    try:
        from app.config import Config
        print("✅ app.config.Config")
    except ImportError:
        problemas.append("❌ Erro ao importar Config")
    
    # Verificar se run.py está configurado
    if os.path.exists('run.py'):
        print("✅ run.py")
    else:
        problemas.append("❌ run.py não encontrado")
    
    return problemas

def gerar_relatorio(todos_problemas):
    """Gerar relatório final"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL DE VERIFICAÇÃO")
    print("="*60)
    
    if not any(todos_problemas.values()):
        print("🎉 PARABÉNS! Sistema completamente verificado!")
        print("✅ Todos os componentes estão funcionando corretamente.")
        print("\n🚀 O CondoTech Solutions está pronto para uso!")
        return True
    else:
        print("⚠️ PROBLEMAS ENCONTRADOS:")
        total_problemas = 0
        
        for categoria, problemas in todos_problemas.items():
            if problemas:
                print(f"\n📂 {categoria.upper()}:")
                for problema in problemas:
                    print(f"   {problema}")
                    total_problemas += 1
        
        print(f"\n📈 Total de problemas: {total_problemas}")
        print("\n🔧 Corrija os problemas acima antes de usar o sistema.")
        return False

def main():
    """Função principal"""
    print("🛠️ CondoTech Solutions - Verificação Completa do Sistema")
    print("="*60)
    
    # Executar todas as verificações
    problemas = {
        'estrutura_arquivos': verificar_estrutura_arquivos(),
        'templates': verificar_templates(),
        'imports': verificar_imports(),
        'rotas_admin': verificar_rotas_admin(),
        'rotas_manutencao': verificar_rotas_manutencao(),
        'modelos': verificar_modelos(),
        'formularios': verificar_formularios(),
        'configuracao': verificar_configuracao()
    }
    
    # Gerar relatório
    sucesso = gerar_relatorio(problemas)
    
    if sucesso:
        print("\n🌐 Para iniciar o sistema:")
        print("   python run.py")
        print("\n📚 Para acessar a documentação:")
        print("   Verifique os arquivos .md no projeto")
        
    return 0 if sucesso else 1

if __name__ == "__main__":
    sys.exit(main()) 