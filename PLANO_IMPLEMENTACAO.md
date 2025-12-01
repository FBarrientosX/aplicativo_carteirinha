# 🚀 Plano de Implementação - CondoTech Solutions

## 📋 DIRETIVA GLOBAL

**Arquitetura**: Multi-tenant com isolamento de dados por `tenant_id`  
**Prioridade**: Mobile-First / Responsiva (Desktop, Tablet, Mobile)  
**Segurança**: Permissões granulares por módulo e ação  
**Padrão**: Seguir especificações em `DOCUMENTACAO_ARQUITETURA_GERAL.md` e `WIREFRAMES_FLUXO_COMPLETO.md`

---

## FASE 0: FUNDAÇÃO E CORE DO SISTEMA 🛠️

**Objetivo**: Estabelecer arquitetura base, autenticação e interface administrativa

### 0.1 Back-end: Configuração da Arquitetura (Core)

#### 0.1.1 Estrutura de Projeto
**Arquivos a criar/modificar**:
```
app/
├── core/
│   ├── __init__.py
│   ├── auth.py          # Autenticação centralizada
│   ├── permissions.py   # Sistema de permissões
│   └── utils.py         # Utilitários compartilhados
├── modules/
│   ├── __init__.py
│   ├── piscina/
│   ├── reservas/
│   ├── acesso/
│   └── encomendas/
├── shared/
│   ├── components/      # Componentes reutilizáveis
│   └── helpers/        # Helpers compartilhados
└── templates/
    ├── base.html
    ├── base_sidebar.html
    └── components/      # Componentes Jinja2
```

**Especificações**:
- Cada módulo deve ter: `routes.py`, `models.py`, `forms.py`, `templates/`
- Usar Blueprints do Flask para isolamento
- Prefixo de URL por módulo: `/piscina/`, `/reservas/`, etc.

#### 0.1.2 Modelos de Dados Fundamentais

**Modelo: `Condominio`**
```python
# app/models.py ou app/core/models.py

class Condominio(db.Model):
    __tablename__ = 'condominio'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Dados básicos
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    endereco = db.Column(db.Text, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    
    # E-mails de configuração
    email_administracao = db.Column(db.String(120), nullable=False)
    email_portaria = db.Column(db.String(120), nullable=True)
    email_sindico = db.Column(db.String(120), nullable=True)
    
    # Documentos (JSON ou relacionamento)
    documentos = db.Column(db.JSON, default=[])  # URLs ou paths
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    unidades = db.relationship('Unidade', backref='condominio', lazy=True)
    moradores = db.relationship('Morador', backref='condominio', lazy=True)
```

**Modelo: `Unidade`**
```python
class Unidade(db.Model):
    __tablename__ = 'unidades'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), nullable=False)
    
    bloco = db.Column(db.String(10), nullable=False)
    apartamento = db.Column(db.String(10), nullable=False)
    
    # Metadados
    tipo = db.Column(db.String(20), default='apartamento')  # apartamento, cobertura, loja
    area_util = db.Column(db.Numeric(10, 2), nullable=True)  # m²
    vagas_garagem = db.Column(db.Integer, default=0)
    
    # Status
    ocupada = db.Column(db.Boolean, default=False)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice único por tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'bloco', 'apartamento', name='uq_unidade_tenant'),
    )
    
    def __repr__(self):
        return f'<Unidade {self.bloco}/{self.apartamento}>'
```

**Modelo: `Usuario` (Expandir existente)**
```python
# Expandir app/models.py - Usuario

class Usuario(UserMixin, db.Model):
    # ... campos existentes ...
    
    # NOVO: Relacionamento com Unidade (se for morador)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=True)
    unidade = db.relationship('Unidade', backref='usuarios')
    
    # NOVO: Tipo de usuário expandido
    tipo_usuario = db.Column(db.String(20), nullable=False)  
    # Valores: 'admin', 'sindico', 'morador', 'portaria', 'funcionario', 'salva_vidas'
    
    # NOVO: Status
    ativo = db.Column(db.Boolean, default=True)
    email_verificado = db.Column(db.Boolean, default=False)
    data_ultimo_acesso = db.Column(db.DateTime, nullable=True)
```

**Migração Alembic**:
```bash
flask db migrate -m "Criar modelos Condominio e Unidade"
flask db upgrade
```

#### 0.1.3 Rotas e Views - CRUD Básico

