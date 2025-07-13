#!/usr/bin/env python3
"""
Script de deploy automatizado para PythonAnywhere
Execute: python deploy_pythonanywhere.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def verificar_prerequisitos():
    """Verifica se todos os pré-requisitos estão atendidos"""
    print("🔍 Verificando pré-requisitos...")
    
    # Verificar se o sistema está funcionando
    if not os.path.exists('app'):
        print("❌ Diretório 'app' não encontrado. Execute na raiz do projeto.")
        return False
    
    if not os.path.exists('requirements.txt'):
        print("❌ Arquivo 'requirements.txt' não encontrado.")
        return False
    
    print("✅ Pré-requisitos verificados!")
    return True

def criar_arquivos_pythonanywhere():
    """Cria arquivos específicos para PythonAnywhere"""
    print("📁 Criando arquivos para PythonAnywhere...")
    
    # Criar wsgi.py para PythonAnywhere
    wsgi_content = '''
import sys
import os

# Adicionar o diretório do seu projeto ao path
project_home = '/home/SEU_USUARIO/aplicativo_carteirinha'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Configurar variáveis de ambiente
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'sqlite:///home/SEU_USUARIO/aplicativo_carteirinha/carteirinha_piscina.db'

# Importar a aplicação
from app import create_app

# Criar aplicação
application = create_app()

if __name__ == "__main__":
    application.run()
'''
    
    with open('wsgi.py', 'w', encoding='utf-8') as f:
        f.write(wsgi_content)
    
    # Criar script de configuração
    config_content = '''#!/bin/bash
# Script de configuração para PythonAnywhere
# Execute este script no console do PythonAnywhere

echo "🚀 Configurando aplicação no PythonAnywhere..."

# Instalar dependências
pip3.10 install --user -r requirements.txt

# Executar migrações
python3.10 migrar_para_saas_simples.py
python3.10 criar_planos_iniciais.py
python3.10 criar_cliente_inicial.py

# Criar diretórios necessários
mkdir -p app/static/uploads/carteirinhas
mkdir -p app/static/uploads/anexos

echo "✅ Configuração concluída!"
echo "🌐 Agora configure o Web App no dashboard do PythonAnywhere"
'''
    
    with open('setup_pythonanywhere.sh', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ Arquivos criados com sucesso!")

def criar_guia_deploy():
    """Cria guia detalhado de deploy"""
    print("📚 Criando guia de deploy...")
    
    guia_content = '''# 🚀 GUIA DE DEPLOY - PYTHONANYWHERE

## PASSO 1: UPLOAD DOS ARQUIVOS

### Método 1: Upload via Interface Web
1. Acesse: https://www.pythonanywhere.com/user/SEU_USUARIO/files/
2. Crie pasta: `aplicativo_carteirinha`
3. Faça upload de todos os arquivos do projeto

### Método 2: Git Clone (Recomendado)
```bash
# No console do PythonAnywhere
git clone https://github.com/SEU_USUARIO/aplicativo_carteirinha.git
cd aplicativo_carteirinha
```

## PASSO 2: CONFIGURAR AMBIENTE

### Instalar Dependências
```bash
# No console do PythonAnywhere
cd aplicativo_carteirinha
pip3.10 install --user -r requirements.txt
```

### Executar Migrações
```bash
python3.10 migrar_para_saas_simples.py
python3.10 criar_planos_iniciais.py
python3.10 criar_cliente_inicial.py
```

## PASSO 3: CONFIGURAR WEB APP

### Criar Web App
1. Acesse: https://www.pythonanywhere.com/user/SEU_USUARIO/webapps/
2. Clique em "Add a new web app"
3. Escolha "Manual configuration"
4. Escolha "Python 3.10"

### Configurar WSGI
1. Vá para aba "Code"
2. Clique em "WSGI configuration file"
3. Cole o conteúdo do arquivo `wsgi.py`
4. Substitua `SEU_USUARIO` pelo seu username

### Configurar Arquivos Estáticos
1. Vá para aba "Static files"
2. Adicione:
   - URL: `/static/`
   - Directory: `/home/SEU_USUARIO/aplicativo_carteirinha/app/static/`

## PASSO 4: TESTAR APLICAÇÃO

### Acessar Sistema
- URL: `https://SEU_USUARIO.pythonanywhere.com`
- Login: `admin@teste.com`
- Senha: `123456`

### Super Admin
- Login: `superadmin@sistema.com`
- Senha: `superadmin123`

## PASSO 5: CONFIGURAR DOMÍNIO (OPCIONAL)

### Plano Gratuito
- Domínio: `SEU_USUARIO.pythonanywhere.com`
- Não suporta domínio personalizado

### Upgrade para Hacker Plan (€5/mês)
- Domínio personalizado disponível
- Mais recursos e poder

## 🎯 PRÓXIMOS PASSOS

1. **Testar todas as funcionalidades**
2. **Configurar email (se necessário)**
3. **Cadastrar primeiros clientes**
4. **Monitorar performance**
5. **Planejar upgrade quando necessário**

## 📊 LIMITES DO PLANO GRATUITO

- **1 web app**
- **512MB de espaço**
- **100 segundos de CPU/dia**
- **Tráfego limitado**
- **Domínio pythonanywhere.com**

## 🚀 BENEFÍCIOS

- **Deploy simples**
- **Manutenção automática**
- **Suporte excelente**
- **Escalabilidade fácil**
- **Backup automático**

---

**Resultado**: Seu SaaS estará online em `https://SEU_USUARIO.pythonanywhere.com` 🎉
'''
    
    with open('GUIA_DEPLOY_PYTHONANYWHERE.md', 'w', encoding='utf-8') as f:
        f.write(guia_content)
    
    print("✅ Guia de deploy criado!")

def main():
    """Função principal"""
    print("🚀 PREPARANDO DEPLOY PARA PYTHONANYWHERE")
    print("=" * 50)
    
    if not verificar_prerequisitos():
        sys.exit(1)
    
    criar_arquivos_pythonanywhere()
    criar_guia_deploy()
    
    print("\n🎉 ARQUIVOS PREPARADOS COM SUCESSO!")
    print("=" * 50)
    print("PRÓXIMOS PASSOS:")
    print("1. Crie conta no PythonAnywhere: https://www.pythonanywhere.com/registration/register/beginner/")
    print("2. Leia o guia: GUIA_DEPLOY_PYTHONANYWHERE.md")
    print("3. Faça upload dos arquivos")
    print("4. Configure o Web App")
    print("5. Acesse seu SaaS online!")
    
    print("\n🌐 SEU SAAS ESTARÁ EM:")
    print("https://SEU_USUARIO.pythonanywhere.com")

if __name__ == '__main__':
    main() 