# 🔧 Ajustes Necessários para SaaS Multi-Tenant

## 🎯 Visão Geral
Transformar o sistema atual em um SaaS requer implementar **multi-tenancy** (múltiplos clientes isolados) e funcionalidades empresariais.

---

## 🏗️ PRIORIDADE ALTA - Multi-Tenancy

### 1. **Isolamento de Dados por Tenant**

#### **Problemas Atuais:**
- ✅ Existe `condominio_id` em algumas tabelas
- ❌ Nem todas as tabelas têm isolamento
- ❌ Consultas não filtram por tenant automaticamente

#### **Ajustes Necessários:**

```python
# 1. Garantir que TODAS as tabelas tenham tenant_id
class Morador(db.Model):
    # ... campos existentes ...
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)

class AnexoMorador(db.Model):
    # ... campos existentes ...
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)

class LogNotificacao(db.Model):
    # ... campos existentes ...
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)

# 2. Criar modelo Tenant
class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    subdominio = db.Column(db.String(50), unique=True, nullable=False)
    dominio_personalizado = db.Column(db.String(100), nullable=True)
    
    # Dados do cliente
    cnpj = db.Column(db.String(18), unique=True)
    email_responsavel = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20))
    
    # Plano e cobrança
    plano_id = db.Column(db.Integer, db.ForeignKey('planos.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='ativo')  # ativo, suspenso, cancelado
    
    # Limites do plano
    limite_moradores = db.Column(db.Integer, default=200)
    limite_usuarios = db.Column(db.Integer, default=1)
    
    # Configurações
    configuracoes = db.Column(db.JSON, default={})
    
    # Personalização
    logo_url = db.Column(db.String(255))
    cor_primaria = db.Column(db.String(7), default='#007bff')
    cor_secundaria = db.Column(db.String(7), default='#6c757d')
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    usuarios = db.relationship('Usuario', backref='tenant', lazy=True)
    moradores = db.relationship('Morador', backref='tenant', lazy=True)
```

### 2. **Middleware de Tenant**

```python
# app/middleware.py
from flask import g, request, abort
from app.models import Tenant

def get_current_tenant():
    """Identifica o tenant atual baseado no subdomínio"""
    host = request.headers.get('Host', '')
    
    # Exemplo: cliente1.sistema.com.br
    if '.' in host:
        subdominio = host.split('.')[0]
        tenant = Tenant.query.filter_by(subdominio=subdominio).first()
        
        if tenant and tenant.status == 'ativo':
            return tenant
    
    # Fallback para localhost ou IP
    return Tenant.query.filter_by(id=1).first()

@app.before_request
def load_tenant():
    """Carrega tenant atual em todas as requisições"""
    g.tenant = get_current_tenant()
    
    if not g.tenant:
        abort(404, "Tenant não encontrado")
```

### 3. **Query Scoping Automático**

```python
# app/models.py
from flask import g

class TenantMixin:
    """Mixin para adicionar funcionalidades de tenant"""
    
    @classmethod
    def query_for_tenant(cls, tenant_id=None):
        """Filtra automaticamente por tenant"""
        if not tenant_id:
            tenant_id = g.tenant.id if hasattr(g, 'tenant') else None
        
        return cls.query.filter_by(tenant_id=tenant_id)
    
    @classmethod
    def create_for_tenant(cls, **kwargs):
        """Cria registro para o tenant atual"""
        if hasattr(g, 'tenant'):
            kwargs['tenant_id'] = g.tenant.id
        return cls(**kwargs)

# Aplicar o mixin
class Morador(TenantMixin, db.Model):
    # ... resto do código ...
```

---

## 🔐 PRIORIDADE ALTA - Sistema de Autenticação

### **Problemas Atuais:**
- ✅ Sistema básico de usuários existe
- ❌ Não há controle de permissões granular
- ❌ Não há sistema de convites
- ❌ Não há recuperação de senha

### **Ajustes Necessários:**

