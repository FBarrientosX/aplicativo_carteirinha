# Configuração MySQL - CondoTech Solutions

## 📋 Configuração do MySQL no PythonAnywhere

### **1. Criar Variáveis de Ambiente**

No console bash do PythonAnywhere, adicione ao arquivo `.bashrc`:

```bash
# Editar .bashrc
nano ~/.bashrc

# Adicionar no final do arquivo:
export MYSQL_DATABASE="barrientos\$default"
export MYSQL_USER="barrientos"
export MYSQL_PASSWORD="SUA_SENHA_MYSQL"
export MYSQL_HOST="barrientos.mysql.pythonanywhere-services.com"

# Recarregar configurações
source ~/.bashrc
```

### **2. Instalar Dependências**

```bash
cd aplicativo_carteirinha
pip3.10 install --user PyMySQL
```

### **3. Executar Configuração**

```bash
python3.10 configurar_condotech_mysql.py
```

### **4. Recarregar Web App**

1. Vá para **Web Apps** no dashboard
2. Clique em **"barrientos.pythonanywhere.com"**
3. Clique em **"Reload"**

## 🔧 Configurações do Banco

- **Host**: `barrientos.mysql.pythonanywhere-services.com`
- **Usuário**: `barrientos`
- **Banco**: `barrientos$default`
- **Senha**: (definida por você)

## ⚡ Vantagens do MySQL

- ✅ **Performance**: Muito mais rápido que SQLite
- ✅ **Concorrência**: Suporta múltiplos usuários
- ✅ **Escalabilidade**: Preparado para crescer
- ✅ **Confiabilidade**: Transações ACID
- ✅ **Backup**: Ferramentas profissionais

## 🔄 Migração de Dados

Se você tinha dados no SQLite, pode exportar:

```bash
# Exportar dados do SQLite (se necessário)
sqlite3 carteirinha_piscina.db ".dump" > backup_sqlite.sql

# Depois adaptar e importar no MySQL
```

## 🚀 Pronto!

Após a configuração, o sistema estará rodando com MySQL profissional! 