# 📧 Configuração de Email SMTP

## Passo 1: Criar arquivo .env

Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:

```bash
# Configurações da Aplicação
SECRET_KEY=sua_chave_secreta_super_segura_aqui

# === CONFIGURAÇÃO GMAIL (RECOMENDADO) ===
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app_do_gmail
MAIL_DEFAULT_SENDER=seu_email@gmail.com
```

## Passo 2: Configurar Gmail (Mais fácil)

### 2.1 Ativar autenticação de 2 fatores
1. Acesse: https://myaccount.google.com/security
2. Ative a "Verificação em duas etapas"

### 2.2 Gerar senha de app
1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Email" e "Computador Windows"
3. Clique em "Gerar"
4. **COPIE A SENHA GERADA** (16 caracteres)
5. Use esta senha no `MAIL_PASSWORD` (não sua senha normal!)

### 2.3 Configurar .env
```bash
MAIL_USERNAME=seuemail@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop  # Senha de app de 16 caracteres
MAIL_DEFAULT_SENDER=seuemail@gmail.com
```

## Passo 3: Outras opções de email

### Outlook/Hotmail
```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu_email@outlook.com
MAIL_PASSWORD=sua_senha
MAIL_DEFAULT_SENDER=seu_email@outlook.com
```

### Yahoo
```bash
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu_email@yahoo.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_DEFAULT_SENDER=seu_email@yahoo.com
```

### Servidor personalizado
```bash
MAIL_SERVER=smtp.suaempresa.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu_email@empresa.com
MAIL_PASSWORD=sua_senha
MAIL_DEFAULT_SENDER=seu_email@empresa.com
```

## Passo 4: Testar a configuração

1. Reinicie a aplicação: `python run.py`
2. Cadastre um morador com seu email
3. Valide a carteirinha com vencimento próximo
4. Acesse Relatórios → "Enviar Notificações"

## Passo 5: Troubleshooting

### Erro "Authentication failed"
- Verifique se ativou a autenticação de 2 fatores (Gmail)
- Use senha de app, não sua senha normal
- Verifique se o email/senha estão corretos

### Erro "Connection refused"
- Verifique se o MAIL_SERVER está correto
- Teste a porta (587 ou 465)
- Verifique sua conexão de internet

### Gmail não funciona
- Certifique-se de usar senha de app
- Verifique se a conta tem 2FA ativado
- Tente desativar/reativar as senhas de app

## Exemplo de .env completo
```bash
SECRET_KEY=minha_chave_super_secreta_123456789

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=admin@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop
MAIL_DEFAULT_SENDER=admin@gmail.com
```

## ⚠️ IMPORTANTE
- **NUNCA** compartilhe o arquivo .env
- Adicione `.env` no `.gitignore`
- Use emails reais para testes
- Mantenha as credenciais seguras 