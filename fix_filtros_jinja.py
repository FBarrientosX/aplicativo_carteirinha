#!/usr/bin/env python3
"""
FIX DE EMERGÊNCIA - Filtros Jinja2 Faltando
Resolver erro: No filter named 'dateformat' found
"""

import os
import sys
from pathlib import Path

def adicionar_filtros_jinja():
    """Adicionar filtros personalizados no __init__.py"""
    print("🔧 ADICIONANDO FILTROS JINJA2...")
    
    try:
        # Ler __init__.py
        with open('app/__init__.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup
        with open('app/__init__.py.backup_filtros', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Verificar se filtros já existem
        if 'def dateformat(' in content:
            print("   ℹ️  Filtros já existem")
            return True
        
        # Adicionar filtros personalizados antes do return app
        filtros_code = '''
    # ===== FILTROS PERSONALIZADOS JINJA2 =====
    
    @app.template_filter('dateformat')
    def dateformat(value, format='%d/%m/%Y'):
        """Filtro para formatar datas"""
        if value is None:
            return ''
        try:
            if isinstance(value, str):
                return value
            return value.strftime(format)
        except Exception:
            return str(value) if value else ''
    
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        """Filtro para formatar data e hora"""
        if value is None:
            return ''
        try:
            if isinstance(value, str):
                return value
            return value.strftime(format)
        except Exception:
            return str(value) if value else ''
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Filtro para formatar moeda"""
        if value is None:
            return 'R$ 0,00'
        try:
            return f'R$ {float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        except Exception:
            return str(value) if value else 'R$ 0,00'
    
    @app.template_filter('status_badge')
    def status_badge(value):
        """Filtro para classe CSS de status"""
        status_classes = {
            'ativo': 'success',
            'inativo': 'secondary',
            'demitido': 'danger',
            'ferias': 'warning',
            'licenca': 'info',
            'regular': 'success',
            'a_vencer': 'warning',
            'vencida': 'danger',
            'sem_carteirinha': 'secondary'
        }
        return status_classes.get(str(value).lower(), 'secondary')

'''
        
        # Encontrar local para inserir (antes do return app)
        if 'return app' in content:
            content = content.replace('return app', filtros_code + '\n    return app')
        else:
            # Se não encontrar return app, adicionar no final da função
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'def create_app(' in line:
                    # Encontrar o final da função
                    indent_level = len(line) - len(line.lstrip())
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent_level:
                            # Inserir antes desta linha
                            lines.insert(j, filtros_code)
                            break
                    break
            content = '\n'.join(lines)
        
        # Salvar arquivo
        with open('app/__init__.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ Filtros Jinja2 adicionados ao __init__.py")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao adicionar filtros: {e}")
        return False

def corrigir_templates():
    """Corrigir templates que usam filtros não existentes"""
    print("\n🎨 CORRIGINDO TEMPLATES...")
    
    templates_dir = Path('app/templates')
    if not templates_dir.exists():
        print("   ❌ Diretório de templates não encontrado")
        return False
    
    # Mapeamento de filtros problemáticos para soluções
    filtro_fixes = {
        '|dateformat': '|dateformat',  # Agora vai funcionar
        '|datetimeformat': '|datetimeformat',  # Agora vai funcionar
        '|currency': '|currency',  # Agora vai funcionar
        '|status_badge': '|status_badge',  # Agora vai funcionar
    }
    
    arquivos_corrigidos = []
    
    # Procurar por todos os arquivos .html
    for template_file in templates_dir.rglob('*.html'):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content_original = content
            
            # Fixes específicos para filtros comuns
            replacements = [
                # Se dateformat não funcionar, usar strftime básico
                ('|dateformat', '|strftime("%d/%m/%Y") if value else ""'),
                ('{{ morador.data_vencimento|dateformat }}', 
                 '{{ morador.data_vencimento.strftime("%d/%m/%Y") if morador.data_vencimento else "Não definido" }}'),
                ('{{ registro.data_hora|datetimeformat }}',
                 '{{ registro.data_hora.strftime("%d/%m/%Y %H:%M") if registro.data_hora else "" }}'),
            ]
            
            # Aplicar apenas se o filtro personalizado falhar
            for old, new in replacements:
                if old in content and '|dateformat' in content:
                    # Backup mais específico
                    with open(f'{template_file}.backup_filtros', 'w', encoding='utf-8') as f:
                        f.write(content_original)
                    
                    content = content.replace(old, new)
                    arquivos_corrigidos.append(str(template_file))
            
            # Salvar se houve mudanças
            if content != content_original:
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        except Exception as e:
            print(f"   ⚠️  Erro ao processar {template_file}: {e}")
    
    if arquivos_corrigidos:
        print(f"   ✅ {len(arquivos_corrigidos)} templates corrigidos")
        for arquivo in arquivos_corrigidos[:5]:  # Mostrar apenas os primeiros 5
            print(f"      - {arquivo}")
        if len(arquivos_corrigidos) > 5:
            print(f"      - ... e mais {len(arquivos_corrigidos) - 5}")
    else:
        print("   ℹ️  Nenhum template precisou de correção")
    
    return True

def verificar_outros_erros():
    """Verificar outros possíveis erros nos templates"""
    print("\n🔍 VERIFICANDO OUTROS PROBLEMAS...")
    
    problemas_comuns = [
        ('|safe', 'Filtro safe usado'),
        ('|length', 'Filtro length usado'),
        ('|default', 'Filtro default usado'),
        ('current_user.', 'Referência a current_user'),
        ('url_for(', 'Função url_for usada'),
    ]
    
    templates_dir = Path('app/templates')
    for template_file in templates_dir.rglob('*.html'):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for padrao, descricao in problemas_comuns:
                if padrao in content:
                    count = content.count(padrao)
                    if count > 0:
                        print(f"   ✓ {template_file.name}: {count}x {descricao}")
        
        except Exception:
            pass
    
    print("   ✅ Verificação concluída")

def main():
    print("🎨 FIX DE EMERGÊNCIA - FILTROS JINJA2")
    print("="*50)
    
    print("❌ PROBLEMA IDENTIFICADO:")
    print("   - Filtro 'dateformat' não encontrado")
    print("   - Templates falham ao renderizar")
    print("   - Sistema inacessível")
    
    print("\n🔧 APLICANDO CORREÇÕES...")
    
    sucesso_filtros = adicionar_filtros_jinja()
    sucesso_templates = corrigir_templates()
    verificar_outros_erros()
    
    if sucesso_filtros and sucesso_templates:
        print("\n✅ CORREÇÕES APLICADAS COM SUCESSO!")
        print("\n🚀 PRÓXIMOS PASSOS NO PYTHONANYWHERE:")
        print("   1. Faça git push das correções:")
        print("      git add .")
        print("      git commit -m 'Fix filtros Jinja2 faltando'")
        print("      git push")
        print("   2. No PythonAnywhere:")
        print("      git pull")
        print("   3. Recarregue a aplicação")
        print("   4. Teste as páginas")
        
        print("\n📋 ARQUIVOS MODIFICADOS:")
        print("   - app/__init__.py (filtros adicionados)")
        print("   - Templates corrigidos")
        
        print("\n🔄 Para restaurar backups:")
        print("   cp app/__init__.py.backup_filtros app/__init__.py")
        
    else:
        print("\n❌ FALHA NAS CORREÇÕES!")
        print("   Verifique os arquivos manualmente")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 