```python
# 1. Melhorar modelo de Usuario
class Usuario(UserMixin, db.Model):
    # ... campos existentes ...
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Novos campos
    cargo = db.Column(db.String(100))
    permissoes = db.Column(db.JSON, default={})
    data_ultimo_acesso = db.Column(db.DateTime)
    tentativas_login = db.Column(db.Integer, default=0)
    conta_bloqueada = db.Column(db.Boolean, default=False)
    
    # Tokens
    token_recuperacao = db.Column(db.String(100), unique=True)
    token_recuperacao_exp = db.Column(db.DateTime)
    
    # Convites
    convidado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    data_convite = db.Column(db.DateTime)
    token_convite = db.Column(db.String(100), unique=True)
    
    def can(self, permission):
        """Verifica se usuário tem permissão específica"""
        return self.permissoes.get(permission, False)
    
    def is_admin_tenant(self):
        """Verifica se é admin do tenant"""
        return self.can('admin_tenant')

# 2. Sistema de Permissões
class Permissao:
    # Moradores
    CRIAR_MORADOR = 'criar_morador'
    EDITAR_MORADOR = 'editar_morador'
    EXCLUIR_MORADOR = 'excluir_morador'
    
    # Carteirinhas
    VALIDAR_CARTEIRINHA = 'validar_carteirinha'
    GERAR_CARTEIRINHA = 'gerar_carteirinha'
    
    # Relatórios
    VER_RELATORIOS = 'ver_relatorios'
    EXPORTAR_DADOS = 'exportar_dados'
    
    # Configurações
    CONFIGURAR_SISTEMA = 'configurar_sistema'
    GERENCIAR_USUARIOS = 'gerenciar_usuarios'
    
    # Admin
    ADMIN_TENANT = 'admin_tenant'
```

---

## 💳 PRIORIDADE ALTA - Sistema de Planos e Cobrança

### **Criar Sistema de Planos:**

```python
# app/models.py
class Plano(db.Model):
    __tablename__ = 'planos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco_mensal = db.Column(db.Numeric(10, 2), nullable=False)
    preco_anual = db.Column(db.Numeric(10, 2))
    
    # Limites
    limite_moradores = db.Column(db.Integer, default=200)
    limite_usuarios = db.Column(db.Integer, default=1)
    limite_anexos_mb = db.Column(db.Integer, default=1000)
    
    # Funcionalidades
    funcionalidades = db.Column(db.JSON, default={})
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    publico = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    tenants = db.relationship('Tenant', backref='plano', lazy=True)

class Cobranca(db.Model):
    __tablename__ = 'cobrancas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Dados da cobrança
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.String(255))
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, vencido, cancelado
    
    # Integração com gateway
    gateway_id = db.Column(db.String(100))  # ID no gateway de pagamento
    link_pagamento = db.Column(db.String(500))
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    tenant = db.relationship('Tenant', backref='cobrancas')
```

---

## 🏢 PRIORIDADE MÉDIA - Sistema de Onboarding

### **Fluxo de Cadastro de Novos Clientes:**

```python
# app/onboarding.py
class OnboardingService:
    @staticmethod
    def criar_novo_tenant(dados_cliente):
        """Cria novo tenant com dados iniciais"""
        
        # 1. Criar tenant
        tenant = Tenant(
            nome=dados_cliente['nome'],
            subdominio=dados_cliente['subdominio'],
            email_responsavel=dados_cliente['email'],
            telefone=dados_cliente['telefone'],
            cnpj=dados_cliente.get('cnpj'),
            plano_id=dados_cliente['plano_id'],
            data_inicio=datetime.now().date(),
            data_vencimento=datetime.now().date() + timedelta(days=30)
        )
        
        db.session.add(tenant)
        db.session.commit()
        
        # 2. Criar usuário administrador
        admin = Usuario(
            username=dados_cliente['email'],
            email=dados_cliente['email'],
            nome_completo=dados_cliente['nome_responsavel'],
            tipo_usuario='admin',
            tenant_id=tenant.id,
            permissoes={
                'admin_tenant': True,
                'criar_morador': True,
                'editar_morador': True,
                'validar_carteirinha': True,
                'ver_relatorios': True,
                'configurar_sistema': True,
                'gerenciar_usuarios': True
            }
        )
        admin.set_password(dados_cliente['senha'])
        
        db.session.add(admin)
        db.session.commit()
        
        # 3. Enviar email de boas-vindas
        OnboardingService.enviar_boas_vindas(tenant, admin)
        
        return tenant, admin
    
    @staticmethod
    def enviar_boas_vindas(tenant, admin):
        """Envia email de boas-vindas com instruções"""
        # Implementar envio de email
        pass
```

---

## 🔧 PRIORIDADE MÉDIA - Configurações por Tenant

### **Sistema de Configurações Flexível:**