**Rotas: Condomínio**
```python
# app/routes.py ou app/core/routes.py

@bp.route('/admin/condominio', methods=['GET', 'POST'])
@login_required
@admin_required
def configurar_condominio():
    """Configuração do condomínio (apenas admin)"""
    condominio = Condominio.query.filter_by(tenant_id=g.tenant_id).first()
    
    form = CondominioForm(obj=condominio)
    
    if form.validate_on_submit():
        if condominio:
            # Atualizar
            form.populate_obj(condominio)
        else:
            # Criar
            condominio = Condominio(
                tenant_id=g.tenant_id,
                **form.data
            )
            db.session.add(condominio)
        
        db.session.commit()
        flash('Condomínio configurado com sucesso!', 'success')
        return redirect(url_for('main.configurar_condominio'))
    
    return render_template('admin/condominio.html', form=form, condominio=condominio)
```

**Rotas: Moradores (Expandir existente)**
- Verificar `app/routes.py` - já existe parcialmente
- Adicionar relacionamento com `Unidade`
- Adicionar filtros por bloco/apto

**Rotas: Funcionários**
```python
# app/routes.py

@bp.route('/admin/funcionarios')
@login_required
@admin_required
def listar_funcionarios():
    """Listar funcionários do condomínio"""
    funcionarios = Usuario.query.filter_by(
        tenant_id=g.tenant_id,
        tipo_usuario.in_(['portaria', 'funcionario', 'salva_vidas'])
    ).all()
    
    return render_template('admin/funcionarios.html', funcionarios=funcionarios)

@bp.route('/admin/funcionario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_funcionario():
    """Cadastrar novo funcionário"""
    form = FuncionarioForm()
    
    if form.validate_on_submit():
        funcionario = Usuario(
            tenant_id=g.tenant_id,
            tipo_usuario=form.tipo_usuario.data,
            nome_completo=form.nome_completo.data,
            email=form.email.data,
            username=form.username.data,
            ativo=True
        )
        funcionario.set_password(form.password.data)
        
        db.session.add(funcionario)
        db.session.commit()
        
        flash('Funcionário cadastrado com sucesso!', 'success')
        return redirect(url_for('main.listar_funcionarios'))
    
    return render_template('admin/funcionario_form.html', form=form)
```

#### 0.1.4 Segurança e Acesso

