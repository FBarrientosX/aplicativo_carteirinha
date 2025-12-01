# 🔧 Correções para PythonAnywhere

## Problemas Identificados

1. **`no such column: registro_acesso.tenant_id`** - A coluna `tenant_id` não existe no banco de dados de produção
2. **`TypeError: unsupported operand type(s) for -: 'str' and 'str'`** - Erro ao calcular duração de permanência
3. **`ImportError: cannot import name '_app_ctx_stack'`** - Código antigo usando API removida do Flask

## Soluções Aplicadas

### 1. Modelo `RegistroAcesso` Resiliente

O modelo agora verifica se a coluna `tenant_id` existe antes de usá-la:
- Método `_has_tenant_id_column()` verifica a existência da coluna
- Queries usam SQL direto quando a coluna não existe
- Métodos `morador_esta_na_piscina()` e `obter_moradores_na_piscina()` são compatíveis

### 2. Migração para Adicionar `tenant_id`

Arquivo: `migrations/versions/fix_registro_acesso_tenant_id.py`

Esta migração:
- Verifica se a coluna `tenant_id` existe
- Adiciona a coluna se não existir
- Atualiza valores NULL para `tenant_id = 1`
- Cria índice e foreign key

### 3. Correções em `app/routes.py`

- Todas as verificações de `has_tenant_id` agora usam `RegistroAcesso._has_tenant_id_column()`
- Cálculo de duração de permanência corrigido para converter strings para datetime
- Criação de registros funciona com ou sem `tenant_id`

## Passos para Aplicar no PythonAnywhere

### 1. Fazer Upload dos Arquivos Atualizados

```bash
# Arquivos que precisam ser atualizados:
- app/models.py
- app/routes.py
- migrations/versions/fix_registro_acesso_tenant_id.py
```

### 2. Aplicar a Migração

No console do PythonAnywhere:

```bash
cd ~/aplicativo_carteirinha
source venv/bin/activate  # ou o nome do seu ambiente virtual
export FLASK_APP=run.py
flask db upgrade
```

### 3. Reiniciar a Aplicação

No painel do PythonAnywhere:
- Vá em "Web" → "Reload"

### 4. Verificar Logs

Após reiniciar, verifique os logs em:
- "Web" → "Error log"

## Verificação

Após aplicar as correções, teste:

1. Acesse `/acesso-piscina` - não deve mais dar erro de `tenant_id`
2. Registre uma entrada e saída - deve calcular a duração corretamente
3. Acesse `/acesso-piscina/historico` - deve funcionar sem erros

## Notas Importantes

- A migração é **idempotente** - pode ser executada múltiplas vezes sem problemas
- O código funciona **com ou sem** a coluna `tenant_id` - compatibilidade total
- Se a migração falhar, o código continuará funcionando usando SQL direto

## Rollback (se necessário)

Se precisar reverter:

```bash
flask db downgrade -1
```

Mas isso não é necessário, pois o código funciona sem a coluna.

