# Novos modelos para SaaS Multi-Tenant
# Este arquivo contém os modelos que devem ser adicionados ao models.py existente

from datetime import datetime, timedelta
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import g

class Tenant(db.Model):
    """Modelo para clientes do SaaS"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    subdominio = db.Column(db.String(50), unique=True, nullable=False)
    dominio_personalizado = db.Column(db.String(100), nullable=True)
    
    # Dados do cliente
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    email_responsavel = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    
    # Plano e cobrança
    plano_id = db.Column(db.Integer, db.ForeignKey('planos.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='ativo')  # ativo, suspenso, cancelado
    
    # Configurações
    configuracoes = db.Column(db.JSON, default={})
    
    # Personalização
    logo_url = db.Column(db.String(255), nullable=True)
    cor_primaria = db.Column(db.String(7), default='#007bff')
    cor_secundaria = db.Column(db.String(7), default='#6c757d')
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    usuarios = db.relationship('Usuario', backref='tenant', lazy=True)
    cobrancas = db.relationship('Cobranca', backref='tenant', lazy=True)
    
    def __repr__(self):
        return f'<Tenant {self.nome}>'
    
    @property
    def plano_atual(self):
        """Retorna o plano atual do tenant"""
        return Plano.query.get(self.plano_id)
    
    @property
    def esta_vencido(self):
        """Verifica se o tenant está vencido"""
        return datetime.now().date() > self.data_vencimento
    
    @property
    def dias_para_vencer(self):
        """Dias para vencer o plano"""
        return (self.data_vencimento - datetime.now().date()).days
    
    def pode_adicionar_morador(self):
        """Verifica se pode adicionar mais moradores"""
        total_moradores = Morador.query.filter_by(tenant_id=self.id).count()
        return total_moradores < self.plano_atual.limite_moradores
    
    def pode_adicionar_usuario(self):
        """Verifica se pode adicionar mais usuários"""
        total_usuarios = Usuario.query.filter_by(tenant_id=self.id).count()
        return total_usuarios < self.plano_atual.limite_usuarios
    
    def get_url_sistema(self):
        """Retorna URL para acessar o sistema"""
        if self.dominio_personalizado:
            return f"https://{self.dominio_personalizado}"
        return f"https://{self.subdominio}.sistema.com.br"

class Plano(db.Model):
    """Planos de assinatura"""
    __tablename__ = 'planos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco_mensal = db.Column(db.Numeric(10, 2), nullable=False)
    preco_anual = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Limites
    limite_moradores = db.Column(db.Integer, default=200)
    limite_usuarios = db.Column(db.Integer, default=1)
    limite_anexos_mb = db.Column(db.Integer, default=1000)
    
    # Funcionalidades (JSON)
    funcionalidades = db.Column(db.JSON, default={})
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    publico = db.Column(db.Boolean, default=True)
    ordem = db.Column(db.Integer, default=0)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    tenants = db.relationship('Tenant', backref='plano', lazy=True)
    
    def __repr__(self):
        return f'<Plano {self.nome}>'
    
    @property
    def preco_anual_com_desconto(self):
        """Preço anual com 10% de desconto"""
        if self.preco_anual:
            return self.preco_anual
        return self.preco_mensal * 12 * 0.9
    
    def tem_funcionalidade(self, funcionalidade):
        """Verifica se o plano tem uma funcionalidade específica"""
        return self.funcionalidades.get(funcionalidade, False)

class Cobranca(db.Model):
    """Cobranças dos tenants"""
    __tablename__ = 'cobrancas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Dados da cobrança
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, vencido, cancelado
    
    # Integração com gateway
    gateway_id = db.Column(db.String(100), nullable=True)
    link_pagamento = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Cobranca {self.tenant.nome} - R$ {self.valor}>'
    
    @property
    def esta_vencida(self):
        """Verifica se a cobrança está vencida"""
        return datetime.now().date() > self.data_vencimento and self.status == 'pendente'
    
    def marcar_como_paga(self):
        """Marca cobrança como paga"""
        self.status = 'pago'
        self.data_pagamento = datetime.now().date()
        
        # Extender vencimento do tenant
        if self.tenant.data_vencimento < datetime.now().date():
            self.tenant.data_vencimento = datetime.now().date() + timedelta(days=30)
        else:
            self.tenant.data_vencimento = self.tenant.data_vencimento + timedelta(days=30)
        
        db.session.commit()

class ConfiguracaoTenant(db.Model):
    """Configurações específicas por tenant"""
    __tablename__ = 'configuracoes_tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Configuração
    categoria = db.Column(db.String(50), nullable=False)
    chave = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), default='texto')  # texto, numero, booleano, email, senha
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        db.Index('idx_tenant_config', 'tenant_id', 'categoria', 'chave'),
        db.UniqueConstraint('tenant_id', 'categoria', 'chave', name='uq_tenant_config')
    )
    
    def __repr__(self):
        return f'<ConfiguracaoTenant {self.tenant_id}:{self.categoria}:{self.chave}>'
    
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
                return config.valor.lower() in ('true', '1', 'sim', 'yes')
            elif config.tipo == 'numero':
                try:
                    return int(config.valor) if config.valor else default
                except ValueError:
                    return default
            return config.valor
        return default
    
    @staticmethod
    def set_valor(tenant_id, categoria, chave, valor, tipo='texto'):
        """Definir configuração específica do tenant"""
        config = ConfiguracaoTenant.query.filter_by(
            tenant_id=tenant_id,
            categoria=categoria,
            chave=chave
        ).first()
        
        if config:
            config.valor = str(valor)
            config.tipo = tipo
            config.data_atualizacao = datetime.utcnow()
        else:
            config = ConfiguracaoTenant(
                tenant_id=tenant_id,
                categoria=categoria,
                chave=chave,
                valor=str(valor),
                tipo=tipo
            )
            db.session.add(config)
        
        db.session.commit()
        return config

class TenantMixin:
    """Mixin para adicionar funcionalidades de tenant aos modelos"""
    
    @classmethod
    def query_for_tenant(cls, tenant_id=None):
        """Filtra automaticamente por tenant"""
        if not tenant_id:
            tenant_id = g.tenant.id if hasattr(g, 'tenant') else None
        
        if not tenant_id:
            raise ValueError("Tenant ID não encontrado")
        
        return cls.query.filter_by(tenant_id=tenant_id)
    
    @classmethod
    def create_for_tenant(cls, **kwargs):
        """Cria registro para o tenant atual"""
        if hasattr(g, 'tenant') and g.tenant:
            kwargs['tenant_id'] = g.tenant.id
        elif 'tenant_id' not in kwargs:
            raise ValueError("Tenant ID obrigatório")
        
        return cls(**kwargs)
    
    def save(self):
        """Salva o registro no banco"""
        db.session.add(self)
        db.session.commit()
        return self

class MetricaTenant(db.Model):
    """Métricas e estatísticas por tenant"""
    __tablename__ = 'metricas_tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Métricas básicas
    total_moradores = db.Column(db.Integer, default=0)
    total_usuarios = db.Column(db.Integer, default=0)
    carteirinhas_ativas = db.Column(db.Integer, default=0)
    carteirinhas_vencidas = db.Column(db.Integer, default=0)
    
    # Uso do sistema
    requests_ultimo_mes = db.Column(db.Integer, default=0)
    storage_usado_mb = db.Column(db.Integer, default=0)
    emails_enviados = db.Column(db.Integer, default=0)
    
    # Timestamps
    data_snapshot = db.Column(db.Date, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    tenant = db.relationship('Tenant', backref='metricas')
    
    # Índices
    __table_args__ = (
        db.Index('idx_tenant_data', 'tenant_id', 'data_snapshot'),
        db.UniqueConstraint('tenant_id', 'data_snapshot', name='uq_tenant_snapshot')
    )
    
    def __repr__(self):
        return f'<MetricaTenant {self.tenant.nome} - {self.data_snapshot}>'
    
    @staticmethod
    def gerar_snapshot_hoje(tenant_id):
        """Gera snapshot das métricas para hoje"""
        hoje = datetime.now().date()
        
        # Verificar se já existe snapshot para hoje
        existing = MetricaTenant.query.filter_by(
            tenant_id=tenant_id,
            data_snapshot=hoje
        ).first()
        
        if existing:
            return existing
        
        # Calcular métricas
        total_moradores = Morador.query.filter_by(tenant_id=tenant_id).count()
        total_usuarios = Usuario.query.filter_by(tenant_id=tenant_id).count()
        
        # Criar snapshot
        snapshot = MetricaTenant(
            tenant_id=tenant_id,
            total_moradores=total_moradores,
            total_usuarios=total_usuarios,
            data_snapshot=hoje
        )
        
        db.session.add(snapshot)
        db.session.commit()
        
        return snapshot

# Exemplo de como modificar o modelo Morador existente
class MoradorSaaS(TenantMixin, db.Model):
    """Exemplo de como o modelo Morador deve ser modificado"""
    __tablename__ = 'moradores_saas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Todos os campos existentes do Morador
    nome_completo = db.Column(db.String(200), nullable=False)
    bloco = db.Column(db.String(10), nullable=False)
    apartamento = db.Column(db.String(10), nullable=False)
    # ... outros campos ...
    
    # Relacionamentos
    tenant = db.relationship('Tenant', backref='moradores_saas')
    
    def __repr__(self):
        return f'<MoradorSaaS {self.nome_completo} - {self.tenant.nome}>' 