**Sistema de Permissões Granulares**
```python
# app/core/permissions.py

from functools import wraps
from flask import g, abort
from flask_login import current_user

# Permissões por módulo e ação
PERMISSIONS = {
    'piscina': {
        'view': ['admin', 'sindico', 'portaria', 'salva_vidas'],
        'create': ['admin', 'sindico', 'portaria', 'salva_vidas'],
        'edit': ['admin', 'sindico'],
        'delete': ['admin']
    },
    'reservas': {
        'view': ['admin', 'sindico', 'morador'],
        'create': ['admin', 'sindico', 'morador'],
        'edit': ['admin', 'sindico'],
        'delete': ['admin']
    },
    # ... outros módulos
}

def has_permission(module, action):
    """Verifica se usuário tem permissão"""
    if not current_user.is_authenticated:
        return False
    
    if current_user.tipo_usuario == 'admin':
        return True
    
    allowed_roles = PERMISSIONS.get(module, {}).get(action, [])
    return current_user.tipo_usuario in allowed_roles

def require_permission(module, action):
    """Decorator para verificar permissão"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(module, action):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**Fluxo de Autenticação (Melhorar existente)**
```python
# app/auth.py - Melhorar existente

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login com rate limiting"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Rate limiting (implementar com flask-limiter)
        user = Usuario.query.filter_by(
            username=form.username.data,
            tenant_id=g.tenant_id  # Multi-tenant
        ).first()
        
        if user and user.check_password(form.password.data):
            if not user.ativo:
                flash('Conta desativada. Contate o administrador.', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            
            # Atualizar último acesso
            user.data_ultimo_acesso = datetime.utcnow()
            db.session.commit()
            
            # Redirecionar por tipo
            next_page = request.args.get('next')
            if not next_page:
                if user.is_admin():
                    next_page = url_for('main.index')
                elif user.is_salva_vidas():
                    next_page = url_for('piscina.dashboard')
                else:
                    next_page = url_for('main.index')
            
            return redirect(next_page)
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('auth/login.html', form=form)
```

### 0.2 Front-end: Design System e Layout Base

#### 0.2.1 Design System Setup

**Arquivo: `app/static/css/design-system.css`**
```css
:root {
    /* Cores Primárias */
    --color-primary: #3498db;
    --color-primary-dark: #2980b9;
    --color-secondary: #2c3e50;
    --color-secondary-light: #34495e;
    
    /* Cores de Status */
    --color-success: #28a745;
    --color-warning: #ffc107;
    --color-danger: #dc3545;
    --color-info: #17a2b8;
    
    /* Cores por Módulo */
    --color-piscina: #007bff;
    --color-reservas: #007bff;
    --color-acesso: #ffc107;
    --color-manutencao: #28a745;
    --color-encomendas: #17a2b8;
    
    /* Espaçamento */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    
    /* Tipografia */
    --font-family-base: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    --font-size-base: 1rem;
    --font-size-sm: 0.875rem;
    --font-size-lg: 1.125rem;
    --font-weight-normal: 400;
    --font-weight-bold: 600;
    
    /* Breakpoints */
    --breakpoint-sm: 576px;
    --breakpoint-md: 768px;
    --breakpoint-lg: 992px;
    --breakpoint-xl: 1200px;
}

/* Mobile First */
@media (max-width: 767.98px) {
    :root {
        --font-size-base: 0.9375rem;
    }
}
```

**Integração Bootstrap 5 + Font Awesome 6**
```html
<!-- app/templates/base.html -->
<head>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- Design System -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/design-system.css') }}">
    
    <!-- Estilos Customizados -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
```

#### 0.2.2 Layout Principal

**Arquivo: `app/templates/base_sidebar.html` (Melhorar existente)**

**Estrutura de 3 Colunas**:
```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <!-- Meta tags, CSS, etc. -->
</head>
<body class="sidebar-layout">
    <!-- HEADER SUPERIOR FIXO -->
    <header class="top-header">
        <div class="header-content">
            <div class="header-left">
                <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle sidebar">
                    <i class="fas fa-bars"></i>
                </button>
                <div class="header-title">
                    <i class="fas fa-building me-2"></i>
                    <span>CondoTech Solutions</span>
                </div>
            </div>
            
            <div class="header-center">
                <!-- Busca Global -->
                <div class="search-container">
                    <i class="fas fa-search"></i>
                    <input type="text" 
                           id="globalSearch" 
                           placeholder="Pesquisar..." 
                           class="search-input"
                           aria-label="Busca global">
                </div>
            </div>
            
            <div class="header-right">
                <!-- Notificações -->
                <button class="header-btn" title="Notificações" aria-label="Notificações">
                    <i class="fas fa-bell"></i>
                    <span class="notification-badge">3</span>
                </button>
                
                <!-- Perfil do Usuário -->
                <div class="user-profile dropdown">
                    <button class="dropdown-toggle" data-bs-toggle="dropdown">
                        <img src="..." alt="Perfil" class="profile-img">
                        <span class="user-name">{{ current_user.nome_completo }}</span>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="{{ url_for('main.perfil') }}">Perfil</a></li>
                        <li><a class="dropdown-item" href="{{ url_for('main.configuracoes') }}">Configurações</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}">Sair</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </header>

    <div class="main-container">
        <!-- SIDEBAR LATERAL FIXA -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-content">
                {% block sidebar_nav %}{% endblock %}
            </div>
        </aside>

        <!-- ÁREA DE CONTEÚDO PRINCIPAL -->
        <main class="main-content">
            <!-- Breadcrumbs -->
            {% block breadcrumbs %}{% endblock %}
            
            <!-- Flash Messages -->
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="container-fluid mt-3">
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}

            <!-- Conteúdo -->
            {% block content %}{% endblock %}
        </main>
    </div>

    <!-- Footer -->
    <footer class="main-footer">
        <div class="container-fluid">
            <p class="mb-0">
                <strong>CondoTech Solutions</strong> - © 2024
            </p>
        </div>
    </footer>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

#### 0.2.3 Componentes de Navegação

**Breadcrumbs Component**
```html
<!-- app/templates/components/breadcrumbs.html -->
{% macro render_breadcrumbs(items) %}
<nav aria-label="breadcrumb" class="breadcrumb-nav">
    <ol class="breadcrumb">
        <li class="breadcrumb-item">
            <a href="{{ url_for('main.index') }}">
                <i class="fas fa-home"></i> Home
            </a>
        </li>
        {% for item in items %}
            {% if loop.last %}
                <li class="breadcrumb-item active" aria-current="page">
                    {{ item.text }}
                </li>
            {% else %}
                <li class="breadcrumb-item">
                    <a href="{{ item.url }}">{{ item.text }}</a>
                </li>
            {% endif %}
        {% endfor %}
    </ol>
</nav>
{% endmacro %}
```

**Uso em Templates**:
```html
{% extends "base_sidebar.html" %}
{% from 'components/breadcrumbs.html' import render_breadcrumbs %}

{% block breadcrumbs %}
{{ render_breadcrumbs([
    {'text': 'Piscina', 'url': url_for('piscina.index')},
    {'text': 'Moradores', 'url': url_for('piscina.listar_moradores')},
    {'text': 'Detalhes', 'url': '#'}
]) }}
{% endblock %}
```

