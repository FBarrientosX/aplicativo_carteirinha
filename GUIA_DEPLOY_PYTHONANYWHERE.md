# 🚀 GUIA DE DEPLOY - PYTHONANYWHERE

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
