"""
Modelos específicos do módulo Piscina
"""
from datetime import datetime
from app import db


class CarteirinhaPiscina(db.Model):
    __tablename__ = 'carteirinhas_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    
    data_emissao = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    data_validade = db.Column(db.Date, nullable=False)
    aprovada = db.Column(db.Boolean, default=False)
    ativa = db.Column(db.Boolean, default=True)
    
    qr_code = db.Column(db.String(500), nullable=False)
    qr_code_image = db.Column(db.String(500), nullable=True)
    
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    morador = db.relationship('Morador', backref='carteirinhas_piscina')
    
    @property
    def esta_valida(self):
        hoje = datetime.utcnow().date()
        return self.ativa and self.aprovada and self.data_validade >= hoje


class RegistroAcessoPiscina(db.Model):
    __tablename__ = 'registros_acesso_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    carteirinha_id = db.Column(db.Integer, db.ForeignKey('carteirinhas_piscina.id'), nullable=True)
    salva_vidas_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    tipo = db.Column(db.String(10), nullable=False)  # entrada/saida
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    metodo = db.Column(db.String(20), nullable=False, default='manual')
    
    tempo_permanencia_minutos = db.Column(db.Integer, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ip_origem = db.Column(db.String(45), nullable=True)
    
    morador = db.relationship('Morador', backref='registros_piscina')
    carteirinha = db.relationship('CarteirinhaPiscina', backref='registros')
    salva_vidas = db.relationship('Usuario', backref='registros_salva_vidas')
    
    @staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id=1):
        ultimo = RegistroAcessoPiscina.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id
        ).order_by(RegistroAcessoPiscina.timestamp.desc()).first()
        return ultimo and ultimo.tipo == 'entrada'
    
    @staticmethod
    def calcular_tempo_permanencia(entrada, saida):
        if not entrada or not saida:
            return None
        diferenca = saida.timestamp - entrada.timestamp
        minutos = int(diferenca.total_seconds() / 60)
        saida.tempo_permanencia_minutos = minutos
        db.session.commit()
        return minutos


class PlantaoSalvaVidas(db.Model):
    __tablename__ = 'plantoes_salva_vidas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
    salva_vidas_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    data_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='ativo')  # ativo/finalizado
    observacoes = db.Column(db.Text, nullable=True)
    
    salva_vidas = db.relationship('Usuario', backref='plantoes_registrados')
    
    @staticmethod
    def plantao_ativo(tenant_id):
        return PlantaoSalvaVidas.query.filter_by(tenant_id=tenant_id, status='ativo').first()
    
    def finalizar(self):
        self.data_fim = datetime.utcnow()
        self.status = 'finalizado'
        db.session.commit()


class OcorrenciaPiscina(db.Model):
    __tablename__ = 'ocorrencias_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
    salva_vidas_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=True)
    
    tipo = db.Column(db.String(50), nullable=False)
    severidade = db.Column(db.String(20), nullable=False, default='baixa')
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    fotos = db.Column(db.JSON, default=[])
    status = db.Column(db.String(20), default='aberta')
    
    data_ocorrencia = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_resolucao = db.Column(db.DateTime, nullable=True)
    
    salva_vidas = db.relationship('Usuario', foreign_keys=[salva_vidas_id])
    morador = db.relationship('Morador', foreign_keys=[morador_id])
"""
Modelos do Módulo Piscina
"""
from datetime import datetime, timedelta
from app import db
import os
import qrcode
from io import BytesIO


class CarteirinhaPiscina(db.Model):
    """Carteirinha de acesso à piscina"""
    __tablename__ = 'carteirinhas_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
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
    
    def __repr__(self):
        return f'<CarteirinhaPiscina {self.morador_id} - {self.data_validade}>'
    
    def gerar_qr_code(self):
        """Gera QR Code único para a carteirinha"""
        # Dados do QR Code
        data = f"PISCINA:{self.tenant_id}:{self.morador_id}:{self.id}"
        
        # Gerar QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salvar imagem
        upload_dir = os.path.join('app', 'static', 'uploads', 'carteirinhas')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = f"carteirinha_{self.id}_{self.morador_id}.png"
        filepath = os.path.join(upload_dir, filename)
        
        img.save(filepath)
        
        # Salvar path relativo
        self.qr_code = data
        self.qr_code_image = f"uploads/carteirinhas/{filename}"
        
        db.session.commit()
        
        return filepath
    
    @property
    def esta_valida(self):
        """Verifica se carteirinha está válida"""
        hoje = datetime.now().date()
        return self.ativa and self.aprovada and self.data_validade >= hoje


