#!/bin/bash

# Script de Deploy para Heroku

echo "🚀 Iniciando deploy para produção..."

# Verificar se o Heroku CLI está instalado
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI não encontrado. Instale em: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Fazer login no Heroku
echo "🔑 Fazendo login no Heroku..."
heroku login

# Solicitar nome da aplicação
read -p "📝 Nome da aplicação no Heroku: " app_name

# Criar aplicação
echo "📦 Criando aplicação '$app_name'..."
heroku create $app_name

# Adicionar PostgreSQL
echo "🐘 Adicionando PostgreSQL..."
heroku addons:create heroku-postgresql:hobby-dev --app $app_name

# Configurar variáveis de ambiente
echo "⚙️ Configurando variáveis de ambiente..."

# Gerar chave secreta
secret_key=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

heroku config:set SECRET_KEY="$secret_key" --app $app_name
heroku config:set FLASK_ENV=production --app $app_name

# Configurações de email
read -p "📧 Email para notificações: " email_username
read -p "🔐 Senha de app do Gmail: " email_password

heroku config:set MAIL_SERVER=smtp.gmail.com --app $app_name
heroku config:set MAIL_PORT=587 --app $app_name
heroku config:set MAIL_USE_TLS=true --app $app_name
heroku config:set MAIL_USERNAME="$email_username" --app $app_name
heroku config:set MAIL_PASSWORD="$email_password" --app $app_name
heroku config:set MAIL_DEFAULT_SENDER="$email_username" --app $app_name

# Configurar git remote
echo "🔗 Configurando git remote..."
heroku git:remote -a $app_name

# Fazer commit das mudanças
echo "💾 Fazendo commit das mudanças..."
git add .
git commit -m "Deploy para produção - $app_name"

# Deploy
echo "🚀 Fazendo deploy..."
git push heroku main

# Inicializar banco de dados
echo "🗄️ Inicializando banco de dados..."
heroku run python init_db.py --app $app_name

# Criar usuário admin
echo "👤 Criando usuário administrador..."
heroku run python criar_admin.py --app $app_name

echo "✅ Deploy concluído com sucesso!"
echo "🌐 Acesse sua aplicação em: https://$app_name.herokuapp.com"
echo "📊 Logs: heroku logs --tail --app $app_name" 