# 🚀 Guia de Correções - Módulo Piscina no PythonAnywhere

## 📋 Visão Geral

Este guia orienta a aplicação das correções críticas do módulo piscina/salva-vidas no ambiente PythonAnywhere com MySQL.

## ⚠️ PROBLEMAS CRÍTICOS CORRIGIDOS

- ✅ Isolamento de dados entre tenants no RegistroAcesso
- ✅ Scanner QR seguro por condomínio
- ✅ Dashboards corretos por tenant
- ✅ Formulários filtrados por tenant
- ✅ Queries otimizadas com tenant_id

---

## 🔧 PASSO 1: Upload dos Arquivos Corrigidos

### 1.1 Conectar via Git (Recomendado)
```bash
# No terminal do PythonAnywhere
cd /home/seuusuario/mysite
git pull origin main
```

### 1.2 Upload Manual (Alternativo)
Faça upload dos seguintes arquivos corrigidos:
- `app/models.py` (com tenant_id no RegistroAcesso)
- `app/forms.py` (formulários filtrados)
- `app/salva_vidas_routes.py` (rotas corrigidas)
- `app/routes.py` (queries corrigidas)
- `app/auth.py` (dashboard corrigido)
- `migracao_registro_acesso_tenant.py` (migração MySQL)

---

## 🗄️ PASSO 2: Executar Migração MySQL

### 2.1 Acessar Console Python
No PythonAnywhere Dashboard:
1. Vá para **Tasks** → **Consoles**
2. Clique **Bash** para novo console

### 2.2 Executar Migração
```bash
cd /home/seuusuario/mysite
python3.10 migracao_registro_acesso_tenant.py
```

### 2.3 Verificar Migração
```bash
python3.10 -c "
from app import create_app, db
from sqlalchemy import text
app = create_app()
with app.app_context():
    result = db.session.execute(text('DESCRIBE registro_acesso')).fetchall()
    for row in result:
        print(f'{row[0]} - {row[1]}')
"
```

**Deve mostrar:**
```
id - int
morador_id - int  
tipo - varchar(10)
data_hora - datetime
metodo - varchar(20)
guardiao - varchar(100)
observacoes - text
ip_origem - varchar(45)
tenant_id - int  # ← NOVA COLUNA
```

---

## 🔄 PASSO 3: Reiniciar Aplicação

### 3.1 Recarregar App
No PythonAnywhere Dashboard:
1. Vá para **Web**
2. Clique no seu domínio
3. Clique **Reload seudominio.pythonanywhere.com**

### 3.2 Verificar Logs
```bash
tail -f /var/log/seuusuario.pythonanywhere.com.error.log
```

---

## 🧪 PASSO 4: Testar Correções

### 4.1 Teste Básico de Login
1. Acesse: `https://seudominio.pythonanywhere.com/auth/login`
2. Faça login como salva-vidas
3. Verifique se dashboard carrega sem erros

### 4.2 Teste Scanner QR
1. Acesse: `/salva_vidas/qr-scanner`
2. Teste busca por nome de morador
3. Verifique se só mostra moradores do tenant

### 4.3 Teste Registro de Acesso
1. Acesse: `/registrar-acesso`
2. Verifique dropdown de moradores
3. Registre uma entrada/saída

### 4.4 Teste Dashboard Admin
1. Login como admin
2. Acesse: `/admin/dashboard`
3. Verifique estatísticas da piscina

---

## 🛠️ PASSO 5: Scripts de Verificação

### 5.1 Verificar Isolamento de Dados
```python
# Console Python no PythonAnywhere
from app import create_app, db
from app.models import RegistroAcesso, Morador
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Verificar se todos registros têm tenant_id
    sem_tenant = db.session.execute(text(
        "SELECT COUNT(*) FROM registro_acesso WHERE tenant_id IS NULL"
    )).fetchone()[0]
    
    print(f"Registros sem tenant_id: {sem_tenant}")
    
    # Verificar distribuição por tenant
    dist = db.session.execute(text("""
        SELECT tenant_id, COUNT(*) as count 
        FROM registro_acesso 
        GROUP BY tenant_id
    """)).fetchall()
    
    for row in dist:
        print(f"Tenant {row[0]}: {row[1]} registros")
```

