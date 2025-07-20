# Modelos de banco de dados (ex: usando SQLAlchemy) serão definidos aqui.
# Exemplo com SQLAlchemy:
# from app import db # Supondo que 'db = SQLAlchemy(app)' está em __init__.py
#
# class Morador(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     nome_completo = db.Column(db.String(200), nullable=False)
#     # ... outros campos ...
#
#     def __repr__(self):
#         return f'<Morador {self.nome_completo}>'

from datetime import datetime, timedelta
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Morador(db.Model):
    __tablename__ = 'moradores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(200), nullable=False)
    bloco = db.Column(db.String(10), nullable=False)
    apartamento = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    celular = db.Column(db.String(20), nullable=False)
    
    # Flag para identificar se é titular
    eh_titular = db.Column(db.Boolean, default=True, nullable=False)
    email_titular = db.Column(db.String(120), nullable=True)  # Só preenchido se não for titular
    
    # Dados da carteirinha
    data_ultima_validacao = db.Column(db.Date, nullable=True)
    data_vencimento = db.Column(db.Date, nullable=True)
    carteirinha_ativa = db.Column(db.Boolean, default=False, nullable=False)
    
    # Observações e anexos
    observacoes = db.Column(db.Text, nullable=True)
    
    # Controle de notificações
    notificacao_30_dias_enviada = db.Column(db.Boolean, default=False)
    notificacao_vencimento_enviada = db.Column(db.Boolean, default=False)
    
    # Timestamps
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com condomínio (mantido por compatibilidade)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), default=1)
    
    # NOVO: Multi-tenancy
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True, default=1)
    
    # Relacionamento com anexos
    anexos = db.relationship('AnexoMorador', backref='morador', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Morador {self.nome_completo}>'
    
    @property
    def status_carteirinha(self):
        """Retorna o status da carteirinha baseado na data de vencimento"""
        if not self.data_vencimento:
            return 'sem_carteirinha'
        
        hoje = datetime.now().date()
        diferenca = (self.data_vencimento - hoje).days
        
        if diferenca < 0:
            return 'vencida'
        elif diferenca <= 30:
            return 'a_vencer'
        elif diferenca <= 150:  # Menos de 5 meses
            return 'regular'
        else:
            return 'regular'
    
    @property
    def dias_para_vencer(self):
        """Retorna quantos dias restam para vencer"""
        if not self.data_vencimento:
            return None
        
        hoje = datetime.now().date()
        return (self.data_vencimento - hoje).days
    
    def validar_carteirinha(self, meses_validade=6):
        """Valida a carteirinha por X meses"""
        hoje = datetime.now().date()
        self.data_ultima_validacao = hoje
        self.data_vencimento = hoje + timedelta(days=meses_validade * 30)
        self.carteirinha_ativa = True
        self.notificacao_30_dias_enviada = False
        self.notificacao_vencimento_enviada = False
        self.data_atualizacao = datetime.utcnow()
    
    def get_email_notificacao(self):
        """Retorna o email para notificação (titular ou próprio)"""
        return self.email_titular if not self.eh_titular and self.email_titular else self.email
    
    @property
    def foto_carteirinha(self):
        """Retorna a foto da carteirinha (apenas uma)"""
        # Buscar primeiro anexo de imagem
        return self.anexos.filter(
            AnexoMorador.tipo_arquivo.in_(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'])
        ).first()
    
    @property
    def documentos(self):
        """Retorna todos os documentos/atestados"""
        # Buscar anexos que não são imagens
        return self.anexos.filter(
            ~AnexoMorador.tipo_arquivo.in_(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'])
        ).all()
    
    def tem_foto_carteirinha(self):
        """Verifica se tem foto da carteirinha"""
        return self.foto_carteirinha is not None

class AnexoMorador(db.Model):
    __tablename__ = 'anexos_moradores'
    
    id = db.Column(db.Integer, primary_key=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_original = db.Column(db.String(255), nullable=False)
    tamanho_arquivo = db.Column(db.Integer, nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    # tipo_anexo = db.Column(db.String(20), nullable=False, default='documento')  # Temporariamente comentado
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NOVO: Multi-tenancy
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True, default=1)
    
    def __repr__(self):
        return f'<AnexoMorador {self.nome_original}>'
    
    @property
    def is_foto_carteirinha(self):
        """Verifica se é uma foto da carteirinha"""
        # Usar tipo de arquivo como fallback
        return self.tipo_arquivo.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    
    @property
    def is_documento(self):
        """Verifica se é um documento"""
        # Usar tipo de arquivo como fallback
        return self.tipo_arquivo.lower() not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

class LogNotificacao(db.Model):
    __tablename__ = 'log_notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    tipo_notificacao = db.Column(db.String(50), nullable=False)  # '30_dias', 'vencimento'
    email_enviado = db.Column(db.String(120), nullable=False)
    status_envio = db.Column(db.String(20), nullable=False)  # 'sucesso', 'erro'
    mensagem_erro = db.Column(db.Text, nullable=True)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NOVO: Multi-tenancy
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True, default=1)
    
    def __repr__(self):
        return f'<LogNotificacao {self.tipo_notificacao} - {self.email_enviado}>'

class ConfiguracaoSistema(db.Model):
    """Configurações gerais do sistema"""
    __tablename__ = 'configuracao_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)
    descricao = db.Column(db.String(255))
    tipo = db.Column(db.String(20), default='texto')  # texto, numero, booleano, email, senha
    categoria = db.Column(db.String(50), default='geral')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_modificacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_valor(chave, default=None):
        """Obter valor de uma configuração"""
        config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
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
    def set_valor(chave, valor, descricao=None, tipo='texto', categoria='geral'):
        """Definir valor de uma configuração"""
        config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
        if config:
            config.valor = str(valor)
            config.data_modificacao = datetime.utcnow()
        else:
            config = ConfiguracaoSistema(
                chave=chave,
                valor=str(valor),
                descricao=descricao,
                tipo=tipo,
                categoria=categoria
            )
            db.session.add(config)
        db.session.commit()
        return config

class Condominio(db.Model):
    """Informações do condomínio"""
    __tablename__ = 'condominio'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18))
    endereco = db.Column(db.Text)
    telefone = db.Column(db.String(20))
    email_administracao = db.Column(db.String(120))
    whatsapp = db.Column(db.String(20))
    horario_funcionamento = db.Column(db.String(100))
    
    # Personalização visual
    logo_filename = db.Column(db.String(100))
    cor_primaria = db.Column(db.String(7), default='#007bff')
    cor_secundaria = db.Column(db.String(7), default='#6c757d')
    
    # Configurações específicas
    dias_aviso_vencimento = db.Column(db.Integer, default=30)
    meses_validade_padrao = db.Column(db.Integer, default=12)
    permitir_dependentes = db.Column(db.Boolean, default=True)
    
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    moradores = db.relationship('Morador', backref='condominio_rel', lazy=True)

class Usuario(UserMixin, db.Model):
    """Modelo de usuário para autenticação"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)  # 'admin' ou 'salva_vidas'
    nome_completo = db.Column(db.String(200), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultimo_login = db.Column(db.DateTime)
    
    # NOVO: Multi-tenancy
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True, default=1)
    
    # NOVO: Sistema de permissões
    permissoes = db.Column(db.JSON, default={})
    cargo = db.Column(db.String(100), nullable=True)
    
    # Relacionamento com salva-vidas (se aplicável)
    salva_vidas_id = db.Column(db.Integer, db.ForeignKey('salva_vidas.id'), nullable=True)
    salva_vidas = db.relationship('SalvaVidas', backref='usuario', uselist=False)
    
    def set_password(self, password):
        """Define a senha do usuário"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.tipo_usuario == 'admin'
    
    def is_salva_vidas(self):
        """Verifica se o usuário é salva-vidas"""
        return self.tipo_usuario == 'salva_vidas'
    
    def can(self, permission):
        """Verifica se usuário tem permissão específica"""
        if not self.permissoes:
            return False
        return self.permissoes.get(permission, False)
    
    def is_admin_tenant(self):
        """Verifica se é admin do tenant"""
        return self.can('admin_tenant')
    
    def __repr__(self):
        return f'<Usuario {self.username}>'

class SalvaVidas(db.Model):
    """Gerenciamento dos salva-vidas da piscina"""
    __tablename__ = 'salva_vidas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados pessoais
    nome_completo = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.Date, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    
    # Dados profissionais
    data_contratacao = db.Column(db.Date, nullable=False)
    data_demissao = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='ativo', nullable=False)  # ativo, inativo, demitido, férias
    salario = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Certificações e qualificações
    certificacao_salvamento = db.Column(db.Boolean, default=False)
    certificacao_primeiros_socorros = db.Column(db.Boolean, default=False)
    data_vencimento_certificacao = db.Column(db.Date, nullable=True)
    outras_qualificacoes = db.Column(db.Text, nullable=True)
    
    # Horários de trabalho
    horario_trabalho = db.Column(db.Text, nullable=True)  # JSON ou texto livre
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    # Controle do sistema
    foto_filename = db.Column(db.String(100), nullable=True)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), default=1)
    
    # Timestamps
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    condominio = db.relationship('Condominio', backref='salva_vidas')
    
    def __repr__(self):
        return f'<SalvaVidas {self.nome_completo}>'
    
    @property
    def idade(self):
        """Calcula a idade baseada na data de nascimento"""
        if not self.data_nascimento:
            return None
        hoje = datetime.now().date()
        return hoje.year - self.data_nascimento.year - ((hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day))
    
    @property
    def tempo_servico(self):
        """Calcula o tempo de serviço em anos"""
        if not self.data_contratacao:
            return None
        fim = self.data_demissao if self.data_demissao else datetime.now().date()
        tempo = fim - self.data_contratacao
        return round(tempo.days / 365.25, 1)
    
    @property
    def certificacao_valida(self):
        """Verifica se as certificações estão válidas"""
        if not self.data_vencimento_certificacao:
            return None
        return self.data_vencimento_certificacao > datetime.now().date()
    
    @property
    def status_badge_class(self):
        """Retorna a classe CSS para o badge de status"""
        status_classes = {
            'ativo': 'bg-success',
            'inativo': 'bg-secondary', 
            'demitido': 'bg-danger',
            'férias': 'bg-warning',
            'licença': 'bg-info'
        }
        return status_classes.get(self.status, 'bg-secondary')