**Sidebar Navigation Component**
```html
<!-- app/templates/navigation/sidebar_nav.html -->
{% macro render_sidebar_nav(active_module=None, active_item=None) %}
<nav class="sidebar-nav">
    <ul class="nav flex-column">
        <li class="nav-item">
            <a class="nav-link {% if not active_module %}active{% endif %}" 
               href="{{ url_for('main.index') }}">
                <i class="fas fa-home"></i>
                <span>Home</span>
            </a>
        </li>
        
        <!-- Módulo Piscina -->
        <li class="nav-item">
            <a class="nav-link {% if active_module == 'piscina' %}active{% endif %}" 
               href="{{ url_for('piscina.dashboard') }}">
                <i class="fas fa-swimming-pool"></i>
                <span>Piscina</span>
            </a>
            {% if active_module == 'piscina' %}
            <ul class="nav flex-column submenu">
                <li><a href="{{ url_for('piscina.dashboard') }}">Dashboard</a></li>
                <li><a href="{{ url_for('piscina.registrar_acesso') }}">Registrar Acesso</a></li>
                <li><a href="{{ url_for('piscina.listar_moradores') }}">Moradores</a></li>
                <li><a href="{{ url_for('piscina.listar_salva_vidas') }}">Salva-vidas</a></li>
                <li><a href="{{ url_for('piscina.listar_ocorrencias') }}">Ocorrências</a></li>
            </ul>
            {% endif %}
        </li>
        
        <!-- Outros módulos... -->
    </ul>
</nav>
{% endmacro %}
```

---

## FASE 1: MVP DE GESTÃO E LAZER 🏊📅

### 1.1 Módulo Controle de Piscina (Implementação Completa)

#### 1.1.1 Modelos de Dados

**Modelo: `CarteirinhaPiscina`**
```python
# app/modules/piscina/models.py

class CarteirinhaPiscina(db.Model):
    __tablename__ = 'carteirinhas_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    
    # Validade
    data_emissao = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    data_validade = db.Column(db.Date, nullable=False)
    aprovada = db.Column(db.Boolean, default=False)
    ativa = db.Column(db.Boolean, default=True)
    
    # QR Code
    qr_code = db.Column(db.String(500), nullable=False, unique=True)
    qr_code_image = db.Column(db.String(500), nullable=True)  # Path da imagem
    
    # Metadados
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='carteirinhas_piscina')
    
    def gerar_qr_code(self):
        """Gera QR Code único para a carteirinha"""
        import qrcode
        from io import BytesIO
        import base64
        
        # Dados do QR Code
        data = f"PISCINA:{self.tenant_id}:{self.morador_id}:{self.id}"
        
        # Gerar QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salvar imagem
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Salvar arquivo
        filename = f"carteirinha_{self.id}_{self.morador_id}.png"
        filepath = os.path.join('static', 'uploads', 'carteirinhas', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(buffer.getvalue())
        
        self.qr_code = data
        self.qr_code_image = filepath
        
        return filepath
    
    @property
    def esta_valida(self):
        """Verifica se carteirinha está válida"""
        hoje = datetime.now().date()
        return self.ativa and self.aprovada and self.data_validade >= hoje
```

**Modelo: `RegistroAcessoPiscina`**
```python
class RegistroAcessoPiscina(db.Model):
    __tablename__ = 'registros_acesso_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    carteirinha_id = db.Column(db.Integer, db.ForeignKey('carteirinhas_piscina.id'), nullable=True)
    salva_vidas_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Tipo de registro
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Método de registro
    metodo = db.Column(db.String(20), nullable=False)  # 'qr_code', 'manual', 'barcode'
    
    # Tempo de permanência (calculado na saída)
    tempo_permanencia_minutos = db.Column(db.Integer, nullable=True)
    
    # Metadados
    observacoes = db.Column(db.Text, nullable=True)
    ip_origem = db.Column(db.String(45), nullable=True)
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='registros_piscina')
    carteirinha = db.relationship('CarteirinhaPiscina', backref='registros')
    salva_vidas = db.relationship('Usuario', backref='registros_piscina')
    
    @staticmethod
    def calcular_tempo_permanencia(morador_id, entrada_id, saida_id):
        """Calcula tempo de permanência entre entrada e saída"""
        entrada = RegistroAcessoPiscina.query.get(entrada_id)
        saida = RegistroAcessoPiscina.query.get(saida_id)
        
        if entrada and saida and entrada.tipo == 'entrada' and saida.tipo == 'saida':
            diferenca = saida.timestamp - entrada.timestamp
            minutos = int(diferenca.total_seconds() / 60)
            
            saida.tempo_permanencia_minutos = minutos
            db.session.commit()
            
            return minutos
        return None
    
    @staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id):
        """Verifica se morador está atualmente na piscina"""
        ultimo_registro = RegistroAcessoPiscina.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id
        ).order_by(RegistroAcessoPiscina.timestamp.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada'
```

