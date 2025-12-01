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
    # Multi-tenancy
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
    
    # Dados básicos
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    endereco = db.Column(db.Text, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    
    # E-mails de configuração
    email_administracao = db.Column(db.String(120), nullable=False)
    email_portaria = db.Column(db.String(120), nullable=True)
    email_sindico = db.Column(db.String(120), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    
    # Documentos (JSON com URLs ou paths)
    documentos = db.Column(db.JSON, default=[])
    
    # Personalização visual
    logo_filename = db.Column(db.String(100), nullable=True)
    cor_primaria = db.Column(db.String(7), default='#007bff')
    cor_secundaria = db.Column(db.String(7), default='#6c757d')
    
    # Configurações específicas
    horario_funcionamento = db.Column(db.String(100), nullable=True)
    dias_aviso_vencimento = db.Column(db.Integer, default=30)
    meses_validade_padrao = db.Column(db.Integer, default=12)
    permitir_dependentes = db.Column(db.Boolean, default=True)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    unidades = db.relationship('Unidade', backref='condominio', lazy=True, cascade='all, delete-orphan')
    moradores = db.relationship('Morador', backref='condominio_rel', lazy=True)
    
    def __repr__(self):
        return f'<Condominio {self.nome}>'


class Unidade(db.Model):
    """Unidades do condomínio (Apartamentos, Coberturas, Lojas)"""
    __tablename__ = 'unidades'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
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
    
    @property
    def bloco_apto(self):
        """Retorna bloco/apto formatado"""
        return f"{self.bloco}/{self.apartamento}"

class Usuario(UserMixin, db.Model):
    """Modelo de usuário para autenticação"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)  
    # Valores: 'admin', 'sindico', 'morador', 'portaria', 'funcionario', 'salva_vidas'
    nome_completo = db.Column(db.String(200), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    email_verificado = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultimo_login = db.Column(db.DateTime, nullable=True)
    data_ultimo_acesso = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True, default=1)
    
    # Sistema de permissões
    permissoes = db.Column(db.JSON, default={})
    cargo = db.Column(db.String(100), nullable=True)
    
    # Relacionamento com Unidade (se for morador)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=True)
    unidade = db.relationship('Unidade', backref='usuarios')
    
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
    
    def is_sindico(self):
        """Verifica se o usuário é síndico"""
        return self.tipo_usuario == 'sindico'
    
    def is_portaria(self):
        """Verifica se o usuário é portaria"""
        return self.tipo_usuario == 'portaria'
    
    def is_funcionario(self):
        """Verifica se o usuário é funcionário"""
        return self.tipo_usuario == 'funcionario'
    
    def is_morador(self):
        """Verifica se o usuário é morador"""
        return self.tipo_usuario == 'morador'
    
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
    
    # Multi-tenancy
    # NOTA: tenant_id será adicionado via migração
    # Se a coluna não existir ainda, o código deve usar queries SQL diretas
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True, default=1)
    
    # Relacionamento
    morador = db.relationship('Morador', backref=db.backref('registros_acesso', lazy=True, order_by='RegistroAcesso.data_hora.desc()'))
    
    def __init__(self, **kwargs):
        """Construtor que garante tenant_id"""
        # Garantir que tenant_id seja definido
        if 'tenant_id' not in kwargs:
            from flask import g
            kwargs['tenant_id'] = getattr(g, 'tenant_id', 1)
        
        # Chamar construtor pai
        super().__init__(**kwargs)
    
    @property
    def tenant_id_safe(self):
        """Propriedade segura para tenant_id"""
        try:
            return getattr(self, 'tenant_id', 1)
        except Exception:
            return 1
    
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
        from sqlalchemy import text
        
        # Verificar se tenant_id existe na tabela (PATCH EMERGÊNCIA)
        try:
            db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1"))
            has_tenant_id = True
        except Exception:
            has_tenant_id = False
        
        if not has_tenant_id:
            # Versão sem tenant_id - usar SQL direto
            result = db.session.execute(text("""
                SELECT tipo, data_hora
                FROM registro_acesso
                WHERE morador_id = :morador_id
                ORDER BY data_hora DESC
                LIMIT 1
            """), {"morador_id": morador_id})
            
            row = result.fetchone()
            if row:
                return row[0] == 'entrada'  # tipo == 'entrada'
            return False
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        ultimo_registro = RegistroAcesso.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id
        ).order_by(RegistroAcesso.data_hora.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada' 

    @staticmethod
    def obter_moradores_na_piscina(tenant_id=None):
        """Retorna lista de moradores que estão atualmente na piscina"""
        from flask import g
        from sqlalchemy import text
        
        # Verificar se tenant_id existe na tabela (PATCH EMERGÊNCIA)
        try:
            db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1"))
            has_tenant_id = True
        except Exception:
            has_tenant_id = False
        
        if not has_tenant_id:
            # Versão sem tenant_id (compatibilidade)
            subq = db.session.query(
                RegistroAcesso.morador_id,
                db.func.max(RegistroAcesso.data_hora).label('ultima_data')
            ).group_by(RegistroAcesso.morador_id).subquery()
            
            moradores_dentro = db.session.query(Morador).join(
                RegistroAcesso, Morador.id == RegistroAcesso.morador_id
            ).join(
                subq, db.and_(
                    RegistroAcesso.morador_id == subq.c.morador_id,
                    RegistroAcesso.data_hora == subq.c.ultima_data
                )
            ).filter(RegistroAcesso.tipo == 'entrada').all()
            
            return moradores_dentro
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        # Subconsulta para obter o último registro de cada morador do tenant
        subq = db.session.query(
            RegistroAcesso.morador_id,
            db.func.max(RegistroAcesso.data_hora).label('ultima_data')
        ).filter(RegistroAcesso.tenant_id == tenant_id).group_by(RegistroAcesso.morador_id).subquery()
        
        # Buscar registros que são entradas no tenant específico
        moradores_dentro = db.session.query(Morador).join(
            RegistroAcesso, Morador.id == RegistroAcesso.morador_id
        ).join(
            subq, db.and_(
                RegistroAcesso.morador_id == subq.c.morador_id,
                RegistroAcesso.data_hora == subq.c.ultima_data
            )
        ).filter(
            RegistroAcesso.tipo == 'entrada',
            RegistroAcesso.tenant_id == tenant_id,
            Morador.tenant_id == tenant_id
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


# ================================
# MÓDULOS ADICIONAIS - SIMILARES AO MYCOND
# ================================

class EspacoComum(db.Model):
    """Espaços comuns do condomínio disponíveis para reserva"""
    __tablename__ = 'espacos_comuns'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Informações do espaço
    nome = db.Column(db.String(200), nullable=False)  # Ex: Salão de Festas, Churrasqueira, Academia
    descricao = db.Column(db.Text, nullable=True)
    capacidade_maxima = db.Column(db.Integer, nullable=True)  # Quantidade de pessoas
    area_metros = db.Column(db.Numeric(10, 2), nullable=True)  # Área em m²
    
    # Configurações de reserva
    tempo_antecipacao_horas = db.Column(db.Integer, default=24)  # Horas mínimas para reservar
    tempo_maximo_horas = db.Column(db.Integer, default=4)  # Tempo máximo de reserva
    valor_taxa = db.Column(db.Numeric(10, 2), default=0)  # Taxa de uso (opcional)
    requer_aprovacao = db.Column(db.Boolean, default=False)  # Requer aprovação do síndico
    
    # Regras
    horario_inicio = db.Column(db.Time, nullable=True)  # Horário de início permitido
    horario_fim = db.Column(db.Time, nullable=True)  # Horário de fim permitido
    dias_semana_disponiveis = db.Column(db.String(20), default='0123456')  # 0=Dom, 6=Sáb
    
    # Status e configuração
    ativo = db.Column(db.Boolean, default=True)
    fotos = db.Column(db.JSON, default=[])  # URLs das fotos
    equipamentos = db.Column(db.Text, nullable=True)  # Lista de equipamentos disponíveis
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    reservas = db.relationship('ReservaEspaco', backref='espaco', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EspacoComum {self.nome}>'


class ReservaEspaco(db.Model):
    """Reservas de espaços comuns"""
    __tablename__ = 'reservas_espacos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)  # Ex: RES2024001
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    espaco_id = db.Column(db.Integer, db.ForeignKey('espacos_comuns.id'), nullable=False)
    
    # Informações da reserva
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    data_reserva = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    quantidade_pessoas = db.Column(db.Integer, default=1)
    
    # Status e aprovação
    status = db.Column(db.String(20), default='pendente')  # pendente, aprovado, recusado, cancelado, concluido
    aprovado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    motivo_recusa = db.Column(db.Text, nullable=True)
    
    # Informações adicionais
    finalidade = db.Column(db.String(200), nullable=True)  # Ex: Aniversário, Reunião familiar
    observacoes = db.Column(db.Text, nullable=True)
    taxa_paga = db.Column(db.Boolean, default=False)
    valor_pago = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Timestamps
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='reservas_espacos')
    aprovador = db.relationship('Usuario', foreign_keys=[aprovado_por])
    
    def gerar_numero(self):
        """Gera número único da reserva"""
        import random
        import string
        year = datetime.now().year
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"RES{year}{random_str}"
    
    @property
    def status_cor(self):
        cores = {
            'pendente': 'warning',
            'aprovado': 'success',
            'recusado': 'danger',
            'cancelado': 'secondary',
            'concluido': 'info'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def esta_em_andamento(self):
        """Verifica se a reserva está em andamento"""
        agora = datetime.now()
        data_hora_inicio = datetime.combine(self.data_reserva, self.hora_inicio)
        data_hora_fim = datetime.combine(self.data_reserva, self.hora_fim)
        
        return data_hora_inicio <= agora <= data_hora_fim and self.status == 'aprovado'
    
    def __repr__(self):
        return f'<ReservaEspaco {self.numero} - {self.espaco.nome}>'


class Visitante(db.Model):
    """Controle de visitantes e funcionários"""
    __tablename__ = 'visitantes'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Informações do visitante
    nome_completo = db.Column(db.String(200), nullable=False)
    documento = db.Column(db.String(20), nullable=True)  # CPF ou RG
    tipo_documento = db.Column(db.String(20), default='rg')  # rg, cpf, cnh
    telefone = db.Column(db.String(20), nullable=True)
    veiculo_placa = db.Column(db.String(10), nullable=True)
    veiculo_modelo = db.Column(db.String(100), nullable=True)
    
    # Tipo de visitante
    tipo = db.Column(db.String(20), nullable=False)  # visitante, funcionario, prestador
    empresa = db.Column(db.String(200), nullable=True)  # Se for prestador ou funcionário
    
    # Relacionamento com morador
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    apartamento_destino = db.Column(db.String(10), nullable=False)  # Ex: 101, 205
    
    # Controle de acesso
    data_entrada = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_saida_prevista = db.Column(db.DateTime, nullable=True)
    data_saida_real = db.Column(db.DateTime, nullable=True)
    autorizado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='em_visita')  # em_visita, saiu, expirado
    entrada_autorizada = db.Column(db.Boolean, default=True)
    observacoes = db.Column(db.Text, nullable=True)
    
    # Foto (opcional)
    foto_url = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='visitantes')
    autorizador = db.relationship('Usuario', foreign_keys=[autorizado_por], backref='visitantes_autorizados')
    
    @property
    def esta_dentro(self):
        """Verifica se o visitante ainda está no condomínio"""
        return self.status == 'em_visita' and self.entrada_autorizada
    
    @property
    def tempo_permanencia(self):
        """Calcula tempo de permanência"""
        if self.data_saida_real:
            return self.data_saida_real - self.data_entrada
        elif self.data_entrada:
            return datetime.utcnow() - self.data_entrada
        return None
    
    def __repr__(self):
        return f'<Visitante {self.nome_completo} - {self.apartamento_destino}>'


class Encomenda(db.Model):
    """Portal de encomendas - Controle de entregas"""
    __tablename__ = 'encomendas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)  # Ex: ENC2024001
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Informações da encomenda
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    transportadora = db.Column(db.String(200), nullable=True)  # Ex: Correios, Mercado Livre
    codigo_rastreamento = db.Column(db.String(100), nullable=True)
    descricao = db.Column(db.Text, nullable=True)  # Descrição do produto
    quantidade_pacotes = db.Column(db.Integer, default=1)
    
    # Status e controle
    status = db.Column(db.String(20), default='aguardando')  # aguardando, recebida, entregue, retirada, devolvida
    data_recebimento = db.Column(db.DateTime, nullable=True)
    data_retirada = db.Column(db.DateTime, nullable=True)
    retirado_por = db.Column(db.String(200), nullable=True)  # Nome de quem retirou
    documento_retirada = db.Column(db.String(20), nullable=True)  # Documento de quem retirou
    
    # Localização
    local_armazenamento = db.Column(db.String(100), nullable=True)  # Ex: Portaria, Sala de Encomendas
    observacoes = db.Column(db.Text, nullable=True)
    
    # Notificações
    notificacao_enviada = db.Column(db.Boolean, default=False)
    data_notificacao = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='encomendas')
    
    def gerar_numero(self):
        """Gera número único da encomenda"""
        import random
        import string
        year = datetime.now().year
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"ENC{year}{random_str}"
    
    @property
    def status_cor(self):
        cores = {
            'aguardando': 'warning',
            'recebida': 'info',
            'entregue': 'success',
            'retirada': 'primary',
            'devolvida': 'danger'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def dias_aguardando(self):
        """Dias desde o recebimento"""
        if self.data_recebimento:
            return (datetime.utcnow() - self.data_recebimento).days
        return None
    
    def __repr__(self):
        return f'<Encomenda {self.numero} - {self.morador.nome_completo}>'


# ======= Lista de Convidados (Eventos em Reservas) =======
class ListaConvidado(db.Model):
    """Convidados vinculados a uma reserva de espaço"""
    __tablename__ = 'lista_convidados'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, default=1)
    reserva_id = db.Column(db.Integer, db.ForeignKey('reservas_espacos.id'), nullable=False)

    nome = db.Column(db.String(200), nullable=False)
    documento = db.Column(db.String(20), nullable=True)
    autorizado = db.Column(db.Boolean, default=True)

    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reserva = db.relationship('ReservaEspaco', backref='convidados')

    def __repr__(self):
        return f'<Convidado {self.nome} - Reserva {self.reserva_id}>'


# ======= Ocorrências =======
class Ocorrencia(db.Model):
    __tablename__ = 'ocorrencias'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, default=1)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)

    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='aberta')  # aberta, em_analise, resolvida, arquivada

    foto_nome = db.Column(db.String(255), nullable=True)
    foto_caminho = db.Column(db.String(500), nullable=True)

    data_abertura = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_fechamento = db.Column(db.DateTime, nullable=True)

    morador = db.relationship('Morador')

    def __repr__(self):
        return f'<Ocorrencia {self.titulo} - {self.status}>'


# ======= Achados e Perdidos =======
class AchadoPerdido(db.Model):
    __tablename__ = 'achados_perdidos'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, default=1)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)

    tipo = db.Column(db.String(20), nullable=False)  # achado, perdido
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    local = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='aberto')  # aberto, devolvido, resolvido

    foto_nome = db.Column(db.String(255), nullable=True)
    foto_caminho = db.Column(db.String(500), nullable=True)

    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    morador = db.relationship('Morador')

    def __repr__(self):
        return f'<AchadoPerdido {self.tipo}:{self.titulo}>'


# ======= Votação (Assembleias) =======
class Assembleia(db.Model):
    __tablename__ = 'assembleias'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    inicio = db.Column(db.DateTime, nullable=False)
    fim = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='aberta')  # aberta, fechada, agendada

    pautas = db.relationship('Pauta', backref='assembleia', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Assembleia {self.titulo}>'


class Pauta(db.Model):
    __tablename__ = 'pautas'

    id = db.Column(db.Integer, primary_key=True)
    assembleia_id = db.Column(db.Integer, db.ForeignKey('assembleias.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    votos = db.relationship('Voto', backref='pauta', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Pauta {self.titulo}>'


class Voto(db.Model):
    __tablename__ = 'votos'

    id = db.Column(db.Integer, primary_key=True)
    pauta_id = db.Column(db.Integer, db.ForeignKey('pautas.id'), nullable=False)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    escolha = db.Column(db.String(10), nullable=False)  # sim, nao, abstenção
    data_voto = db.Column(db.DateTime, default=datetime.utcnow)

    morador = db.relationship('Morador')

    __table_args__ = (
        db.UniqueConstraint('pauta_id', 'morador_id', name='uq_voto_unico'),
    )

    def __repr__(self):
        return f'<Voto {self.escolha}>'

# Importa modelos dos módulos para que o Alembic os reconheça
from app.modules.piscina import models as piscina_models  # noqa: F401,E402


# ======= Atividades/Inscrições =======
class Atividade(db.Model):
    __tablename__ = 'atividades'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    exige_pagamento = db.Column(db.Boolean, default=False)
    valor_taxa = db.Column(db.Numeric(10, 2), nullable=True)

    turmas = db.relationship('TurmaAtividade', backref='atividade', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Atividade {self.nome}>'


class TurmaAtividade(db.Model):
    __tablename__ = 'turmas_atividade'

    id = db.Column(db.Integer, primary_key=True)
    atividade_id = db.Column(db.Integer, db.ForeignKey('atividades.id'), nullable=False)
    nome_turma = db.Column(db.String(200), nullable=False)
    horario = db.Column(db.String(100), nullable=True)
    vagas = db.Column(db.Integer, default=0)

    inscricoes = db.relationship('InscricaoAtividade', backref='turma', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Turma {self.nome_turma}>'


class InscricaoAtividade(db.Model):
    __tablename__ = 'inscricoes_atividade'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas_atividade.id'), nullable=False)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='ativa')  # ativa, cancelada
    pago = db.Column(db.Boolean, default=False)

    morador = db.relationship('Morador')

    __table_args__ = (
        db.UniqueConstraint('turma_id', 'morador_id', name='uq_inscricao_unica'),
    )

    def __repr__(self):
        return f'<Inscricao {self.turma_id}-{self.morador_id}>'


class Classificado(db.Model):
    """Classificados - Marketplace para condôminos divulgarem produtos e serviços"""
    __tablename__ = 'classificados'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Informações do anúncio
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # produto, servico
    categoria = db.Column(db.String(100), nullable=True)  # Ex: Limpeza, Manutenção, Alimentação
    
    # Informações de contato
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    
    # Preços e valores
    preco = db.Column(db.Numeric(10, 2), nullable=True)  # Preço do produto/serviço
    tipo_preco = db.Column(db.String(20), nullable=True)  # fixo, negociavel, sob_consulta
    
    # Status e controle
    status = db.Column(db.String(20), default='ativo')  # ativo, pausado, vendido, encerrado
    destaque = db.Column(db.Boolean, default=False)  # Anúncio em destaque
    visualizacoes = db.Column(db.Integer, default=0)  # Contador de visualizações
    
    # Localização (opcional)
    apartamento = db.Column(db.String(10), nullable=True)  # Bloco-Apartamento do anunciante
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_expiracao = db.Column(db.DateTime, nullable=True)  # Data de expiração do anúncio
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='classificados')
    fotos = db.relationship('FotoClassificado', backref='classificado', lazy=True, cascade='all, delete-orphan')
    avaliacoes = db.relationship('AvaliacaoClassificado', backref='classificado', lazy=True, cascade='all, delete-orphan')
    
    @property
    def avaliacao_media(self):
        """Calcula a média das avaliações"""
        if not self.avaliacoes:
            return 0.0
        avaliacoes_positivas = [a for a in self.avaliacoes if a.nota is not None]
        if not avaliacoes_positivas:
            return 0.0
        soma = sum(a.nota for a in avaliacoes_positivas)
        return round(soma / len(avaliacoes_positivas), 1)
    
    @property
    def total_avaliacoes(self):
        """Total de avaliações"""
        return len([a for a in self.avaliacoes if a.nota is not None])
    
    @property
    def status_cor(self):
        cores = {
            'ativo': 'success',
            'pausado': 'warning',
            'vendido': 'info',
            'encerrado': 'secondary'
        }
        return cores.get(self.status, 'secondary')
    
    def incrementar_visualizacao(self):
        """Incrementa contador de visualizações"""
        self.visualizacoes += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<Classificado {self.titulo} - {self.morador.nome_completo}>'


class FotoClassificado(db.Model):
    """Fotos dos classificados"""
    __tablename__ = 'fotos_classificados'
    
    id = db.Column(db.Integer, primary_key=True)
    classificado_id = db.Column(db.Integer, db.ForeignKey('classificados.id'), nullable=False)
    
    # Informações do arquivo
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    nome_original = db.Column(db.String(255), nullable=False)
    tamanho = db.Column(db.Integer, nullable=True)
    ordem = db.Column(db.Integer, default=0)  # Ordem de exibição
    
    # Timestamps
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FotoClassificado {self.nome_original}>'


class AvaliacaoClassificado(db.Model):
    """Avaliações e comentários dos classificados"""
    __tablename__ = 'avaliacoes_classificados'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    classificado_id = db.Column(db.Integer, db.ForeignKey('classificados.id'), nullable=False)
    
    # Informações da avaliação
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)  # Quem avaliou
    nota = db.Column(db.Integer, nullable=True)  # 1 a 5 estrelas
    comentario = db.Column(db.Text, nullable=True)
    
    # Indicadores de experiência
    comprou = db.Column(db.Boolean, default=False)  # Comprou o produto/serviço
    utilizou = db.Column(db.Boolean, default=False)  # Utilizou o serviço
    
    # Status
    aprovado = db.Column(db.Boolean, default=True)  # Avaliação aprovada (moderação)
    
    # Timestamps
    data_avaliacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='avaliacoes_feitas')
    
    @property
    def nota_estrelas(self):
        """Retorna HTML com estrelas"""
        if not self.nota:
            return ""
        estrelas = "★" * self.nota + "☆" * (5 - self.nota)
        return estrelas
    
    def __repr__(self):
        return f'<AvaliacaoClassificado {self.nota} estrelas - {self.morador.nome_completo}>'