# 🏊‍♂️ Sistema de Controle de Carteirinhas da Piscina

Sistema web para controle da validade das carteirinhas de acesso à piscina de condomínios, desenvolvido em Python Flask.

## 📋 Funcionalidades

### ✅ Implementadas
- **Cadastro de Moradores**: Registro completo com dados pessoais, bloco, apartamento
- **Controle de Titularidade**: Diferenciação entre titulares e dependentes
- **Gestão de Carteirinhas**: Validação, renovação e controle de vencimento
- **Dashboard Analítico**: Gráficos e estatísticas em tempo real
- **Sistema de Notificações**: Emails automáticos 30 dias antes do vencimento e no vencimento
- **Upload de Anexos**: Armazenamento de documentos por morador
- **Filtros e Busca**: Pesquisa avançada de moradores
- **Relatórios**: Análises por bloco, período e status

### 🎯 Categorias de Status
- **Regular**: Carteirinha válida por mais de 30 dias
- **A Vencer**: Vence em 30 dias ou menos
- **Vencida**: Carteirinha expirada
- **Sem Carteirinha**: Morador sem carteirinha cadastrada

## 🚀 Tecnologias Utilizadas

- **Backend**: Python 3.8+ com Flask
- **Banco de Dados**: MySQL
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Gráficos**: Plotly.js
- **Email**: Flask-Mail
- **Tarefas Automáticas**: APScheduler
- **Upload de Arquivos**: Werkzeug
- **Formulários**: WTForms

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- MySQL 5.7+ ou MariaDB 10.3+
- pip (gerenciador de pacotes Python)

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd aplicativo_carteirinha
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS  
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados
Crie um banco de dados MySQL:
```sql
CREATE DATABASE carteirinha_piscina;
CREATE USER 'carteirinha_user'@'localhost' IDENTIFIED BY 'sua_senha';
GRANT ALL PRIVILEGES ON carteirinha_piscina.* TO 'carteirinha_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações
```

Exemplo de configuração `.env`:
```env
SECRET_KEY=sua_chave_secreta_muito_longa_e_segura
DEBUG=True

# Banco de dados
MYSQL_HOST=localhost
MYSQL_USER=carteirinha_user
MYSQL_PASSWORD=sua_senha
MYSQL_DB=carteirinha_piscina

# Email (opcional - para notificações)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_DEFAULT_SENDER=seu_email@gmail.com
```

### 6. Inicialize o banco de dados
```bash
python init_db.py
```

### 7. Execute a aplicação
```bash
python run.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 🎯 Como Usar

### Dashboard Principal
- Acesse a página inicial para ver estatísticas gerais
- Visualize gráficos de distribuição de status
- Use ações rápidas para navegação

### Cadastro de Moradores
1. Clique em "Novo Morador" no menu
2. Preencha os dados obrigatórios:
   - Nome completo
   - Bloco e apartamento
   - Email e celular
3. Marque "É Titular" se for o responsável pelo apartamento
4. Para dependentes, informe o email do titular
5. Opcionalmente, adicione observações e anexos

### Validação de Carteirinhas
1. Acesse a lista de moradores
2. Clique no ícone de validação (✓) ao lado do morador
3. Escolha o período de validade (6 ou 12 meses)
4. Adicione observações se necessário
5. Confirme a validação

### Sistema de Notificações
- **Automático**: Notificações são enviadas diariamente às 9h
- **Manual**: Use o botão "Enviar Notificações" no dashboard
- **30 dias antes**: Aviso de vencimento próximo
- **No vencimento**: Notificação de carteirinha vencida

### Filtros e Busca
- Use os filtros por bloco e status
- Busque por nome do morador
- Navegue pelas páginas de resultados

## 📊 Relatórios e Analytics

### Dashboard
- Total de moradores cadastrados
- Distribuição por status (Regular, A Vencer, Vencida, Sem Carteirinha)
- Gráfico de pizza interativo
- Percentuais e métricas

### Página de Relatórios
- Moradores por bloco
- Histórico de validações
- Gráficos de tendências

## 🔧 Configurações Avançadas

### Personalização de Emails
Edite os templates em `app/templates/email/`:
- `notificacao_30_dias.html/txt`: Aviso de 30 dias
- `notificacao_vencimento.html/txt`: Carteirinha vencida
- `boas_vindas.html/txt`: Boas-vindas a novos moradores

### Configuração de Tarefas Automáticas
Por padrão, as notificações são enviadas às 9h diariamente. Para alterar:

```python
# Em app/routes.py, altere:
@scheduler.task('cron', id='verificar_notificacoes', hour=9, minute=0)
```

### Upload de Arquivos
- Tamanho máximo: 16MB
- Tipos permitidos: PDF, DOC, DOCX, PNG, JPG, JPEG, GIF, TXT
- Armazenamento: `app/static/uploads/morador_{id}/`

## 🐛 Solução de Problemas

### Erro de Conexão com Banco
```bash
# Verifique se o MySQL está rodando
mysql -u root -p

# Teste a conexão
mysql -h localhost -u carteirinha_user -p carteirinha_piscina
```

### Erro de Importação
```bash
# Reinstale as dependências
pip install --force-reinstall -r requirements.txt
```

### Problemas com Email
```bash
# Para Gmail, use senhas de aplicativo
# Configurações > Segurança > Senhas de app
```

### Erro de Permissões de Arquivo
```bash
# Linux/macOS
chmod -R 755 app/static/uploads/
```

## 📝 Estrutura do Projeto

```
aplicativo_carteirinha/
├── app/
│   ├── __init__.py          # Inicialização da aplicação
│   ├── config.py            # Configurações
│   ├── models.py            # Modelos do banco de dados
│   ├── routes.py            # Rotas da aplicação
│   ├── forms.py             # Formulários WTF
│   ├── email_service.py     # Serviço de emails
│   ├── static/              # Arquivos estáticos
│   │   ├── css/
│   │   └── uploads/         # Upload de arquivos
│   └── templates/           # Templates HTML
│       ├── base.html
│       ├── index.html
│       ├── moradores/
│       └── email/
├── migrations/              # Migrações do banco
├── requirements.txt         # Dependências
├── run.py                  # Executar aplicação
├── init_db.py             # Inicializar banco
├── .env.example           # Exemplo de configuração
└── README.md              # Este arquivo
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a seção de "Solução de Problemas"
2. Consulte os logs da aplicação
3. Abra uma issue no repositório

## 🔄 Atualizações Futuras

### Próximas Funcionalidades
- [ ] Integração com WhatsApp Business API
- [ ] Exportação de relatórios em PDF/Excel
- [ ] Sistema de backup automático
- [ ] API REST para integração
- [ ] App mobile (Flutter/React Native)
- [ ] Sistema de pagamentos online
- [ ] Controle de acesso por QR Code
- [ ] Notificações push no navegador

### Melhorias Planejadas
- [ ] Interface mais responsiva
- [ ] Temas personalizáveis
- [ ] Relatórios mais detalhados
- [ ] Sistema de logs avançado
- [ ] Testes automatizados
- [ ] Documentação da API
