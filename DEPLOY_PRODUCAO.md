# 🚀 DEPLOY EM PRODUÇÃO - PASSO A PASSO

## Status Atual
✅ Sistema multi-tenant implementado  
✅ Modelos SaaS criados  
✅ Middleware de tenants funcionando  
✅ Scripts de migração prontos  
✅ Configuração para produção criada  

## O QUE FALTA PARA PRODUÇÃO

### 1. PREPARAÇÃO DO AMBIENTE LOCAL
```bash
# 1.1 Instalar dependências atualizadas
pip install -r requirements.txt

# 1.2 Executar migração para SaaS
python migrar_para_saas.py

# 1.3 Criar planos iniciais
python criar_planos_iniciais.py

# 1.4 Testar sistema localmente
python run.py
```

### 2. CONFIGURAÇÃO DO BANCO DE DADOS
```bash
# 2.1 Executar migrações do Flask-Migrate
flask db upgrade

# 2.2 Criar usuário administrador global
python criar_admin.py
```

### 3. CONFIGURAÇÃO DE PRODUÇÃO

#### 3.1 Heroku (Recomendado)
```bash
# Criar app no Heroku
heroku create seu-app-carteirinha

# Configurar PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Configurar variáveis de ambiente
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=sua-chave-secreta-super-forte
heroku config:set MAIL_USERNAME=seu-email@gmail.com
heroku config:set MAIL_PASSWORD=sua-senha-app

# Deploy
git push heroku main
```

#### 3.2 DigitalOcean/AWS (Alternativa)
```bash
# Criar droplet/instância
# Instalar Docker
# Usar docker-compose.yml (a ser criado)
```

### 4. CONFIGURAÇÃO DE DNS E SUBDOMÍNIOS

#### 4.1 Registrar Domínio
- Registrar dominio.com.br
- Configurar DNS com suporte a wildcard

#### 4.2 Configurar Subdomínios Wildcard
```
# No provedor DNS (Cloudflare, GoDaddy, etc.)
A record: * -> IP-do-servidor
A record: @ -> IP-do-servidor
CNAME: www -> dominio.com.br
```

### 5. CRIAÇÃO DO PRIMEIRO CLIENTE

#### 5.1 Cadastrar Cliente via Interface
```
https://seu-dominio.com.br/onboarding
```

#### 5.2 Ou via Script
```python
python criar_cliente_inicial.py
```

### 6. CONFIGURAÇÃO DE EMAIL

#### 6.1 Gmail App Password
- Ativar 2FA na conta Google
- Gerar senha de app específica
- Configurar nas variáveis de ambiente

#### 6.2 SendGrid (Recomendado para produção)
```bash
heroku config:set SENDGRID_API_KEY=sua-chave-sendgrid
```

### 7. MONITORAMENTO E LOGS

#### 7.1 Configurar Logs
```bash
heroku logs --tail
```

#### 7.2 Monitoramento de Erros
- Configurar Sentry (opcional)
- Configurar New Relic (opcional)

### 8. SEGURANÇA

#### 8.1 HTTPS
- Heroku já inclui SSL automático
- Para outros provedores, configurar Let's Encrypt

#### 8.2 Firewall e Segurança
- Configurar WAF se necessário
- Backup automático do banco

### 9. PERFORMANCE

#### 9.1 CDN (Opcional)
- Configurar Cloudflare para assets estáticos

#### 9.2 Cache (Futuro)
- Implementar Redis para cache de sessões

## CRONOGRAMA DE DEPLOY

### DIA 1: Preparação Local
- [ ] Executar migrações
- [ ] Testar sistema localmente
- [ ] Criar dados de teste

### DIA 2: Deploy Inicial
- [ ] Configurar Heroku
- [ ] Fazer primeiro deploy
- [ ] Testar em produção

### DIA 3: DNS e Domínio
- [ ] Registrar domínio
- [ ] Configurar DNS wildcard
- [ ] Testar subdomínios

### DIA 4: Primeiro Cliente
- [ ] Criar cliente de teste
- [ ] Testar fluxo completo
- [ ] Documentar problemas

### DIA 5: Ajustes Finais
- [ ] Corrigir bugs encontrados
- [ ] Otimizar performance
- [ ] Preparar lançamento

## CUSTOS ESTIMADOS

### Heroku
- Dyno Básico: $7/mês
- PostgreSQL: $9/mês
- Total: ~$16/mês (~R$80/mês)

### DigitalOcean
- Droplet $5/mês
- PostgreSQL $15/mês
- Total: ~$20/mês (~R$100/mês)

### Outros
- Domínio: ~R$40/ano
- Email SendGrid: Gratuito até 100 emails/dia

## PRÓXIMOS PASSOS IMEDIATOS

1. **AGORA**: Testar migração local
2. **HOJE**: Configurar Heroku
3. **AMANHÃ**: Primeiro deploy
4. **ESTA SEMANA**: Registrar domínio
5. **PRÓXIMA SEMANA**: Primeiro cliente pagante

## SCRIPTS AUTOMATIZADOS

### deploy.ps1 (Windows)
```powershell
# Script automático de deploy
Write-Host "Iniciando deploy..."
git add .
git commit -m "Deploy para produção"
git push heroku main
heroku run python migrar_para_saas.py
heroku run python criar_planos_iniciais.py
Write-Host "Deploy concluído!"
```

### deploy.sh (Linux/Mac)
```bash
#!/bin/bash
echo "Iniciando deploy..."
git add .
git commit -m "Deploy para produção"
git push heroku main
heroku run python migrar_para_saas.py
heroku run python criar_planos_iniciais.py
echo "Deploy concluído!"
```

## CHECKLIST FINAL

### Antes do Deploy
- [ ] Código testado localmente
- [ ] Banco migrado
- [ ] Planos criados
- [ ] Email configurado
- [ ] Variáveis de ambiente definidas

### Após Deploy
- [ ] Aplicação acessível
- [ ] Banco funcionando
- [ ] Emails sendo enviados
- [ ] Subdomínios resolvendo
- [ ] Primeiro cliente cadastrado

### Validação Final
- [ ] Cliente consegue se cadastrar
- [ ] Carteirinhas sendo geradas
- [ ] QR codes funcionando
- [ ] Notificações enviadas
- [ ] Sistema de cobrança ativo

## SUPORTE E MANUTENÇÃO

### Monitoramento Diário
- Verificar logs de erro
- Acompanhar performance
- Verificar backups

### Atualizações
- Atualizações de segurança
- Novas funcionalidades
- Correções de bugs

### Backup
- Backup automático diário
- Teste de restauração mensal
- Documentação atualizada 