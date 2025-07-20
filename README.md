# 🏢 CondoTech Solutions

**Sistema SaaS multi-tenant para gestão completa de condomínios**

Plataforma modular com **Controle de Piscina** e **Manutenção & Chamados** rodando no MySQL.

## ✨ Funcionalidades

### 🏊 **Módulo Controle de Piscina**
- **Cadastro de Moradores**: Registro completo com dados pessoais, bloco, apartamento
- **Controle de Titularidade**: Diferenciação entre titulares e dependentes
- **Gestão de Carteirinhas**: Validação, renovação e controle de vencimento
- **Dashboard Analítico**: Gráficos e estatísticas em tempo real
- **Sistema de Notificações**: Emails automáticos 30 dias antes do vencimento
- **Upload de Anexos**: Armazenamento de documentos por morador
- **Filtros e Busca**: Pesquisa avançada de moradores
- **QR Code Scanner**: Validação de acesso via câmera

### 🔧 **Módulo Manutenção & Chamados**
- **Gestão de Chamados**: Abertura, acompanhamento e fechamento
- **Categorias Predefinidas**: 
  - ⚡ Elétrica (4h resposta - Prioridade Alta)
  - 💧 Hidráulica (2h resposta - Prioridade Alta)  
  - ❄️ Ar Condicionado (24h resposta - Prioridade Média)
  - 🎨 Pintura (72h resposta - Prioridade Baixa)
  - 🧹 Limpeza (12h resposta - Prioridade Média)
  - 🛡️ Segurança (1h resposta - Prioridade Urgente)
- **SLA por Categoria**: Tempo de resposta automatizado
- **Dashboard de Chamados**: Acompanhamento em tempo real
- **Histórico Completo**: Rastreamento de todas as ações

### 🏢 **Arquitetura Multi-Tenant SaaS**
- **Isolamento de Dados**: Cada condomínio com dados próprios
- **Módulos Flexíveis**: Ativação por tenant individual
- **Planos de Assinatura**: Sistema de cobrança e limites
- **Usuários e Permissões**: Controle granular de acesso
- **Configurações por Tenant**: Personalização completa

## 🎯 Status das Carteirinhas

- **Regular**: Carteirinha válida por mais de 30 dias
- **A Vencer**: Vence em 30 dias ou menos
- **Vencida**: Carteirinha expirada
- **Sem Carteirinha**: Morador sem carteirinha cadastrada

## 🚀 Tecnologias

- **Backend**: Python 3.10+ com Flask 3.1.1
- **Banco de Dados**: MySQL Professional (PythonAnywhere)
- **ORM**: SQLAlchemy 2.x com suporte multi-tenant
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Gráficos**: Plotly.js para dashboards
- **Email**: Flask-Mail com templates HTML
- **Tarefas**: APScheduler para notificações automáticas
- **Formulários**: WTForms com validação
- **Autenticação**: Flask-Login + Werkzeug

## 📦 Configuração

### Pré-requisitos
- Python 3.10+
- MySQL 8.0+ (PythonAnywhere)
- pip (gerenciador de pacotes Python)

### 1. Clone o repositório
```bash
git clone https://github.com/FBarrientosX/aplicativo_carteirinha.git
cd aplicativo_carteirinha
```

### 2. Instale as dependências
```bash
pip3.10 install --user -r requirements.txt
```

### 3. Configure o MySQL
```bash
# Configure as variáveis de ambiente no .bashrc
export MYSQL_DATABASE="barrientos$default"
export MYSQL_USER="barrientos"
export MYSQL_PASSWORD="SUA_SENHA_MYSQL"
export MYSQL_HOST="barrientos.mysql.pythonanywhere-services.com"

# Recarregue o ambiente
source ~/.bashrc
```

### 4. Execute a configuração
```bash
python3.10 configurar_condotech_mysql.py
```

### 5. Acesse o sistema
- **URL**: https://barrientos.pythonanywhere.com
- **Login**: admin
- **Senha**: admin123

## 🗂️ Estrutura do Projeto