class LogAuditoria(db.Model):
    """Log de auditoria do sistema"""
    __tablename__ = 'log_auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    acao = db.Column(db.String(100), nullable=False)
    tabela = db.Column(db.String(50))
    registro_id = db.Column(db.Integer)
    detalhes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref='logs_auditoria')

class RegistroAcesso(db.Model):
    """Modelo para registrar entradas e saídas da piscina"""
    __tablename__ = 'registro_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    metodo = db.Column(db.String(20), nullable=False)  # 'manual', 'qrcode', 'barcode'
    guardiao = db.Column(db.String(100))  # Nome do guardião que registrou
    observacoes = db.Column(db.Text)
    ip_origem = db.Column(db.String(45))  # IP de onde foi registrado
    
    # NOVO: Multi-tenancy (COMENTADO ATÉ MIGRAÇÃO)
    # tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, default=1, index=True)
    
    # Relacionamento
    morador = db.relationship('Morador', backref=db.backref('registros_acesso', lazy=True, order_by='RegistroAcesso.data_hora.desc()'))
    # tenant = db.relationship('Tenant', backref='registros_acesso')  # COMENTADO ATÉ MIGRAÇÃO
    
    def __repr__(self):
        return f'<RegistroAcesso {self.morador.nome_completo} - {self.tipo} em {self.data_hora}>'
    
    @property
    def duracao_permanencia(self):
        """Calcula duração da permanência se houver entrada e saída"""
        if self.tipo == 'saida':
            # Buscar última entrada
            entrada = RegistroAcesso.query.filter_by(
                morador_id=self.morador_id,
                tipo='entrada'
            ).filter(
                RegistroAcesso.data_hora < self.data_hora
            ).order_by(RegistroAcesso.data_hora.desc()).first()
            
            if entrada:
                return self.data_hora - entrada.data_hora
        return None
    
    @staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id=None):
        """Verifica se o morador está atualmente na piscina"""
        from flask import g
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        ultimo_registro = RegistroAcesso.query.filter_by(
            morador_id=morador_id
            # tenant_id=tenant_id  # TEMPORARIAMENTE DESABILITADO
        ).order_by(RegistroAcesso.data_hora.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada' 

    @staticmethod
    def obter_moradores_na_piscina(tenant_id=None):
        """Retorna lista de moradores que estão atualmente na piscina"""
        from flask import g
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        # Subconsulta para obter o último registro de cada morador (SEM TENANT TEMPORÁRIO)
        subq = db.session.query(
            RegistroAcesso.morador_id,
            db.func.max(RegistroAcesso.data_hora).label('ultima_data')
        ).group_by(RegistroAcesso.morador_id).subquery()
        
        # Buscar registros que são entradas (SEM FILTRO TENANT TEMPORÁRIO)
        moradores_dentro = db.session.query(Morador).join(
            RegistroAcesso, Morador.id == RegistroAcesso.morador_id
        ).join(
            subq, db.and_(
                RegistroAcesso.morador_id == subq.c.morador_id,
                RegistroAcesso.data_hora == subq.c.ultima_data
            )
        ).filter(
            RegistroAcesso.tipo == 'entrada'
            # RegistroAcesso.tenant_id == tenant_id,  # TEMPORARIAMENTE DESABILITADO
            # Morador.tenant_id == tenant_id  # TEMPORARIAMENTE DESABILITADO
        ).all()
        
        return moradores_dentro


# ================================
# MODELOS SAAS MULTI-TENANT
# ================================

from flask import g

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
        plano = self.plano_atual
        if not plano:
            return False
        total_moradores = Morador.query.filter_by(tenant_id=self.id).count()
        return total_moradores < plano.limite_moradores
    
    def pode_adicionar_usuario(self):
        """Verifica se pode adicionar mais usuários"""
        plano = self.plano_atual
        if not plano:
            return False
        total_usuarios = Usuario.query.filter_by(tenant_id=self.id).count()
        return total_usuarios < plano.limite_usuarios
    
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
    
    # Relacionamentos
    tenant = db.relationship('Tenant', backref='cobrancas')
    
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

# Módulos do Sistema CondoTech Solutions
class Modulo(db.Model):
    """Módulos disponíveis no sistema CondoTech"""
    __tablename__ = 'modulos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    icone = db.Column(db.String(50), default='fas fa-cog')
    cor = db.Column(db.String(20), default='#007bff')
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    
    # Configurações do módulo
    config_json = db.Column(db.JSON, default={})
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModuloTenant(db.Model):
    """Módulos habilitados por tenant"""
    __tablename__ = 'modulos_tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulos.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    # Configurações específicas do tenant para este módulo
    configuracoes = db.Column(db.JSON, default={})
    
    # Timestamps
    data_ativacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_desativacao = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    tenant = db.relationship('Tenant', backref='modulos_ativos')
    modulo = db.relationship('Modulo', backref='tenants_ativos')
    
    # Índices
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'modulo_id', name='uq_tenant_modulo'),
    )