**Modelo: `OcorrenciaPiscina`**
```python
class OcorrenciaPiscina(db.Model):
    __tablename__ = 'ocorrencias_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    salva_vidas_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=True)
    
    # Tipo e severidade
    tipo = db.Column(db.String(50), nullable=False)  # 'acidente', 'incidente', 'advertencia', 'outro'
    severidade = db.Column(db.String(20), nullable=False)  # 'baixa', 'media', 'alta', 'critica'
    
    # Descrição
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    
    # Fotos (JSON com paths)
    fotos = db.Column(db.JSON, default=[])
    
    # Status
    status = db.Column(db.String(20), default='aberta')  # 'aberta', 'resolvida', 'arquivada'
    
    # Timestamps
    data_ocorrencia = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_resolucao = db.Column(db.DateTime, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    salva_vidas = db.relationship('Usuario', backref='ocorrencias_piscina')
    morador = db.relationship('Morador', backref='ocorrencias_piscina')
```

**Modelo: `PlantaoSalvaVidas`**
```python
class PlantaoSalvaVidas(db.Model):
    __tablename__ = 'plantoes_salva_vidas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    salva_vidas_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Horários
    data_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='ativo')  # 'ativo', 'finalizado'
    
    # Metadados
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    salva_vidas = db.relationship('Usuario', backref='plantoes')
    
    @staticmethod
    def obter_plantao_ativo(tenant_id):
        """Retorna plantão ativo do tenant (apenas um por vez)"""
        return PlantaoSalvaVidas.query.filter_by(
            tenant_id=tenant_id,
            status='ativo'
        ).first()
    
    def finalizar(self):
        """Finaliza o plantão"""
        self.data_fim = datetime.utcnow()
        self.status = 'finalizado'
        db.session.commit()
```

#### 1.1.2 Lógica de Acesso (Portaria/Tablet)

**Rota: Registrar Acesso (Mobile-First)**
```python
# app/modules/piscina/routes.py

@piscina_bp.route('/registrar-acesso', methods=['GET', 'POST'])
@login_required
@require_permission('piscina', 'create')
def registrar_acesso():
    """Registro de acesso otimizado para tablet"""
    form = RegistroAcessoForm()
    
    if form.validate_on_submit():
        morador_id = form.morador_id.data
        tipo = form.tipo.data
        
        # Verificar carteirinha válida
        morador = Morador.query.get_or_404(morador_id)
        carteirinha = CarteirinhaPiscina.query.filter_by(
            morador_id=morador_id,
            tenant_id=g.tenant_id,
            ativa=True
        ).order_by(CarteirinhaPiscina.data_criacao.desc()).first()
        
        if not carteirinha or not carteirinha.esta_valida:
            flash('Carteirinha inválida ou vencida!', 'danger')
            return render_template('piscina/registrar_acesso.html', form=form)
        
        # Verificar se já está dentro (para entrada) ou fora (para saída)
        esta_dentro = RegistroAcessoPiscina.morador_esta_na_piscina(morador_id, g.tenant_id)
        
        if tipo == 'entrada' and esta_dentro:
            flash(f'{morador.nome_completo} já está na piscina!', 'warning')
            return render_template('piscina/registrar_acesso.html', form=form)
        
        if tipo == 'saida' and not esta_dentro:
            flash(f'{morador.nome_completo} não está na piscina!', 'warning')
            return render_template('piscina/registrar_acesso.html', form=form)
        
        # Criar registro
        registro = RegistroAcessoPiscina(
            tenant_id=g.tenant_id,
            morador_id=morador_id,
            carteirinha_id=carteirinha.id,
            salva_vidas_id=current_user.id if current_user.is_salva_vidas() else None,
            tipo=tipo,
            metodo=form.metodo.data,
            observacoes=form.observacoes.data,
            ip_origem=request.remote_addr
        )
        
        # Se for saída, calcular tempo de permanência
        if tipo == 'saida':
            entrada = RegistroAcessoPiscina.query.filter_by(
                morador_id=morador_id,
                tipo='entrada',
                tenant_id=g.tenant_id
            ).order_by(RegistroAcessoPiscina.timestamp.desc()).first()
            
            if entrada:
                RegistroAcessoPiscina.calcular_tempo_permanencia(
                    morador_id, entrada.id, registro.id
                )
        
        db.session.add(registro)
        db.session.commit()
        
        flash(f'✅ {morador.nome_completo} {tipo} piscina!', 'success')
        return redirect(url_for('piscina.registrar_acesso'))
    
    return render_template('piscina/registrar_acesso.html', form=form)
```

