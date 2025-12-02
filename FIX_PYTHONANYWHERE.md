# 🔧 Correções para PythonAnywhere

## Problemas Identificados

1. **`no such column: registro_acesso.tenant_id`** - A coluna `tenant_id` não existe no banco de dados de produção
2. **`no such column: usuarios.email_verificado`** - Colunas opcionais não existem na tabela `usuarios`
3. **`TypeError: unsupported operand type(s) for -: 'str' and 'str'`** - Erro ao calcular duração de permanência
4. **`ImportError: cannot import name '_app_ctx_stack'`** - Código antigo usando API removida do Flask

## Soluções Aplicadas

### 1. Modelo `RegistroAcesso` Resiliente

O modelo agora verifica se a coluna `tenant_id` existe antes de usá-la:
- Método `_has_tenant_id_column()` verifica a existência da coluna
- Queries usam SQL direto quando a coluna não existe
- Métodos `morador_esta_na_piscina()` e `obter_moradores_na_piscina()` são compatíveis

### 2. Migrações para Adicionar Colunas Faltantes

**Arquivo 1:** `migrations/versions/fix_registro_acesso_tenant_id.py`
- Verifica se a coluna `tenant_id` existe em `registro_acesso`
- Adiciona a coluna se não existir
- Atualiza valores NULL para `tenant_id = 1`
- Cria índice e foreign key

**Arquivo 2:** `migrations/versions/fix_usuarios_campos.py`
- Verifica se as colunas opcionais existem em `usuarios`
- Adiciona `email_verificado`, `data_ultimo_acesso`, `unidade_id`, `permissoes` se não existirem
- Atualiza valores NULL com defaults apropriados

**Arquivo 3:** `migrations/versions/fix_all_missing_columns.py`
- Verifica e adiciona colunas faltantes em múltiplas tabelas:
  - `condominio`: `tenant_id`, `email_portaria`, `email_sindico`, `documentos`, `data_atualizacao`
  - `unidades`: `tenant_id`
  - `moradores`: `tenant_id`
  - `anexos_moradores`: `tenant_id`
  - `log_notificacoes`: `tenant_id`

### 3. Correções em `app/routes.py`

- Todas as verificações de `has_tenant_id` agora usam `RegistroAcesso._has_tenant_id_column()`
- Cálculo de duração de permanência corrigido para converter strings para datetime
- Criação de registros funciona com ou sem `tenant_id`

### 4. Correções em `app/models.py`

- Modelo `Usuario` agora tem colunas opcionais com `nullable=True` para compatibilidade
- Colunas `email_verificado`, `data_ultimo_acesso`, `unidade_id`, `permissoes` são opcionais
- Modelo `Condominio` agora tem colunas opcionais: `tenant_id`, `email_portaria`, `email_sindico`, `documentos`, `data_atualizacao`
- Modelo `Unidade` agora tem `tenant_id` como `nullable=True` para compatibilidade
- Todos os modelos com `tenant_id` agora têm `nullable=True` para compatibilidade

### 5. Correções em `app/core/routes.py`

- Queries de `Condominio` agora verificam se `tenant_id` existe antes de usar
- Queries de `Usuario` agora verificam se `tenant_id` existe antes de usar
- Criação de registros funciona com ou sem `tenant_id`

## Passos para Aplicar no PythonAnywhere

### 1. Fazer Upload dos Arquivos Atualizados

```bash
# Arquivos que precisam ser atualizados:
- app/models.py
- app/routes.py
- app/core/routes.py
- migrations/versions/fix_registro_acesso_tenant_id.py
- migrations/versions/fix_usuarios_campos.py
- migrations/versions/fix_all_missing_columns.py
```

### 2. Aplicar as Migrações

No console do PythonAnywhere:

```bash
cd ~/aplicativo_carteirinha
source venv/bin/activate  # ou o nome do seu ambiente virtual
export FLASK_APP=run.py
flask db upgrade
```

**IMPORTANTE:** As migrações são idempotentes e podem ser executadas múltiplas vezes sem problemas.

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