# Sistema de Manutenção & Chamados
class CategoriaManutencao(db.Model):
    """Categorias de manutenção"""
    __tablename__ = 'categorias_manutencao'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    cor = db.Column(db.String(20), default='#007bff')
    icone = db.Column(db.String(50), default='fas fa-tools')
    ativo = db.Column(db.Boolean, default=True)
    
    # Configurações
    tempo_resposta_horas = db.Column(db.Integer, default=24)
    prioridade_default = db.Column(db.String(20), default='media')
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)


class ChamadoManutencao(db.Model):
    """Chamados de manutenção"""
    __tablename__ = 'chamados_manutencao'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Informações básicas
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    local = db.Column(db.String(200), nullable=False)  # Apartamento, área comum, etc.
    
    # Relacionamentos
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_manutencao.id'), nullable=False)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Status e prioridade
    status = db.Column(db.String(20), default='aberto')  # aberto, em_andamento, aguardando, concluido, cancelado
    prioridade = db.Column(db.String(20), default='media')  # baixa, media, alta, urgente
    
    # Controle de tempo
    data_abertura = db.Column(db.DateTime, default=datetime.utcnow)
    data_inicio = db.Column(db.DateTime, nullable=True)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    prazo_estimado = db.Column(db.DateTime, nullable=True)
    
    # Informações técnicas
    diagnostico = db.Column(db.Text, nullable=True)
    solucao = db.Column(db.Text, nullable=True)
    observacoes_internas = db.Column(db.Text, nullable=True)
    
    # Avaliação
    avaliacao_atendimento = db.Column(db.Integer, nullable=True)  # 1-5
    comentario_avaliacao = db.Column(db.Text, nullable=True)
    
    # Custos
    custo_estimado = db.Column(db.Numeric(10, 2), nullable=True)
    custo_real = db.Column(db.Numeric(10, 2), nullable=True)
    aprovado_custo = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    categoria = db.relationship('CategoriaManutencao', backref='chamados')
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref='chamados_solicitados')
    responsavel = db.relationship('Usuario', foreign_keys=[responsavel_id], backref='chamados_responsavel')
    
    def gerar_numero(self):
        """Gera número único do chamado"""
        import random
        import string
        year = datetime.now().year
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"CH{year}{random_str}"
    
    @property
    def status_cor(self):
        cores = {
            'aberto': 'danger',
            'em_andamento': 'warning', 
            'aguardando': 'info',
            'concluido': 'success',
            'cancelado': 'secondary'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def prioridade_cor(self):
        cores = {
            'baixa': 'secondary',
            'media': 'primary',
            'alta': 'warning',
            'urgente': 'danger'
        }
        return cores.get(self.prioridade, 'secondary')
    
    @property
    def tempo_aberto(self):
        """Tempo desde abertura em horas"""
        if self.data_conclusao:
            return (self.data_conclusao - self.data_abertura).total_seconds() / 3600
        return (datetime.utcnow() - self.data_abertura).total_seconds() / 3600


class AnexoChamado(db.Model):
    """Anexos dos chamados"""
    __tablename__ = 'anexos_chamados'
    
    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados_manutencao.id'), nullable=False)
    
    # Informações do arquivo
    nome_original = db.Column(db.String(255), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho = db.Column(db.String(500), nullable=False)
    tipo_mime = db.Column(db.String(100), nullable=True)
    tamanho = db.Column(db.Integer, nullable=True)
    
    # Metadados
    tipo = db.Column(db.String(20), default='foto')  # foto, documento, video
    descricao = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    chamado = db.relationship('ChamadoManutencao', backref='anexos')


class HistoricoChamado(db.Model):
    """Histórico de mudanças nos chamados"""
    __tablename__ = 'historico_chamados'
    
    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados_manutencao.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Informações da mudança
    acao = db.Column(db.String(50), nullable=False)  # criado, atualizado, comentario, etc
    campo_alterado = db.Column(db.String(50), nullable=True)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_novo = db.Column(db.Text, nullable=True)
    comentario = db.Column(db.Text, nullable=True)
    
    # Timestamp
    data_acao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    chamado = db.relationship('ChamadoManutencao', backref='historico')
    usuario = db.relationship('Usuario', backref='acoes_chamados')