**Template: Registrar Acesso (Mobile-First)**
```html
<!-- app/templates/piscina/registrar_acesso.html -->
{% extends "base_sidebar.html" %}
{% from 'components/breadcrumbs.html' import render_breadcrumbs %}

{% block breadcrumbs %}
{{ render_breadcrumbs([
    {'text': 'Piscina', 'url': url_for('piscina.dashboard')},
    {'text': 'Registrar Acesso', 'url': '#'}
]) }}
{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row">
        <div class="col-12 col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header">
                    <h4 class="mb-0">
                        <i class="fas fa-swimming-pool"></i> Registrar Acesso
                    </h4>
                </div>
                <div class="card-body">
                    <!-- Busca por QR Code ou Manual -->
                    <div class="row mb-4">
                        <div class="col-12 col-md-6">
                            <button class="btn btn-primary btn-lg w-100" id="scanQRBtn">
                                <i class="fas fa-qrcode"></i> Escanear QR Code
                            </button>
                        </div>
                        <div class="col-12 col-md-6">
                            <button class="btn btn-secondary btn-lg w-100" id="searchManualBtn">
                                <i class="fas fa-search"></i> Buscar Manualmente
                            </button>
                        </div>
                    </div>
                    
                    <!-- Formulário -->
                    <form method="POST" id="registroForm">
                        {{ form.hidden_tag() }}
                        
                        <!-- Campo de busca (aparece ao clicar em Buscar Manualmente) -->
                        <div class="mb-3" id="searchField" style="display: none;">
                            {{ form.morador_id.label }}
                            <input type="text" 
                                   class="form-control" 
                                   id="moradorSearch"
                                   placeholder="Digite nome ou apartamento...">
                            <div id="moradorResults" class="list-group mt-2"></div>
                        </div>
                        
                        <!-- Tipo de registro -->
                        <div class="mb-3">
                            {{ form.tipo.label }}
                            <div class="btn-group w-100" role="group">
                                <input type="radio" class="btn-check" name="tipo" id="tipoEntrada" value="entrada" checked>
                                <label class="btn btn-outline-success" for="tipoEntrada">
                                    <i class="fas fa-sign-in-alt"></i> Entrada
                                </label>
                                
                                <input type="radio" class="btn-check" name="tipo" id="tipoSaida" value="saida">
                                <label class="btn btn-outline-danger" for="tipoSaida">
                                    <i class="fas fa-sign-out-alt"></i> Saída
                                </label>
                            </div>
                        </div>
                        
                        <!-- Observações -->
                        <div class="mb-3">
                            {{ form.observacoes.label }}
                            {{ form.observacoes(class="form-control", rows="3") }}
                        </div>
                        
                        <button type="submit" class="btn btn-primary btn-lg w-100">
                            <i class="fas fa-check"></i> Confirmar Registro
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Script para busca e QR Code -->
<script>
// Implementar busca em tempo real
// Implementar scanner QR Code (usar biblioteca como html5-qrcode)
</script>
{% endblock %}
```

#### 1.1.3 Dashboard e Métricas (Tempo Real)

**Rota: Dashboard**
```python
@piscina_bp.route('/dashboard')
@login_required
@require_permission('piscina', 'view')
def dashboard():
    """Dashboard do módulo Piscina"""
    tenant_id = g.tenant_id
    
    # Contador de pessoas atuais
    moradores_na_piscina = RegistroAcessoPiscina.query.filter_by(
        tenant_id=tenant_id,
        tipo='entrada'
    ).join(
        RegistroAcessoPiscina.morador
    ).filter(
        ~exists().where(
            and_(
                RegistroAcessoPiscina.morador_id == Morador.id,
                RegistroAcessoPiscina.tipo == 'saida',
                RegistroAcessoPiscina.timestamp > RegistroAcessoPiscina.timestamp
            )
        )
    ).count()
    
    # Tempo médio de permanência (últimas 24h)
    registros_24h = RegistroAcessoPiscina.query.filter(
        RegistroAcessoPiscina.tenant_id == tenant_id,
        RegistroAcessoPiscina.tipo == 'saida',
        RegistroAcessoPiscina.timestamp >= datetime.utcnow() - timedelta(hours=24),
        RegistroAcessoPiscina.tempo_permanencia_minutos.isnot(None)
    ).all()
    
    tempo_medio = 0
    if registros_24h:
        tempo_medio = sum(r.tempo_permanencia_minutos for r in registros_24h) / len(registros_24h)
    
    # Salva-vidas de plantão
    plantao = PlantaoSalvaVidas.obter_plantao_ativo(tenant_id)
    
    # Dados para gráfico (pessoas por hora - hoje)
    dados_grafico = obter_dados_grafico_por_hora(tenant_id)
    
    return render_template('piscina/dashboard.html',
                         moradores_na_piscina=moradores_na_piscina,
                         tempo_medio_minutos=int(tempo_medio),
                         plantao=plantao,
                         dados_grafico=dados_grafico)
```

