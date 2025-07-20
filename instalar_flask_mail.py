#!/usr/bin/env python3
"""
Script para instalar Flask-Mail se necessário
Execute no PythonAnywhere se der erro de importação
"""

import subprocess
import sys
import importlib

def verificar_e_instalar_flask_mail():
    """Verifica se Flask-Mail está instalado e instala se necessário"""
    
    print("🔍 Verificando Flask-Mail...")
    
    try:
        # Tentar importar Flask-Mail
        import flask_mail
        print("✅ Flask-Mail já está instalado!")
        print(f"   Versão: {flask_mail.__version__}")
        return True
    except ImportError:
        print("❌ Flask-Mail não encontrado. Instalando...")
        
        try:
            # Instalar Flask-Mail
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user', 'Flask-Mail'
            ])
            print("✅ Flask-Mail instalado com sucesso!")
            
            # Verificar se funcionou
            import flask_mail
            print(f"   Versão instalada: {flask_mail.__version__}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao instalar Flask-Mail: {e}")
            return False

def verificar_outras_dependencias():
    """Verifica outras dependências importantes"""
    
    dependencias = [
        'flask',
        'flask_sqlalchemy', 
        'flask_migrate',
        'flask_login',
        'flask_wtf',
        'wtforms',
        'pymysql'
    ]
    
    print("\n🔍 Verificando outras dependências...")
    
    for dep in dependencias:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - FALTANDO!")

if __name__ == "__main__":
    print("🛠️ CondoTech Solutions - Verificação de Dependências")
    print("=" * 55)
    
    # Verificar e instalar Flask-Mail
    flask_mail_ok = verificar_e_instalar_flask_mail()
    
    # Verificar outras dependências
    verificar_outras_dependencias()
    
    print("\n" + "=" * 55)
    if flask_mail_ok:
        print("✅ TUDO OK! Agora recarregue a aplicação web.")
        print("🌐 Acesse: https://barrientos.pythonanywhere.com")
    else:
        print("❌ Problemas encontrados. Verifique os erros acima.")
        
    print("\n🚀 Após resolver, execute 'git pull' e recarregue a app!") 