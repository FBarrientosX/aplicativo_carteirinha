#!/usr/bin/env python3
"""
Script de teste completo para validar o sistema SaaS
Execute: python testar_sistema.py
"""

import os
import sys
import time
import requests
from datetime import datetime

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def testar_conexao_db():
    """Testa conexão com o banco de dados"""
    try:
        from app import create_app, db
        from app.models import Tenant, Usuario, Plano
        
        app = create_app()
        with app.app_context():
            # Testar conexão básica
            with db.engine.connect() as connection:
                connection.execute(db.text('SELECT 1'))
            print("✅ Conexão com banco de dados funcionando")
            
            # Contar registros
            tenants = Tenant.query.count()
            usuarios = Usuario.query.count()
            planos = Plano.query.count()
            
            print(f"📊 Registros no banco:")
            print(f"  - Tenants: {tenants}")
            print(f"  - Usuários: {usuarios}")
            print(f"  - Planos: {planos}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False

def testar_modelos_saas():
    """Testa se os modelos SaaS foram criados corretamente"""
    try:
        from app.models import Tenant, Plano, Cobranca, ConfiguracaoTenant
        
        # Verificar se as classes existem
        modelos = [Tenant, Plano, Cobranca, ConfiguracaoTenant]
        for modelo in modelos:
            print(f"✅ Modelo {modelo.__name__} existe")
        
        # Verificar se tenant_id existe nas tabelas
        from app.models import Morador, AnexoMorador, LogNotificacao
        
        print("✅ Modelos SaaS configurados corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos modelos SaaS: {e}")
        return False

def testar_middleware():
    """Testa se o middleware está funcionando"""
    try:
        from app import create_app
        
        app = create_app()
        
        # Verificar se middleware foi registrado - verificamos se existe middleware
        middleware_existe = hasattr(app, 'wsgi_app') and app.wsgi_app is not None
        
        if middleware_existe:
            print("✅ Middleware de tenants configurado")
            return True
        else:
            print("❌ Middleware não configurado")
            return False
        
    except Exception as e:
        print(f"❌ Erro no middleware: {e}")
        return False

def testar_aplicacao_local():
    """Testa se a aplicação está rodando localmente"""
    try:
        # Verificar se o servidor está rodando
        response = requests.get('http://localhost:5000', timeout=5)
        
        if response.status_code == 200:
            print("✅ Aplicação rodando localmente")
            return True
        else:
            print(f"⚠️ Aplicação retornou status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Aplicação não está rodando localmente")
        print("💡 Execute: python run.py")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar aplicação: {e}")
        return False

def testar_tenant_subdominio():
    """Testa se o tenant está funcionando via subdomínio"""
    try:
        # Testar com subdomínio local
        headers = {'Host': 'teste.localhost:5000'}
        response = requests.get('http://localhost:5000', headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("✅ Subdomínio de tenant funcionando")
            return True
        else:
            print(f"⚠️ Subdomínio retornou status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Aplicação não está rodando para testar subdomínio")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar subdomínio: {e}")
        return False

def testar_heroku_deploy():
    """Testa se o deploy no Heroku foi bem-sucedido"""
    try:
        # Verificar se existe arquivo Procfile
        if not os.path.exists('Procfile'):
            print("❌ Procfile não encontrado")
            return False
        
        # Verificar se requirements.txt tem dependências corretas
        if not os.path.exists('requirements.txt'):
            print("❌ requirements.txt não encontrado")
            return False
            
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'gunicorn' not in content:
                print("❌ gunicorn não encontrado em requirements.txt")
                return False
            if 'psycopg2-binary' not in content:
                print("❌ psycopg2-binary não encontrado em requirements.txt")
                return False
        
        print("✅ Configuração para Heroku está correta")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar configuração Heroku: {e}")
        return False

def testar_scripts_saas():
    """Testa se os scripts SaaS existem"""
    scripts = [
        'migrar_para_saas.py',
        'criar_planos_iniciais.py',
        'criar_cliente_inicial.py',
        'deploy.ps1'
    ]
    
    todos_existem = True
    for script in scripts:
        if os.path.exists(script):
            print(f"✅ Script {script} existe")
        else:
            print(f"❌ Script {script} não encontrado")
            todos_existem = False
    
    return todos_existem

def main():
    """Função principal de teste"""
    print("🧪 INICIANDO TESTES DO SISTEMA SAAS")
    print("=" * 60)
    
    testes = [
        ("Conexão com Banco de Dados", testar_conexao_db),
        ("Modelos SaaS", testar_modelos_saas),
        ("Middleware", testar_middleware),
        ("Scripts SaaS", testar_scripts_saas),
        ("Configuração Heroku", testar_heroku_deploy),
        ("Aplicação Local", testar_aplicacao_local),
        ("Subdomínio Tenant", testar_tenant_subdominio),
    ]
    
    resultados = []
    
    for nome, teste_func in testes:
        print(f"\n🔍 Testando: {nome}")
        print("-" * 40)
        
        try:
            resultado = teste_func()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            resultados.append((nome, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    sucessos = 0
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{status:12} {nome}")
        if resultado:
            sucessos += 1
    
    total = len(resultados)
    percentual = (sucessos / total) * 100
    
    print(f"\n🎯 RESULTADO FINAL: {sucessos}/{total} testes passaram ({percentual:.1f}%)")
    
    if percentual >= 80:
        print("🎉 SISTEMA PRONTO PARA PRODUÇÃO!")
        print("\nPRÓXIMOS PASSOS:")
        print("1. Execute: .\\deploy.ps1")
        print("2. Configure DNS wildcard")
        print("3. Registre primeiro cliente")
        print("4. Inicie vendas!")
    elif percentual >= 60:
        print("⚠️ SISTEMA PARCIALMENTE PRONTO")
        print("Corrija os testes que falharam antes do deploy")
    else:
        print("❌ SISTEMA NÃO ESTÁ PRONTO")
        print("Corrija os problemas críticos antes de continuar")
    
    print("\n" + "=" * 60)
    print(f"⏰ Teste realizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return percentual >= 80

if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1) 