class RegistroAcessoPiscina(db.Model):
    """Registro de entrada/saída na piscina"""
    __tablename__ = 'registros_acesso_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
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
    
    def __repr__(self):
        return f'<RegistroAcessoPiscina {self.morador_id} - {self.tipo} em {self.timestamp}>'
    
    @staticmethod
    def calcular_tempo_permanencia(morador_id, entrada_id, saida_id, tenant_id=None):
        """Calcula tempo de permanência entre entrada e saída"""
        from flask import g
        tenant_id = tenant_id or getattr(g, 'tenant_id', 1)
        
        entrada = RegistroAcessoPiscina.query.filter_by(
            id=entrada_id,
            tenant_id=tenant_id
        ).first()
        saida = RegistroAcessoPiscina.query.filter_by(
            id=saida_id,
            tenant_id=tenant_id
        ).first()
        
        if entrada and saida and entrada.tipo == 'entrada' and saida.tipo == 'saida':
            diferenca = saida.timestamp - entrada.timestamp
            minutos = int(diferenca.total_seconds() / 60)
            
            saida.tempo_permanencia_minutos = minutos
            db.session.commit()
            
            return minutos
        return None
    
    @staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id=None):
        """Verifica se morador está atualmente na piscina"""
        from flask import g
        tenant_id = tenant_id or getattr(g, 'tenant_id', 1)
        
        ultimo_registro = RegistroAcessoPiscina.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id
        ).order_by(RegistroAcessoPiscina.timestamp.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada'
    
    @staticmethod
    def obter_moradores_na_piscina(tenant_id=None):
        """Retorna lista de moradores que estão atualmente na piscina"""
        from flask import g
        from sqlalchemy import and_
        tenant_id = tenant_id or getattr(g, 'tenant_id', 1)
        
        # Subconsulta para obter último registro de cada morador
        from sqlalchemy import func
        subq = db.session.query(
            RegistroAcessoPiscina.morador_id,
            func.max(RegistroAcessoPiscina.timestamp).label('ultima_data')
        ).filter_by(tenant_id=tenant_id).group_by(RegistroAcessoPiscina.morador_id).subquery()
        
        # Buscar registros que são entradas
        from app.models import Morador
        moradores_dentro = db.session.query(Morador).join(
            RegistroAcessoPiscina, Morador.id == RegistroAcessoPiscina.morador_id
        ).join(
            subq, and_(
                RegistroAcessoPiscina.morador_id == subq.c.morador_id,
                RegistroAcessoPiscina.timestamp == subq.c.ultima_data
            )
        ).filter(
            RegistroAcessoPiscina.tipo == 'entrada',
            RegistroAcessoPiscina.tenant_id == tenant_id
        ).all()
        
        return moradores_dentro


class OcorrenciaPiscina(db.Model):
    """Ocorrências registradas na piscina"""
    __tablename__ = 'ocorrencias_piscina'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
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
    
    def __repr__(self):
        return f'<OcorrenciaPiscina {self.titulo} - {self.status}>'


class PlantaoSalvaVidas(db.Model):
    """Plantões dos salva-vidas"""
    __tablename__ = 'plantoes_salva_vidas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True, default=1)
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
    
    def __repr__(self):
        return f'<PlantaoSalvaVidas {self.salva_vidas_id} - {self.status}>'
    
    @staticmethod
    def obter_plantao_ativo(tenant_id=None):
        """Retorna plantão ativo do tenant (apenas um por vez)"""
        from flask import g
        tenant_id = tenant_id or getattr(g, 'tenant_id', 1)
        
        return PlantaoSalvaVidas.query.filter_by(
            tenant_id=tenant_id,
            status='ativo'
        ).first()
    
    def finalizar(self):
        """Finaliza o plantão"""
        self.data_fim = datetime.utcnow()
        self.status = 'finalizado'
        db.session.commit()