```
aplicativo_carteirinha/
├── app/                          # Aplicação Flask
│   ├── __init__.py              # Factory pattern e configuração
│   ├── models.py                # Modelos SQLAlchemy multi-tenant
│   ├── routes.py                # Rotas principais (piscina)
│   ├── manutencao_routes.py     # Rotas do módulo manutenção
│   ├── salva_vidas_routes.py    # Rotas salva-vidas
│   ├── auth.py                  # Autenticação e middleware
│   ├── forms.py                 # Formulários WTForms
│   ├── email_service.py         # Serviço de email
│   ├── carteirinha_service.py   # Serviço de carteirinhas
│   ├── static/                  # CSS, JS, uploads
│   └── templates/               # Templates Jinja2
├── configurar_condotech_mysql.py # Script de configuração MySQL
├── requirements.txt             # Dependências Python
├── run.py                      # Ponto de entrada da aplicação
└── README.md                   # Este arquivo
```

## 🔐 Sistema Multi-Tenant

### Isolamento de Dados
- Cada condomínio possui `tenant_id` único
- Dados completamente isolados por tenant
- Middleware automático de filtragem

### Módulos por Tenant
- Ativação independente de módulos
- Cobrança baseada em módulos ativos
- Configuração flexível por cliente

### Planos de Assinatura
- **Básico**: Módulos Piscina + Manutenção
- **Limite**: 10 usuários, 1000 moradores
- **Funcionalidades**: JSON configurável

## 📊 Dashboard e Relatórios

### Módulo Piscina
- Gráfico de status das carteirinhas
- Análise por bloco e apartamento
- Histórico de validações
- Relatórios de vencimento

### Módulo Manutenção
- Chamados por categoria
- Tempo médio de resolução
- SLA por tipo de serviço
- Dashboard em tempo real

## 📧 Sistema de Notificações

### Automáticas
- **30 dias antes**: Aviso de vencimento
- **No vencimento**: Notificação urgente
- **Chamados**: Updates por email

### Templates
- HTML responsivo
- Personalização por tenant
- Logos e cores customizáveis

## 🔧 Módulo Manutenção & Chamados

### Categorias Predefinidas
```python
Elétrica     → 4h  → Alta     → ⚡
Hidráulica   → 2h  → Alta     → 💧  
Ar Condic.   → 24h → Média    → ❄️
Pintura      → 72h → Baixa    → 🎨
Limpeza      → 12h → Média    → 🧹
Segurança    → 1h  → Urgente  → 🛡️
```

### Fluxo de Chamados
1. **Abertura**: Morador/Admin cria chamado
2. **Triagem**: Categoria e prioridade automática
3. **Atribuição**: Técnico responsável
4. **Execução**: Acompanhamento em tempo real
5. **Fechamento**: Validação e histórico

## 🚀 Deploy em Produção

### PythonAnywhere
1. **Git**: Push para repositório
2. **Pull**: `git pull origin main` no servidor
3. **Configuração**: Execute o script MySQL
4. **Reload**: Recarregue a aplicação web

### Ambiente
- **Python**: 3.10
- **MySQL**: Profissional PythonAnywhere
- **WSGI**: Gunicorn/uWSGI
- **SSL**: Certificado automático

## 🛡️ Segurança

- **Autenticação**: Flask-Login com hash Werkzeug
- **Autorização**: Middleware multi-tenant
- **SQL Injection**: SQLAlchemy ORM protegido
- **XSS**: Templates Jinja2 com escape automático
- **CSRF**: WTForms com tokens CSRF

## 📈 Performance

### MySQL Otimizado
- **Índices**: tenant_id, foreign keys
- **Pool de Conexões**: SQLAlchemy pool
- **Cache**: Query cache ativado

### Frontend
- **CDN**: Bootstrap, jQuery via CDN
- **Minificação**: CSS/JS otimizados
- **Lazy Loading**: Imagens e componentes

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Email**: admin@condotech.com
- **Issues**: GitHub Issues
- **Documentação**: README.md

---

**CondoTech Solutions** - Transformando a gestão de condomínios com tecnologia! 🚀