```python
# app/models.py
class ConfiguracaoTenant(db.Model):
    __tablename__ = 'configuracoes_tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Configuração
    categoria = db.Column(db.String(50), nullable=False)
    chave = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Text)
    tipo = db.Column(db.String(20), default='texto')
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        db.Index('idx_tenant_config', 'tenant_id', 'categoria', 'chave'),
        db.UniqueConstraint('tenant_id', 'categoria', 'chave')
    )
    
    @staticmethod
    def get_valor(tenant_id, categoria, chave, default=None):
        """Obter configuração específica do tenant"""
        config = ConfiguracaoTenant.query.filter_by(
            tenant_id=tenant_id,
            categoria=categoria,
            chave=chave
        ).first()
        
        if config:
            if config.tipo == 'booleano':
                return config.valor.lower() in ('true', '1', 'sim')
            elif config.tipo == 'numero':
                return int(config.valor) if config.valor else default
            return config.valor
        return default
```

---

## 🌐 PRIORIDADE MÉDIA - API REST

### **API para Integrações:**

```python
# app/api/__init__.py
from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(api_bp)

# app/api/resources.py
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

class MoradorResource(Resource):
    @jwt_required()
    def get(self, id=None):
        """Listar moradores do tenant"""
        tenant_id = get_jwt_identity()['tenant_id']
        
        if id:
            morador = Morador.query.filter_by(
                id=id, tenant_id=tenant_id
            ).first_or_404()
            return morador.to_dict()
        
        moradores = Morador.query.filter_by(tenant_id=tenant_id).all()
        return [m.to_dict() for m in moradores]
    
    @jwt_required()
    def post(self):
        """Criar novo morador"""
        # Implementar criação via API
        pass

# Registrar recursos
api.add_resource(MoradorResource, '/moradores', '/moradores/<int:id>')
```

---

## 📊 PRIORIDADE BAIXA - Métricas e Monitoramento

### **Sistema de Métricas:**

```python
# app/models.py
class MetricaTenant(db.Model):
    __tablename__ = 'metricas_tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Métricas
    total_moradores = db.Column(db.Integer, default=0)
    total_usuarios = db.Column(db.Integer, default=0)
    carteirinhas_ativas = db.Column(db.Integer, default=0)
    carteirinhas_vencidas = db.Column(db.Integer, default=0)
    
    # Uso
    requests_ultimo_mes = db.Column(db.Integer, default=0)
    storage_usado_mb = db.Column(db.Integer, default=0)
    emails_enviados = db.Column(db.Integer, default=0)
    
    # Timestamps
    data_snapshot = db.Column(db.Date, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        db.Index('idx_tenant_data', 'tenant_id', 'data_snapshot'),
        db.UniqueConstraint('tenant_id', 'data_snapshot')
    )
```

---

## 🚀 Cronograma de Implementação

### **Sprint 1 (2 semanas) - Multi-Tenancy Básico**
- [ ] Criar modelo Tenant
- [ ] Adicionar tenant_id em todas as tabelas
- [ ] Implementar middleware de tenant
- [ ] Testar isolamento básico

### **Sprint 2 (2 semanas) - Sistema de Planos**
- [ ] Criar modelos Plano e Cobranca
- [ ] Implementar limitações por plano
- [ ] Interface de cadastro de clientes
- [ ] Sistema de onboarding

### **Sprint 3 (2 semanas) - Autenticação Avançada**
- [ ] Melhorar sistema de usuários
- [ ] Sistema de permissões
- [ ] Recuperação de senha
- [ ] Sistema de convites

### **Sprint 4 (2 semanas) - Configurações e API**
- [ ] Sistema de configurações por tenant
- [ ] API REST básica
- [ ] Interface de configurações
- [ ] Testes e ajustes

---

## 💡 Considerações Importantes

### **Migração de Dados:**
- Criar script para migrar dados existentes
- Definir tenant padrão para dados atuais
- Backup completo antes da migração

### **Testes:**
- Implementar testes unitários para multi-tenancy
- Testar isolamento de dados
- Testes de carga para múltiplos tenants

### **Segurança:**
- Validar isolamento de dados
- Implementar rate limiting
- Logs de auditoria por tenant

### **Performance:**
- Índices adequados nas tabelas
- Cache por tenant
- Otimização de queries

---

## 🎯 Próximos Passos Imediatos

1. **Definir modelo de dados definitivo**
2. **Implementar multi-tenancy básico**
3. **Criar interface de cadastro de clientes**
4. **Implementar sistema de planos**
5. **Testar com 2-3 tenants**
6. **Ajustar baseado no feedback**

**Estimativa:** 2-3 meses para versão SaaS funcional 