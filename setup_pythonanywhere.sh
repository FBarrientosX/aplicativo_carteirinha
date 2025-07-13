#!/bin/bash
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
