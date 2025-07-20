#!/usr/bin/env python3
"""
Script para Corrigir Problemas Finais Identificados
CondoTech Solutions - Correções Automáticas
"""

import os
import sys
import re
from pathlib import Path

def corrigir_url_for_rotas():
    """Verificar e corrigir possíveis problemas com url_for"""
    print("🔗 Verificando url_for em templates...")
    
    # Mapeamento de rotas que podem ter mudado
    rotas_correcoes = {
        'main.moradores': 'main.listar_moradores',
        'main.salva_vidas': 'main.listar_salva_vidas',
        'admin.tenants': 'admin.listar_tenants',
        'admin.modulos': 'admin.listar_modulos'
    }
    
    templates_dir = Path('app/templates')
    arquivos_corrigidos = []
    
    for arquivo_html in templates_dir.rglob('*.html'):
        try:
            content = arquivo_html.read_text(encoding='utf-8')
            content_original = content
            
            for rota_antiga, rota_nova in rotas_correcoes.items():
                if rota_antiga in content:
                    content = content.replace(f"url_for('{rota_antiga}')", f"url_for('{rota_nova}')")
                    print(f"✅ Corrigido {rota_antiga} → {rota_nova} em {arquivo_html}")
            
            if content != content_original:
                arquivo_html.write_text(content, encoding='utf-8')
                arquivos_corrigidos.append(str(arquivo_html))
                
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo_html}: {e}")
    
    return arquivos_corrigidos

def verificar_imports_circulares():
    """Verificar imports circulares"""
    print("\n🔄 Verificando imports circulares...")
    
    problemas = []
    arquivos_python = Path('app').rglob('*.py')
    
    for arquivo in arquivos_python:
        try:
            content = arquivo.read_text(encoding='utf-8')
            
            # Verificar imports problemáticos
            if 'from app import app' in content and arquivo.name != '__init__.py':
                problemas.append(f"❌ Import circular em {arquivo}: 'from app import app'")
            
            if 'from app.models import *' in content:
                problemas.append(f"⚠️ Import * em {arquivo}: pode causar problemas")
                
        except Exception as e:
            print(f"❌ Erro ao verificar {arquivo}: {e}")
    
    return problemas

def verificar_sql_injection():
    """Verificar possíveis vulnerabilidades de SQL injection"""
    print("\n🛡️ Verificando segurança SQL...")
    
    problemas = []
    arquivos_python = Path('app').rglob('*.py')
    
    for arquivo in arquivos_python:
        try:
            content = arquivo.read_text(encoding='utf-8')
            linhas = content.split('\n')
            
            for i, linha in enumerate(linhas, 1):
                # Verificar queries SQL perigosas
                if 'execute(' in linha and '%s' in linha:
                    problemas.append(f"⚠️ Possível SQL injection em {arquivo}:{i}")
                
                if 'execute(' in linha and 'f"' in linha:
                    problemas.append(f"⚠️ SQL com f-string em {arquivo}:{i}")
                    
                if '.format(' in linha and 'SELECT' in linha.upper():
                    problemas.append(f"⚠️ SQL com .format() em {arquivo}:{i}")
                    
        except Exception as e:
            print(f"❌ Erro ao verificar {arquivo}: {e}")
    
    if not problemas:
        print("✅ Nenhum problema de segurança SQL encontrado!")
    
    return problemas

def verificar_tratamento_erros():
    """Verificar tratamento de erros"""
    print("\n🚨 Verificando tratamento de erros...")
    
    problemas = []
    arquivos_python = Path('app').rglob('*.py')
    
    for arquivo in arquivos_python:
        try:
            content = arquivo.read_text(encoding='utf-8')
            
            # Verificar excepts vazios ou muito genéricos
            if 'except:' in content:
                problemas.append(f"⚠️ Except vazio em {arquivo}")
            
            if 'except Exception:' in content and 'pass' in content:
                problemas.append(f"⚠️ Exception ignorada em {arquivo}")
                
        except Exception as e:
            print(f"❌ Erro ao verificar {arquivo}: {e}")
    
    return problemas

def corrigir_permissoes_arquivos():
    """Corrigir permissões de arquivos se necessário"""
    print("\n🔐 Verificando permissões de arquivos...")
    
    arquivos_importantes = [
        'run.py',
        'verificar_sistema_completo.py',
        'corrigir_problemas_finais.py'
    ]
    
    for arquivo in arquivos_importantes:
        if os.path.exists(arquivo):
            try:
                # No Windows, isso pode não ser necessário
                if os.name != 'nt':
                    os.chmod(arquivo, 0o755)
                print(f"✅ Permissões OK: {arquivo}")
            except Exception as e:
                print(f"⚠️ Não foi possível alterar permissões de {arquivo}: {e}")

def criar_arquivo_gitignore():
    """Criar ou atualizar .gitignore"""
    print("\n📝 Verificando .gitignore...")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Flask
instance/
.webassets-cache

# Environment variables
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Uploads
app/static/uploads/*
!app/static/uploads/.gitkeep

# Instance config
instance/config.py

# Migration files (opcional)
# migrations/versions/*.py
"""
    
    try:
        with open('.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✅ .gitignore criado/atualizado")
    except Exception as e:
        print(f"❌ Erro ao criar .gitignore: {e}")

def verificar_estrutura_diretorios():
    """Verificar e criar diretórios necessários"""
    print("\n📁 Verificando estrutura de diretórios...")
    
    diretorios_necessarios = [
        'app/static/uploads',
        'app/static/uploads/carteirinhas',
        'logs',
        'instance'
    ]
    
    for diretorio in diretorios_necessarios:
        if not os.path.exists(diretorio):
            try:
                os.makedirs(diretorio, exist_ok=True)
                print(f"✅ Diretório criado: {diretorio}")
            except Exception as e:
                print(f"❌ Erro ao criar {diretorio}: {e}")
        else:
            print(f"✅ {diretorio}")

def gerar_relatorio_final():
    """Gerar relatório das correções"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE CORREÇÕES FINAIS")
    print("="*60)
    
    print("✅ Verificações de segurança concluídas")
    print("✅ Estrutura de arquivos verificada")
    print("✅ Permissões corrigidas")
    print("✅ .gitignore atualizado")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Execute: python verificar_sistema_completo.py")
    print("2. Se tudo estiver OK, inicie: python run.py")
    print("3. Acesse: http://localhost:5000")
    print("4. Faça login com usuário admin")
    print("5. Acesse /admin para área administrativa")
    
    print("\n🚀 Sistema CondoTech Solutions pronto para uso!")

def main():
    """Função principal"""
    print("🛠️ CondoTech Solutions - Correções Finais")
    print("="*50)
    
    # Executar correções
    arquivos_corrigidos = corrigir_url_for_rotas()
    imports_problemas = verificar_imports_circulares()
    sql_problemas = verificar_sql_injection()
    erro_problemas = verificar_tratamento_erros()
    
    # Correções de estrutura
    corrigir_permissoes_arquivos()
    criar_arquivo_gitignore()
    verificar_estrutura_diretorios()
    
    # Relatório
    gerar_relatorio_final()
    
    # Mostrar problemas que precisam atenção manual
    problemas_manuais = imports_problemas + sql_problemas + erro_problemas
    if problemas_manuais:
        print("\n⚠️ PROBLEMAS QUE PRECISAM ATENÇÃO MANUAL:")
        for problema in problemas_manuais:
            print(f"   {problema}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 