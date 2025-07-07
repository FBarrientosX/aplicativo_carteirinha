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
    
    # Relacionamento com condomínio
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), default=1)
    
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

class AnexoMorador(db.Model):
    __tablename__ = 'anexos_moradores'
    
    id = db.Column(db.Integer, primary_key=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_original = db.Column(db.String(255), nullable=False)
    tamanho_arquivo = db.Column(db.Integer, nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AnexoMorador {self.nome_original}>'

class LogNotificacao(db.Model):
    __tablename__ = 'log_notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    tipo_notificacao = db.Column(db.String(50), nullable=False)  # '30_dias', 'vencimento'
    email_enviado = db.Column(db.String(120), nullable=False)
    status_envio = db.Column(db.String(20), nullable=False)  # 'sucesso', 'erro'
    mensagem_erro = db.Column(db.Text, nullable=True)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    
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

class Usuario(db.Model):
    """Usuários do sistema"""
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255))
    
    # Permissões
    tipo_usuario = db.Column(db.String(20), default='admin')  # admin, operador, visualizador
    ativo = db.Column(db.Boolean, default=True)
    
    # Auditoria
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime)
    
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'))
    condominio = db.relationship('Condominio', backref='usuarios')

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
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
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
    
    # Relacionamento
    morador = db.relationship('Morador', backref=db.backref('registros_acesso', lazy=True, order_by='RegistroAcesso.data_hora.desc()'))
    
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
    def morador_esta_na_piscina(morador_id):
        """Verifica se o morador está atualmente na piscina"""
        ultimo_registro = RegistroAcesso.query.filter_by(
            morador_id=morador_id
        ).order_by(RegistroAcesso.data_hora.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada'
    
    @staticmethod
    def obter_moradores_na_piscina():
        """Retorna lista de moradores que estão atualmente na piscina"""
        # Subconsulta para obter o último registro de cada morador
        subq = db.session.query(
            RegistroAcesso.morador_id,
            db.func.max(RegistroAcesso.data_hora).label('ultima_data')
        ).group_by(RegistroAcesso.morador_id).subquery()
        
        # Buscar registros que são entradas
        moradores_dentro = db.session.query(Morador).join(
            RegistroAcesso, Morador.id == RegistroAcesso.morador_id
        ).join(
            subq, db.and_(
                RegistroAcesso.morador_id == subq.c.morador_id,
                RegistroAcesso.data_hora == subq.c.ultima_data
            )
        ).filter(RegistroAcesso.tipo == 'entrada').all()
        
        return moradores_dentro