**Função: Dados do Gráfico**
```python
def obter_dados_grafico_por_hora(tenant_id, data=None):
    """Retorna dados para gráfico de pessoas por hora"""
    if not data:
        data = datetime.now().date()
    
    # Agrupar por hora
    registros = db.session.query(
        func.extract('hour', RegistroAcessoPiscina.timestamp).label('hora'),
        RegistroAcessoPiscina.tipo,
        func.count(RegistroAcessoPiscina.id).label('quantidade')
    ).filter(
        RegistroAcessoPiscina.tenant_id == tenant_id,
        func.date(RegistroAcessoPiscina.timestamp) == data
    ).group_by(
        'hora', 'tipo'
    ).all()
    
    # Processar dados
    horas = list(range(24))
    dados = {h: 0 for h in horas}
    
    for registro in registros:
        hora = int(registro.hora)
        if registro.tipo == 'entrada':
            dados[hora] += registro.quantidade
        else:
            dados[hora] -= registro.quantidade
    
    # Calcular acumulado
    acumulado = 0
    resultado = []
    for h in horas:
        acumulado += dados[h]
        resultado.append({'hora': h, 'pessoas': max(0, acumulado)})
    
    return resultado
```

**Template: Dashboard com Gráfico**
```html
<!-- app/templates/piscina/dashboard.html -->
{% extends "base_sidebar.html" %}

{% block content %}
<div class="container-fluid mt-4">
    <!-- Indicadores -->
    <div class="row mb-4">
        <div class="col-12 col-md-4 mb-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title">👥 Na Piscina</h5>
                    <h2 class="display-4" id="contadorPessoas">{{ moradores_na_piscina }}</h2>
                    <p class="text-muted">pessoas</p>
                </div>
            </div>
        </div>
        
        <div class="col-12 col-md-4 mb-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title">⏱️ Tempo Médio</h5>
                    <h2 class="display-4">{{ tempo_medio_minutos // 60 }}h {{ tempo_medio_minutos % 60 }}min</h2>
                    <p class="text-muted">últimas 24h</p>
                </div>
            </div>
        </div>
        
        <div class="col-12 col-md-4 mb-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title">🏊 Salva-vidas</h5>
                    {% if plantao %}
                        <h4>{{ plantao.salva_vidas.nome_completo }}</h4>
                        <p class="text-muted">Desde {{ plantao.data_inicio.strftime('%H:%M') }}</p>
                    {% else %}
                        <p class="text-muted">Nenhum plantão ativo</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Gráfico -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>📊 Pessoas na Piscina por Hora (Hoje)</h5>
                </div>
                <div class="card-body">
                    <canvas id="graficoPessoasPorHora"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// Dados do gráfico
const dadosGrafico = {{ dados_grafico | tojson }};

// Criar gráfico
const ctx = document.getElementById('graficoPessoasPorHora').getContext('2d');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: dadosGrafico.map(d => d.hora + ':00'),
        datasets: [{
            label: 'Pessoas na Piscina',
            data: dadosGrafico.map(d => d.pessoas),
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

// Atualizar contador em tempo real (a cada 10s)
setInterval(() => {
    fetch('{{ url_for("piscina.api_contador_pessoas") }}')
        .then(response => response.json())
        .then(data => {
            document.getElementById('contadorPessoas').textContent = data.contador;
        });
}, 10000);
</script>
{% endblock %}
```

#### 1.1.4 Sistema de Plantão e Ocorrências

