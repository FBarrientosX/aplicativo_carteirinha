# Script de Deploy Automático para Produção
# Execute com: .\deploy.ps1

Write-Host "🚀 INICIANDO DEPLOY PARA PRODUÇÃO" -ForegroundColor Green
Write-Host "=" * 50

# Verificar se está no diretório correto
if (-not (Test-Path "app\models.py")) {
    Write-Host "❌ ERRO: Execute o script no diretório raiz do projeto" -ForegroundColor Red
    exit 1
}

# Verificar se git está configurado
try {
    git status | Out-Null
} catch {
    Write-Host "❌ ERRO: Projeto não está inicializado com Git" -ForegroundColor Red
    exit 1
}

# Verificar se Heroku CLI está instalado
try {
    heroku --version | Out-Null
} catch {
    Write-Host "❌ ERRO: Heroku CLI não está instalado" -ForegroundColor Red
    Write-Host "Instale em: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
    exit 1
}

# Perguntar nome da aplicação
$app_name = Read-Host "Digite o nome da aplicação no Heroku (ex: minha-carteirinha)"

# Verificar se a aplicação já existe
$app_exists = $false
try {
    heroku apps:info $app_name | Out-Null
    $app_exists = $true
    Write-Host "✅ Aplicação $app_name já existe no Heroku" -ForegroundColor Green
} catch {
    Write-Host "🆕 Aplicação $app_name será criada" -ForegroundColor Yellow
}

# Criar aplicação se não existir
if (-not $app_exists) {
    Write-Host "📦 Criando aplicação no Heroku..." -ForegroundColor Blue
    heroku create $app_name --region us
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERRO: Falha ao criar aplicação no Heroku" -ForegroundColor Red
        exit 1
    }
}

# Adicionar PostgreSQL se não existir
Write-Host "🗄️ Configurando PostgreSQL..." -ForegroundColor Blue
try {
    heroku addons:info heroku-postgresql --app $app_name | Out-Null
    Write-Host "✅ PostgreSQL já configurado" -ForegroundColor Green
} catch {
    heroku addons:create heroku-postgresql:hobby-dev --app $app_name
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERRO: Falha ao configurar PostgreSQL" -ForegroundColor Red
        exit 1
    }
}

# Configurar variáveis de ambiente
Write-Host "⚙️ Configurando variáveis de ambiente..." -ForegroundColor Blue

# Gerar chave secreta se não existir
$secret_key = Read-Host "Digite uma chave secreta (ou pressione Enter para gerar automaticamente)"
if ([string]::IsNullOrWhiteSpace($secret_key)) {
    $secret_key = [System.Web.Security.Membership]::GeneratePassword(50, 10)
    Write-Host "🔑 Chave secreta gerada automaticamente" -ForegroundColor Yellow
}

heroku config:set FLASK_ENV=production --app $app_name
heroku config:set SECRET_KEY=$secret_key --app $app_name

# Configurar email
$email_username = Read-Host "Digite o email para envio de notificações (Gmail)"
$email_password = Read-Host "Digite a senha de app do Gmail" -AsSecureString
$email_password_text = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($email_password))

heroku config:set MAIL_USERNAME=$email_username --app $app_name
heroku config:set MAIL_PASSWORD=$email_password_text --app $app_name

# Fazer commit e push
Write-Host "📤 Fazendo deploy..." -ForegroundColor Blue
git add .
git commit -m "Deploy para produção - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push heroku main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERRO: Falha no deploy" -ForegroundColor Red
    exit 1
}

# Executar migrações
Write-Host "🗄️ Executando migrações..." -ForegroundColor Blue
heroku run python migrar_para_saas.py --app $app_name
heroku run python criar_planos_iniciais.py --app $app_name

# Verificar se aplicação está rodando
Write-Host "🔍 Verificando aplicação..." -ForegroundColor Blue
$app_url = "https://$app_name.herokuapp.com"
try {
    $response = Invoke-WebRequest -Uri $app_url -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Aplicação está rodando!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Aplicação pode não estar respondendo ainda" -ForegroundColor Yellow
}

# Resumo final
Write-Host ""
Write-Host "🎉 DEPLOY CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host "🌐 URL da aplicação: $app_url" -ForegroundColor Cyan
Write-Host "📧 Email configurado: $email_username" -ForegroundColor Cyan
Write-Host "🔑 Chave secreta: [OCULTA]" -ForegroundColor Cyan
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Acessar $app_url e testar" -ForegroundColor White
Write-Host "2. Configurar domínio personalizado" -ForegroundColor White
Write-Host "3. Criar primeiro cliente de teste" -ForegroundColor White
Write-Host "4. Configurar DNS com wildcard" -ForegroundColor White
Write-Host ""
Write-Host "COMANDOS ÚTEIS:" -ForegroundColor Yellow
Write-Host "heroku logs --tail --app $app_name" -ForegroundColor White
Write-Host "heroku config --app $app_name" -ForegroundColor White
Write-Host "heroku ps --app $app_name" -ForegroundColor White 