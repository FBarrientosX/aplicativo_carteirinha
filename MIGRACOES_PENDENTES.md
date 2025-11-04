# Migrações Pendentes - Instruções para Aplicar

## ⚠️ IMPORTANTE: Tabelas Pendentes

As seguintes tabelas precisam ser criadas no banco de dados:

1. **visitantes** - Tabela para controle de visitantes
2. **espacos_comuns** - Tabela para espaços comuns do condomínio
3. **reservas_espacos** - Tabela para reservas de espaços
4. **lista_convidados** - Tabela para lista de convidados das reservas

## 📋 Opção 1: Usando Flask-Migrate (Recomendado)

No servidor PythonAnywhere, execute:

```bash
cd ~/aplicativo_carteirinha
flask db upgrade
```

Ou, se o comando `flask` não estiver disponível:

```bash
cd ~/aplicativo_carteirinha
python -m flask db upgrade
```

## 📋 Opção 2: Script SQL Manual (Alternativa)

Se a migration não funcionar, você pode executar o script SQL manualmente:

1. Acesse o console do PythonAnywhere
2. Execute o script SQL:

```bash
cd ~/aplicativo_carteirinha
sqlite3 instance/app.db < scripts/criar_tabelas_reservas.sql
```

**Nota:** Se o banco de dados não estiver em `instance/app.db`, ajuste o caminho conforme necessário.

## 📋 Opção 3: Executar SQL Manualmente no PythonAnywhere

Se você tiver acesso ao console SQLite do PythonAnywhere:

1. Abra o console SQLite:
   ```bash
   sqlite3 ~/aplicativo_carteirinha/instance/app.db
   ```

2. Execute os comandos do arquivo `scripts/criar_tabelas_reservas.sql`

3. Saia do SQLite:
   ```sql
   .quit
   ```

## ✅ Verificar se as Tabelas Foram Criadas

Após executar a migration ou script SQL, você pode verificar se as tabelas foram criadas:

```bash
sqlite3 ~/aplicativo_carteirinha/instance/app.db
.tables
```

Você deve ver as seguintes tabelas na lista:
- `visitantes`
- `espacos_comuns`
- `reservas_espacos`
- `lista_convidados`

## 🔄 Migrations Pendentes

As seguintes migrations precisam ser aplicadas:

1. `a1b2c3d4e5f6_criar_tabela_visitantes.py` - Cria tabela `visitantes`
2. `b2c3d4e5f6a7_criar_tabelas_reservas.py` - Cria tabelas `espacos_comuns`, `reservas_espacos` e `lista_convidados`

## 📝 Notas

- As migrations estão na pasta `migrations/versions/`
- O script SQL alternativo está em `scripts/criar_tabelas_reservas.sql`
- Após aplicar as migrations, reinicie a aplicação no PythonAnywhere