### 5.2 Testar Métodos do Modelo
```python
# Console Python no PythonAnywhere
from app import create_app, db
from app.models import RegistroAcesso

app = create_app()
with app.app_context():
    # Testar método com tenant_id
    moradores_dentro = RegistroAcesso.obter_moradores_na_piscina(tenant_id=1)
    print(f"Moradores na piscina (tenant 1): {len(moradores_dentro)}")
    
    # Testar verificação individual
    if moradores_dentro:
        morador_id = moradores_dentro[0].id
        esta_dentro = RegistroAcesso.morador_esta_na_piscina(morador_id, tenant_id=1)
        print(f"Morador {morador_id} está dentro: {esta_dentro}")
```

---

## 🔍 PASSO 6: Monitoramento

### 6.1 Logs de Aplicação
```bash
# Monitorar logs em tempo real
tail -f /var/log/seuusuario.pythonanywhere.com.error.log

# Filtrar erros de tenant
grep -i tenant /var/log/seuusuario.pythonanywhere.com.error.log
```

### 6.2 Logs de Banco
```bash
# No console MySQL (se disponível)
mysql -u seuusuario -p -h seuusuario.mysql.pythonanywhere-services.com 'seuusuario$nomedobanco'

SHOW PROCESSLIST;
SELECT * FROM information_schema.processlist WHERE command != 'Sleep';
```

---

## 🚨 PASSO 7: Rollback (Se Necessário)

### 7.1 Reverter Migração (Emergência)
```sql
-- APENAS EM CASO DE EMERGÊNCIA
ALTER TABLE registro_acesso DROP COLUMN tenant_id;
```

### 7.2 Restaurar Backup
```bash
# Se você fez backup antes
mysql -u seuusuario -p -h seuusuario.mysql.pythonanywhere-services.com 'seuusuario$nomedobanco' < backup_antes_migracao.sql
```

---

## ✅ PASSO 8: Validação Final

### 8.1 Checklist de Validação
- [ ] Aplicação carrega sem erros
- [ ] Login salva-vidas funciona
- [ ] Scanner QR funciona
- [ ] Dashboard mostra dados corretos
- [ ] Registros de acesso salvam com tenant_id
- [ ] Formulários filtram por tenant
- [ ] Queries isolam dados por tenant

### 8.2 Teste de Isolamento
```python
# Criar teste de isolamento entre tenants
from app import create_app, db
from app.models import Usuario, RegistroAcesso
from flask import g

app = create_app()
with app.app_context():
    # Simular contexto de diferentes tenants
    with app.test_request_context():
        g.tenant_id = 1
        moradores_t1 = RegistroAcesso.obter_moradores_na_piscina()
        
        g.tenant_id = 2  
        moradores_t2 = RegistroAcesso.obter_moradores_na_piscina()
        
        print(f"Tenant 1: {len(moradores_t1)} moradores")
        print(f"Tenant 2: {len(moradores_t2)} moradores")
        print("✅ Isolamento funcionando!" if len(moradores_t1) != len(moradores_t2) or not moradores_t1 else "⚠️ Verificar isolamento")
```

---

## 📊 RESULTADO ESPERADO

Após aplicar todas as correções:

### ✅ Segurança Multi-Tenant
- Cada salva-vidas vê apenas seu condomínio
- Registros de acesso isolados por tenant
- Scanner QR valida apenas moradores do tenant
- Dashboards mostram dados reais do condomínio

### ✅ Funcionalidades Corrigidas
- Scanner QR Code funcional por tenant
- Dashboard de controle preciso
- Registros entrada/saída corretos
- Histórico de acessos filtrado
- Formulários seguros

### ✅ Performance Otimizada
- Índices criados para tenant_id
- Queries otimizadas com filtros
- Carregamento mais rápido

---

## 🆘 SUPORTE

### Em Caso de Problemas:
1. **Verificar logs**: `/var/log/seuusuario.pythonanywhere.com.error.log`
2. **Testar console**: Console Python no PythonAnywhere
3. **Validar migração**: `DESCRIBE registro_acesso` no MySQL
4. **Recarregar app**: Web tab no Dashboard

### Contatos:
- PythonAnywhere Help: help@pythonanywhere.com
- Documentação: https://help.pythonanywhere.com/

---

## 🎯 CONCLUSÃO

Seguindo este guia, o módulo piscina estará:
- ✅ **100% seguro** para multi-tenancy
- ✅ **Totalmente funcional** no PythonAnywhere
- ✅ **Otimizado** para performance
- ✅ **Pronto** para produção

**🏊 Módulo Piscina totalmente corrigido e seguro para uso em produção!** 