**Rota: Iniciar/Finalizar Plantão**
```python
@piscina_bp.route('/plantao/iniciar', methods=['POST'])
@login_required
@require_permission('piscina', 'create')
def iniciar_plantao():
    """Inicia plantão do salva-vidas"""
    if not current_user.is_salva_vidas():
        abort(403)
    
    # Verificar se já existe plantão ativo
    plantao_ativo = PlantaoSalvaVidas.obter_plantao_ativo(g.tenant_id)
    if plantao_ativo:
        flash('Já existe um plantão ativo!', 'warning')
        return redirect(url_for('piscina.dashboard'))
    
    # Criar novo plantão
    plantao = PlantaoSalvaVidas(
        tenant_id=g.tenant_id,
        salva_vidas_id=current_user.id,
        status='ativo'
    )
    db.session.add(plantao)
    db.session.commit()
    
    flash('Plantão iniciado com sucesso!', 'success')
    return redirect(url_for('piscina.dashboard'))

@piscina_bp.route('/plantao/finalizar', methods=['POST'])
@login_required
def finalizar_plantao():
    """Finaliza plantão do salva-vidas"""
    plantao = PlantaoSalvaVidas.obter_plantao_ativo(g.tenant_id)
    if not plantao or plantao.salva_vidas_id != current_user.id:
        abort(403)
    
    plantao.finalizar()
    flash('Plantão finalizado com sucesso!', 'success')
    return redirect(url_for('piscina.dashboard'))
```

**Rota: Registrar Ocorrência**
```python
@piscina_bp.route('/ocorrencia/nova', methods=['GET', 'POST'])
@login_required
@require_permission('piscina', 'create')
def nova_ocorrencia():
    """Registrar nova ocorrência (apenas salva-vidas)"""
    if not current_user.is_salva_vidas():
        abort(403)
    
    form = OcorrenciaPiscinaForm()
    
    if form.validate_on_submit():
        ocorrencia = OcorrenciaPiscina(
            tenant_id=g.tenant_id,
            salva_vidas_id=current_user.id,
            morador_id=form.morador_id.data if form.morador_id.data else None,
            tipo=form.tipo.data,
            severidade=form.severidade.data,
            titulo=form.titulo.data,
            descricao=form.descricao.data,
            fotos=form.fotos.data if form.fotos.data else []
        )
        
        db.session.add(ocorrencia)
        db.session.commit()
        
        flash('Ocorrência registrada com sucesso!', 'success')
        return redirect(url_for('piscina.listar_ocorrencias'))
    
    return render_template('piscina/ocorrencia_form.html', form=form)
```

---

## FASE 2: SEGURANÇA E LOGÍSTICA 🛡️📦

### 2.1 Módulo Controle de Encomendas

**Modelo e Rotas** (já existe parcialmente - verificar e melhorar)

**Melhorias Sugeridas**:
- Notificações push (WebSockets)
- Integração com APIs de rastreamento
- QR Code para retirada
- Foto da encomenda

### 2.2 Módulo Controle de Acesso

**Modelo e Rotas** (já existe parcialmente - verificar e melhorar)

**Melhorias Sugeridas**:
- Interfone virtual (WebSockets)
- Pré-cadastro de visitantes
- Integração com sistema de portaria
- Histórico de acessos

---

## FASE 3: ENGAJAMENTO E CONSOLIDAÇÃO 🗣️📁

### 3.1 Módulo Comunicação

**Chat Interno** (Novo)
- WebSockets para comunicação em tempo real
- Sistema de mutar/bloquear moradores
- Chat com administração sempre disponível

### 3.2 Módulo Administrativo

**Gestão de Documentos** (Novo)
- Upload de documentos categorizados
- Permissões por tipo de documento
- Versionamento de documentos

---

## CHECKLIST DE IMPLEMENTAÇÃO

### Fase 0 - Fundação
- [ ] Estrutura de diretórios
- [ ] Modelos Condominio e Unidade
- [ ] CRUD de Condomínio
- [ ] CRUD de Funcionários
- [ ] Sistema de permissões
- [ ] Layout base com sidebar
- [ ] Breadcrumbs component
- [ ] Design system CSS

### Fase 1 - Piscina
- [ ] Modelos (Carteirinha, Registro, Ocorrência, Plantão)
- [ ] Registro de acesso (QR Code + Manual)
- [ ] Dashboard com indicadores
- [ ] Gráfico de pessoas por hora
- [ ] Sistema de plantão
- [ ] Registro de ocorrências
- [ ] Atualização em tempo real

### Fase 2 - Reservas
- [ ] Modelos (Espaço, Reserva)
- [ ] Calendário de disponibilidade
- [ ] Formulário de reserva
- [ ] Aprovação de reservas
- [ ] Notificações por email

### Fase 3 - Encomendas e Acesso
- [ ] Melhorias no módulo Encomendas
- [ ] Melhorias no módulo Acesso
- [ ] Notificações push
- [ ] Interfone virtual

---

**Versão**: 1.0  
**Data**: 2024  
**Status**: Diretiva de Implementação para CoPiloto de Código

