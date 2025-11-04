# Solução para Erro de Migrations

## Problema
O erro `Table 'moradores' already exists` ocorre porque:
- As tabelas antigas já existem no banco de dados
- O Alembic não está rastreando quais migrations já foram aplicadas
- O Alembic tenta executar migrations antigas que criam tabelas já existentes

## Solução: Marcar migrations antigas como aplicadas

### Opção 1: Marcar a última migration aplicada (Recomendado)

No PythonAnywhere, execute:

```bash
cd ~/aplicativo_carteirinha
flask db stamp 54fe7b36cfb8
```

Isso marca a migration `54fe7b36cfb8` (última migration antes das novas) como já aplicada.

Depois, execute:

```bash
flask db upgrade
```

Isso aplicará apenas as novas migrations (`a1b2c3d4e5f6` e `b2c3d4e5f6a7`).

### Opção 2: Marcar a migration inicial

Se a migration `54fe7b36cfb8` não existir na tabela `alembic_version`, marque a migration inicial:

```bash
cd ~/aplicativo_carteirinha
flask db stamp 5f7958945e30
flask db upgrade
```

### Opção 3: Verificar e corrigir manualmente

1. Verifique qual migration está registrada no banco:
   ```bash
   sqlite3 ~/aplicativo_carteirinha/instance/app.db
   SELECT * FROM alembic_version;
   .quit
   ```

2. Se a tabela `alembic_version` não existir ou estiver vazia, crie/atualize:
   ```bash
   flask db stamp head
   ```

3. Depois execute:
   ```bash
   flask db upgrade
   ```

## Ordem das Migrations

1. `5f7958945e30` - Migração inicial (já aplicada - tabelas já existem)
2. `024ec9e42b13` - Migração inicial adicional
3. `c22ad5b7299f` - Adicionar relacionamento condominio_id
4. `54fe7b36cfb8` - Adicionar campo tipo_anexo
5. `a1b2c3d4e5f6` - Criar tabela visitantes (NOVA)
6. `b2c3d4e5f6a7` - Criar tabelas reservas (NOVA)

## Verificar se funcionou

Após aplicar as migrations, verifique se as tabelas foram criadas:

```bash
sqlite3 ~/aplicativo_carteirinha/instance/app.db
.tables
```

Você deve ver:
- `visitantes`
- `espacos_comuns`
- `reservas_espacos`
- `lista_convidados`

## Se ainda der erro

Se ainda houver erro, você pode aplicar apenas as novas migrations usando o script SQL manual:

```bash
sqlite3 ~/aplicativo_carteirinha/instance/app.db < scripts/criar_tabelas_reservas.sql
```

E depois marcar a migration como aplicada:

```bash
flask db stamp b2c3d4e5f6a7
```

